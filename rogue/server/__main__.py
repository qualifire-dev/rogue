import uvicorn
import os
from .main import app

if __name__ == "__main__":
    host = os.getenv("HOST", "127.0.0.1")  # Default to localhost for security
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(
        app,
        host=host,
        port=port,
        reload=True,
    )
