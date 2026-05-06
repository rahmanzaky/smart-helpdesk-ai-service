# Smart Helpdesk AI Service

Node.js + Express service for analyzing EPSON printer defects using Google Gemini Vision API.

## Features

✅ Image-based defect analysis (Gemini Vision)
✅ Text-based defect analysis
✅ Combined image + text analysis
✅ Severity classification (low, medium, high, critical)
✅ Recommended actions for each defect type

## Prerequisites

- Node.js 18+
- Google Gemini API key
- npm/yarn

## Quick Start

### 1. Clone and setup
```bash
git clone https://github.com/YOUR_ORG/smart-helpdesk-ai-service.git
cd smart-helpdesk-ai-service
```

### 2. Install dependencies
```bash
npm install
```

### 3. Get Gemini API Key

1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Click "Create API key"
3. Copy the key

### 4. Setup environment
```bash
cp .env.example .env
# Edit .env and paste your Gemini API key
```

### 5. Create folder structure
```bash
mkdir -p src/{services,routes}
mkdir -p uploads
```

### 6. Copy source files
- Copy provided `.ts` files to `src/` directory
- Copy `package.json`, `tsconfig.json`, `.env.example`

### 7. Run service
```bash
npm run dev
```

Service will start on **http://localhost:8000**

## API Endpoints

### Health Check
```bash
GET /api/health
```

Response:
```json
{
  "status": "AI Service is running ✅",
  "service": "Gemini Vision Analysis"
}
```

### Analyze Image Only
```bash
POST /api/analyze/image
Content-Type: multipart/form-data

Form Data:
  - image: <image_file>
```

Response:
```json
{
  "success": true,
  "analysis": {
    "defectDetected": true,
    "defectType": "paper jam",
    "severity": "high",
    "description": "Paper is jammed in the feed mechanism",
    "recommendedAction": "Open the printer cover and carefully remove the jammed paper",
    "confidence": 0.95
  }
}
```

### Analyze Text Only
```bash
POST /api/analyze/text
Content-Type: application/json

{
  "description": "The printer is making strange noises and won't print"
}
```

### Analyze Image + Text
```bash
POST /api/analyze/combined
Content-Type: multipart/form-data

Form Data:
  - image: <image_file>
  - description: "The printer head seems misaligned"
```

## Testing with cURL

### Test health endpoint
```bash
curl http://localhost:8000/api/health
```

### Test image analysis
```bash
curl -X POST http://localhost:8000/api/analyze/image \
  -F "image=@/path/to/printer_image.jpg"
```

### Test text analysis
```bash
curl -X POST http://localhost:8000/api/analyze/text \
  -H "Content-Type: application/json" \
  -d '{"description":"Printer not responding"}'
```

## Folder Structure

```
smart-helpdesk-ai-service/
├── src/
│   ├── index.ts              # Main server
│   └── services/
│       └── geminiService.ts  # Gemini integration
├── uploads/                  # Temporary image storage
├── package.json
├── tsconfig.json
├── .env.example
└── README.md
```

## Environment Variables

```
PORT=8000                              # Service port
NODE_ENV=development                   # Environment
GEMINI_API_KEY=your_api_key_here      # Google Gemini API key
CORS_ORIGIN=http://localhost:5000     # Allowed origins
MAX_FILE_SIZE=5242880                 # Max upload size (5MB)
UPLOAD_DIR=./uploads                  # Upload directory
```

## Integration with Backend

In your backend service, call the AI service:

```typescript
// Backend example (Node.js)
async function analyzeDefect(imagePath: string, description?: string) {
  const formData = new FormData();
  formData.append('image', fs.createReadStream(imagePath));
  if (description) {
    formData.append('description', description);
  }

  const response = await fetch('http://localhost:8000/api/analyze/combined', {
    method: 'POST',
    body: formData,
  });

  return response.json();
}
```

## Deployment

### Docker
```bash
docker build -t smart-helpdesk-ai .
docker run -p 8000:8000 \
  -e GEMINI_API_KEY=your_key \
  smart-helpdesk-ai
```

### Railway/Render
1. Push code to GitHub
2. Connect to Railway/Render
3. Set environment variable `GEMINI_API_KEY`
4. Deploy

## Future Enhancements

- [ ] Caching analyzed images
- [ ] ML model fine-tuning on EPSON defect dataset
- [ ] Real-time defect detection
- [ ] Multi-language support
- [ ] Integration with EPSON knowledge base
- [ ] Defect prediction (preventive analysis)

## Troubleshooting

**"No API key provided"**
- Make sure `.env` has `GEMINI_API_KEY` set
- Check the key is valid in Google AI Studio

**"File too large"**
- Increase `MAX_FILE_SIZE` in `.env`
- Default is 5MB

**"CORS errors"**
- Update `CORS_ORIGIN` in `.env` with your frontend URL

## Support

For issues with Gemini API, visit [Google AI Documentation](https://ai.google.dev/docs)
