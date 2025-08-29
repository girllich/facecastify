# Facecastify - AI Expression Generator

**Live Application**: [https://girllich.github.io/facecastify/](https://girllich.github.io/facecastify/)

Facecastify is a dual-application project that generates facial expressions for character art using AI technology. The project consists of a TypeScript web application for generating expressions and a Python application for managing Glowfic galleries.

## 🎭 TypeScript Web Application

### Overview
A React-based web application that uses Google's Gemini AI to generate different facial expressions from a reference character image.

### Features
- **AI-Powered Expression Generation**: Upload a reference character image and generate multiple facial expressions
- **Customizable Expression Categories**: Choose from various emotion categories (happy, sad, angry, surprised, etc.)
- **Batch Processing**: Generate multiple expressions simultaneously
- **Secure API Key Management**: API keys are stored locally in browser storage only
- **Export Functionality**: Download generated expressions as individual images or as a zip file
- **Glowfic Integration**: Upload generated expressions directly to Glowfic galleries

### Technology Stack
- **Frontend**: React 19.1.1 with TypeScript
- **Build Tool**: Vite 7.1.2
- **AI Service**: Google Gemini AI (@google/genai)
- **Styling**: Tailwind CSS (inferred from component styles)
- **Deployment**: GitHub Pages

### Getting Started

#### Prerequisites
- Node.js (version 18 or higher)
- Google AI API key

#### Installation
```bash
# Clone the repository
git clone https://github.com/girllich/facecastify.git
cd facecastify

# Install dependencies
npm install

# Start development server
npm run dev
```

#### Getting a Google AI API Key
1. Go to the [Google AI Console](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the generated key and paste it into the application

**Privacy Note**: Your API key is stored only in your browser's local storage and never leaves your device except for direct communication with Google's Gemini API.

#### Building for Production
```bash
npm run build
```

#### Deploying to GitHub Pages
```bash
npm run deploy
```

### Usage
1. Enter your Gemini API key in the input field
2. Upload a reference character image
3. Select the expressions you want to generate
4. Customize the generation prompt if needed
5. Click "Generate Expressions" and wait for the AI to process
6. Download individual expressions or export all as a zip file

## 🐍 Python Application - Glowfic Scraper & Gallery Manager

### Overview
A comprehensive Python application for managing Glowfic.com galleries, including automated icon uploads, image processing, and gallery management through both command-line and GUI interfaces.

### Features
- **Glowfic Authentication**: Secure login with session persistence
- **Gallery Management**: List, browse, and manage user galleries
- **Automated Icon Upload**: Upload images to galleries with automatic resizing (150x150px)
- **Image Processing**: Automatic image scaling and format conversion
- **Batch Operations**: Upload multiple images simultaneously
- **GUI Interface**: PyQt6-based graphical interface for easy gallery management
- **File Association**: Register custom file types (.glowficgirllichgallery)
- **Cross-Platform**: Supports Linux, Windows, and macOS
- **Drag & Drop**: GUI supports drag-and-drop for images and zip files

### Technology Stack
- **Language**: Python 3.8+
- **GUI Framework**: PyQt6
- **Web Scraping**: requests, BeautifulSoup4
- **Image Processing**: Pillow (PIL)
- **Authentication**: keyring for secure credential storage
- **Package Management**: uv (Python package installer)

### Dependencies
```python
requests>=2.25.0
beautifulsoup4>=4.9.0
lxml>=4.6.0
python-dotenv>=0.19.0
pillow>=8.0.0
PyQt6>=6.0.0
keyring>=23.0.0
```

### Getting Started

#### Prerequisites
- Python 3.8 or higher
- Valid Glowfic.com account

#### Installation & Usage

##### Command Line Interface
```bash
# List all galleries
./glowfic_scraper.py --list-galleries

# Upload a single icon to a gallery
./glowfic_scraper.py --upload icon.jpg --gallery 12345 --keyword "happy expression"

# Resize image and upload
./glowfic_scraper.py --resize resized.jpg --upload large_image.png --gallery 12345

# Launch GUI interface
./glowfic_scraper.py --gui
```

##### Environment Configuration
Create a `.env` file for automatic authentication:
```env
GLOWFIC_USERNAME=your_username
GLOWFIC_PASSWORD=your_password
GLOWFIC_REMEMBER_ME=true
```

##### GUI Mode
The GUI provides a user-friendly interface with:
- Gallery browser with icon previews
- Drag-and-drop upload area
- Progress tracking for batch uploads
- Real-time upload status updates

### File Handlers & URL Schemes
The Python application can register itself as a handler for:
- **Custom URLs**: `glowficgirlichgallery://` scheme
- **File Types**: `.glowficgirllichgallery` files (zip archives of images)

```bash
# Register both handlers
./glowfic_scraper.py --register-all

# Register only URL scheme
./glowfic_scraper.py --register-handler

# Register only file association
./glowfic_scraper.py --register-files
```

## 📁 Project Structure

```
facecastify/
├── src/                          # TypeScript/React source code
│   ├── components/
│   │   ├── FacecastGenerator.tsx # Main application component
│   │   ├── ApiKeyInput.tsx       # API key input with privacy info
│   │   ├── ImageUpload.tsx       # Image upload component
│   │   └── ExpressionGrid.tsx    # Expression selection grid
│   ├── services/
│   │   ├── GeminiService.ts      # Gemini AI integration
│   │   └── GlowficUploadService.ts # Glowfic upload service
│   └── main.tsx                  # Application entry point
├── glowfic_scraper.py           # Python gallery manager
├── expressions.json             # Expression categories data
├── package.json                 # Node.js dependencies
├── vite.config.ts              # Vite configuration
└── README.md                   # This file
```

## 🔗 Integration

The two applications work together seamlessly:
1. Generate expressions using the web application
2. Export expressions as a `.glowficgirllichgallery` file
3. Open the file with the Python application
4. Upload expressions directly to your Glowfic galleries

## 🛠️ Development

### TypeScript Application Development
```bash
npm run dev        # Start development server
npm run build      # Build for production
npm run preview    # Preview production build
```

### Python Application Development
The Python script uses modern Python tooling with uv for dependency management and follows PEP standards for code organization.

## 📄 License

This project is part of the Glowfic.com ecosystem tools. Please ensure compliance with Glowfic.com's terms of service when using the gallery management features.

## 🤝 Contributing

Contributions are welcome! Please ensure that:
- TypeScript code follows React best practices
- Python code adheres to PEP 8 standards  
- New features include appropriate error handling
- UI changes maintain accessibility standards

## ⚠️ Important Notes

- **API Keys**: Never commit API keys to the repository
- **Authentication**: The Python application securely stores credentials using the system keyring
- **Rate Limiting**: Both applications implement appropriate rate limiting for API calls
- **Image Processing**: Images are automatically optimized for Glowfic's requirements (150x150px icons)
- **Privacy**: All processing happens locally; images are only sent to specified AI services and Glowfic