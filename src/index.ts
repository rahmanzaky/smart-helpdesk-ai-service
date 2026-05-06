import express, { Express, Request, Response } from "express";
import cors from "cors";
import dotenv from "dotenv";
import multer from "multer";
import path from "path";
import fs from "fs";
import {
  analyzeDefectImage,
  analyzeDefectWithText,
} from "./services/geminiService";

dotenv.config();

const app: Express = express();
const PORT = process.env.PORT || 8000;

// Create uploads directory if it doesn't exist
const uploadsDir = process.env.UPLOAD_DIR || "./uploads";
if (!fs.existsSync(uploadsDir)) {
  fs.mkdirSync(uploadsDir, { recursive: true });
}

// Middleware
app.use(cors({ origin: process.env.CORS_ORIGIN?.split(",") || "*" }));
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// File upload configuration
const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    cb(null, uploadsDir);
  },
  filename: (req, file, cb) => {
    const uniqueName = `${Date.now()}-${file.originalname}`;
    cb(null, uniqueName);
  },
});

const upload = multer({
  storage,
  limits: { fileSize: parseInt(process.env.MAX_FILE_SIZE || "5242880") },
  fileFilter: (req, file, cb) => {
    const allowedMimes = ["image/jpeg", "image/png", "image/gif", "image/webp"];
    if (allowedMimes.includes(file.mimetype)) {
      cb(null, true);
    } else {
      cb(new Error("Invalid file type. Only images are allowed."));
    }
  },
});

// Routes

/**
 * Health check endpoint
 */
app.get("/api/health", (_req: Request, res: Response) => {
  res.json({
    status: "AI Service is running ✅",
    service: "Gemini Vision Analysis",
  });
});

/**
 * Analyze defect from image only
 * POST /api/analyze/image
 */
app.post(
  "/api/analyze/image",
  upload.single("image"),
  async (req: Request, res: Response) => {
    try {
      if (!req.file) {
        return res.status(400).json({ error: "No image provided" });
      }

      const imagePath = req.file.path;
      const analysis = await analyzeDefectImage(imagePath);

      // Clean up uploaded file after analysis
      fs.unlink(imagePath, (err) => {
        if (err) console.error("Error deleting file:", err);
      });

      res.json({
        success: true,
        analysis,
        message: "Image analyzed successfully",
      });
    } catch (error) {
      res.status(500).json({
        error: "Failed to analyze image",
        details: error instanceof Error ? error.message : "Unknown error",
      });
    }
  },
);

/**
 * Analyze defect from image + text description
 * POST /api/analyze/combined
 */
app.post(
  "/api/analyze/combined",
  upload.single("image"),
  async (req: Request, res: Response) => {
    try {
      const { description } = req.body;

      if (!description) {
        return res.status(400).json({ error: "Description is required" });
      }

      let imagePath: string | null = null;
      if (req.file) {
        imagePath = req.file.path;
      }

      const analysis = await analyzeDefectWithText(imagePath, description);

      // Clean up uploaded file after analysis
      if (imagePath) {
        fs.unlink(imagePath, (err) => {
          if (err) console.error("Error deleting file:", err);
        });
      }

      res.json({
        success: true,
        analysis,
        message: "Defect analyzed successfully",
      });
    } catch (error) {
      res.status(500).json({
        error: "Failed to analyze defect",
        details: error instanceof Error ? error.message : "Unknown error",
      });
    }
  },
);

/**
 * Analyze defect from text description only
 * POST /api/analyze/text
 */
app.post(
  "/api/analyze/text",
  express.json(),
  async (req: Request, res: Response) => {
    try {
      const { description } = req.body;

      if (!description) {
        return res.status(400).json({ error: "Description is required" });
      }

      const analysis = await analyzeDefectWithText(null, description);

      res.json({
        success: true,
        analysis,
        message: "Description analyzed successfully",
      });
    } catch (error) {
      res.status(500).json({
        error: "Failed to analyze description",
        details: error instanceof Error ? error.message : "Unknown error",
      });
    }
  },
);

// 404 handler
app.use((_req: Request, res: Response) => {
  res.status(404).json({ error: "Route not found" });
});

// Error handler
app.use((err: Error, _req: Request, res: Response) => {
  console.error("Error:", err.message);
  res
    .status(500)
    .json({ error: "Internal server error", details: err.message });
});

// Start server
app.listen(PORT, () => {
  console.log(`✅ AI Service running on http://localhost:${PORT}`);
  console.log(`📸 Gemini Vision API enabled`);
  console.log(`\n🧪 Test endpoints:`);
  console.log(`   GET  http://localhost:${PORT}/api/health`);
  console.log(
    `   POST http://localhost:${PORT}/api/analyze/image (with image)`,
  );
  console.log(
    `   POST http://localhost:${PORT}/api/analyze/text (with description)`,
  );
  console.log(
    `   POST http://localhost:${PORT}/api/analyze/combined (image + text)\n`,
  );
});

export default app;
