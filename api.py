import os
import time
import uuid
import shutil
from fastapi import FastAPI, Request, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional, List
from src.services.rag_pipeline import chatbot  # Asumsi core logic kamu
from fastapi import UploadFile, File, Form

app = FastAPI(title="SEJAHE AI Service", version="1.0.0")

# --- 1. Request & Response Models sesuai Kontrak ---

class RAGContext(BaseModel):
    doc_id: str
    title: str
    similarity_score: float

class ChatbotResponseData(BaseModel):
    user_message_id: int
    assistant_message_id: int
    response: str
    defect_category: Optional[str] = None
    rag_context_used: List[RAGContext]
    processing_time_ms: int

class GlobalResponse(BaseModel):
    success: bool
    data: Optional[ChatbotResponseData] = None
    message: str
    request_id: str
    error: Optional[dict] = None

class QueryRequest(BaseModel):
    chat_id: int = Field(..., description="ID sesi chat")
    message: str = Field(..., min_length=1, max_length=2000)
    image_key: Optional[str] = None
    image_url: Optional[str] = None
    defect_category: Optional[str] = None

# --- 2. Middleware untuk Request ID ---
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response

# --- 3. Endpoint Utama: POST /api/v1/chatbot/query ---

@app.post("/api/v1/chatbot/query", response_model=GlobalResponse)
async def query_chatbot(request: QueryRequest, req_raw: Request):
    start_time = time.time()
    req_id = req_raw.headers.get("X-Request-ID", str(uuid.uuid4()))

    full_image_path = None
    if request.image_key:
        full_image_path = os.path.join("static", request.image_key)

    try:
        ai_result = chatbot(
            query_text=request.message,
            image_path=full_image_path,
            image_url=request.image_url,
        )
        
        processing_time = int((time.time() - start_time) * 1000)
        
        data = ChatbotResponseData(
            user_message_id=int(time.time()),
            assistant_message_id=int(time.time()) + 1,
            response=ai_result["response"], # Ambil kunci 'response'
            defect_category=request.defect_category or "Printing Quality",
            rag_context_used=[
                RAGContext(
                    doc_id=ctx["doc_id"], 
                    title=ctx["title"], 
                    similarity_score=ctx["score"]
                    ) for ctx in ai_result["context"]
            ],
            processing_time_ms=processing_time
        )
        
        
        # data = ChatbotResponseData(
        #     user_message_id=int(time.time()), # Dummy ID untuk contoh
        #     assistant_message_id=int(time.time()) + 1,
        #     response=ai_result["answer"],
        #     defect_category=request.defect_category or "Printing Quality",
        #     rag_context_used=[
        #         RAGContext(
        #             doc_id=ctx["doc_id"], 
        #             title=ctx["title"], 
        #             similarity_score=ctx["score"]
        #         ) for ctx in ai_result["context"]
        #     ],
        #     processing_time_ms=processing_time
        # )
        
        return GlobalResponse(
            success=True,
            data=data,
            message="Operation successful",
            request_id=req_id
        )

    except Exception as e:
        # Error handling sesuai Registry di kontrak 
        return GlobalResponse(
            success=False,
            message="Cloud AI service unreachable",
            error={"code": "AI_SERVICE_UNAVAILABLE", "details": str(e)},
            request_id=req_id
        )
    
# --- Endpoint: POST /api/v1/chatbot/upload-image ---
@app.post("/api/v1/chatbot/upload-image", status_code=201)
async def upload_image(
    chat_id: int = Form(...), 
    file: UploadFile = File(...)
):
    # Buat folder temporary jika belum ada
    upload_dir = "static/uploads"
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)

    # Buat nama file unik (image_key) 
    file_extension = file.filename.split(".")[-1]
    image_key = f"uploads/{int(time.time())}_{uuid.uuid4().hex}.{file_extension}"
    file_path = os.path.join("static", image_key)

    # Simpan file secara lokal di server
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Response sesuai Global Envelope & Model 3.3 
    return {
        "success": True,
        "data": {
            "image_key": image_key,
            "mime_type": file.content_type,
            "size_bytes": os.path.getsize(file_path),
            "expires_at": str(time.time() + 10800) # TTL 3 jam [cite: 900]
        },
        "message": "Image uploaded successfully",
        "request_id": str(uuid.uuid4())
    }

# --- 4. Health Check Endpoint ---
@app.get("/api/v1/health")
async def health_check():
    return {"status": "ok", "version": "v1.0"}
