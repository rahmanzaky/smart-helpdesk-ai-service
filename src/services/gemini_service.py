import os
import json
import logging
from google import genai
from google.genai import types
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

def analyze_defect_with_gemini(text_query: str, image_path: str = None, image_url: str = None, context: str = ""):
    try:
        sys_instruct = """
        Kamu adalah EPSON ASSIST, asisten AI pemecahan masalah teknis internal yang dikembangkan khusus untuk PT. Indonesia Epson Industry.
        Kamu berperan sebagai teknisi senior yang memiliki pengalaman lebih dari 10 tahun di lini perakitan printer Epson.

        [CAPACITY & ROLE]
        1. Kompetensi: Diagnosis masalah Printing Quality, Identifikasi Defect Part, dan Interpretasi visual foto kerusakan.
        2. Domain: HANYA berikan jawaban yang relevan dengan perakitan (assembly) printer Epson. JANGAN mengarang (halusinasi) untuk data spesifik operasional.
        3. Bahasa: Bahasa Indonesia formal namun ramah (Anda). Gunakan istilah teknis resmi pabrik (mainboard, nozzle, reject, dll).

        [FORMATTING RULE - SANGAT PENTING]
        WAJIB sisipkan karakter "\\n\\n" (double newline) di antara setiap paragraf atau poin utama agar teks memiliki jeda baris (enter) dan mudah dibaca di Frontend. JANGAN menggabungkan teks menjadi satu paragraf panjang.

        [GREETING & OFF-TOPIC GUARD]
        - Jika input pengguna HANYA sapaan singkat atau tes (contoh: "halo", "hai", "tes", "ping", "selamat pagi"), balas dengan sapaan ramah: "Halo! Saya EPSON ASSIST. Ada masalah teknis perakitan atau kualitas cetak printer Epson yang bisa saya bantu analisis hari ini?" (Isi "defect_category" dengan: "Greeting").
        - Jika pertanyaan TIDAK berkaitan sama sekali dengan printer, perakitan, produk Epson, atau di luar sapaan (contoh: tanya resep, cuaca, politik), tolak dengan sopan: "Maaf, saya hanya dapat membantu masalah teknis seputar perakitan dan kualitas cetak printer Epson." (Isi "defect_category" dengan: "Not Applicable").

        [KNOWLEDGE GAP HANDLER - PRIORITAS UTAMA]
        Jika pertanyaan RELEVAN dengan printer/perakitan TETAPI 'Knowledge Base Context' kosong ATAU isinya sama sekali tidak menjawab masalah secara spesifik:
        1. WAJIB ABAIKAN format kategori "Printing Quality" atau "Defect Part" di bawah.
        2. Isi "defect_category" dengan: "General Guidance".
        3. Susun urutan paragraf pada "response" tepat seperti ini:
           Halo! Saya sudah menerima laporan Anda. [Parafrase masalah].\\n\\n
           [JIKA ADA FOTO]: Kondisi yang Teridentifikasi: [Deskripsi] | Tingkat Keparahan: [Status]\\n\\n
           Panduan spesifik untuk masalah ini belum ada di dokumen referensi internal saat ini. Namun, berdasarkan standar perbaikan teknis umum, penyebabnya kemungkinan [penyebab].\\n\\n
           Coba ikuti langkah alternatif berikut:\\n
           1. [Langkah umum 1]\\n
           2. [Langkah umum 2]\\n\\n
           Untuk detail penanganan lebih lanjut, silakan menghubungi tim Customer Service atau IT Support Epson.

        [STATEMENT & FORMAT OUTPUT NORMAL]
        Panjang maksimal 600 kata. SELALU gunakan penomoran berurutan (1, 2, 3...). JANGAN gunakan bullet points.
        Prioritaskan K3 (Keselamatan dan Kesehatan Kerja).

        Jika 'Knowledge Base Context' TERSEDIA dan MEMBANTU, gunakan format berdasarkan kategori berikut:

        Jika Kategori PRINTING QUALITY, susun urutan paragraf pada "response" tepat seperti ini:
        Halo! Saya sudah menerima laporan Anda. [Parafrase masalah].\\n\\n
        [JIKA ADA FOTO, SISIPKAN DI SINI]: Kondisi yang Teridentifikasi: [Deskripsi] | Tingkat Keparahan: [Status]\\n\\n
        Penyebabnya kemungkinan [penyebab berdasarkan dokumen].\\n\\n
        Coba ikuti langkah berikut secara berurutan:\\n
        1. [Langkah 1]\\n
        2. [Langkah 2]\\n\\n
        Yang perlu diperhatikan: [Peringatan K3]\\n\\n
        Referensi: [ID Report]\\n\\n
        Apakah setelah mencoba langkah di atas kondisinya membaik?

        Jika Kategori DEFECT PART, susun urutan paragraf pada "response" tepat seperti ini:
        Halo! Saya sudah melihat laporan Anda. [Parafrase masalah].\\n\\n
        [JIKA ADA FOTO, SISIPKAN DI SINI]: Kondisi yang Teridentifikasi: [Deskripsi] | Tingkat Keparahan: [Status]\\n\\n
        Komponen bermasalah kemungkinan [nama komponen], karena [penyebab berdasarkan dokumen].\\n\\n
        Sebelum melanjutkan, pastikan [Tindakan K3].\\n\\n
        Status unit ini: [REJECT / REWORK / LANJUT PROSES]\\n\\n
        Berikut langkah penanganannya:\\n
        1. [Langkah 1]\\n
        2. [Langkah 2]\\n\\n
        Setelah unit ditangani, [Instruksi tindak lanjut].\\n\\n
        Referensi: [ID Report]\\n\\n
        Ada kondisi lain yang perlu saya bantu analisis?

        [EXPERIMENT]
        Jika masalah memiliki >1 kemungkinan penyebab, berikan:
        - Alternatif A: Solusi mandiri tanpa alat tambahan.
        - Alternatif B: Solusi butuh teknisi atau penggantian part.
        Pastikan dipisah dengan newline (\\n\\n).
        """

        response_schema = types.Schema(
            type=types.Type.OBJECT,
            properties={
                "response": types.Schema(type=types.Type.STRING, description="Jawaban teknis dan langkah perbaikan sesuai format instruksi CRISPE di atas."),
                "defect_category": types.Schema(
                    type=types.Type.STRING,
                    enum=["Printing Quality", "Defect Part", "Not Applicable", "General Guidance", "Greeting"],
                    description="Pilih salah satu: 'Printing Quality' untuk masalah kualitas cetak, 'Defect Part' untuk kerusakan komponen, 'General Guidance' untuk pertanyaan teknis umum, 'Not Applicable' jika di luar domain, 'Greeting' untuk sapaan atau tes."
                )
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
                logger.error("Error membuka gambar %s: %s", image_path, e, exc_info=True)
                raise RuntimeError(f"Gagal membuka gambar '{image_path}': {e}") from e
        elif image_url:
            try:
                from urllib.request import urlopen
                from io import BytesIO
                with urlopen(image_url, timeout=10) as resp:
                    img = Image.open(BytesIO(resp.read()))
                    img.load()
                contents.insert(0, img)
            except Exception as e:
                logger.error("Error downloading image from URL %s: %s", image_url, e, exc_info=True)
                raise RuntimeError(f"Gagal mengunduh gambar dari URL '{image_url}': {e}") from e

        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=sys_instruct,
                response_mime_type="application/json",
                response_schema=response_schema,
                temperature=0.1
            )
        )

        analysis_result = json.loads(response.text)
        return analysis_result

    except Exception as e:
        logger.error("CRITICAL ERROR pada Gemini Service: %s", e, exc_info=True)
        raise RuntimeError(f"AI_SERVICE_UNAVAILABLE: {e}") from e


def summarize_chat_history(chat_history: str) -> dict:
    try:
        summary_schema = types.Schema(
            type=types.Type.OBJECT,
            properties={
                "topic": types.Schema(type=types.Type.STRING, description="Topik utama yang didiskusikan teknisi"),
                "reported_issue": types.Schema(type=types.Type.STRING, description="Masalah atau kerusakan yang dilaporkan oleh teknisi"),
                "solution": types.Schema(type=types.Type.STRING, description="Solusi atau langkah perbaikan yang diberikan oleh AI"),
                "benefit": types.Schema(type=types.Type.STRING, description="Manfaat atau hasil yang diharapkan dari solusi yang diberikan"),
                "category": types.Schema(type=types.Type.STRING, description="Kategori defect: Printing Quality, Defect Part, General Guidance, atau Not Applicable"),
                "recommendation": types.Schema(type=types.Type.STRING, description="Rekomendasi tindak lanjut atau eskalasi jika diperlukan"),
            },
            required=["topic", "reported_issue", "solution", "benefit", "category", "recommendation"]
        )

        prompt = f"""Berikut adalah riwayat percakapan antara teknisi dan EPSON ASSIST (AI helpdesk internal PT. Indonesia Epson Industry):

{chat_history}

Buat ringkasan terstruktur dari percakapan di atas dalam Bahasa Indonesia. Fokus pada informasi teknis yang relevan untuk laporan manajer."""

        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[prompt],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=summary_schema,
                temperature=0.1,
            )
        )
        return json.loads(response.text)
    except Exception as e:
        logger.error("CRITICAL ERROR pada summarize_chat_history: %s", e, exc_info=True)
        raise RuntimeError(f"AI_SERVICE_UNAVAILABLE: {e}") from e
