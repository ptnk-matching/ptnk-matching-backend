"""
Vercel serverless function handler for FastAPI app.
This file is used when deploying to Vercel.
"""
import sys
import os

# Add backend directory to path
backend_path = os.path.join(os.path.dirname(__file__), '..', 'backend')
sys.path.insert(0, backend_path)

# Set environment variables if needed
os.environ.setdefault('PYTHONUNBUFFERED', '1')

try:
    from mangum import Mangum
    from main import app
    
    # Wrap FastAPI app with Mangum for AWS Lambda/Vercel compatibility
    handler = Mangum(app, lifespan="off")
except Exception as e:
    # Fallback for development
    import logging
    logging.error(f"Error initializing app: {e}")
    handler = None

