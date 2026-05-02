import asyncio
import re
from langchain_openai import ChatOpenAI
from app.services.tools import search_pubmed_metadata, fetch_pubmed_abstracts, search_openalex, search_clinical_trials, fetch_pmc_fulltext
from app.utils.ranking import normalize_results, rank_and_filter
from app.config.database import get_chat_history, save_session_results, get_session_results
from app.config.config import settings
from pydantic import BaseModel, Field
from typing import List, Dict, Any

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

async def run_research(query: str, disease: str, session_id: str, location: str = None):
    history = await get_chat_history(session_id)
    chat_context = ""
    if history:
        chat_context = "\n".join([f"{m['role']}: {m['content']}" for m in history])

    # --- STEP 0: Routing & Intent ---
    intent_prompt = f"Decide if '{query}' needs NEW_SEARCH or DEEP_DIVE (follow-up). RETURN ONE WORD."
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
        
        try:
            structured_llm = llm.with_structured_output(SearchQueries)
            queries = await structured_llm.ainvoke(expansion_prompt)
            final_pubmed = f"{disease} {queries.pubmed}"
            final_openalex = f"{disease} {queries.openalex}"
        except:
            final_pubmed = f"{disease} {query}"
            final_openalex = f"{disease} {query}"

        # CLINICAL TRIALS: Focus on the Condition + Intent
        # WE EXCLUDE location from the API call itself because the API expects conditions,
        # not city names. We will handle location relevance in the Ranking layer.
        trial_query = f"{disease} {query}"

        pubmed_titles = await search_pubmed_metadata(final_pubmed, limit=40)
        shortlist = rank_and_filter(normalize_results(pubmed_titles, "pubmed"), final_pubmed, disease, top_n=12)
        
        pubmed_full, openalex_res, clinical_res = await asyncio.gather(
            fetch_pubmed_abstracts([c['url'].split('/')[-2] for c in shortlist if 'pubmed' in c['url']]),
            search_openalex(final_openalex, limit=12),
            search_clinical_trials(trial_query, limit=15)
        )
        all_candidates = normalize_results(pubmed_full, "pubmed") + normalize_results(openalex_res, "openalex") + normalize_results(clinical_res, "clinical_trials")
        await save_session_results(session_id, all_candidates)

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
    
    # --- STEP 5: Final Neural Briefing ---
    final_prompt = f"""
    You are a Senior Medical Assistant at CuraLink. Brief the user on {query} regarding {disease}.
    Target Location: {location if location else "Global"}
    
    EVIDENCE: {context_block[:8000]}
    
    RULES:
    1. NO LETTER FORMAT: Do not include "Dear Patient", signatures, or personal greetings. 
    2. STRICT TOPICALITY: Only discuss {query}. If a paper is about an unrelated topic (e.g. stem cells), IGNORE IT completely.
    3. STRUCTURE: Use headers: ### Condition Overview, ### {query} Insights, ### Clinical Trials, ### Evidence Citations.
    4. CITATIONS: Cite every claim with [1], [2].
    """
    final_response = await llm.ainvoke(final_prompt)
    thought_process = f"Analyzed {len(top_results)} sources. Focus: {location if location else 'Global'}. Decision: {intent}."
    
    return {
        "answer": final_response.content,
        "thought_process": thought_process,
        "sources": top_results
    }
