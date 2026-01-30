"""
Vercel serverless function handler for FastAPI app.
This file is used when deploying to Vercel.
"""
import sys
import os

# Mark as serverless environment early - MUST be first
os.environ['VERCEL'] = '1'
os.environ.setdefault('PYTHONUNBUFFERED', '1')

# Add backend directory to path
backend_path = os.path.join(os.path.dirname(__file__), '..', 'backend')
sys.path.insert(0, backend_path)

# Import after setting environment variables
from mangum import Mangum
from main import app

# Wrap FastAPI app with Mangum for AWS Lambda/Vercel compatibility
_mangum_handler = Mangum(app, lifespan="off")

# Create a callable wrapper function that Vercel can recognize
def handler(event, context):
    """
    Vercel serverless function handler.
    This wrapper ensures Vercel recognizes it as a callable function.
    """
    return _mangum_handler(event, context)

# Also export the Mangum instance directly for compatibility
__all__ = ['handler']

