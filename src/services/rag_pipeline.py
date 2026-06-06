import json
import logging
from src.services.retrieval import retrieve
from src.services.gemini_service import analyze_defect_with_gemini

logger = logging.getLogger(__name__)

def chatbot(query_text=None, image_path=None, image_url=None):
    query_text = query_text or ""

    # 1. RETRIEVAL (RAG): Ambil referensi dari dataset FAQ
    context_text = ""
    if query_text.strip():
        context_text = retrieve(query_text, top_k=1)

    logger.info("Running RAG pipeline (image_path=%s, image_url=%s)", image_path, image_url)

    # 2. GENERATION (Gemini): Kirim data ke Gemini
    analysis = analyze_defect_with_gemini(
        text_query=query_text,
        image_path=image_path,
        image_url=image_url,
        context=context_text
    )

    if isinstance(analysis, str):
        try:
            analysis = json.loads(analysis)
        except:
            analysis = {"response": analysis}

    return {
        "response": analysis.get("response", analysis.get("answer", "Maaf, saya tidak menemukan jawaban.")),
        "context": [
            {
                "doc_id": "FAQ-EPSON", # ID default
                "title": "Epson Knowledge Base",
                "score": 0.95
            }
        ]
    }
