import React, { useState, useEffect } from 'react';
import GeminiService from '../services/GeminiService';
import GlowficUploadService from '../services/GlowficUploadService';
import ImageUpload from './ImageUpload';
import ExpressionGrid from './ExpressionGrid';
import ApiKeyInput from './ApiKeyInput';
import expressionsData from '../../expressions.json';

interface ExpressionResult {
  expression: string;
  imageData?: string;
  error?: string;
}

const FacecastGenerator: React.FC = () => {
  const [referenceImage, setReferenceImage] = useState<string>('');
  const [hasApiKey, setHasApiKey] = useState<boolean>(GeminiService.hasApiKey());
  const [isGenerating, setIsGenerating] = useState<boolean>(false);
  const [results, setResults] = useState<ExpressionResult[]>([]);
  const [selectedExpressions, setSelectedExpressions] = useState<string[]>([]);
  const [expandedCategories, setExpandedCategories] = useState<string[]>([]);
  const [customPrompt, setCustomPrompt] = useState<string>('Make the character in the reference image have the following expression: {expression}. Focus on the face and upper shoulders only, but otherwise try to replicate the reference image (colors, clothes, theme, age, setting) as closely as possible. The resulting image must be SQUARE format (1:1 aspect ratio).');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const unsubscribe = GeminiService.addApiKeyListener(setHasApiKey);
    return () => unsubscribe();
  }, []);

  const handleApiKeySubmit = (apiKey: string) => {
    GeminiService.setApiKey(apiKey);
    setError(null);
  };

  const getAllExpressions = (): string[] => {
    return selectedExpressions;
  };

  const getCategoryDisplayName = (categoryKey: string): string => {
    return categoryKey.split('_').map(word => 
      word.charAt(0).toUpperCase() + word.slice(1)
    ).join(' & ');
  };

  const handleExpressionToggle = (expression: string) => {
    setSelectedExpressions(prev => {
      if (prev.includes(expression)) {
        return prev.filter(e => e !== expression);
      } else {
        return [...prev, expression];
      }
    });
  };

  const handleCategoryToggle = (category: string) => {
    const categoryExpressions = expressionsData.actor_expressions[category as keyof typeof expressionsData.actor_expressions];
    if (!categoryExpressions) return;

    const allCategorySelected = categoryExpressions.every(expr => selectedExpressions.includes(expr));
    
    if (allCategorySelected) {
      // Unselect all expressions in this category
      setSelectedExpressions(prev => prev.filter(expr => !categoryExpressions.includes(expr)));
    } else {
      // Select all expressions in this category
      setSelectedExpressions(prev => {
        const newExpressions = [...prev];
        categoryExpressions.forEach(expr => {
          if (!newExpressions.includes(expr)) {
            newExpressions.push(expr);
          }
        });
        return newExpressions;
      });
    }
  };

  const selectAllExpressions = () => {
    const allExpressions: string[] = [];
    Object.values(expressionsData.actor_expressions).forEach(expressions => {
      allExpressions.push(...expressions);
    });
    setSelectedExpressions(allExpressions);
  };

  const clearAllExpressions = () => {
    setSelectedExpressions([]);
  };

  const isCategoryFullySelected = (category: string): boolean => {
    const categoryExpressions = expressionsData.actor_expressions[category as keyof typeof expressionsData.actor_expressions];
    if (!categoryExpressions) return false;
    return categoryExpressions.every(expr => selectedExpressions.includes(expr));
  };

  const isCategoryPartiallySelected = (category: string): boolean => {
    const categoryExpressions = expressionsData.actor_expressions[category as keyof typeof expressionsData.actor_expressions];
    if (!categoryExpressions) return false;
    return categoryExpressions.some(expr => selectedExpressions.includes(expr)) && !isCategoryFullySelected(category);
  };

  const toggleCategoryExpanded = (category: string) => {
    setExpandedCategories(prev => {
      if (prev.includes(category)) {
        return prev.filter(c => c !== category);
      } else {
        return [...prev, category];
      }
    });
  };

  const expandAllCategories = () => {
    setExpandedCategories(Object.keys(expressionsData.actor_expressions));
  };

  const collapseAllCategories = () => {
    setExpandedCategories([]);
  };

  const generateFacecasts = async () => {
    if (!referenceImage) {
      setError('Please upload a reference image first');
      return;
    }

    if (!hasApiKey) {
      setError('Please provide a Gemini API key');
      return;
    }

    const expressions = getAllExpressions();
    if (expressions.length === 0) {
      setError('Please select at least one expression');
      return;
    }

    setIsGenerating(true);
    setError(null);
    setResults([]);

    try {
      console.log(`Starting generation of ${expressions.length} facecasts...`);
      
      const batchResults = await GeminiService.generateFacecastBatch(
        referenceImage,
        expressions,
        4, // concurrency limit
        customPrompt
      );

      setResults(batchResults);
      console.log(`Generation complete: ${batchResults.filter(r => r.imageData).length}/${batchResults.length} successful`);
      
    } catch (error) {
      console.error('Error generating facecasts:', error);
      setError(`Error: ${error instanceof Error ? error.message : String(error)}`);
    } finally {
      setIsGenerating(false);
    }
  };

  const downloadAll = () => {
    const successfulResults = results.filter(r => r.imageData);
    if (successfulResults.length === 0) return;

    successfulResults.forEach((result, index) => {
      setTimeout(() => {
        const link = document.createElement('a');
        link.href = result.imageData!;
        link.download = `facecast-${result.expression.replace(/\s+/g, '-').toLowerCase()}.png`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
      }, index * 100); // Small delay between downloads
    });
  };

  const zipAndLaunchGlowfic = async () => {
    const successfulResults = results.filter(r => r.imageData);
    if (successfulResults.length === 0) {
      setError('No successful facecasts to upload');
      return;
    }

    try {
      setError(null);
      console.log(`Creating zip with ${successfulResults.length} facecasts...`);
      
      // Create timestamp for unique filename
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
      const zipFilename = `facecasts-${timestamp}.glowficgirllichgallery`;
      
      // Create zip, download, and launch app
      await GlowficUploadService.zipDownloadAndLaunch(successfulResults, zipFilename);
      
      console.log('Successfully created zip and launched Glowfic Gallery Manager!');
      
    } catch (error) {
      console.error('Error in zip/launch workflow:', error);
      setError(`Error preparing upload: ${error instanceof Error ? error.message : String(error)}`);
    }
  };

  const expressionCount = getAllExpressions().length;

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 space-y-8">
      {/* Header */}
      <div className="text-center space-y-4">
        <h1 className="text-4xl font-bold text-gray-900">Facecastify</h1>
        <p className="text-lg text-gray-600 max-w-2xl mx-auto">
          Generate portrait-style faces showing different expressions using AI. 
          Upload a reference image and select expression categories to create a complete set of facecasts.
        </p>
      </div>

      {/* API Key Section */}
      {!hasApiKey && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
          <h2 className="text-xl font-semibold text-blue-900 mb-4">
            🔑 Gemini API Key Required
          </h2>
          <p className="text-blue-800 mb-4">
            To generate facecasts, you need to provide a Gemini API key with access to the image generation models.
          </p>
          <ApiKeyInput onApiKeySubmit={handleApiKeySubmit} />
        </div>
      )}

      {/* Main Generation Interface */}
      {hasApiKey && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Panel - Controls */}
          <div className="lg:col-span-1 space-y-6">
            <div className="bg-white rounded-lg shadow-md p-6">
              <h2 className="text-xl font-semibold text-gray-800 mb-4">
                Reference Image
              </h2>
              <ImageUpload
                onImageUpload={setReferenceImage}
                currentImage={referenceImage}
                disabled={isGenerating}
              />
            </div>

            <div className="bg-white rounded-lg shadow-md p-6">
              <h2 className="text-xl font-semibold text-gray-800 mb-4">
                Custom Prompt
              </h2>
              <div className="space-y-3">
                <textarea
                  value={customPrompt}
                  onChange={(e) => setCustomPrompt(e.target.value)}
                  disabled={isGenerating}
                  rows={4}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-y"
                  placeholder="Enter custom prompt template..."
                />
                <p className="text-xs text-gray-500">
                  Use {"{expression}"} as a placeholder for the specific expression. 
                  This template will be applied to each selected expression.
                </p>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow-md p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-semibold text-gray-800">
                  Expression Selection
                </h2>
                <div className="text-xs space-x-2">
                  <button
                    onClick={selectAllExpressions}
                    className="text-blue-600 hover:underline"
                    disabled={isGenerating}
                  >
                    All
                  </button>
                  <span className="text-gray-400">|</span>
                  <button
                    onClick={clearAllExpressions}
                    className="text-red-600 hover:underline"
                    disabled={isGenerating}
                  >
                    None
                  </button>
                  <span className="text-gray-400">|</span>
                  <button
                    onClick={expandAllCategories}
                    className="text-green-600 hover:underline"
                    disabled={isGenerating}
                  >
                    Expand
                  </button>
                  <span className="text-gray-400">|</span>
                  <button
                    onClick={collapseAllCategories}
                    className="text-orange-600 hover:underline"
                    disabled={isGenerating}
                  >
                    Collapse
                  </button>
                </div>
              </div>
              
              <div className="space-y-1 max-h-96 overflow-y-auto">
                {Object.entries(expressionsData.actor_expressions).map(([category, expressions]) => (
                  <div key={category} className="border border-gray-200 rounded">
                    {/* Category Header */}
                    <div 
                      className="flex items-center justify-between p-3 bg-gray-50 hover:bg-gray-100 cursor-pointer rounded-t"
                      onClick={() => toggleCategoryExpanded(category)}
                    >
                      <div className="flex items-center space-x-3">
                        <div className="flex items-center">
                          <input
                            type="checkbox"
                            checked={isCategoryFullySelected(category)}
                            ref={(el) => {
                              if (el) el.indeterminate = isCategoryPartiallySelected(category);
                            }}
                            onChange={() => handleCategoryToggle(category)}
                            onClick={(e) => e.stopPropagation()}
                            disabled={isGenerating}
                            className="rounded border-gray-300 text-blue-600 focus:ring-blue-500 mr-3"
                          />
                          <div>
                            <div className="font-medium text-gray-800 text-sm">
                              {getCategoryDisplayName(category)}
                            </div>
                            <div className="text-xs text-gray-500">
                              {expressions.filter(expr => selectedExpressions.includes(expr)).length}/{expressions.length} selected
                            </div>
                          </div>
                        </div>
                      </div>
                      <div className="text-gray-400">
                        {expandedCategories.includes(category) ? '▼' : '▶'}
                      </div>
                    </div>

                    {/* Individual Expressions */}
                    {expandedCategories.includes(category) && (
                      <div className="p-2 space-y-1 bg-white border-t border-gray-100">
                        {expressions.map(expression => (
                          <label
                            key={expression}
                            className="flex items-center space-x-2 p-2 hover:bg-gray-50 rounded cursor-pointer text-sm"
                          >
                            <input
                              type="checkbox"
                              checked={selectedExpressions.includes(expression)}
                              onChange={() => handleExpressionToggle(expression)}
                              disabled={isGenerating}
                              className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                            />
                            <span className="text-gray-700 capitalize">
                              {expression}
                            </span>
                          </label>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>

              <div className="mt-4 pt-4 border-t border-gray-200">
                <p className="text-sm text-gray-600 mb-4">
                  {expressionCount} expression{expressionCount !== 1 ? 's' : ''} selected
                </p>
                <button
                  onClick={generateFacecasts}
                  disabled={!referenceImage || isGenerating || expressionCount === 0}
                  className={`w-full py-3 px-4 rounded-lg font-semibold ${
                    !referenceImage || isGenerating || expressionCount === 0
                      ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                      : 'bg-blue-600 hover:bg-blue-700 text-white'
                  }`}
                >
                  {isGenerating ? (
                    <div className="flex items-center justify-center space-x-2">
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                      <span>Generating...</span>
                    </div>
                  ) : (
                    `Generate ${expressionCount} Facecast${expressionCount !== 1 ? 's' : ''}`
                  )}
                </button>
              </div>
            </div>
          </div>

          {/* Right Panel - Results */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-lg shadow-md p-6">
              {results.length > 0 && (
                <div className="mb-4 flex justify-end space-x-3">
                  <button
                    onClick={downloadAll}
                    disabled={results.filter(r => r.imageData).length === 0}
                    className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg disabled:bg-gray-300 disabled:cursor-not-allowed"
                  >
                    Download All ({results.filter(r => r.imageData).length})
                  </button>
                  <button
                    onClick={zipAndLaunchGlowfic}
                    disabled={results.filter(r => r.imageData).length === 0}
                    className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg disabled:bg-gray-300 disabled:cursor-not-allowed flex items-center space-x-2"
                  >
                    <span>📤</span>
                    <span>Upload to Glowfic ({results.filter(r => r.imageData).length})</span>
                  </button>
                </div>
              )}
              
              <ExpressionGrid
                results={results}
                isGenerating={isGenerating}
              />
            </div>
          </div>
        </div>
      )}

      {/* Error Display */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center space-x-2">
            <div className="text-red-500">❌</div>
            <p className="text-red-700">{error}</p>
          </div>
        </div>
      )}
    </div>
  );
};

export default FacecastGenerator;