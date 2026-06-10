"""
Main entry point — run the FastAPI server.
"""
import uvicorn
from app.api.routes import app
from app.config import get_settings

settings = get_settings()

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level="info",
    )

# reload trigger - updated
