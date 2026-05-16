"""
AI Agent Platform - Simple Server
Serves both API and frontend
"""
import http.server
import socketserver
import json
import os
from urllib.parse import urlparse, parse_qs

PORT = 3000

skills = [
    {"id": "1", "name": "Code Assistant", "description": "Helps with programming tasks", "enabled": True},
    {"id": "2", "name": "Email Writer", "description": "Drafts professional emails", "enabled": False},
    {"id": "3", "name": "Data Analyst", "description": "Analyzes data and creates insights", "enabled": True},
]

tools = [
    {"id": "1", "name": "Web Search", "description": "Search the internet for information", "enabled": True},
    {"id": "2", "name": "Calculator", "description": "Perform mathematical calculations", "enabled": True},
    {"id": "3", "name": "Calendar", "description": "Manage your schedule", "enabled": False},
]

class APIHandler(http.server.SimpleHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_GET(self):
        path = urlparse(self.path).path
        
        if path == '/api/skills':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(skills).encode())
            
        elif path == '/api/tools':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(tools).encode())
            
        elif path == '/api/status':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "ok",
                "skills_enabled": len([s for s in skills if s["enabled"]]),
                "tools_enabled": len([t for t in tools if t["enabled"]])
            }).encode())
            
        else:
            # Serve static files (index.html)
            if path == '/':
                path = '/index.html'
            
            file_path = os.path.join(os.path.dirname(__file__), path.lstrip('/'))
            
            if os.path.exists(file_path) and os.path.isfile(file_path):
                self.send_response(200)
                if file_path.endswith('.html'):
                    self.send_header('Content-type', 'text/html')
                elif file_path.endswith('.js'):
                    self.send_header('Content-type', 'application/javascript')
                elif file_path.endswith('.css'):
                    self.send_header('Content-type', 'text/css')
                else:
                    self.send_header('Content-type', 'application/octet-stream')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                with open(file_path, 'rb') as f:
                    self.wfile.write(f.read())
            else:
                self.send_response(404)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(b'{"error": "Not found"}')
    
    def do_POST(self):
        path = urlparse(self.path).path
        
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8')
        
        try:
            data = json.loads(body) if body else {}
        except:
            data = {}
        
        if path == '/api/chat':
            user_message = data.get('message', '')
            active_skills = [s['name'] for s in skills if s['enabled']]
            active_tools = [t['name'] for t in tools if t['enabled']]
            
            response = f"I received your message: \"{user_message}\"\n\n"
            response += f"Active skills: {', '.join(active_skills) if active_skills else 'none'}\n"
            response += f"Available tools: {', '.join(active_tools) if active_tools else 'none'}\n\n"
            response += "How else can I help you?"
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                "response": response,
                "conversation_id": "conv-1",
                "tokens_used": len(response.split())
            }).encode())
            
        elif '/toggle' in path:
            # Parse skill or tool ID from path
            parts = path.split('/')
            item_id = parts[-2] if len(parts) >= 2 else None
            item_type = parts[1] if len(parts) >= 2 else None
            
            if item_type == 'skills':
                for s in skills:
                    if s['id'] == item_id:
                        s['enabled'] = not s['enabled']
                        self.send_response(200)
                        self.send_header('Content-type', 'application/json')
                        self.send_header('Access-Control-Allow-Origin', '*')
                        self.end_headers()
                        self.wfile.write(json.dumps({"success": True, "skill": s}).encode())
                        return
                        
            elif item_type == 'tools':
                for t in tools:
                    if t['id'] == item_id:
                        t['enabled'] = not t['enabled']
                        self.send_response(200)
                        self.send_header('Content-type', 'application/json')
                        self.send_header('Access-Control-Allow-Origin', '*')
                        self.end_headers()
                        self.wfile.write(json.dumps({"success": True, "tool": t}).encode())
                        return
            
            self.send_response(404)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"error": "Not found"}')
        else:
            self.send_response(404)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"error": "Not found"}')
    
    def log_message(self, format, *args):
        print(f"[{self.log_date_time_string()}] {format % args}")

os.chdir(os.path.dirname(os.path.abspath(__file__)))

print("=" * 50)
print("🚀 AI Agent Platform")
print("=" * 50)
print(f"🌐 Open: http://localhost:{PORT}")
print(f"📡 API:  http://localhost:{PORT}/api/*")
print("=" * 50)

with socketserver.TCPServer(("", PORT), APIHandler) as httpd:
    httpd.serve_forever()
