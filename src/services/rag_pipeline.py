from src.services.retrieval import retrieve
from src.services.gemini_service import analyze_defect_with_gemini
import json

def chatbot(query_text=None, image_path=None):
    query_text = query_text or ""
    
    # 1. RETRIEVAL (RAG): Ambil referensi dari dataset FAQ
    context_text = ""
    if query_text.strip():
        context_text = retrieve(query_text, top_k=1)
    
    # 2. GENERATION (Gemini): Kirim data ke Gemini
    analysis = analyze_defect_with_gemini(
        text_query=query_text, 
        image_path=image_path, 
        context=context_text
    )

    # --- PERBAIKAN UNTUK API CONTRACT & FIX KEYERROR ---
    
    # Pastikan analysis adalah dictionary. 
    # Jika Gemini mengembalikan JSON string, kita parse dulu.
    if isinstance(analysis, str):
        try:
            analysis = json.loads(analysis)
        except:
            analysis = {"response": analysis}

    # Kita bungkus hasilnya agar sesuai dengan harapan api.py
    # Gunakan kunci 'response' sesuai API Contract v1.0 
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