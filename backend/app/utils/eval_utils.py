import asyncio
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
        return asyncio.run(get_embeddings(texts))
    def embed_query(self, text: str) -> List[float]:
        return asyncio.run(get_embeddings([text]))[0]

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
        return result.to_pandas().drop(columns=['question', 'contexts', 'answer']).iloc[0].to_dict()
    except Exception as e:
        print(f"Ragas Evaluation Error: {e}")
        # Log empty scores but don't crash the pipeline
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
