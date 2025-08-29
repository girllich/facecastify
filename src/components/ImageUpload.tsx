import React, { useRef, useEffect, useState } from 'react';
import GeminiService from '../services/GeminiService';

interface ImageUploadProps {
  onImageUpload: (imageData: string) => void;
  currentImage?: string;
  disabled?: boolean;
}

const ImageUpload: React.FC<ImageUploadProps> = ({ 
  onImageUpload, 
  currentImage,
  disabled = false 
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [showGenerateModal, setShowGenerateModal] = useState(false);
  const [characterDescription, setCharacterDescription] = useState('old woman with red hair');
  const [generatePrompt, setGeneratePrompt] = useState('Create a portrait-style reference image of a {character}. The character should be an English character actor with an interesting, expressive face. The image should be square format (1:1 aspect ratio) and show the character from the head to upper shoulders. Focus on clear facial features suitable for generating expressions.');
  const [isGenerating, setIsGenerating] = useState(false);

  useEffect(() => {
    const handlePaste = (e: ClipboardEvent) => {
      if (disabled) return;
      
      const items = e.clipboardData?.items;
      if (!items) return;

      for (let i = 0; i < items.length; i++) {
        const item = items[i];
        if (item.type.startsWith('image/')) {
          e.preventDefault();
          const file = item.getAsFile();
          if (file) {
            const reader = new FileReader();
            reader.onload = (event) => {
              const result = event.target?.result as string;
              if (result) {
                onImageUpload(result);
              }
            };
            reader.readAsDataURL(file);
          }
          break;
        }
      }
    };

    // Add paste event listener to the document
    document.addEventListener('paste', handlePaste);
    
    return () => {
      document.removeEventListener('paste', handlePaste);
    };
  }, [onImageUpload, disabled]);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Check if it's an image
    if (!file.type.startsWith('image/')) {
      alert('Please select an image file');
      return;
    }

    const reader = new FileReader();
    reader.onload = (event: ProgressEvent<FileReader>) => {
      const result = event.target?.result as string;
      if (result) {
        onImageUpload(result);
      }
    };
    reader.readAsDataURL(file);

    // Reset the input
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleButtonClick = () => {
    fileInputRef.current?.click();
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (disabled) return;

    const files = e.dataTransfer.files;
    if (files.length > 0) {
      const file = files[0];
      if (file.type.startsWith('image/')) {
        const reader = new FileReader();
        reader.onload = (event) => {
          const result = event.target?.result as string;
          if (result) {
            onImageUpload(result);
          }
        };
        reader.readAsDataURL(file);
      }
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  const generateReferenceImage = async () => {
    if (!GeminiService.hasApiKey()) {
      alert('Please provide a Gemini API key first');
      return;
    }

    setIsGenerating(true);
    
    try {
      // Replace {character} placeholder in prompt
      const finalPrompt = generatePrompt.replace('{character}', characterDescription);
      
      console.log('Generating reference image with prompt:', finalPrompt);
      
      // Generate image using Gemini service
      const imageData = await GeminiService.generateImage('', finalPrompt);
      
      if (imageData) {
        onImageUpload(imageData);
        setShowGenerateModal(false);
        console.log('Reference image generated successfully');
      } else {
        throw new Error('No image data returned from Gemini');
      }
      
    } catch (error) {
      console.error('Error generating reference image:', error);
      alert(`Error generating image: ${error instanceof Error ? error.message : String(error)}`);
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <>
      {/* Generate Modal */}
      {showGenerateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-2xl w-full mx-4">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Generate Reference Image</h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Character Description
                </label>
                <input
                  type="text"
                  value={characterDescription}
                  onChange={(e) => setCharacterDescription(e.target.value)}
                  placeholder="e.g., old woman with red hair, young man with beard"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Generation Prompt
                </label>
                <textarea
                  value={generatePrompt}
                  onChange={(e) => setGeneratePrompt(e.target.value)}
                  rows={4}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Use {"{character}"} as a placeholder for the character description
                </p>
              </div>
            </div>
            
            <div className="flex justify-end space-x-3 mt-6">
              <button
                onClick={() => setShowGenerateModal(false)}
                disabled={isGenerating}
                className="px-4 py-2 text-gray-600 hover:text-gray-800 disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                onClick={generateReferenceImage}
                disabled={isGenerating || !characterDescription.trim()}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center space-x-2"
              >
                {isGenerating ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                    <span>Generating...</span>
                  </>
                ) : (
                  <span>Generate Image</span>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
      
      {/* Main Upload Area */}
    <div className="space-y-4">
      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        onChange={handleFileSelect}
        className="hidden"
        disabled={disabled}
      />
      
      <div
        onClick={handleButtonClick}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        className={`relative border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors ${
          disabled
            ? 'border-gray-200 bg-gray-50 cursor-not-allowed'
            : 'border-gray-300 hover:border-blue-400 hover:bg-blue-50'
        }`}
      >
        {currentImage ? (
          <div className="space-y-3">
            <img
              src={currentImage}
              alt="Reference"
              className="max-w-full max-h-48 mx-auto rounded-md shadow-sm object-contain"
            />
            <p className="text-sm text-gray-600">
              Click or drag to replace image
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            <div className="text-gray-400">
              <svg className="mx-auto h-12 w-12" stroke="currentColor" fill="none" viewBox="0 0 48 48">
                <path d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </div>
            <div>
              <p className="text-gray-600 font-medium">Upload or Generate Reference Image</p>
              <p className="text-sm text-gray-500">
                Click to browse, drag and drop, or paste (Ctrl+V)
              </p>
            </div>
          </div>
        )}
      </div>
      
      {/* Generate Button */}
      <div className="flex justify-center">
        <button
          onClick={() => setShowGenerateModal(true)}
          disabled={disabled}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center space-x-2"
        >
          <span>✨</span>
          <span>Generate Reference Image</span>
        </button>
      </div>
    </div>
    </>
  );
};

export default ImageUpload;