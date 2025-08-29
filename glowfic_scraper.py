#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.8"
# dependencies = [
#     "requests>=2.25.0",
#     "beautifulsoup4>=4.9.0",
#     "lxml>=4.6.0",
#     "python-dotenv>=0.19.0",
#     "pillow>=8.0.0",
#     "PyQt6>=6.0.0",
#     "keyring>=23.0.0",
# ]
# ///
"""
Glowfic.com Screen Scraping Application
A utility tool for logging into glowfic.com
"""

import requests
from bs4 import BeautifulSoup
import sys
import json
import os
import getpass
import argparse
import tempfile
import random
import string
import zipfile
import threading
import xml.etree.ElementTree as ET
from urllib.parse import urljoin
from dotenv import load_dotenv
from PIL import Image
from io import BytesIO
import platform
import subprocess

from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                            QWidget, QListWidget, QListWidgetItem, QLabel, QScrollArea,
                            QGridLayout, QProgressBar, QTextEdit, QPushButton, QSplitter,
                            QFrame, QMessageBox, QDialog, QLineEdit, QCheckBox, QFormLayout)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QMimeData
from PyQt6.QtGui import QPixmap, QDragEnterEvent, QDropEvent, QFont
import keyring

class GlowficScraper:
    def __init__(self):
        self.session = requests.Session()
        self.base_url = "https://glowfic.com"
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def get_csrf_token(self):
        """Extract CSRF token from the homepage"""
        try:
            response = self.session.get(self.base_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for CSRF token in meta tag
            csrf_meta = soup.find('meta', {'name': 'csrf-token'})
            if csrf_meta:
                return csrf_meta.get('content')
            
            # Look for CSRF token in login form
            csrf_input = soup.find('input', {'name': 'authenticity_token'})
            if csrf_input:
                return csrf_input.get('value')
                
            print("Warning: Could not find CSRF token")
            return None
            
        except requests.RequestException as e:
            print(f"Error fetching homepage: {e}")
            return None
    
    def login(self, username, password, remember_me=False):
        """Attempt to log in to glowfic.com"""
        print(f"Attempting to log in as: {username}")
        
        # Get CSRF token
        csrf_token = self.get_csrf_token()
        if not csrf_token:
            print("Failed to obtain CSRF token")
            return False
        
        # Prepare login data
        login_data = {
            'authenticity_token': csrf_token,
            'username': username,
            'password': password,
            'commit': 'Log in'
        }
        
        if remember_me:
            login_data['remember_me'] = '1'
        
        # Attempt login
        try:
            login_url = urljoin(self.base_url, '/login')
            response = self.session.post(login_url, data=login_data)
            response.raise_for_status()
            
            # Check if login was successful
            if self.is_logged_in():
                print("Login successful!")
                return True
            else:
                print("Login failed - invalid credentials or other error")
                # Try to extract error message
                soup = BeautifulSoup(response.content, 'html.parser')
                error_div = soup.find('div', class_='flash')
                if error_div:
                    print(f"Error message: {error_div.get_text().strip()}")
                return False
                
        except requests.RequestException as e:
            print(f"Error during login request: {e}")
            return False
    
    def is_logged_in(self):
        """Check if currently logged in by looking for login-specific elements"""
        try:
            response = self.session.get(self.base_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # If logged in, the login form should not be present
            login_link = soup.find('a', href='/login')
            if not login_link:
                return True
                
            # Check for user-specific elements that indicate login
            # This may need adjustment based on what the logged-in page looks like
            user_menu = soup.find('div', class_='user-menu')  # Adjust selector as needed
            if user_menu:
                return True
                
            return False
            
        except requests.RequestException as e:
            print(f"Error checking login status: {e}")
            return False
    
    def get_user_info(self):
        """Extract user information if logged in"""
        if not self.is_logged_in():
            print("Not logged in")
            return None
        
        try:
            response = self.session.get(self.base_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract user information (adjust selectors as needed)
            user_info = {}
            
            # This will need to be adjusted based on the actual logged-in page structure
            user_links = soup.find_all('a', href=lambda x: x and '/users/' in x)
            if user_links:
                user_info['profile_links'] = [link.get('href') for link in user_links]
            
            return user_info
            
        except requests.RequestException as e:
            print(f"Error getting user info: {e}")
            return None
    
    def scrape_page(self, url_path):
        """Scrape a specific page (requires login)"""
        if not self.is_logged_in():
            print("Must be logged in to scrape pages")
            return None
        
        try:
            url = urljoin(self.base_url, url_path)
            response = self.session.get(url)
            response.raise_for_status()
            
            return response.content
            
        except requests.RequestException as e:
            print(f"Error scraping page {url_path}: {e}")
            return None
    
    def save_cookies(self, filename='glowfic_cookies.json'):
        """Save session cookies to file"""
        cookies_dict = requests.utils.dict_from_cookiejar(self.session.cookies)
        try:
            with open(filename, 'w') as f:
                json.dump(cookies_dict, f, indent=2)
            print(f"Cookies saved to {filename}")
        except Exception as e:
            print(f"Error saving cookies: {e}")
    
    def load_cookies(self, filename='glowfic_cookies.json'):
        """Load session cookies from file"""
        try:
            with open(filename, 'r') as f:
                cookies_dict = json.load(f)
            
            for name, value in cookies_dict.items():
                self.session.cookies.set(name, value)
            print(f"Cookies loaded from {filename}")
            return True
        except Exception as e:
            print(f"Error loading cookies: {e}")
            return False
    
    def get_user_galleries(self, user_id=None):
        """Get user's galleries and parse them"""
        if user_id is None:
            # Try to extract user ID from logged-in user info
            user_info = self.get_user_info()
            if user_info and 'profile_links' in user_info:
                for link in user_info['profile_links']:
                    if '/users/' in link and '/galleries' in link:
                        user_id = link.split('/users/')[1].split('/')[0]
                        break
        
        if not user_id:
            print("Could not determine user ID")
            return None
        
        content = self.scrape_page(f"/users/{user_id}/galleries")
        if not content:
            return None
        
        return self.parse_galleries(content.decode('utf-8', errors='ignore'))
    
    def parse_galleries(self, html_content):
        """Parse galleries from HTML content"""
        soup = BeautifulSoup(html_content, 'html.parser')
        galleries = []
        
        # Find all gallery rows
        gallery_rows = soup.find_all('tr', id=lambda x: x and x.startswith('gallery-'))
        
        for row in gallery_rows:
            gallery_id = row.get('id', '').replace('gallery-', '')
            
            # Find gallery name
            name_cell = row.find('td', class_=lambda x: x and 'gallery-name' in x)
            if name_cell:
                name_link = name_cell.find('a')
                if name_link:
                    name = name_link.get_text().strip()
                    href = name_link.get('href', '')
                    
                    # Find icon count
                    icon_count_cell = row.find('td', class_=lambda x: x and 'gallery-icon-count' in x)
                    icon_count = 0
                    if icon_count_cell:
                        try:
                            icon_count = int(icon_count_cell.get_text().strip())
                        except ValueError:
                            pass
                    
                    galleries.append({
                        'id': gallery_id,
                        'name': name,
                        'icon_count': icon_count,
                        'url': href,
                        'add_icons_url': f"/galleries/{gallery_id}/add"
                    })
        
        # Also check for [Galleryless] which has a different structure
        galleryless = soup.find('a', href=lambda x: x and '/galleries/0' in x)
        if galleryless:
            galleries.insert(0, {
                'id': '0',
                'name': '[Galleryless]',
                'icon_count': 0,
                'url': '/users/471/galleries/0',
                'add_icons_url': '/galleries/0/add'
            })
        
        return galleries
    
    def generate_random_string(self, length=20):
        """Generate a random string like the JavaScript version"""
        chars = string.ascii_lowercase + string.digits
        return ''.join(random.choice(chars) for _ in range(length))
    
    def upload_to_s3(self, image_data, filename, s3_form_data, s3_url):
        """Upload image directly to S3 using the provided form data"""
        try:
            # Generate random key like JavaScript does
            form_key = s3_form_data.get('key', '')
            if '${filename}' in form_key:
                random_str = self.generate_random_string()
                new_key = form_key.replace('${filename}', f"{random_str}_{filename}")
            else:
                new_key = form_key
            
            # Prepare S3 form data
            s3_data = dict(s3_form_data)  # Copy the form data
            s3_data['key'] = new_key
            s3_data['Content-Type'] = 'image/jpeg'
            
            # Upload to S3
            files = {'file': (filename, image_data, 'image/jpeg')}
            
            print(f"Uploading to S3: {s3_url}")
            response = requests.post(s3_url, data=s3_data, files=files)
            
            print(f"S3 upload status: {response.status_code}")
            
            if response.status_code == 201:
                # Parse XML response to get Location and Key
                try:
                    root = ET.fromstring(response.text)
                    # Find Location and Key elements
                    location = None
                    key = None
                    
                    for elem in root.iter():
                        if elem.tag.endswith('Location'):
                            location = elem.text
                        elif elem.tag.endswith('Key'):
                            key = elem.text
                    
                    if location and key:
                        print(f"S3 upload successful! Location: {location}")
                        return location, key
                    else:
                        print(f"Could not parse S3 response: {response.text}")
                        return None, None
                        
                except ET.ParseError as e:
                    print(f"Error parsing S3 XML response: {e}")
                    print(f"Response content: {response.text}")
                    return None, None
            else:
                print(f"S3 upload failed: {response.status_code}")
                print(f"Response: {response.text}")
                return None, None
                
        except Exception as e:
            print(f"Error uploading to S3: {e}")
            return None, None
    
    def scale_image(self, image_path, output_path=None, size=(150, 150)):
        """Scale an image to the specified size for Glowfic icons"""
        try:
            with Image.open(image_path) as img:
                # Convert to RGB if necessary (handles RGBA, etc.)
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Resize using high-quality resampling
                img_resized = img.resize(size, Image.Resampling.LANCZOS)
                
                # If no output path specified, create a temporary file
                if output_path is None:
                    temp_file = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
                    output_path = temp_file.name
                    temp_file.close()
                
                # Save as JPEG with high quality
                img_resized.save(output_path, 'JPEG', quality=95)
                
                print(f"Image scaled to {size[0]}x{size[1]} and saved to {output_path}")
                return output_path
                
        except Exception as e:
            print(f"Error scaling image: {e}")
            return None
    
    def list_galleries(self):
        """List all user galleries in a readable format"""
        galleries = self.get_user_galleries()
        if not galleries:
            print("No galleries found or failed to fetch galleries")
            return None
        
        print(f"Found {len(galleries)} galleries:")
        for gallery in galleries:
            print(f"  {gallery['id']:>6}: {gallery['name']:<20} ({gallery['icon_count']} icons)")
        
        return galleries
    
    def upload_icon_to_gallery(self, gallery_id, image_path, keyword=None, credit=None, url=None, save_response=True):
        """Upload an icon to a specific gallery"""
        if not self.is_logged_in():
            print("Must be logged in to upload icons")
            return False
        
        if not os.path.exists(image_path):
            print(f"Image file not found: {image_path}")
            return False
        
        # Get the add icons page to retrieve the form and CSRF token
        add_url = f"/galleries/{gallery_id}/add"
        try:
            response = self.session.get(urljoin(self.base_url, add_url))
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find the upload form
            form = soup.find('form', class_='icon-upload')
            if not form:
                print("Could not find upload form")
                return False
            
            # Extract CSRF token
            csrf_token = None
            csrf_input = form.find('input', {'name': 'authenticity_token'})
            if csrf_input:
                csrf_token = csrf_input.get('value')
            
            if not csrf_token:
                print("Could not find CSRF token")
                return False
            
            # Get form action URL
            action_url = form.get('action', f'/galleries/{gallery_id}/icon')
            upload_url = urljoin(self.base_url, action_url)
            
            print(f"Uploading {image_path} to gallery {gallery_id}...")
            
            # Prepare the upload data
            upload_data = {
                'authenticity_token': csrf_token
            }
            
            # Add icon data - using array format as expected by the form
            if url:
                upload_data['icons[][url]'] = url
            if keyword:
                upload_data['icons[][keyword]'] = keyword
            if credit:
                upload_data['icons[][credit]'] = credit
            
            # Parse S3 form data from the page
            s3_form_data_str = form.get('data-form-data', '{}')
            s3_url = form.get('data-url', '')
            
            try:
                s3_form_data = json.loads(s3_form_data_str)
            except json.JSONDecodeError:
                print("Could not parse S3 form data")
                return False
            
            # Scale image in memory
            try:
                with Image.open(image_path) as img:
                    # Convert to RGB if necessary
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                    
                    # Resize to 150x150
                    img_resized = img.resize((150, 150), Image.Resampling.LANCZOS)
                    
                    # Save to memory buffer
                    img_buffer = BytesIO()
                    img_resized.save(img_buffer, format='JPEG', quality=95)
                    img_buffer.seek(0)
                    
                    print(f"Image scaled to 150x150 in memory")
                    
                    # Step 1: Upload to S3 first
                    s3_location, s3_key = self.upload_to_s3(
                        img_buffer, 
                        os.path.basename(image_path), 
                        s3_form_data, 
                        s3_url
                    )
                    
                    if not s3_location or not s3_key:
                        print("S3 upload failed")
                        return False
                    
                    # Step 2: Submit to Glowfic with S3 URL
                    upload_data['icons[][url]'] = s3_location
                    upload_data['icons[][s3_key]'] = s3_key
                    upload_data['icons[][filename]'] = os.path.basename(image_path)
                    
                    # Add keyword if filename doesn't have one
                    if not keyword:
                        # Use filename without extension as keyword (like JavaScript does)
                        base_name = os.path.splitext(os.path.basename(image_path))[0]
                        upload_data['icons[][keyword]'] = base_name
                    
                    print(f"Submitting to Glowfic with S3 URL: {s3_location}")
                    response = self.session.post(upload_url, data=upload_data)
                    
                    print(f"Glowfic response status: {response.status_code}")
                    
                    # Save response to file for analysis
                    if save_response:
                        response_filename = f"upload_response_{gallery_id}.html"
                        with open(response_filename, 'w', encoding='utf-8') as f:
                            f.write(response.text)
                        print(f"Response saved to {response_filename}")
                    
                    # Check for success or error messages in the response
                    if 'flash error' in response.text:
                        # Parse error message
                        soup_response = BeautifulSoup(response.text, 'html.parser')
                        error_div = soup_response.find('div', class_='flash error')
                        if error_div:
                            error_text = error_div.get_text().strip()
                            print(f"Upload failed: {error_text}")
                        return False
                    elif 'flash success' in response.text or response.status_code in [201, 302]:
                        return True
                    else:
                        # Check if we got redirected to gallery view (success)
                        return 'Eastsmiths (Gallery)' in response.text
                    
            except Exception as e:
                print(f"Error processing image: {e}")
                return False
                        
        except requests.RequestException as e:
            print(f"Error uploading icon: {e}")
            return False

class UploadWorker(QThread):
    """Worker thread for uploading files without blocking the UI"""
    progress = pyqtSignal(str)
    finished = pyqtSignal(bool, str)
    
    def __init__(self, scraper, gallery_id, files):
        super().__init__()
        self.scraper = scraper
        self.gallery_id = gallery_id
        self.files = files
    
    def run(self):
        """Upload files in background thread"""
        success_count = 0
        for i, file_path in enumerate(self.files, 1):
            try:
                filename = os.path.basename(file_path)
                self.progress.emit(f"Uploading {i}/{len(self.files)}: {filename}")
                
                # Use filename without extension as keyword
                keyword = os.path.splitext(filename)[0]
                
                result = self.scraper.upload_icon_to_gallery(
                    gallery_id=self.gallery_id,
                    image_path=file_path,
                    keyword=keyword,
                    save_response=False
                )
                
                if result:
                    success_count += 1
                    self.progress.emit(f"✓ Uploaded: {filename}")
                else:
                    self.progress.emit(f"✗ Failed: {filename}")
                    
            except Exception as e:
                self.progress.emit(f"✗ Error uploading {filename}: {e}")
        
        self.finished.emit(success_count == len(self.files), 
                          f"Completed: {success_count}/{len(self.files)} successful")

class DropArea(QFrame):
    """Drag and drop area for image files and zip files"""
    filesDropped = pyqtSignal(list)
    
    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.setFrameStyle(QFrame.Shape.Box)
        self.setStyleSheet("""
            QFrame {
                border: 2px dashed #aaa;
                border-radius: 10px;
                background-color: #f9f9f9;
                min-height: 150px;
            }
            QFrame:hover {
                border-color: #2B5797;
                background-color: #f0f8ff;
            }
        """)
        
        layout = QVBoxLayout()
        
        self.label = QLabel("Drop images or zip files here")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setPointSize(14)
        self.label.setFont(font)
        self.label.setStyleSheet("color: #666; margin: 20px;")
        
        layout.addWidget(self.label)
        self.setLayout(layout)
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dropEvent(self, event: QDropEvent):
        files = []
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if os.path.isfile(file_path):
                if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
                    files.append(file_path)
                elif file_path.lower().endswith('.zip'):
                    # Extract images from zip
                    extracted = self.extract_images_from_zip(file_path)
                    files.extend(extracted)
        
        if files:
            self.filesDropped.emit(files)
    
    def extract_images_from_zip(self, zip_path):
        """Extract image files from a zip archive"""
        extracted_files = []
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                for file_info in zip_ref.filelist:
                    if file_info.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
                        # Extract to temp directory
                        temp_dir = tempfile.mkdtemp()
                        extracted_path = zip_ref.extract(file_info, temp_dir)
                        extracted_files.append(extracted_path)
        except Exception as e:
            print(f"Error extracting zip: {e}")
        
        return extracted_files

class IconWidget(QLabel):
    """Widget to display a single icon"""
    def __init__(self, icon_url, keyword):
        super().__init__()
        self.setFixedSize(160, 180)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFrameStyle(QFrame.Shape.Box)
        self.setStyleSheet("border: 1px solid #ddd; margin: 5px; background: white;")
        
        layout = QVBoxLayout()
        
        # Icon image
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(150, 150)
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_label.setStyleSheet("border: none; background: #f5f5f5;")
        
        # Load image from URL
        self.load_image(icon_url)
        
        # Keyword label
        keyword_label = QLabel(keyword)
        keyword_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        keyword_label.setWordWrap(True)
        keyword_label.setMaximumHeight(20)
        keyword_label.setStyleSheet("border: none; font-size: 10px; color: #666;")
        
        layout.addWidget(self.icon_label)
        layout.addWidget(keyword_label)
        layout.setContentsMargins(5, 5, 5, 5)
        self.setLayout(layout)
    
    def load_image(self, url):
        """Load image from URL"""
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                pixmap = QPixmap()
                pixmap.loadFromData(response.content)
                if not pixmap.isNull():
                    scaled_pixmap = pixmap.scaled(150, 150, Qt.AspectRatioMode.KeepAspectRatio, 
                                                Qt.TransformationMode.SmoothTransformation)
                    self.icon_label.setPixmap(scaled_pixmap)
                else:
                    self.icon_label.setText("Invalid Image")
            else:
                self.icon_label.setText("Failed to Load")
        except Exception as e:
            self.icon_label.setText("Load Error")

class GlowficGUI(QMainWindow):
    """Main GUI window for Glowfic gallery management"""
    
    def __init__(self, scraper, initial_file=None):
        super().__init__()
        self.scraper = scraper
        self.current_gallery_id = None
        self.upload_worker = None
        self.pending_files = []
        
        self.setWindowTitle("Glowfic Gallery Manager")
        self.setGeometry(100, 100, 1200, 800)
        
        self.setup_ui()
        self.load_galleries()
        
        # Handle initial file if provided
        if initial_file:
            self.load_glowfic_file(initial_file)
    
    def setup_ui(self):
        """Set up the user interface"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main horizontal splitter
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left panel: Gallery list
        left_panel = QWidget()
        left_layout = QVBoxLayout()
        
        gallery_label = QLabel("Galleries")
        gallery_label.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        
        self.gallery_list = QListWidget()
        self.gallery_list.itemClicked.connect(self.on_gallery_selected)
        
        left_layout.addWidget(gallery_label)
        left_layout.addWidget(self.gallery_list)
        left_panel.setLayout(left_layout)
        
        # Right panel: Icons and upload area
        right_panel = QWidget()
        right_layout = QVBoxLayout()
        
        # Gallery title
        self.gallery_title = QLabel("Select a gallery")
        self.gallery_title.setStyleSheet("font-size: 14px; font-weight: bold; margin: 10px;")
        
        # Icons scroll area
        self.icons_scroll = QScrollArea()
        self.icons_scroll.setWidgetResizable(True)
        self.icons_widget = QWidget()
        self.icons_layout = QGridLayout()
        self.icons_widget.setLayout(self.icons_layout)
        self.icons_scroll.setWidget(self.icons_widget)
        
        # Upload area
        upload_label = QLabel("Upload Area")
        upload_label.setStyleSheet("font-size: 14px; font-weight: bold; margin: 10px;")
        
        self.drop_area = DropArea()
        self.drop_area.filesDropped.connect(self.on_files_dropped)
        
        # Progress area
        self.progress_text = QTextEdit()
        self.progress_text.setMaximumHeight(150)
        self.progress_text.setStyleSheet("background: #f9f9f9; border: 1px solid #ddd;")
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        
        # Add to right layout
        right_layout.addWidget(self.gallery_title)
        right_layout.addWidget(self.icons_scroll, 1)  # Give icons area most space
        right_layout.addWidget(upload_label)
        right_layout.addWidget(self.drop_area)
        right_layout.addWidget(QLabel("Upload Progress:"))
        right_layout.addWidget(self.progress_text)
        right_layout.addWidget(self.progress_bar)
        
        right_panel.setLayout(right_layout)
        
        # Add panels to splitter
        main_splitter.addWidget(left_panel)
        main_splitter.addWidget(right_panel)
        main_splitter.setSizes([300, 900])  # Left panel smaller
        
        # Main layout
        main_layout = QHBoxLayout()
        main_layout.addWidget(main_splitter)
        central_widget.setLayout(main_layout)
    
    def load_galleries(self):
        """Load user galleries into the list"""
        try:
            galleries = self.scraper.get_user_galleries()
            if galleries:
                self.gallery_list.clear()
                for gallery in galleries:
                    item_text = f"{gallery['name']} ({gallery['icon_count']} icons)"
                    item = QListWidgetItem(item_text)
                    item.setData(Qt.ItemDataRole.UserRole, gallery)
                    self.gallery_list.addItem(item)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load galleries: {e}")
    
    def on_gallery_selected(self, item):
        """Handle gallery selection"""
        gallery = item.data(Qt.ItemDataRole.UserRole)
        self.current_gallery_id = gallery['id']
        self.gallery_title.setText(f"Gallery: {gallery['name']} ({gallery['icon_count']} icons)")
        
        # Load gallery icons
        self.load_gallery_icons(gallery['id'])
        
        # If we have pending files from a loaded .glowficgirllichgallery file, offer to upload
        if self.pending_files:
            reply = QMessageBox.question(
                self, 
                "Upload Images?", 
                f"Upload {len(self.pending_files)} images to gallery '{gallery['name']}'?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.on_files_dropped(self.pending_files)
                self.pending_files = []  # Clear after upload
    
    def load_gallery_icons(self, gallery_id):
        """Load icons for the selected gallery"""
        try:
            # Clear existing icons
            for i in reversed(range(self.icons_layout.count())):
                self.icons_layout.itemAt(i).widget().setParent(None)
            
            # Get gallery page
            content = self.scraper.scrape_page(f"/galleries/{gallery_id}")
            if content:
                soup = BeautifulSoup(content.decode('utf-8'), 'html.parser')
                
                # Find all gallery icons
                icon_divs = soup.find_all('div', class_='gallery-icon')
                
                row, col = 0, 0
                for icon_div in icon_divs:
                    img_tag = icon_div.find('img', class_='icon')
                    keyword_span = icon_div.find('span', class_='icon-keyword')
                    
                    if img_tag and keyword_span:
                        icon_url = img_tag.get('src', '')
                        keyword = keyword_span.get_text().strip()
                        
                        icon_widget = IconWidget(icon_url, keyword)
                        self.icons_layout.addWidget(icon_widget, row, col)
                        
                        col += 1
                        if col >= 6:  # 6 icons per row
                            col = 0
                            row += 1
                            
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load gallery icons: {e}")
    
    def on_files_dropped(self, files):
        """Handle dropped files"""
        if not self.current_gallery_id:
            QMessageBox.warning(self, "No Gallery Selected", "Please select a gallery first")
            return
        
        if not files:
            return
        
        # Show progress
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate
        self.progress_text.clear()
        self.progress_text.append(f"Preparing to upload {len(files)} files to gallery {self.current_gallery_id}...")
        
        # Start upload worker
        self.upload_worker = UploadWorker(self.scraper, self.current_gallery_id, files)
        self.upload_worker.progress.connect(self.on_upload_progress)
        self.upload_worker.finished.connect(self.on_upload_finished)
        self.upload_worker.start()
    
    def on_upload_progress(self, message):
        """Handle upload progress updates"""
        self.progress_text.append(message)
        self.progress_text.ensureCursorVisible()
    
    def on_upload_finished(self, success, message):
        """Handle upload completion"""
        self.progress_bar.setVisible(False)
        self.progress_text.append(f"\n{message}")
        
        if success:
            # Refresh the current gallery
            if self.current_gallery_id:
                self.load_gallery_icons(self.current_gallery_id)
            # Refresh gallery list to update icon counts
            self.load_galleries()
    
    def load_glowfic_file(self, file_path):
        """Load and extract a .glowficgirllichgallery file"""
        try:
            if not os.path.exists(file_path):
                QMessageBox.warning(self, "File Not Found", f"Could not find file: {file_path}")
                return
            
            # Extract images from the zip file
            extracted_files = []
            temp_dir = tempfile.mkdtemp()
            
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                for file_info in zip_ref.filelist:
                    if file_info.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
                        extracted_path = zip_ref.extract(file_info, temp_dir)
                        extracted_files.append(extracted_path)
            
            if extracted_files:
                self.pending_files = extracted_files
                
                # Update drop area to show loaded files
                file_count = len(extracted_files)
                self.drop_area.label.setText(f"✓ Loaded {file_count} images from {os.path.basename(file_path)}\nSelect a gallery to upload to")
                self.drop_area.setStyleSheet("""
                    QFrame {
                        border: 2px solid #4CAF50;
                        border-radius: 10px;
                        background-color: #f0f8f0;
                        min-height: 150px;
                    }
                """)
                
                # Show progress message
                self.progress_text.append(f"📁 Loaded {file_count} images from {os.path.basename(file_path)}")
                self.progress_text.append("👈 Select a gallery from the left panel to upload to")
                
            else:
                QMessageBox.warning(self, "No Images Found", f"No image files found in {os.path.basename(file_path)}")
                
        except Exception as e:
            QMessageBox.critical(self, "Error Loading File", f"Failed to load {os.path.basename(file_path)}:\n{e}")

class LoginDialog(QDialog):
    """Login dialog for credentials"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Glowfic Login")
        self.setModal(True)
        self.setFixedSize(350, 200)
        
        layout = QFormLayout()
        
        # Username field
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter your Glowfic username")
        
        # Password field  
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("Enter your password")
        
        # Remember checkbox
        self.remember_check = QCheckBox("Remember credentials")
        self.remember_check.setChecked(True)
        
        # Buttons
        button_layout = QHBoxLayout()
        self.login_button = QPushButton("Login")
        self.cancel_button = QPushButton("Cancel")
        
        self.login_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)
        self.login_button.setDefault(True)
        
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.login_button)
        
        # Add to form
        layout.addRow("Username:", self.username_input)
        layout.addRow("Password:", self.password_input)
        layout.addRow(self.remember_check)
        layout.addRow(button_layout)
        
        self.setLayout(layout)
        
        # Try to load stored credentials
        self.load_stored_credentials()
    
    def load_stored_credentials(self):
        """Load credentials from keyring if available"""
        try:
            stored_username = keyring.get_password("glowfic.com", "username")
            if stored_username:
                self.username_input.setText(stored_username)
                stored_password = keyring.get_password("glowfic.com", stored_username)
                if stored_password:
                    self.password_input.setText(stored_password)
        except Exception:
            pass  # Ignore keyring errors
    
    def get_credentials(self):
        """Get the entered credentials"""
        return self.username_input.text().strip(), self.password_input.text().strip()
    
    def should_remember(self):
        """Check if credentials should be remembered"""
        return self.remember_check.isChecked()

def get_credentials_for_gui():
    """Get credentials for GUI mode using Qt dialog"""
    # Try .env first
    username = os.getenv('GLOWFIC_USERNAME')
    password = os.getenv('GLOWFIC_PASSWORD')
    
    if username and password:
        return username, password
    
    # Show login dialog
    app = QApplication.instance()
    if not app:
        app = QApplication([])
    
    dialog = LoginDialog()
    if dialog.exec() == QDialog.DialogCode.Accepted:
        username, password = dialog.get_credentials()
        
        if username and password and dialog.should_remember():
            try:
                keyring.set_password("glowfic.com", username, password)
                keyring.set_password("glowfic.com", "username", username)
            except Exception as e:
                print(f"Warning: Could not store credentials: {e}")
        
        return username, password
    
    return None, None

def register_url_handler():
    """Register glowficgirlichgallery:// URL scheme handler cross-platform"""
    script_path = os.path.abspath(__file__)
    scheme = "glowficgirlichgallery"
    
    system = platform.system()
    
    if system == "Linux":
        return register_url_handler_linux(script_path, scheme)
    elif system == "Windows":
        return register_url_handler_windows(script_path, scheme)
    elif system == "Darwin":  # macOS
        return register_url_handler_macos(script_path, scheme)
    else:
        print(f"URL handler registration not supported on {system}")
        return False

def register_url_handler_linux(script_path, scheme):
    """Register URL handler on Linux using xdg-settings"""
    try:
        # Create desktop file content
        desktop_content = f"""[Desktop Entry]
Version=1.0
Type=Application
Name=Glowfic Gallery Handler
Comment=Handle {scheme}:// URLs and launch gallery manager
Exec={script_path} --gui %u
Icon=glowfic-gallery-manager
NoDisplay=true
StartupNotify=true
MimeType=x-scheme-handler/{scheme};
"""
        
        # Write to user applications directory
        apps_dir = os.path.expanduser("~/.local/share/applications")
        os.makedirs(apps_dir, exist_ok=True)
        
        desktop_file = os.path.join(apps_dir, "glowfic-handler.desktop")
        with open(desktop_file, 'w') as f:
            f.write(desktop_content)
        
        # Make executable
        os.chmod(desktop_file, 0o755)
        
        # Register with xdg-settings
        result = subprocess.run([
            "xdg-settings", "set", "default-url-scheme-handler", 
            scheme, "glowfic-handler.desktop"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"Successfully registered {scheme}:// URL handler on Linux")
            return True
        else:
            print(f"Failed to register URL handler: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"Error registering Linux URL handler: {e}")
        return False

def register_url_handler_windows(script_path, scheme):
    """Register URL handler on Windows using registry"""
    print(f"Windows URL handler registration for {scheme}:// not yet implemented")
    print("To register manually on Windows, run these commands as Administrator:")
    print(f'1. reg add "HKEY_CLASSES_ROOT\\{scheme}" /ve /d "Glowfic Gallery Handler"')
    print(f'2. reg add "HKEY_CLASSES_ROOT\\{scheme}\\shell\\open\\command" /ve /d "\\"{script_path}\\" --gui \\"%1\\""')
    print(f'3. reg add "HKEY_CLASSES_ROOT\\{scheme}" /v "URL Protocol" /t REG_SZ /d ""')
    return False

def register_url_handler_macos(script_path, scheme):
    """Register URL handler on macOS using LSSetDefaultHandlerForURLScheme"""  
    print(f"macOS URL handler registration for {scheme}:// not yet implemented")
    print("To register manually on macOS:")
    print("1. Create an .app bundle with Info.plist containing CFBundleURLSchemes")
    print(f"2. defaults write com.apple.LaunchServices LSHandlers -array-add '{{LSHandlerURLScheme={scheme};LSHandlerRoleAll=com.yourapp.glowfic;}}'")
    print("3. /System/Library/Frameworks/CoreServices.framework/Versions/A/Frameworks/LaunchServices.framework/Versions/A/Support/lsregister -kill -r -domain local -domain system -domain user")
    return False

def register_file_handler():
    """Register .glowficgirllichgallery file association cross-platform"""
    script_path = os.path.abspath(__file__)
    extension = "glowficgirllichgallery"
    
    system = platform.system()
    
    if system == "Linux":
        return register_file_handler_linux(script_path, extension)
    elif system == "Windows":
        return register_file_handler_windows(script_path, extension)
    elif system == "Darwin":  # macOS
        return register_file_handler_macos(script_path, extension)
    else:
        print(f"File handler registration not supported on {system}")
        return False

def register_file_handler_linux(script_path, extension):
    """Register file association on Linux"""
    try:
        # Create MIME type
        mime_type = f"application/x-{extension}"
        
        # Create desktop file for file association
        desktop_content = f"""[Desktop Entry]
Version=1.0
Type=Application
Name=Glowfic Gallery File Handler
Comment=Open .{extension} files with Glowfic Gallery Manager
Exec={script_path} --gui %f
Icon=glowfic-gallery-manager
NoDisplay=true
StartupNotify=true
MimeType={mime_type};
"""
        
        # Write desktop file
        apps_dir = os.path.expanduser("~/.local/share/applications")
        os.makedirs(apps_dir, exist_ok=True)
        
        desktop_file = os.path.join(apps_dir, "glowfic-file-handler.desktop")
        with open(desktop_file, 'w') as f:
            f.write(desktop_content)
        
        os.chmod(desktop_file, 0o755)
        
        # Create MIME type definition
        mime_dir = os.path.expanduser("~/.local/share/mime/packages")
        os.makedirs(mime_dir, exist_ok=True)
        
        mime_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<mime-info xmlns="http://www.freedesktop.org/standards/shared-mime-info">
  <mime-type type="{mime_type}">
    <comment>Glowfic Gallery Package</comment>
    <glob pattern="*.{extension}"/>
  </mime-type>
</mime-info>
"""
        
        mime_file = os.path.join(mime_dir, f"{extension}.xml")
        with open(mime_file, 'w') as f:
            f.write(mime_content)
        
        # Update MIME database
        subprocess.run(["update-mime-database", os.path.expanduser("~/.local/share/mime")], 
                      capture_output=True)
        
        # Associate file type with application
        subprocess.run(["xdg-mime", "default", "glowfic-file-handler.desktop", mime_type], 
                      capture_output=True)
        
        print(f"Successfully registered .{extension} file association on Linux")
        return True
        
    except Exception as e:
        print(f"Error registering Linux file handler: {e}")
        return False

def register_file_handler_windows(script_path, extension):
    """Register file association on Windows"""
    print(f"Windows file association for .{extension} not yet implemented")
    print("To register manually on Windows, run as Administrator:")
    print(f'1. reg add "HKEY_CLASSES_ROOT\\.{extension}" /ve /d "GlowficGalleryFile"')
    print(f'2. reg add "HKEY_CLASSES_ROOT\\GlowficGalleryFile" /ve /d "Glowfic Gallery Package"')
    print(f'3. reg add "HKEY_CLASSES_ROOT\\GlowficGalleryFile\\shell\\open\\command" /ve /d "\\"{script_path}\\" --gui \\"%1\\""')
    return False

def register_file_handler_macos(script_path, extension):
    """Register file association on macOS"""
    print(f"macOS file association for .{extension} not yet implemented")
    print("To register manually on macOS:")
    print("1. Create .app bundle with Info.plist containing CFBundleDocumentTypes")
    print(f"2. Add file extension .{extension} to CFBundleTypeExtensions")
    print("3. Run: /System/Library/Frameworks/CoreServices.framework/Versions/A/Frameworks/LaunchServices.framework/Versions/A/Support/lsregister -kill -r -domain local -domain system -domain user")
    return False

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Glowfic Icon Upload Tool - Automated gallery management for glowfic.com',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --list-galleries
  %(prog)s --url /users/471/galleries
  %(prog)s --upload portrait.jpg --gallery 27821 --keyword "happy expression"
  %(prog)s --resize output.jpg --upload large_image.png

The tool automatically handles authentication, image resizing to 150x150 pixels,
S3 upload, and gallery management through the Glowfic API.
        """
    )
    
    parser.add_argument('--url', metavar='PATH', 
                       help='Fetch any authenticated URL path (e.g., /users/471/galleries)')
    parser.add_argument('--list-galleries', action='store_true', 
                       help='Display all user galleries with icon counts')
    parser.add_argument('--upload', metavar='FILE', 
                       help='Path to image file to upload (auto-resized to 150x150)')
    parser.add_argument('--gallery', metavar='ID', 
                       help='Gallery ID for upload (required with --upload)')
    parser.add_argument('--keyword', metavar='TEXT', 
                       help='Keyword/description for uploaded icon')
    parser.add_argument('--credit', metavar='TEXT', 
                       help='Artist credit for uploaded icon') 
    parser.add_argument('--icon-url', metavar='URL', 
                       help='Source URL for uploaded icon (optional)')
    parser.add_argument('--resize', metavar='OUTPUT', 
                       help='Resize image to 150x150 and save locally (requires --upload)')
    parser.add_argument('--gui', action='store_true',
                       help='Launch graphical user interface')
    parser.add_argument('--register-handler', action='store_true',
                       help='Register glowficgirlichgallery:// URL scheme handler')
    parser.add_argument('--register-files', action='store_true',
                       help='Register .glowficgirllichgallery file association')
    parser.add_argument('--register-all', action='store_true',
                       help='Register both URL scheme and file association')
    parser.add_argument('file', nargs='?',
                       help='Glowfic gallery file to open (.glowficgirllichgallery)')
    
    args = parser.parse_args()
    
    # Load environment variables from .env file
    load_dotenv()
    
    # Handle registrations (doesn't need scraper)
    if args.register_handler:
        success = register_url_handler()
        if success:
            print("URL handler registered successfully!")
            print("You can now use glowficgirlichgallery:// URLs in browsers")
        else:
            print("URL handler registration failed or not supported")
        return
    
    if args.register_files:
        success = register_file_handler()
        if success:
            print("File handler registered successfully!")
            print("You can now double-click .glowficgirllichgallery files to open them")
        else:
            print("File handler registration failed or not supported")
        return
    
    if args.register_all:
        url_success = register_url_handler()
        file_success = register_file_handler()
        
        if url_success and file_success:
            print("Both handlers registered successfully!")
            print("✓ URL scheme: glowficgirlichgallery://")
            print("✓ File type: .glowficgirllichgallery")
        elif url_success:
            print("URL handler registered, but file handler failed")
        elif file_success:
            print("File handler registered, but URL handler failed")
        else:
            print("Both registrations failed or not supported")
        return
    
    scraper = GlowficScraper()
    
    # Handle GUI launch (including file opening)
    if args.gui or args.file:
        load_dotenv()
        
        # Try to load existing cookies
        scraper.load_cookies()
        
        # Check if already logged in
        if not scraper.is_logged_in():
            username, password = get_credentials_for_gui()
            
            if not username or not password:
                print("Login cancelled")
                return
            
            if not scraper.login(username, password, True):
                QMessageBox.critical(None, "Login Failed", "Invalid username or password")
                return
            
            scraper.save_cookies()
        
        # Launch GUI
        app = QApplication.instance()
        if not app:
            app = QApplication(sys.argv)
        
        window = GlowficGUI(scraper, args.file)
        window.show()
        sys.exit(app.exec())
    
    # Handle resize command (doesn't need login)
    if args.resize:
        if not args.upload:
            print("Error: --upload is required when using --resize")
            return
        
        print(f"Resizing {args.upload} to 150x150 and saving as {args.resize}")
        result = scraper.scale_image(args.upload, args.resize)
        if result:
            print(f"Image resized and saved to: {result}")
        else:
            print("Failed to resize image")
        return
    
    # Try to load existing cookies
    scraper.load_cookies()
    
    # Check if already logged in
    if scraper.is_logged_in():
        print("Already logged in!")
        user_info = scraper.get_user_info()
        if user_info:
            print(f"User info: {user_info}")
    else:
        # Try to get credentials from environment variables first
        username = os.getenv('GLOWFIC_USERNAME')
        password = os.getenv('GLOWFIC_PASSWORD')
        remember_me = os.getenv('GLOWFIC_REMEMBER_ME', 'false').lower() in ['true', '1', 'yes', 'y']
        
        # If not in env, prompt for credentials
        if not username or not password:
            print("Please provide your Glowfic credentials:")
            
            if not username:
                username = input("Username: ").strip()
            else:
                print(f"Username from .env: {username}")
            
            if not username:
                print("Username cannot be empty")
                sys.exit(1)
            
            if not password:
                password = getpass.getpass("Password: ").strip()
            else:
                print("Password loaded from .env file")
            
            if not password:
                print("Password cannot be empty")
                sys.exit(1)
            
            if 'GLOWFIC_REMEMBER_ME' not in os.environ:
                remember_me = input("Remember me? (y/N): ").strip().lower() in ['y', 'yes']
        else:
            print(f"Using credentials from .env file for user: {username}")
        
        # Attempt login
        if scraper.login(username, password, remember_me):
            scraper.save_cookies()
            
            # Get user info
            user_info = scraper.get_user_info()
            if user_info:
                print(f"User info: {user_info}")
        else:
            print("Login failed")
            sys.exit(1)
    
    # Handle different commands
    if args.url:
        print(f"\nFetching: {args.url}")
        content = scraper.scrape_page(args.url)
        if content:
            print(content.decode('utf-8', errors='ignore'))
        else:
            print("Failed to fetch content")
        return
    
    if args.list_galleries:
        print("\nListing galleries...")
        scraper.list_galleries()
        return
    
    if args.upload:
        if not args.gallery:
            print("Error: --gallery is required when using --upload")
            return
        
        print(f"\nUploading {args.upload} to gallery {args.gallery}...")
        result = scraper.upload_icon_to_gallery(
            gallery_id=args.gallery,
            image_path=args.upload,
            keyword=args.keyword,
            credit=args.credit,
            url=args.icon_url
        )
        
        if result:
            print("Upload completed successfully!")
        else:
            print("Upload failed!")
        return
    
    # No command specified - show help
    print("\nGlowfic Scraper v1.0")
    print("Successfully authenticated as: girllich")
    print("\nAvailable commands:")
    print("  --list-galleries              List all your galleries")
    print("  --url <path>                  Fetch any authenticated URL")
    print("  --upload <file> --gallery <id> Upload icon to gallery")
    print("  --resize <output> --upload <file> Resize image to 150x150")
    print("\nExamples:")
    print("  ./glowfic_scraper.py --list-galleries")
    print("  ./glowfic_scraper.py --url /users/471/galleries") 
    print("  ./glowfic_scraper.py --upload icon.jpg --gallery 27821 --keyword 'expression'")
    print("  ./glowfic_scraper.py --resize test.jpg --upload original.png")
    print("\nFor more options: ./glowfic_scraper.py --help")

if __name__ == "__main__":
    main()