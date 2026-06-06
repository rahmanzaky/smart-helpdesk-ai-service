import json
import logging
from src.services.retrieval import retrieve
from src.services.gemini_service import analyze_defect_with_gemini

logger = logging.getLogger(__name__)

def chatbot(query_text=None, image_path=None, image_url=None):
    query_text = query_text or ""

    # 1. RETRIEVAL: fetch up to 3 relevant KB entries
    retrieved = []
    context_text = ""
    if query_text.strip():
        retrieved = retrieve(query_text)
        if retrieved:
            # Combine top results into a single context block
            context_parts = []
            for r in retrieved:
                context_parts.append(f"Q: {r['question']}\nA: {r['answer']}")
            context_text = "\n\n---\n\n".join(context_parts)

    logger.info(
        "RAG pipeline: query=%r retrieved=%d entries (image_path=%s, image_url=%s)",
        query_text[:60], len(retrieved), image_path, image_url
    )

    # 2. GENERATION: send context + query to Gemini
    analysis = analyze_defect_with_gemini(
        text_query=query_text,
        image_path=image_path,
        image_url=image_url,
        context=context_text
    )

    if isinstance(analysis, str):
        try:
            analysis = json.loads(analysis)
        except Exception:
            analysis = {"response": analysis}

    # 3. Build context metadata with real retrieval scores
    context_meta = [
        {
            "doc_id": f"KB-{r['index']:04d}",
            "title": r["question"][:80],
            "similarity_score": round(1.0 - min(r["score"], 1.0), 4),
        }
        for r in retrieved
    ] or [{"doc_id": "NONE", "title": "No KB match found", "similarity_score": 0.0}]

    return {
        "response": analysis.get("response", "Maaf, saya tidak menemukan jawaban."),
        "defect_category": analysis.get("defect_category", "General Guidance"),
        "context": context_meta,
    }
