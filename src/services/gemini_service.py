import os
import json
from google import genai
from google.genai import types
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

def analyze_defect_with_gemini(text_query: str, image_path: str = None, context: str = ""):
    try:
        sys_instruct = (
            "Anda adalah expert EPSON printer technician untuk PT. Indonesia Epson Industry. "
            "Tugas Anda memberikan solusi teknis operasional (assembly) berdasarkan dokumen Knowledge Base.\n\n"
            "ATURAN MUTLAK:\n"
            "1. Format jawaban harus terstruktur: (1) Analisis Masalah, (2) Langkah Solusi, (3) Pencegahan.\n"
            "2. Jika jawaban TIDAK ADA di 'Knowledge Base Context', DILARANG MENGARANG (halusinasi). Katakan: 'Maaf, panduan belum tersedia di dokumen referensi.'\n"
            "3. Analisis dan tentukan kategori masalahnya ('Printing Quality' atau 'Defect Part')."
        )

        response_schema = types.Schema(
            type=types.Type.OBJECT,
            properties={
                "response": types.Schema(type=types.Type.STRING, description="Jawaban teknis dan langkah perbaikan"),
                "defect_category": types.Schema(type=types.Type.STRING, description="Pilih salah satu: 'Printing Quality' atau 'Defect Part'")
            },
            required=["response", "defect_category"]
        )

        prompt = f"User Description: \"{text_query}\"\nKnowledge Base Context: \"{context}\""
        contents = [prompt]

        if image_path:
            try:
                img = Image.open(image_path)
                contents.insert(0, img)
            except Exception as e:
                print(f"Error membuka gambar {image_path}: {e}")

        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=sys_instruct,
                response_mime_type="application/json",
                response_schema=response_schema,       
                temperature=0.2
            )
        )

        analysis_result = json.loads(response.text)
        
        return analysis_result

    except Exception as e:
        print(f"CRITICAL ERROR pada Gemini Service: {e}")
        raise Exception("AI_SERVICE_UNAVAILABLE")