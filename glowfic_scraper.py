#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.8"
# dependencies = [
#     "requests>=2.25.0",
#     "beautifulsoup4>=4.9.0",
#     "lxml>=4.6.0",
#     "python-dotenv>=0.19.0",
#     "pillow>=8.0.0",
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
import xml.etree.ElementTree as ET
from urllib.parse import urljoin
from dotenv import load_dotenv
from PIL import Image
from io import BytesIO

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

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Glowfic scraper')
    parser.add_argument('--url', help='URL path to fetch (e.g., /users/471/galleries)')
    parser.add_argument('--list-galleries', action='store_true', help='List user galleries')
    parser.add_argument('--upload', help='Path to image file to upload')
    parser.add_argument('--gallery', help='Gallery ID to upload to (required with --upload)')
    parser.add_argument('--keyword', help='Keyword for uploaded icon')
    parser.add_argument('--credit', help='Credit for uploaded icon') 
    parser.add_argument('--icon-url', help='URL for uploaded icon')
    parser.add_argument('--resize', help='Resize image to 150x150 and save locally (provide output filename)')
    args = parser.parse_args()
    
    # Load environment variables from .env file
    load_dotenv()
    
    scraper = GlowficScraper()
    
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
    
    # Example: Scrape a specific page
    print("\nScraper ready. You can now use it to scrape pages.")
    print("Example usage:")
    print("  ./glowfic_scraper.py --url /posts")
    print("  ./glowfic_scraper.py --url /users/471/galleries")
    print("  ./glowfic_scraper.py --list-galleries")
    print("  ./glowfic_scraper.py --upload image.jpg --gallery 19703 --keyword 'test'")

if __name__ == "__main__":
    main()