#!/usr/bin/env node

/**
 * Smart Helpdesk AI Service - Node.js Scaffolder
 * Creates complete project structure for Gemini Vision-based defect analysis
 *
 * Usage: node scaffold-ai-nodejs.js
 */

import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

const colors = {
  reset: "\x1b[0m",
  green: "\x1b[32m",
  blue: "\x1b[34m",
  yellow: "\x1b[33m",
  cyan: "\x1b[36m",
};

function log(message, color = "reset") {
  console.log(`${colors[color]}${message}${colors.reset}`);
}

function createFile(filePath, content) {
  const dir = path.dirname(filePath);
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
  fs.writeFileSync(filePath, content);
  log(`  ✓ ${path.relative(process.cwd(), filePath)}`, "green");
}

function createFolder(folderPath) {
  if (!fs.existsSync(folderPath)) {
    fs.mkdirSync(folderPath, { recursive: true });
    log(`  ✓ ${path.relative(process.cwd(), folderPath)}/`, "cyan");
  }
}

// File contents
const files = {
  "package.json": `{
  "name": "smart-helpdesk-ai-service",
  "version": "1.0.0",
  "description": "Smart Helpdesk AI Service - Image Analysis with Gemini Vision",
  "main": "dist/index.js",
  "type": "module",
  "scripts": {
    "dev": "npm run build && node dist/index.js",
    "build": "tsc",
    "start": "node dist/index.js",
    "lint": "echo 'Linting disabled for MVP'",
    "format": "echo 'Formatting disabled for MVP'"
  },
  "dependencies": {
    "express": "^4.18.2",
    "dotenv": "^16.3.1",
    "cors": "^2.8.5",
    "@google/generative-ai": "^0.11.4",
    "axios": "^1.6.2",
    "multer": "^1.4.5-lts.1"
  },
  "devDependencies": {
    "@types/express": "^4.17.21",
    "@types/node": "^20.10.5",
    "@types/multer": "^1.4.11",
    "typescript": "^5.3.3"
  }
}`,

  "tsconfig.json": `{
  "compilerOptions": {
    "target": "ES2020",
    "module": "ES2020",
    "lib": ["ES2020"],
    "outDir": "./dist",
    "rootDir": "./src",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "resolveJsonModule": true,
    "declaration": true,
    "sourceMap": true,
    "moduleResolution": "node"
  },
  "include": ["src"],
  "exclude": ["node_modules", "dist"]
}`,

  ".env.example": `# AI Service
PORT=8000
NODE_ENV=development

# Gemini API
GEMINI_API_KEY=your_gemini_api_key_here

# CORS
CORS_ORIGIN=http://localhost:5000,http://localhost:3000

# File Upload
MAX_FILE_SIZE=5242880
UPLOAD_DIR=./uploads`,

  ".gitignore": `# Dependencies
node_modules/
package-lock.json
yarn.lock
pnpm-lock.yaml

# Build
dist/
*.tsbuildinfo

# Environment
.env
.env.local
.env.*.local

# Uploads
uploads/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~
.DS_Store

# Logs
logs/
*.log
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Cache
.eslintcache
.cache/`,

  "src/index.ts": `import express, { Express, Request, Response } from 'express';
import cors from 'cors';
import dotenv from 'dotenv';
import multer from 'multer';
import path from 'path';
import fs from 'fs';
import { analyzeDefectImage, analyzeDefectWithText } from './services/geminiService.js';

dotenv.config();

const app: Express = express();
const PORT = process.env.PORT || 8000;

// Create uploads directory if it doesn't exist
const uploadsDir = process.env.UPLOAD_DIR || './uploads';
if (!fs.existsSync(uploadsDir)) {
  fs.mkdirSync(uploadsDir, { recursive: true });
}

// Middleware
app.use(cors({ origin: process.env.CORS_ORIGIN?.split(',') || '*' }));
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// File upload configuration
const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    cb(null, uploadsDir);
  },
  filename: (req, file, cb) => {
    const uniqueName = \`\${Date.now()}-\${file.originalname}\`;
    cb(null, uniqueName);
  },
});

const upload = multer({
  storage,
  limits: { fileSize: parseInt(process.env.MAX_FILE_SIZE || '5242880') },
  fileFilter: (req, file, cb) => {
    const allowedMimes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp'];
    if (allowedMimes.includes(file.mimetype)) {
      cb(null, true);
    } else {
      cb(new Error('Invalid file type. Only images are allowed.'));
    }
  },
});

// Routes

/**
 * Health check endpoint
 */
app.get('/api/health', (_req: Request, res: Response) => {
  res.json({ status: 'AI Service is running ✅', service: 'Gemini Vision Analysis' });
});

/**
 * Analyze defect from image only
 * POST /api/analyze/image
 */
app.post('/api/analyze/image', upload.single('image'), async (req: Request, res: Response) => {
  try {
    if (!req.file) {
      return res.status(400).json({ error: 'No image provided' });
    }

    const imagePath = req.file.path;
    const analysis = await analyzeDefectImage(imagePath);

    // Clean up uploaded file after analysis
    fs.unlink(imagePath, (err) => {
      if (err) console.error('Error deleting file:', err);
    });

    res.json({
      success: true,
      analysis,
      message: 'Image analyzed successfully',
    });
  } catch (error) {
    res.status(500).json({
      error: 'Failed to analyze image',
      details: error instanceof Error ? error.message : 'Unknown error',
    });
  }
});

/**
 * Analyze defect from image + text description
 * POST /api/analyze/combined
 */
app.post('/api/analyze/combined', upload.single('image'), async (req: Request, res: Response) => {
  try {
    const { description } = req.body;

    if (!description) {
      return res.status(400).json({ error: 'Description is required' });
    }

    let imagePath: string | null = null;
    if (req.file) {
      imagePath = req.file.path;
    }

    const analysis = await analyzeDefectWithText(imagePath, description);

    // Clean up uploaded file after analysis
    if (imagePath) {
      fs.unlink(imagePath, (err) => {
        if (err) console.error('Error deleting file:', err);
      });
    }

    res.json({
      success: true,
      analysis,
      message: 'Defect analyzed successfully',
    });
  } catch (error) {
    res.status(500).json({
      error: 'Failed to analyze defect',
      details: error instanceof Error ? error.message : 'Unknown error',
    });
  }
});

/**
 * Analyze defect from text description only
 * POST /api/analyze/text
 */
app.post('/api/analyze/text', express.json(), async (req: Request, res: Response) => {
  try {
    const { description } = req.body;

    if (!description) {
      return res.status(400).json({ error: 'Description is required' });
    }

    const analysis = await analyzeDefectWithText(null, description);

    res.json({
      success: true,
      analysis,
      message: 'Description analyzed successfully',
    });
  } catch (error) {
    res.status(500).json({
      error: 'Failed to analyze description',
      details: error instanceof Error ? error.message : 'Unknown error',
    });
  }
});

// 404 handler
app.use((_req: Request, res: Response) => {
  res.status(404).json({ error: 'Route not found' });
});

// Error handler
app.use((err: Error, _req: Request, res: Response) => {
  console.error('Error:', err.message);
  res.status(500).json({ error: 'Internal server error', details: err.message });
});

// Start server
app.listen(PORT, () => {
  console.log(\`✅ AI Service running on http://localhost:\${PORT}\`);
  console.log(\`📸 Gemini Vision API enabled\`);
  console.log(\`\\n🧪 Test endpoints:\`);
  console.log(\`   GET  http://localhost:\${PORT}/api/health\`);
  console.log(\`   POST http://localhost:\${PORT}/api/analyze/image (with image)\`);
  console.log(\`   POST http://localhost:\${PORT}/api/analyze/text (with description)\`);
  console.log(\`   POST http://localhost:\${PORT}/api/analyze/combined (image + text)\\n\`);
});

export default app;`,

  "src/services/geminiService.ts": `import { GoogleGenerativeAI } from '@google/generative-ai';
import fs from 'fs';
import path from 'path';

const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY || '');

export interface AnalysisResult {
  defectDetected: boolean;
  defectType: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  description: string;
  recommendedAction: string;
  confidence: number;
}

export async function analyzeDefectImage(imagePath: string): Promise<AnalysisResult> {
  try {
    // Read image file and convert to base64
    const imageBuffer = fs.readFileSync(imagePath);
    const base64Image = imageBuffer.toString('base64');

    // Determine image type from file extension
    const ext = path.extname(imagePath).toLowerCase();
    const mimeType = getMimeType(ext);

    // Initialize model
    const model = genAI.getGenerativeModel({ model: 'gemini-1.5-flash' });

    // Create the prompt for defect analysis
    const prompt = \`You are an expert EPSON printer technician. Analyze this image and identify any defects or issues.

Provide your analysis in the following JSON format (no markdown, just plain JSON):
{
  "defectDetected": boolean,
  "defectType": "string (e.g., 'paper jam', 'ink leak', 'mechanical damage', 'thermal issue', 'none')",
  "severity": "string ('low', 'medium', 'high', or 'critical')",
  "description": "string (detailed description of the defect)",
  "recommendedAction": "string (what action to take)",
  "confidence": number (0-1 scale)
}

Be concise and technical. Focus on EPSON printer-specific issues.\`;

    // Send image to Gemini
    const response = await model.generateContent([
      {
        inlineData: {
          data: base64Image,
          mimeType: mimeType,
        },
      },
      prompt,
    ]);

    const responseText = response.response.text();

    // Parse JSON from response
    const jsonMatch = responseText.match(/\\{[\\s\\S]*\\}/);
    if (!jsonMatch) {
      console.error('Could not parse JSON from response:', responseText);
      return defaultResponse();
    }

    const analysis = JSON.parse(jsonMatch[0]) as AnalysisResult;
    return analysis;
  } catch (error) {
    console.error('Error analyzing image:', error);
    return defaultResponse();
  }
}

export async function analyzeDefectWithText(
  imagePath: string | null,
  text: string
): Promise<AnalysisResult> {
  try {
    const model = genAI.getGenerativeModel({ model: 'gemini-1.5-flash' });

    const prompt = \`You are an expert EPSON printer technician. Based on the following information, identify any defects or issues:

User Description: "\${text}"

\${imagePath ? '[An image is also provided for analysis]' : '[No image provided]'}

Provide your analysis in JSON format (no markdown, just plain JSON):
{
  "defectDetected": boolean,
  "defectType": "string",
  "severity": "string ('low', 'medium', 'high', or 'critical')",
  "description": "string",
  "recommendedAction": "string",
  "confidence": number (0-1)
}\`;

    let parts: any[] = [prompt];

    // If image exists, include it
    if (imagePath) {
      const imageBuffer = fs.readFileSync(imagePath);
      const base64Image = imageBuffer.toString('base64');
      const ext = path.extname(imagePath).toLowerCase();
      const mimeType = getMimeType(ext);

      parts.unshift({
        inlineData: {
          data: base64Image,
          mimeType: mimeType,
        },
      });
    }

    const response = await model.generateContent(parts);
    const responseText = response.response.text();

    const jsonMatch = responseText.match(/\\{[\\s\\S]*\\}/);
    if (!jsonMatch) {
      return defaultResponse();
    }

    const analysis = JSON.parse(jsonMatch[0]) as AnalysisResult;
    return analysis;
  } catch (error) {
    console.error('Error analyzing defect:', error);
    return defaultResponse();
  }
}

function getMimeType(ext: string): 'image/jpeg' | 'image/png' | 'image/gif' | 'image/webp' {
  const mimeTypes: Record<string, 'image/jpeg' | 'image/png' | 'image/gif' | 'image/webp'> = {
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.png': 'image/png',
    '.gif': 'image/gif',
    '.webp': 'image/webp',
  };
  return mimeTypes[ext] || 'image/jpeg';
}

function defaultResponse(): AnalysisResult {
  return {
    defectDetected: false,
    defectType: 'unknown',
    severity: 'low',
    description: 'Unable to analyze image',
    recommendedAction: 'Please provide a clearer image',
    confidence: 0,
  };
}`,
};

function scaffold() {
  log("\n🚀 Smart Helpdesk AI Service - Node.js Scaffolder\n", "blue");
  log(
    "Creating project structure for Gemini Vision defect analysis...\n",
    "cyan",
  );

  // Create root files
  log("📝 Creating configuration files...", "yellow");
  Object.entries(files).forEach(([filename, content]) => {
    if (!filename.includes("/")) {
      createFile(filename, content);
    }
  });

  // Create folders
  log("\n📁 Creating folder structure...", "yellow");
  createFolder("src");
  createFolder("src/services");
  createFolder("uploads");

  // Create nested files
  log("\n📄 Creating source files...", "yellow");
  Object.entries(files).forEach(([filename, content]) => {
    if (filename.includes("/")) {
      createFile(filename, content);
    }
  });

  log("\n✨ Project scaffolding complete!\n", "green");
  log("📋 Next steps:\n", "blue");
  log("  1. npm install");
  log("  2. Get Gemini API key from https://aistudio.google.com/app/apikey");
  log("  3. cp .env.example .env");
  log("  4. Add GEMINI_API_KEY to .env");
  log("  5. npm run dev\n");
  log("🎯 Service will run on http://localhost:8000\n", "green");
}

try {
  scaffold();
} catch (error) {
  log(
    `\n❌ Error: ${error instanceof Error ? error.message : "Unknown error"}\n`,
    "red",
  );
  process.exit(1);
}
