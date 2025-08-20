"""
Vercel Serverless Function - Authentication
Handles login/register for botphIA
"""
from http.server import BaseHTTPRequestHandler
import json
import jwt
import hashlib
import os
from datetime import datetime, timedelta
from supabase import create_client, Client

# Initialize Supabase client
supabase: Client = create_client(
    os.environ.get("SUPABASE_URL", ""),
    os.environ.get("SUPABASE_ANON_KEY", "")
)

JWT_SECRET = os.environ.get("JWT_SECRET_KEY", "your-secret-key")

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        """Handle POST requests"""
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data)
        
        path = self.path
        
        if path == "/api/auth/login":
            response = self.handle_login(data)
        elif path == "/api/auth/register":
            response = self.handle_register(data)
        else:
            response = {"error": "Not found"}, 404
            
        # Send response
        status = response[1] if isinstance(response, tuple) else 200
        body = response[0] if isinstance(response, tuple) else response
        
        self.send_response(status)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(body).encode())
        
    def do_OPTIONS(self):
        """Handle CORS preflight"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()
        
    def handle_login(self, data):
        """Handle user login"""
        email = data.get("email")
        password = data.get("password")
        
        if not email or not password:
            return {"error": "Email and password required"}, 400
            
        # Query user from Supabase
        result = supabase.table("users").select("*").eq("email", email).execute()
        
        if not result.data:
            return {"error": "Invalid credentials"}, 401
            
        user = result.data[0]
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        if user["password_hash"] != password_hash:
            return {"error": "Invalid credentials"}, 401
            
        # Generate JWT token
        token = jwt.encode({
            "user_id": user["id"],
            "email": user["email"],
            "exp": datetime.utcnow() + timedelta(days=7)
        }, JWT_SECRET, algorithm="HS256")
        
        return {
            "access_token": token,
            "user": {
                "id": user["id"],
                "email": user["email"],
                "full_name": user.get("full_name", "")
            }
        }
        
    def handle_register(self, data):
        """Handle user registration"""
        email = data.get("email")
        password = data.get("password")
        full_name = data.get("full_name", "")
        
        if not email or not password:
            return {"error": "Email and password required"}, 400
            
        # Check if user exists
        existing = supabase.table("users").select("id").eq("email", email).execute()
        if existing.data:
            return {"error": "User already exists"}, 409
            
        # Create user
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        result = supabase.table("users").insert({
            "email": email,
            "password_hash": password_hash,
            "full_name": full_name
        }).execute()
        
        if not result.data:
            return {"error": "Registration failed"}, 500
            
        user = result.data[0]
        
        # Generate JWT token
        token = jwt.encode({
            "user_id": user["id"],
            "email": user["email"],
            "exp": datetime.utcnow() + timedelta(days=7)
        }, JWT_SECRET, algorithm="HS256")
        
        return {
            "access_token": token,
            "user": {
                "id": user["id"],
                "email": user["email"],
                "full_name": full_name
            }
        }