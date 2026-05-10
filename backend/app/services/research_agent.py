import asyncio
import re
from app.utils.eval_utils import run_quality_check
from langchain_openai import ChatOpenAI
from app.services.tools import search_pubmed_metadata, fetch_pubmed_abstracts, search_openalex, search_clinical_trials, fetch_pmc_fulltext
from app.utils.ranking import normalize_results, rank_and_filter
from app.config.database import (
    get_chat_history, save_session_results, get_session_results, 
    save_to_knowledge_graph, query_knowledge_graph,
    find_cached_response, save_semantic_cache
)
from app.config.config import settings
from pydantic import BaseModel, Field
from typing import List, Dict, Any
import json

def _make_llm() -> ChatOpenAI:
    if settings.GROQ_API_KEY.strip():
        return ChatOpenAI(
            base_url=settings.GROQ_BASE_URL.rstrip("/"),
            api_key=settings.GROQ_API_KEY,
            model=settings.GROQ_MODEL,
            temperature=0.1,
        )
    return ChatOpenAI(
        base_url=settings.LM_STUDIO_URL.rstrip("/"),
        api_key="not-needed",
        model=settings.LM_STUDIO_MODEL,
        temperature=0.1,
    )

llm = _make_llm()

class SearchQueries(BaseModel):
    pubmed: str = Field(description="Query optimized for medical literature (PubMed)")
    openalex: str = Field(description="Query optimized for general academic papers (OpenAlex)")

async def _extract_medical_context(history: List[Dict[str, Any]]) -> str:
    """Extracts a tight keyword-focused summary of the previous medical conversation."""
    if not history: return ""
    
    # Focus on the last few turns for relevance and token efficiency
    recent_history = history[-6:]
    formatted = "\n".join([f"{m['role']}: {m['content'][:300]}" for m in recent_history])
    
    context_prompt = f"""
    Summarize the key medical entities and specific treatments discussed in this conversation history. 
    Focus on KEYWORDS and maintaining clinical continuity. Limit to 60 words.
    
    HISTORY:
    {formatted}
    """
    try:
        # Use a high-speed inference for the summary
        res = await llm.ainvoke(context_prompt)
        return res.content.strip()
    except:
        return ""

async def run_research(query: str, disease: str, session_id: str, location: str = None):
    # --- STEP -2: Semantic Cache Lookup ---
    try:
        cache_hit = await find_cached_response(query)
        if cache_hit:
            print(f"--- SEMANTIC CACHE HIT: {query} ---")
            # Yield sources first to maintain consistent UI layout
            yield json.dumps({"type": "sources", "data": cache_hit["sources"]}) + "\n"
            
            # Stream the cached content to simulate responsiveness and typing feel
            content = cache_hit["content"]
            chunk_size = 40
            for i in range(0, len(content), chunk_size):
                yield json.dumps({"type": "chunk", "text": content[i:i+chunk_size]}) + "\n"
                await asyncio.sleep(0.01) # Ultra-fast simulated stream
            
            yield json.dumps({
                "type": "done",
                "thoughts": cache_hit.get("thoughts", "Retrieved from neural memory."),
                "full_text": content,
                "sources": cache_hit["sources"]
            }) + "\n"
            return
    except Exception as e:
        print(f"Cache Lookup Error: {e}")

    # --- STEP -1: Input Guardrail & Safety ---
    safety_prompt = f"""
    Analyze the following user query for a Medical Research Assistant.
    QUERY: "{query}" regarding "{disease}"
    
    RULES:
    1. If the query is absolute gibberish, nonsensical, or clearly "bullshit", return 'BLOCK: NONSENSE'.
    2. If the query is dangerous (asking for help with self-harm, illegal manufacturing, or life-threatening pseudoscience), return 'BLOCK: DANGER'.
    3. If the query is completely unrelated to healthcare, medicine, or clinical research (e.g. "how to bake a cake"), return 'BLOCK: OFF_TOPIC'.
    4. If the query is safe and medically relevant, return 'PASS'.
    
    RETURN ONLY ONE LINE.
    """
    try:
        safety_res = await llm.ainvoke(safety_prompt)
        safety_status = safety_res.content.strip().upper()
        
        if safety_status.startswith("BLOCK"):
            reason = "nonsensical" if "NONSENSE" in safety_status else "off-topic"
            if "DANGER" in safety_status: reason = "violates safety guidelines"
            
            yield json.dumps({
                "type": "error", 
                "message": f"Query Refused: Your input appears to be {reason}. CuraLink only processes clinical and medically relevant research requests."
            }) + "\n"
            return
    except Exception as e:
        print(f"Safety Guardrail Error: {e}")

    history = await get_chat_history(session_id)
    chat_summary = await _extract_medical_context(history)

    # --- STEP 0: Routing & Intent ---
    intent_prompt = f"CONVERSATION SUMMARY: {chat_summary}\n\nDecide if the NEW QUERY: '{query}' needs NEW_SEARCH or DEEP_DIVE (refining existing data). RETURN ONE WORD."
    intent_res = await llm.ainvoke(intent_prompt)
    intent = intent_res.content.strip().upper()
    cached_library = await get_session_results(session_id)
    
    needs_new_search = True
    all_candidates = []
    
    if 'DEEP_DIVE' in intent and cached_library:
        test_rank = rank_and_filter(cached_library, query, disease, top_n=1)
        acronyms = re.findall(r'\b[A-Z]{2,}\b', query)
        has_new_term = any(acr not in str(test_rank[0]) for acr in acronyms) if test_rank else True

        if test_rank and test_rank[0]['score'] >= 15 and not has_new_term:
            needs_new_search = False
            print("--- ROUTING: DEEP DIVE (LOCAL LIBRARY) ---")
            all_candidates = cached_library
        else:
            print("--- LOCAL LIBRARY INSUFFICIENT OR NEW TERMS DETECTED: PIVOTING ---")
            needs_new_search = True

    if needs_new_search or not cached_library:
        print("--- ROUTING: NEW SEARCH (INTERNET) ---")
        intent = "NEW_SEARCH"
        # Incorporate Location into expansion if provided
        loc_clause = f" specifically in {location}" if location else ""
        expansion_prompt = f"Generate 2 medical queries for {query} about {disease}{loc_clause}. MUST include '{disease}'."
        
        # -- KNOWLEDGE GRAPH FIRST PASS --
        graph_candidates = await query_knowledge_graph(disease, limit=100)
        print(f"[ARCHIVE] Scanning Global Knowledge Graph... Found {len(graph_candidates)} previously indexed papers.")
        
        # Rank graph knowledge to see if it satisfies the user's intent 
        ranked_graph = rank_and_filter(graph_candidates, query, disease, top_n=20)
        
        # Determine if we have a critical mass of HIGH-QUALITY documents (score > 50 means excellent intent + disease overlap)
        high_quality_docs = [doc for doc in ranked_graph if doc.get('score', 0) > 50]
        
        all_candidates = []
        fresh_candidates = []
        
        if len(high_quality_docs) >= 3:
            # Short-circuit: Graph already knows the answer! Skip live searches.
            intent = "KNOWLEDGE_GRAPH_CACHE_HIT"
            print(f"[ARCHIVE] Knowledge Graph Sufficient: Found {len(high_quality_docs)} highly relevant clinical resources locally. Bypassing external latency pipelines...")
            all_candidates = ranked_graph
            
        else:
            # Fallback: Live Deep Web Search
            print("[ARCHIVE] Knowledge Graph insufficient for specific intent. Instantiating deep-web clinical retrieval protocol...")
            try:
                structured_llm = llm.with_structured_output(SearchQueries)
                queries = await structured_llm.ainvoke(expansion_prompt)
                final_pubmed = f"{disease} {queries.pubmed}"
                final_openalex = f"{disease} {queries.openalex}"
            except:
                final_pubmed = f"{disease} {query}"
                final_openalex = f"{disease} {query}"

            trial_query = f"{disease} {query}"
            pubmed_titles = await search_pubmed_metadata(final_pubmed, limit=40)
            shortlist = rank_and_filter(normalize_results(pubmed_titles, "pubmed"), final_pubmed, disease, top_n=12)
            
            pubmed_full, openalex_res, clinical_res = await asyncio.gather(
                fetch_pubmed_abstracts([c['url'].split('/')[-2] for c in shortlist if 'pubmed' in c['url']]),
                search_openalex(final_openalex, limit=12),
                search_clinical_trials(trial_query, limit=15)
            )
            fresh_candidates = normalize_results(pubmed_full, "pubmed") + normalize_results(openalex_res, "openalex") + normalize_results(clinical_res, "clinical_trials")

            # Blend graph results into the newly discovered candidates
            known_urls = {p.get('url') for p in fresh_candidates if p.get('url')}
            graph_new = [p for p in graph_candidates if p.get('url') not in known_urls]
            all_candidates = fresh_candidates + graph_new

            # Save fresh discoveries into both session archive and global knowledge graph
            await save_session_results(session_id, all_candidates)
            await save_to_knowledge_graph(disease, fresh_candidates)

    top_results = rank_and_filter(all_candidates, query, disease, top_n=8)

    # --- STEP 4: Context Building & JIT-RAG ---
    from app.utils.rag_utils import get_top_chunks
    context_block = ""
    for i, res in enumerate(top_results):
        summary = res.get('summary')
        display_text = str(summary or "") if not isinstance(summary, dict) else res.get('title', "")
        
        # Build Metadata Header
        meta = f"[{res.get('source')}] {res.get('date', 'N/A')}"
        if res.get('authors'): meta += f" | Authors: {res['authors']}"
        if res.get('status'): meta += f" | STATUS: {res['status']}"
        if res.get('location'): meta += f" | LOCATION: {res['location']}"
        
        if i < 2 and res.get('pmc'): 
            try:
                full_text = await fetch_pmc_fulltext(res['pmc'])
                if full_text: display_text = await get_top_chunks(query, full_text, top_k=2)
            except: pass
                
        context_block += f"[{i+1}] {res['title']}\nMETADATA: {meta}\n"
        if res.get('eligibility'): context_block += f"ELIGIBILITY: {res['eligibility'][:500]}\n"
        context_block += f"Data: {display_text[:1200]}\n\n"
    
    # Broadcast Sources back to client directly
    yield json.dumps({"type": "sources", "data": top_results}) + "\n"

    # --- STEP 5: Final Neural Briefing ---
    final_prompt = f"""
    You are a Senior Medical Assistant at CuraLink. Brief the user on {query} regarding {disease}.
    
    CONVERSATIONAL PROGRESSION: {chat_summary if chat_summary else "Initial Query"}
    Target Location: {location if location else "Global"}
    
    EVIDENCE: {context_block[:8000]}
    
    RULES:
    1. NO LETTER FORMAT: Do not include "Dear Patient", signatures, or personal greetings. 
    2. STRICT TOPICALITY: Only discuss {query}. If a paper is about an unrelated topic (e.g. stem cells), IGNORE IT completely.
    3. STRUCTURE: Use headers: ### Condition Overview, ### {query} Insights, ### Clinical Trials, ### Evidence Citations.
    4. CITATIONS: Cite every claim with [1], [2].
    """
    
    full_response = ""
    async for chunk in llm.astream(final_prompt):
        full_response += chunk.content
        yield json.dumps({"type": "chunk", "text": chunk.content}) + "\n"
        
    # --- STEP 6: Ragas Evaluation ---
    contexts = [str(r.get('summary', r.get('title', ''))) for r in top_results]
    eval_result = await run_quality_check(query, contexts, full_response)
    
    thought_process = f"Analyzed {len(top_results)} sources. Focus: {location if location else 'Global'}. Decision: {intent}."
    thought_process += f" | Quality: {'PASSED' if eval_result['passed'] else 'LOW'} (Faithfulness: {eval_result['scores'].get('faithfulness', 0):.2f}, Relevancy: {eval_result['scores'].get('answer_relevancy', 0):.2f})"
    
    yield json.dumps({
        "type": "done",
        "thoughts": thought_process,
        "full_text": full_response,
        "sources": top_results
    }) + "\n"

    # Persistent Semantic Caching
    try:
        await save_semantic_cache(query, {
            "content": full_response,
            "thoughts": thought_process,
            "sources": top_results
        })
    except Exception as e:
        print(f"Cache Save Error: {e}")
