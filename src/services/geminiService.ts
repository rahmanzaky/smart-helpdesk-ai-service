import { GoogleGenerativeAI } from "@google/generative-ai";
import fs from "fs";
import path from "path";

const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY || "");

export interface AnalysisResult {
  defectDetected: boolean;
  defectType: string;
  severity: "low" | "medium" | "high" | "critical";
  description: string;
  recommendedAction: string;
  confidence: number;
}

export async function analyzeDefectImage(
  imagePath: string,
): Promise<AnalysisResult> {
  try {
    // Read image file and convert to base64
    const imageBuffer = fs.readFileSync(imagePath);
    const base64Image = imageBuffer.toString("base64");

    // Determine image type from file extension
    const ext = path.extname(imagePath).toLowerCase();
    const mimeType = getMimeType(ext);

    // Initialize model
    const model = genAI.getGenerativeModel({ model: "gemini-1.5-flash" });

    // Create the prompt for defect analysis
    const prompt = `You are an expert EPSON printer technician. Analyze this image and identify any defects or issues.

Provide your analysis in the following JSON format (no markdown, just plain JSON):
{
  "defectDetected": boolean,
  "defectType": "string (e.g., 'paper jam', 'ink leak', 'mechanical damage', 'thermal issue', 'none')",
  "severity": "string ('low', 'medium', 'high', or 'critical')",
  "description": "string (detailed description of the defect)",
  "recommendedAction": "string (what action to take)",
  "confidence": number (0-1 scale)
}

Be concise and technical. Focus on EPSON printer-specific issues.`;

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
    const jsonMatch = responseText.match(/\{[\s\S]*\}/);
    if (!jsonMatch) {
      console.error("Could not parse JSON from response:", responseText);
      return defaultResponse();
    }

    const analysis = JSON.parse(jsonMatch[0]) as AnalysisResult;
    return analysis;
  } catch (error) {
    console.error("Error analyzing image:", error);
    return defaultResponse();
  }
}

export async function analyzeDefectWithText(
  imagePath: string | null,
  text: string,
): Promise<AnalysisResult> {
  try {
    const model = genAI.getGenerativeModel({ model: "gemini-1.5-flash" });

    const prompt = `You are an expert EPSON printer technician. Based on the following information, identify any defects or issues:

User Description: "${text}"

${imagePath ? "[An image is also provided for analysis]" : "[No image provided]"}

Provide your analysis in JSON format (no markdown, just plain JSON):
{
  "defectDetected": boolean,
  "defectType": "string",
  "severity": "string ('low', 'medium', 'high', or 'critical')",
  "description": "string",
  "recommendedAction": "string",
  "confidence": number (0-1)
}`;

    const parts: any[] = [prompt];

    // If image exists, include it
    if (imagePath) {
      const imageBuffer = fs.readFileSync(imagePath);
      const base64Image = imageBuffer.toString("base64");
      const ext = path.extname(imagePath).toLowerCase();
      const mimeType = getMimeType(ext);

      parts.unshift({
        inlineData: {
          data: base64Image,
          mimeType: mimeType,
        },
      });
    }

    const response = await model.generateContent(parts as any);
    const responseText = response.response.text();

    const jsonMatch = responseText.match(/\{[\s\S]*\}/);
    if (!jsonMatch) {
      return defaultResponse();
    }

    const analysis = JSON.parse(jsonMatch[0]) as AnalysisResult;
    return analysis;
  } catch (error) {
    console.error("Error analyzing defect:", error);
    return defaultResponse();
  }
}

function getMimeType(
  ext: string,
): "image/jpeg" | "image/png" | "image/gif" | "image/webp" {
  const mimeTypes: Record<
    string,
    "image/jpeg" | "image/png" | "image/gif" | "image/webp"
  > = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
    ".webp": "image/webp",
  };
  return mimeTypes[ext] || "image/jpeg";
}

function defaultResponse(): AnalysisResult {
  return {
    defectDetected: false,
    defectType: "unknown",
    severity: "low",
    description: "Unable to analyze image",
    recommendedAction: "Please provide a clearer image",
    confidence: 0,
  };
}
