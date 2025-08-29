/**
 * Service for handling zip creation, download, and Glowfic app launching
 */

import JSZip from 'jszip';

interface FacecastResult {
  expression: string;
  imageData?: string;
  error?: string;
}

class GlowficUploadService {

  /**
   * Create a zip file from facecast results and trigger download
   */
  static async createAndDownloadZip(
    results: FacecastResult[], 
    filename: string = 'facecasts.glowficgirllichgallery'
  ): Promise<void> {
    try {
      // Filter successful results
      const successfulResults = results.filter(r => r.imageData);
      
      if (successfulResults.length === 0) {
        throw new Error('No successful facecasts to zip');
      }

      // Create zip
      const zip = new JSZip();
      
      // Add each image to zip
      for (const result of successfulResults) {
        const imageData = result.imageData!;
        
        // Convert base64 to binary
        const base64Data = imageData.split(',')[1]; // Remove data:image/png;base64, prefix
        const binaryData = atob(base64Data);
        const bytes = new Uint8Array(binaryData.length);
        
        for (let i = 0; i < binaryData.length; i++) {
          bytes[i] = binaryData.charCodeAt(i);
        }
        
        // Create filename from expression
        const safeExpression = result.expression
          .replace(/[^a-zA-Z0-9\s-]/g, '') // Remove special chars
          .replace(/\s+/g, '-') // Replace spaces with hyphens
          .toLowerCase();
        
        const imageFilename = `facecast-${safeExpression}.png`;
        zip.file(imageFilename, bytes);
      }

      // Generate zip blob
      const zipBlob = await zip.generateAsync({ type: 'blob' });
      
      // Trigger download
      const downloadUrl = URL.createObjectURL(zipBlob);
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      
      // Clean up blob URL
      URL.revokeObjectURL(downloadUrl);
      
    } catch (error) {
      console.error('Error creating zip:', error);
      throw error;
    }
  }



  /**
   * Complete workflow: zip and download
   */
  static async zipDownloadAndLaunch(
    results: FacecastResult[],
    filename: string = 'facecasts.glowficgirllichgallery'
  ): Promise<void> {
    try {
      // Create and download zip
      console.log('Creating zip file...');
      await this.createAndDownloadZip(results, filename);
      console.log('Zip file downloaded successfully');
      
    } catch (error) {
      console.error('Error in zip/download workflow:', error);
      throw error;
    }
  }
}

export default GlowficUploadService;