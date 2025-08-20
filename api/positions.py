"""
Vercel Serverless Function - Trading Positions
Handles positions CRUD for botphIA
"""
from http.server import BaseHTTPRequestHandler
import json
import jwt
import os
from supabase import create_client, Client

# Initialize Supabase client
supabase: Client = create_client(
    os.environ.get("SUPABASE_URL", ""),
    os.environ.get("SUPABASE_ANON_KEY", "")
)

JWT_SECRET = os.environ.get("JWT_SECRET_KEY", "your-secret-key")

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Get user positions"""
        # Verify JWT token
        auth_header = self.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            self.send_error(401, "Unauthorized")
            return
            
        token = auth_header.replace("Bearer ", "")
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
            user_id = payload["user_id"]
        except:
            self.send_error(401, "Invalid token")
            return
            
        # Get positions from Supabase
        result = supabase.table("positions")\
            .select("*")\
            .eq("user_id", user_id)\
            .eq("status", "OPEN")\
            .execute()
            
        positions = result.data if result.data else []
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(positions).encode())
        
    def do_POST(self):
        """Create new position"""
        # Verify JWT token
        auth_header = self.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            self.send_error(401, "Unauthorized")
            return
            
        token = auth_header.replace("Bearer ", "")
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
            user_id = payload["user_id"]
        except:
            self.send_error(401, "Invalid token")
            return
            
        # Parse request body
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data)
        
        # Create position
        position = {
            "user_id": user_id,
            "symbol": data.get("symbol"),
            "type": data.get("type", "BUY"),
            "entry_price": data.get("entry_price"),
            "quantity": data.get("quantity"),
            "stop_loss": data.get("stop_loss"),
            "take_profit": data.get("take_profit"),
            "status": "OPEN"
        }
        
        result = supabase.table("positions").insert(position).execute()
        
        self.send_response(201)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(result.data[0]).encode())
        
    def do_OPTIONS(self):
        """Handle CORS preflight"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()