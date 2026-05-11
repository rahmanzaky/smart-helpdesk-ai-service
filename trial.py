# # ==========================================
# # SMART HELPDESK CHATBOT (RAG SIMULATION)
# # ==========================================

# # --- KNOWLEDGE BASE (FAQ perusahaan realistis) ---
# knowledge_base = [
#     {
#         "id": 1,
#         "category": "Account Access",
#         "keywords": ["password", "login", "akun", "lupa password"],
#         "content": """Reset password akun korporat:
# 1. Buka portal SSO perusahaan.
# 2. Klik 'Forgot Password'.
# 3. Masukkan email korporat.
# 4. Cek email untuk link reset (berlaku 15 menit).
# Jika email tidak diterima, hubungi IT Service Desk."""
#     },

#     {
#         "id": 2,
#         "category": "Network & VPN",
#         "keywords": ["vpn", "remote", "koneksi kantor", "tidak bisa connect"],
#         "content": """VPN tidak bisa terhubung:
# 1. Pastikan internet stabil.
# 2. Login VPN menggunakan akun domain perusahaan.
# 3. Pastikan aplikasi VPN versi terbaru.
# 4. Jika muncul error certificate → restart laptop.
# Jika masih gagal, tiket akan dieskalasi ke Network Team."""
#     },

#     {
#         "id": 3,
#         "category": "Email & Communication",
#         "keywords": ["email", "outlook", "mailbox", "email penuh"],
#         "content": """Mailbox penuh:
# 1. Hapus email besar (attachment >10MB).
# 2. Kosongkan folder Deleted Items.
# 3. Archive email lama ke local archive.
# Jika storage masih penuh → request upgrade mailbox ke IT."""
#     },

#     {
#         "id": 4,
#         "category": "Hardware & Device",
#         "keywords": ["printer", "kertas macet", "print gagal"],
#         "content": """Printer kantor bermasalah:
# 1. Cek status printer di Control Panel.
# 2. Pastikan tidak ada kertas tersangkut.
# 3. Restart printer dan komputer.
# 4. Pastikan terhubung ke jaringan kantor.
# Jika masih gagal → laporkan nomor aset printer."""
#     },

#     {
#         "id": 5,
#         "category": "Business Application",
#         "keywords": ["hris", "absensi", "cuti", "aplikasi internal"],
#         "content": """Tidak bisa login HRIS:
# 1. Pastikan akun aktif.
# 2. Gunakan VPN jika akses dari luar kantor.
# 3. Clear cache browser.
# Jika error tetap muncul → kirim screenshot ke IT."""
#     }
# ]


# # ==========================================
# # 1. RETRIEVAL (keyword matching sederhana)
# # ==========================================
# def retrieve_docs(query, kb):
#     query = query.lower()
#     results = []

#     for item in kb:
#         if any(keyword in query for keyword in item["keywords"]):
#             results.append(item)

#     return results


# # ==========================================
# # 2. KLASIFIKASI INTENT SEDERHANA
# # ==========================================
# def detect_urgency(query):
#     urgent_words = ["urgent", "segera", "penting", "tidak bisa kerja", "down"]
#     return any(word in query.lower() for word in urgent_words)


# # ==========================================
# # 3. AGENTIC FLOW
# # ==========================================
# def smart_helpdesk_chatbot(user_input):

#     # --- Klarifikasi jika terlalu pendek ---
#     if len(user_input.split()) < 2:
#         return "Mohon jelaskan masalah Anda lebih detail (contoh: 'VPN tidak bisa connect dari rumah')."

#     # --- Retrieval ---
#     docs = retrieve_docs(user_input, knowledge_base)

#     # --- Jika tidak ada solusi ---
#     if not docs:
#         return """Saya tidak menemukan solusi di knowledge base.

# Apakah Anda ingin saya buatkan tiket helpdesk?
# Silakan kirim:
# - Deskripsi masalah
# - Screenshot error
# - Nomor aset perangkat (jika ada)
# """

#     best = docs[0]

#     # --- Jika urgent ---
#     if detect_urgency(user_input):
#         escalation_note = "\n\n⚠ Masalah terdeteksi URGENT. Jika langkah tidak berhasil, tiket akan diprioritaskan (SLA 2 jam)."
#     else:
#         escalation_note = ""

#     # --- Response ---
#     return f"""
# Kategori masalah: {best['category']}

# Langkah penyelesaian:
# {best['content']}
# {escalation_note}
# """


# # ==========================================
# # 4. CHAT INTERAKTIF
# # ==========================================
# print("=== SMART HELPDESK CHATBOT ===")
# print("Ketik 'exit' untuk keluar\n")

# while True:
#     user = input("User: ")

#     if user.lower() == "exit":
#         print("Terima kasih. Sistem helpdesk siap membantu Anda kembali.")
#         break

#     response = smart_helpdesk_chatbot(user)
#     print("Chatbot:", response)
#     print("-" * 50)