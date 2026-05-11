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
        response_data = chatbot(query_text=user_input)
        answer = response_data.get('response', 'Maaf, sistem tidak memberikan jawaban.')
        context_used = response_data.get('context', [])
        print("\n" + "="*50)
        print("🔧 HASIL ANALISIS SMART HELPDESK")
        print("="*50)
        print(f"Solusi & Rekomendasi:\n{answer}\n")
        print("="*50)
