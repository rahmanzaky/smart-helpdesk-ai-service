# import pandas as pd
# import faiss
# import numpy as np
# import pytesseract
# from PIL import Image
# from sentence_transformers import SentenceTransformer

# # =========================
# # LOAD MODEL EMBEDDING (GRATIS)
# # =========================
# print("Loading embedding model...")
# model = SentenceTransformer('all-MiniLM-L6-v2')

# # =========================
# # LOAD DATASET
# # =========================
# print("Loading dataset...")
# df = pd.read_csv("data/faq_epson.csv")

# # NORMALISASI KOLOM (ANTI ERROR)
# df.columns = df.columns.str.strip().str.lower()

# print("Kolom CSV:", df.columns.tolist())

# # =========================
# # AUTO DETECT KOLOM
# # =========================
# def find_column(possible_names):
#     for name in possible_names:
#         if name in df.columns:
#             return name
#     return None

# question_col = find_column(["question", "pertanyaan", "faq"])
# answer_col = find_column(["answer", "anwer", "jawaban", "solution", "solusi"])

# if not question_col or not answer_col:
#     raise ValueError(
#         f"Kolom tidak ditemukan!\n"
#         f"Kolom tersedia: {df.columns.tolist()}"
#     )

# print(f"Menggunakan kolom: {question_col} & {answer_col}")

# # =========================
# # PREPARE DATA
# # =========================
# questions = df[question_col].astype(str).tolist()
# answers = df[answer_col].astype(str).tolist()

# # =========================
# # EMBEDDING
# # =========================
# print("Creating embeddings...")
# embeddings = model.encode(questions)

# # =========================
# # FAISS INDEX
# # =========================
# dimension = embeddings.shape[1]
# index = faiss.IndexFlatL2(dimension)
# index.add(np.array(embeddings).astype("float32"))

# print("FAISS index siap!")

# # =========================
# # OCR (GAMBAR → TEXT)
# # =========================
# def extract_text_from_image(image_path):
#     try:
#         img = Image.open(image_path)
#         text = pytesseract.image_to_string(img)
#         return text
#     except Exception as e:
#         print("OCR error:", e)
#         return ""

# # =========================
# # RETRIEVAL
# # =========================
# def retrieve(query, top_k=1):
#     query_vector = model.encode([query])
#     D, I = index.search(np.array(query_vector).astype("float32"), top_k)
#     return I[0][0]

# # =========================
# # CHATBOT
# # =========================
# def chatbot(query_text=None, image_path=None):
#     image_text = ""

#     if image_path:
#         image_text = extract_text_from_image(image_path)
#         print("Teks dari gambar:", image_text)

#     final_query = f"{query_text or ''} {image_text}".strip()

#     idx = retrieve(final_query)
#     return answers[idx]

# # =========================
# # MAIN TEST
# # =========================
# if __name__ == "__main__":
#     print("\n=== CHATBOT EPSON   ===")

#     while True:
#         user_input = input("\nMasukkan pertanyaan (atau 'exit'): ")

#         if user_input.lower() == "exit":
#             break

#         use_image = input("Pakai gambar? (y/n): ")

#         if use_image.lower() == "y":
#             image_path = input("Masukkan path gambar: ")
#             response = chatbot(query_text=user_input, image_path=image_path)
#         else:
#             response = chatbot(query_text=user_input)

#         print("\nJawaban:")
#         print(response)

from src.services.rag_pipeline import chatbot

if __name__ == "__main__":
    print("\n=== CHATBOT HELPDESK EPSON (Powered by Gemini) ===")
    print("      Manufacturing Defect Troubleshooting Assistant")

    while True:
        user_input = input("\nMasukkan pertanyaan (atau 'exit'): ")

        if user_input.lower() == "exit":
            print("Terima kasih telah menggunakan layanan Smart Helpdesk SEJAHE.")
            break

        if not user_input.strip():
            continue

        print("\nMemproses analisis AI dengan basis data Epson, harap tunggu...")
        
        # Panggil Chatbot RAG (saat ini fokus pada teks)
        # Sesuai API Contract, chatbot() mengembalikan {'response': '...', 'context': [...]}
        response_data = chatbot(query_text=user_input)

        # Ambil data utama dari response
        answer = response_data.get('response', 'Maaf, sistem tidak memberikan jawaban.')
        context_used = response_data.get('context', [])

        print("\n" + "="*50)
        print("🔧 HASIL ANALISIS SMART HELPDESK")
        print("="*50)
        
        # Menampilkan jawaban utama yang sudah digenerasi oleh Gemini
        print(f"Solusi & Rekomendasi:\n{answer}\n")
        
        
        print("="*50)