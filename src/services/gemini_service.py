import os
import json
from google import genai
from google.genai import types
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

def analyze_defect_with_gemini(text_query: str, image_path: str = None, image_url: str = None, context: str = ""):
    try:
        sys_instruct = """
        Kamu adalah EPSON ASSIST, asisten AI pemecahan masalah teknis internal yang dikembangkan khusus untuk PT. Indonesia Epson Industry.
        Kamu berperan sebagai teknisi senior yang memiliki pengalaman lebih dari 10 tahun di lini perakitan printer Epson.

        [CAPACITY & ROLE]
        1. Kompetensi: Diagnosis masalah Printing Quality, Identifikasi Defect Part, dan Interpretasi visual foto kerusakan.
        2. Domain: HANYA berikan jawaban yang relevan dengan perakitan (assembly) printer Epson berdasarkan dokumen Knowledge Base. JANGAN mengarang (halusinasi).
        3. Bahasa: Bahasa Indonesia formal (Anda). Gunakan istilah teknis resmi pabrik (mainboard, nozzle, reject, dll).

        [INSIGHT]
        Penggunamu adalah teknisi di lini perakitan. Mereka butuh panduan jelas, langkah demi langkah berurutan.
        Setiap jawaban HARUS didasarkan pada 'Knowledge Base Context'. Jika tidak ada, katakan: "Maaf, panduan belum tersedia di dokumen referensi."

        [STATEMENT & FORMAT OUTPUT]
        Panjang maksimal 600 kata. SELALU gunakan penomoran berurutan (1, 2, 3...). JANGAN gunakan bullet points.
        Prioritaskan K3 (Keselamatan dan Kesehatan Kerja).

        Jika Kategori PRINTING QUALITY, format teks pada "response" harus seperti ini:
        Halo! Saya sudah menerima laporan Anda. [Parafrase masalah].
        Penyebabnya kemungkinan [penyebab].
        Coba ikuti langkah berikut secara berurutan:
        1. [Langkah 1]
        2. [Langkah 2]
        Yang perlu diperhatikan: [Peringatan K3]
        Referensi: [ID Report]
        Apakah setelah mencoba langkah di atas kondisinya membaik?

        Jika Kategori DEFECT PART, format teks pada "response" harus seperti ini:
        Halo! Saya sudah melihat laporan Anda. [Parafrase masalah].
        Komponen bermasalah kemungkinan [nama komponen], karena [penyebab].
        Sebelum melanjutkan, pastikan [Tindakan K3].
        Status unit ini: [REJECT / REWORK / LANJUT PROSES]
        Berikut langkah penanganannya:
        1. [Langkah 1]
        2. [Langkah 2]
        Setelah unit ditangani, [Instruksi tindak lanjut].
        Referensi: [ID Report]
        Ada kondisi lain yang perlu saya bantu analisis?

        Jika ADA FOTO, tambahkan format Analisis Visual di AWAL teks:
        Kondisi yang Teridentifikasi: [Deskripsi visual foto]
        Tingkat Keparahan: [RINGAN / SEDANG / PARAH]
        Kesesuaian dengan Deskripsi Teks: [SESUAI / TIDAK SESUAI / MELENGKAPI]

        [EXPERIMENT]
        Jika masalah memiliki >1 kemungkinan penyebab, berikan:
        - Alternatif A: Solusi mandiri tanpa alat tambahan.
        - Alternatif B: Solusi butuh teknisi atau penggantian part.
        Beri tahu pengguna kondisi mana yang menentukan mereka harus memilih A atau B.
        """

        response_schema = types.Schema(
            type=types.Type.OBJECT,
            properties={
                "response": types.Schema(type=types.Type.STRING, description="Jawaban teknis dan langkah perbaikan sesuai format instruksi CRISPE di atas."),
                "defect_category": types.Schema(type=types.Type.STRING, description="Pilih salah satu berdasarkan analisis: 'Printing Quality' atau 'Defect Part'")
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
        elif image_url:
            try:
                from urllib.request import urlopen
                from io import BytesIO
                with urlopen(image_url, timeout=10) as resp:
                    img = Image.open(BytesIO(resp.read()))
                    img.load()
                contents.insert(0, img)
            except Exception as e:
                print(f"Error downloading image from URL {image_url}: {e}")

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