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
  private static readonly DOWNLOAD_TIMEOUT = 30000; // 30 seconds

  /**
   * Create a zip file from facecast results and trigger download
   */
  static async createAndDownloadZip(
    results: FacecastResult[], 
    filename: string = 'facecasts.glowficgirllichgallery'
  ): Promise<string | null> {
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
      
      // Wait for download to complete
      const downloadPath = await this.waitForDownload(filename);
      
      // Clean up blob URL
      URL.revokeObjectURL(downloadUrl);
      
      return downloadPath;
      
    } catch (error) {
      console.error('Error creating zip:', error);
      throw error;
    }
  }

  /**
   * Wait for download to complete and return the local file path
   */
  private static async waitForDownload(filename: string): Promise<string> {
    return new Promise((resolve, reject) => {
      // Try to detect download completion
      // Note: Browser security prevents direct access to download directory
      // This is a best-effort approach
      
      const startTime = Date.now();
      const checkInterval = setInterval(() => {
        const elapsed = Date.now() - startTime;
        
        if (elapsed > this.DOWNLOAD_TIMEOUT) {
          clearInterval(checkInterval);
          // Return default downloads path
          const defaultPath = this.getDefaultDownloadPath(filename);
          resolve(defaultPath);
        }
      }, 1000);
      
      // For now, assume download completes after 2 seconds
      // In a real implementation, you might use File System Access API
      // or Electron's download manager
      setTimeout(() => {
        clearInterval(checkInterval);
        const downloadPath = this.getDefaultDownloadPath(filename);
        resolve(downloadPath);
      }, 2000);
    });
  }

  /**
   * Get the expected download path for the file
   */
  private static getDefaultDownloadPath(filename: string): string {
    // Default browser download locations by OS
    const userAgent = navigator.userAgent;
    
    if (userAgent.includes('Win')) {
      return `${process.env.USERPROFILE || 'C:\\Users\\User'}\\Downloads\\${filename}`;
    } else if (userAgent.includes('Mac')) {
      return `/Users/${process.env.USER || 'user'}/Downloads/${filename}`;
    } else {
      // Linux
      return `/home/${process.env.USER || 'user'}/Downloads/${filename}`;
    }
  }

  /**
   * Launch Glowfic app with the downloaded zip file
   */
  static async launchGlowficApp(zipPath: string): Promise<void> {
    try {
      // Create custom URL to launch the app
      const encodedPath = encodeURIComponent(zipPath);
      const launchUrl = `glowficgirlichgallery://upload?file=${encodedPath}`;
      
      console.log(`Launching Glowfic app with: ${launchUrl}`);
      
      // Try to open the custom URL
      window.location.href = launchUrl;
      
    } catch (error) {
      console.error('Error launching Glowfic app:', error);
      
      // Fallback: Show instructions
      const message = `
Could not auto-launch Glowfic Gallery Manager.
Please run manually:

./glowfic_scraper.py --gui

Then drag the downloaded zip file: ${zipPath}
      `.trim();
      
      alert(message);
    }
  }

  /**
   * Complete workflow: zip, download, and launch app
   */
  static async zipDownloadAndLaunch(
    results: FacecastResult[],
    filename: string = 'facecasts.zip'
  ): Promise<void> {
    try {
      // Step 1: Create and download zip
      console.log('Creating zip file...');
      const zipPath = await this.createAndDownloadZip(results, filename);
      
      if (!zipPath) {
        throw new Error('Failed to create zip file');
      }
      
      console.log(`Zip downloaded to: ${zipPath}`);
      
      // Step 2: Wait a moment for download to settle
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Step 3: Launch Glowfic app
      console.log('Launching Glowfic Gallery Manager...');
      await this.launchGlowficApp(zipPath);
      
    } catch (error) {
      console.error('Error in zip/download/launch workflow:', error);
      throw error;
    }
  }
}

export default GlowficUploadService;