import os
import json
from google import genai
from PIL import Image
from dotenv import load_dotenv

# Load environment variable
load_dotenv()

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

def analyze_defect_with_gemini(text_query: str, image_path: str = None, context: str = ""):
    try:
        prompt = f"""Anda adalah expert EPSON printer technician untuk PT. Indonesia Epson Industry.
Tugas: Berikan solusi teknis yang akurat berdasarkan konteks dan pertanyaan user.

User Description: "{text_query}"
Knowledge Base Context: "{context}"

Format respons HARUS berupa JSON murni (tanpa markdown) dengan struktur:
{{
  "response": "tuliskan jawaban teknis dan langkah perbaikan di sini secara natural"
}}"""

        contents = [prompt]

        if image_path:
            try:
                img = Image.open(image_path)
                contents.insert(0, img)
            except Exception as e:
                print(f"Error membuka gambar: {e}")

        # Menggunakan model gemini-2.5-flash 
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=contents
        )
        
        response_text = response.text

        # Parsing JSON yang lebih robust
        clean_json_string = response_text.replace("```json", "").replace("```", "").strip()
        analysis_result = json.loads(clean_json_string)
        
        return analysis_result

    except Exception as e:
        print("Error pada Gemini Service:", e)
        # Fallback 
        return {
            "response": "Sistem sedang mengalami gangguan teknis dalam memproses AI. Silakan coba beberapa saat lagi atau hubungi IT Support."
        }
