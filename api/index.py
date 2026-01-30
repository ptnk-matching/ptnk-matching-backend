"""
Vercel serverless function handler for FastAPI app.
Vercel supports FastAPI directly as an ASGI app - no need for Mangum.
"""
import sys
import os

# Mark as serverless environment early - MUST be first
os.environ['VERCEL'] = '1'
os.environ.setdefault('PYTHONUNBUFFERED', '1')

# Add backend directory to path
backend_path = os.path.join(os.path.dirname(__file__), '..', 'backend')
sys.path.insert(0, backend_path)

# Import FastAPI app directly
from main import app

# Export app directly - Vercel Python runtime supports ASGI apps natively
# No need for Mangum wrapper
handler = app

