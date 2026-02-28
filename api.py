#!/usr/bin/env python3
"""
Simple API server to handle scraper requests
Run with: python api.py
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import subprocess
import os
import threading
import time
from urllib.parse import urlparse

# Global progress state
progress_state = {
    'running': False,
    'current': 0,
    'total': 25,  # Total query groups
    'message': '',
    'articles_found': 0,
    'start_time': 0
}

class ScraperAPIHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        """Handle CORS preflight"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        """Handle GET requests for progress"""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/api/progress':
            self.handle_progress()
        else:
            self.send_error(404, "Endpoint not found")

    def do_POST(self):
        """Handle POST requests"""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/api/scrape':
            self.handle_scrape()
        else:
            self.send_error(404, "Endpoint not found")

    def handle_progress(self):
        """Return current progress"""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        # Calculate ETA
        elapsed = time.time() - progress_state['start_time'] if progress_state['start_time'] else 0
        if progress_state['current'] > 0 and elapsed > 0:
            time_per_item = elapsed / progress_state['current']
            remaining_items = progress_state['total'] - progress_state['current']
            eta_seconds = int(time_per_item * remaining_items)
        else:
            eta_seconds = 0
        
        response = {
            'running': progress_state['running'],
            'current': progress_state['current'],
            'total': progress_state['total'],
            'percentage': int((progress_state['current'] / progress_state['total']) * 100) if progress_state['total'] > 0 else 0,
            'message': progress_state['message'],
            'articles_found': progress_state['articles_found'],
            'eta_seconds': eta_seconds
        }
        
        self.wfile.write(json.dumps(response).encode())

    def handle_scrape(self):
        """Run the scraper and return results"""
        global progress_state
        
        if progress_state['running']:
            self.send_response(409)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                'success': False,
                'message': 'Scraper is already running'
            }).encode())
            return
        
        # Start scraper in background thread
        def run_scraper():
            global progress_state
            progress_state['running'] = True
            progress_state['current'] = 0
            progress_state['articles_found'] = 0
            progress_state['message'] = 'Starting scraper...'
            progress_state['start_time'] = time.time()
            
            try:
                scraper_dir = os.path.join(os.path.dirname(__file__), 'scraper')
                
                # Run main.py with unbuffered output
                process = subprocess.Popen(
                    ['python3', '-u', 'main.py'],  # -u flag for unbuffered output
                    cwd=scraper_dir,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    universal_newlines=True
                )
                
                # Monitor output for progress
                while True:
                    line = process.stdout.readline()
                    if not line and process.poll() is not None:
                        break
                    if not line:
                        continue
                    
                    line = line.strip()
                    print(f"[SCRAPER] {line}")  # Log to API server console
                    
                    # Update progress based on output
                    if '[' in line and '/' in line and ']' in line:
                        try:
                            # Parse [X/Y] pattern
                            bracket_content = line.split('[')[1].split(']')[0]
                            parts = bracket_content.split('/')
                            progress_state['current'] = int(parts[0])
                            progress_state['total'] = int(parts[1])
                        except:
                            pass
                    
                    if 'Found' in line and 'relevant' in line:
                        try:
                            num = int(line.split('Found ')[1].split(' relevant')[0])
                            progress_state['articles_found'] += num
                        except:
                            pass
                    
                    if 'Searching:' in line:
                        progress_state['message'] = line
                
                process.wait()
                progress_state['message'] = 'Scraping completed!'
                
            except Exception as e:
                progress_state['message'] = f'Error: {str(e)}'
                print(f"[ERROR] {str(e)}")
            finally:
                progress_state['running'] = False
                progress_state['current'] = progress_state['total']
        
        threading.Thread(target=run_scraper, daemon=True).start()
        
        self.send_response(202)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        response = {
            'success': True,
            'message': 'Scraper started. Poll /api/progress for updates.'
        }
        self.wfile.write(json.dumps(response).encode())

    def log_message(self, format, *args):
        """Custom log format"""
        print(f"[API] {args[0]}")

def run_server(port=8002):
    server_address = ('', port)
    httpd = HTTPServer(server_address, ScraperAPIHandler)
    print(f"\n🚀 Scraper API running on http://localhost:{port}")
    print(f"📍 Endpoint: POST http://localhost:{port}/api/scrape\n")
    httpd.serve_forever()

if __name__ == '__main__':
    # Use Railway's PORT environment variable if available
    port = int(os.environ.get('PORT', 8002))
    run_server(port)
