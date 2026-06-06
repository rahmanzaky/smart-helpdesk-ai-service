import os
import time
import uuid
import shutil
import logging
from fastapi import FastAPI, Request, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional, List
from src.services.rag_pipeline import chatbot
from fastapi import UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

app = FastAPI(title="SEJAHE AI Service", version="1.0.0")

# ==========================================
# 1. CORS CONFIGURATION
# ==========================================
_raw_origins = os.environ.get("ALLOWED_ORIGINS", "")
allowed_origins = [o.strip() for o in _raw_origins.split(",") if o.strip()] or ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# 2. VPC IP FILTER MIDDLEWARE
# ==========================================
@app.middleware("http")
async def vpc_ip_filter_middleware(request: Request, call_next):
    # Ambil IP (dari header proxy Nginx atau langsung dari client)
    client_ip = request.headers.get("X-Forwarded-For", request.client.host).split(",")[0].strip()

    # Cek apakah IP adalah IP internal Epson (Class A, Class C, atau Localhost)
    is_internal = (
        client_ip.startswith("10.") or
        client_ip.startswith("192.168.") or
        client_ip == "127.0.0.1" or
        client_ip == "::1"
    )

    # Jika IP dari luar (Internet Publik), tolak dengan 403 Forbidden
    if not is_internal:
        req_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        logger.warning("Access denied for external IP: %s", client_ip)
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={
                "success": False,
                "data": None,
                "message": "Endpoint ini hanya dapat diakses dari jaringan internal Epson (VPC).",
                "error": {
                    "code": "FORBIDDEN",
                    "message": f"Akses ditolak untuk IP: {client_ip}"
                },
                "request_id": req_id
            }
        )

    # Lolos pengecekan, teruskan request
    return await call_next(request)

# ==========================================
# 3. REQUEST ID MIDDLEWARE
# ==========================================
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response

# ==========================================
# 4. REQUEST & RESPONSE MODELS
# ==========================================
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

class SummarizeRequest(BaseModel):
    chat_id: int = Field(..., description="ID sesi chat")
    chat_history: str = Field(..., min_length=1, description="Riwayat percakapan dalam format teks")

# ==========================================
# 5. ENDPOINTS
# ==========================================
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

        logger.info("Query processed successfully in %dms (request_id=%s)", processing_time, req_id)
        return GlobalResponse(
            success=True,
            data=data,
            message="Operation successful",
            request_id=req_id
        )

    except Exception as e:
        logger.error("Error processing query (request_id=%s): %s", req_id, e)
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
    upload_dir = "static/uploads"
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)

    file_extension = file.filename.split(".")[-1]
    image_key = f"uploads/{int(time.time())}_{uuid.uuid4().hex}.{file_extension}"
    file_path = os.path.join("static", image_key)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    logger.info("Image uploaded: %s (chat_id=%d)", image_key, chat_id)
    return {
        "success": True,
        "data": {
            "image_key": image_key,
            "mime_type": file.content_type,
            "size_bytes": os.path.getsize(file_path),
            "expires_at": str(time.time() + 10800) # TTL 3 jam
        },
        "message": "Image uploaded successfully",
        "request_id": str(uuid.uuid4())
    }

@app.post("/api/v1/chatbot/summarize")
async def summarize_chat(request: SummarizeRequest, req_raw: Request):
    req_id = req_raw.headers.get("X-Request-ID", str(uuid.uuid4()))
    try:
        from src.services.gemini_service import summarize_chat_history
        summary = summarize_chat_history(request.chat_history)
        return {
            "success": True,
            "data": {"chat_id": request.chat_id, "summary": summary},
            "message": "Summary berhasil dibuat",
            "request_id": req_id,
        }
    except Exception as e:
        logger.error("Error summarizing chat (request_id=%s): %s", req_id, e)
        return {
            "success": False,
            "data": None,
            "message": "Gagal membuat summary",
            "error": {"code": "AI_SERVICE_UNAVAILABLE", "details": str(e)},
            "request_id": req_id,
        }

@app.get("/api/v1/health")
async def health_check():
    return {"status": "ok", "version": "v1.0"}
