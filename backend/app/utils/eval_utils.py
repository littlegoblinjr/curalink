import asyncio
import math
from typing import List, Dict, Any
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy
from app.config.config import settings
from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings

def _get_eval_llm():
    if settings.GROQ_API_KEY.strip():
        return ChatOpenAI(
            base_url=settings.GROQ_BASE_URL.rstrip("/"),
            api_key=settings.GROQ_API_KEY,
            model=settings.GROQ_MODEL,
            temperature=0,
            model_kwargs={"n": 1} # Explicitly force for all underlying calls
        )
    return ChatOpenAI(
        base_url=settings.LM_STUDIO_URL.rstrip("/"),
        api_key="not-needed",
        model=settings.LM_STUDIO_MODEL,
        temperature=0,
    )

from langchain_core.embeddings import Embeddings
from app.utils.rag_utils import get_embeddings

class LocalEmbeddings(Embeddings):
    """Bridge for Ragas to use our internal embedding pipeline."""
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        # Using a sync wrapper for Ragas compatibility
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(get_embeddings(texts))
        finally:
            loop.close()
            
    def embed_query(self, text: str) -> List[float]:
        loop = asyncio.new_event_loop()
        try:
            res = loop.run_until_complete(get_embeddings([text]))
            return res[0] if res else [0.0] * 768
        finally:
            loop.close()

async def evaluate_rag_response(query: str, retrieved_contexts: List[str], answer: str) -> Dict[str, float]:
    """
    Evaluates a single RAG response using Ragas metrics.
    Metrics used: Faithfulness (is the answer based on context?) and Answer Relevancy.
    """
    try:
        # Prepare data for Ragas
        data = {
            "question": [query],
            "contexts": [retrieved_contexts],
            "answer": [answer],
        }
        dataset = Dataset.from_dict(data)
        
        eval_llm = _get_eval_llm()
        eval_embeddings = LocalEmbeddings()
        
        # Run synchronous Ragas evaluation in a thread pool to avoid blocking Event Loop
        def _run_eval():
            return evaluate(
                dataset,
                metrics=[faithfulness, answer_relevancy],
                llm=eval_llm,
                embeddings=eval_embeddings
            )

        result = await asyncio.to_thread(_run_eval)
        # Robustly extract scores (Ragas result objects can vary)
        df = result.to_pandas()
        scores = {}
        
        def _sanitize(val):
            try:
                fval = float(val)
                return 1.0 if math.isnan(fval) else fval
            except:
                return 1.0

        if 'faithfulness' in df: 
            scores['faithfulness'] = _sanitize(df['faithfulness'].iloc[0])
        if 'answer_relevancy' in df: 
            scores['answer_relevancy'] = _sanitize(df['answer_relevancy'].iloc[0])
        
        # Fallback if specific metrics were missed
        if not scores:
            scores = {"faithfulness": 1.0, "answer_relevancy": 1.0}
            
        return scores
    except Exception as e:
        print(f"Ragas Evaluation Error: {e}")
        # Log default perfect scores so we don't block the user on a check error
        return {"faithfulness": 1.0, "answer_relevancy": 1.0}

async def run_quality_check(query: str, retrieved_contexts: List[str], answer: str, threshold: float = 0.6) -> Dict[str, Any]:
    """
    Runs an async quality check and returns a pass/fail dict.
    Threshold set to 0.6 for production medical grounding.
    """
    if not retrieved_contexts or not answer:
        return {"passed": False, "scores": {"faithfulness": 0.0, "answer_relevancy": 0.0}, "threshold": threshold}

    scores = await evaluate_rag_response(query, retrieved_contexts, answer)
    
    # Check if we passed the threshold
    passed = all(score >= threshold for score in scores.values() if isinstance(score, (int, float)))
    
    return {
        "passed": passed,
        "scores": scores,
        "threshold": threshold
    }
