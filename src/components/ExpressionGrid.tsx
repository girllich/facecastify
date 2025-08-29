import React from 'react';

interface ExpressionResult {
  expression: string;
  imageData?: string;
  error?: string;
}

interface ExpressionGridProps {
  results: ExpressionResult[];
  isGenerating: boolean;
  onDownload?: (imageData: string, expression: string) => void;
  onDelete?: (index: number) => void;
}

const ExpressionGrid: React.FC<ExpressionGridProps> = ({ 
  results, 
  isGenerating,
  onDownload,
  onDelete
}) => {
  const handleDownload = (imageData: string, expression: string) => {
    if (onDownload) {
      onDownload(imageData, expression);
      return;
    }

    // Default download behavior
    const link = document.createElement('a');
    link.href = imageData;
    link.download = `facecast-${expression.replace(/\s+/g, '-').toLowerCase()}.png`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const capitalizeWords = (str: string) => {
    return str.split(' ').map(word => 
      word.charAt(0).toUpperCase() + word.slice(1)
    ).join(' ');
  };

  if (results.length === 0 && !isGenerating) {
    return (
      <div className="text-center py-12 text-gray-500">
        <div className="text-6xl mb-4">🎭</div>
        <p className="text-lg">No facecasts generated yet</p>
        <p className="text-sm">Upload an image and click "Generate Facecasts" to begin</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-800">
          Generated Facecasts
        </h2>
        {results.length > 0 && (
          <p className="text-sm text-gray-600">
            {results.filter(r => r.imageData).length} / {results.length} successful
          </p>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        {results.map((result, index) => (
          <div
            key={`${result.expression}-${index}`}
            className="bg-white rounded-lg shadow-md overflow-hidden border border-gray-200"
          >
            <div className="aspect-[3/4] bg-gray-100 relative">
              {result.imageData ? (
                <>
                  <img
                    src={result.imageData}
                    alt={result.expression}
                    className="w-full h-full object-cover"
                  />
                  <div className="absolute top-2 right-2 flex space-x-1">
                    <button
                      onClick={() => handleDownload(result.imageData!, result.expression)}
                      className="p-2 bg-black bg-opacity-50 hover:bg-opacity-70 rounded-full text-white transition-opacity"
                      title="Download image"
                    >
                      <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z" clipRule="evenodd" />
                      </svg>
                    </button>
                    {onDelete && (
                      <button
                        onClick={() => onDelete(index)}
                        className="p-2 bg-red-500 bg-opacity-70 hover:bg-opacity-90 rounded-full text-white transition-opacity"
                        title="Delete image"
                      >
                        <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M9 2a1 1 0 000 2h2a1 1 0 100-2H9z" clipRule="evenodd" />
                          <path fillRule="evenodd" d="M10 5a2 2 0 00-2 2v6a2 2 0 104 0V7a2 2 0 00-2-2zM8 7v6h4V7H8z" clipRule="evenodd" />
                          <path d="M3 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zM4 6v10a2 2 0 002 2h8a2 2 0 002-2V6H4z" />
                        </svg>
                      </button>
                    )}
                  </div>
                </>
              ) : result.error ? (
                <div className="w-full h-full flex items-center justify-center text-red-500">
                  <div className="text-center p-4">
                    <div className="text-2xl mb-2">❌</div>
                    <p className="text-xs">Generation failed</p>
                  </div>
                </div>
              ) : (
                <div className="w-full h-full flex items-center justify-center">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                </div>
              )}
            </div>
            
            <div className="p-4">
              <h3 className="font-semibold text-sm text-gray-800 mb-1">
                {capitalizeWords(result.expression)}
              </h3>
              {result.error && (
                <p className="text-xs text-red-500 truncate" title={result.error}>
                  {result.error}
                </p>
              )}
            </div>
          </div>
        ))}

        {/* Show loading placeholders for pending generations */}
        {isGenerating && results.length === 0 && (
          Array.from({ length: 8 }, (_, index) => (
            <div
              key={`loading-${index}`}
              className="bg-white rounded-lg shadow-md overflow-hidden border border-gray-200 animate-pulse"
            >
              <div className="aspect-[3/4] bg-gray-200"></div>
              <div className="p-4">
                <div className="h-4 bg-gray-200 rounded w-3/4"></div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default ExpressionGrid;