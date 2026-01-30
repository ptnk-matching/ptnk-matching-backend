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
try:
    from mangum import Mangum
    from main import app
    
    # Wrap FastAPI app with Mangum for AWS Lambda/Vercel compatibility
    # Mangum returns a callable ASGI application, which Vercel expects
    _mangum_app = Mangum(app, lifespan="off")
    
    # Export handler as a callable function to avoid Vercel's type checking issues
    def handler(event, context):
        """Vercel serverless function handler."""
        return _mangum_app(event, context)
    
except Exception as e:
    # Fallback: create a simple error handler
    import logging
    logging.error(f"Error initializing handler: {e}")
    
    def handler(event, context):
        """Fallback error handler."""
        return {
            "statusCode": 500,
            "body": f"Error initializing handler: {str(e)}"
        }

