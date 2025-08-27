interface GeminiResponse {
  imageData?: string;
  textResponse?: string;
}

// interface GeminiBatchResponse {
//   images?: string[];
//   textResponse?: string;
// }

const API_KEY_STORAGE_KEY = 'gemini_api_key';

class GeminiService {
  private apiKey: string | null = null;
  private apiKeyListeners: ((hasApiKey: boolean) => void)[] = [];
  
  constructor() {
    this.loadApiKey();
  }
  
  private loadApiKey(): void {
    // First try to get from environment variables (Vite)
    // @ts-ignore - Vite specific environment variables
    const envApiKey = import.meta.env?.VITE_GEMINI_API_KEY;
    
    if (envApiKey) {
      this.apiKey = envApiKey;
      return;
    }
    
    // Then try localStorage
    const storedApiKey = localStorage.getItem(API_KEY_STORAGE_KEY);
    if (storedApiKey) {
      this.apiKey = storedApiKey;
    }
  }
  
  public setApiKey(key: string): void {
    this.apiKey = key;
    localStorage.setItem(API_KEY_STORAGE_KEY, key);
    this.notifyApiKeyListeners();
  }
  
  public hasApiKey(): boolean {
    return !!this.apiKey;
  }
  
  public addApiKeyListener(listener: (hasApiKey: boolean) => void): () => void {
    this.apiKeyListeners.push(listener);
    listener(this.hasApiKey());
    
    return () => {
      this.apiKeyListeners = this.apiKeyListeners.filter(l => l !== listener);
    };
  }
  
  private notifyApiKeyListeners(): void {
    const hasKey = this.hasApiKey();
    this.apiKeyListeners.forEach(listener => listener(hasKey));
  }
  
  async generateFacecast(referenceImageData: string, expression: string, customPrompt?: string): Promise<GeminiResponse> {
    try {
      const modelName = 'models/gemini-2.0-flash-exp';
      
      if (!this.apiKey) {
        throw new Error("No Gemini API key available. Please provide an API key.");
      }

      const base64Data = referenceImageData.split(',')[1];
      
      // Use custom prompt if provided, otherwise use default
      const defaultPrompt = `Make the character in the reference image have the following expression: ${expression}. Focus on the face and upper shoulders only, but otherwise try to replicate the reference image (colors, clothes, theme, age, setting) as closely as possible.`;
      const prompt = customPrompt ? customPrompt.replace('{expression}', expression) : defaultPrompt;
      
      const requestBody = {
        contents: [
          {
            parts: [
              {
                inlineData: {
                  data: base64Data,
                  mimeType: "image/png"
                }
              },
              {
                text: prompt
              }
            ],
            role: "user"
          }
        ],
        generationConfig: {
          responseModalities: ["Text", "Image"],
          temperature: 0.9
        }
      };
      
      const url = `https://generativelanguage.googleapis.com/v1beta/${modelName}:generateContent?key=${this.apiKey}`;
      
      const headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'facecastify/1.0.0',
        'x-goog-api-client': 'facecastify/1.0.0'
      };
      
      console.log(`Generating facecast for expression: ${expression}`);
      
      const response = await fetch(url, {
        method: 'POST',
        headers: headers,
        body: JSON.stringify(requestBody)
      });
      
      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`API request failed with status ${response.status}: ${errorText}`);
      }
      
      const result = await response.json();
      const geminiResponse: GeminiResponse = {};
      
      if (result.candidates && result.candidates.length > 0) {
        const candidate = result.candidates[0];
        if (candidate.content && candidate.content.parts) {
          for (const part of candidate.content.parts) {
            if (part.inlineData) {
              geminiResponse.imageData = `data:${part.inlineData.mimeType};base64,${part.inlineData.data}`;
            } else if (part.text) {
              geminiResponse.textResponse = part.text;
            }
          }
        }
      }
      
      if (!geminiResponse.imageData && !geminiResponse.textResponse) {
        throw new Error("No content found in Gemini response");
      }
      
      return geminiResponse;
    } catch (error) {
      console.error("Error generating facecast:", error);
      throw error;
    }
  }
  
  async generateFacecastBatch(
    referenceImageData: string, 
    expressions: string[], 
    concurrencyLimit: number = 4,
    customPrompt?: string
  ): Promise<{ expression: string; imageData?: string; error?: string }[]> {
    console.log(`Starting batch generation of ${expressions.length} facecasts with concurrency limit of ${concurrencyLimit}...`);
    
    const results: { expression: string; imageData?: string; error?: string }[] = [];
    
    try {
      for (let i = 0; i < expressions.length; i += concurrencyLimit) {
        const batch = [];
        const batchSize = Math.min(concurrencyLimit, expressions.length - i);
        
        for (let j = 0; j < batchSize; j++) {
          const expression = expressions[i + j];
          batch.push(
            this.generateFacecast(referenceImageData, expression, customPrompt)
              .then(response => ({ expression, imageData: response.imageData }))
              .catch(error => ({ expression, error: error.message }))
          );
        }
        
        console.log(`Processing batch ${Math.floor(i / concurrencyLimit) + 1}/${Math.ceil(expressions.length / concurrencyLimit)}...`);
        
        const batchResults = await Promise.all(batch);
        results.push(...batchResults);
        
        // Small delay between batches to avoid rate limiting
        if (i + concurrencyLimit < expressions.length) {
          await new Promise(resolve => setTimeout(resolve, 1000));
        }
      }
      
      console.log(`Batch generation complete. Generated ${results.filter(r => r.imageData).length} out of ${expressions.length} requested facecasts`);
      
      return results;
    } catch (error) {
      console.error("Error generating facecast batch:", error);
      throw error;
    }
  }
}

export default new GeminiService();