# api.py

"""
FastAPI server entry point
"""

import uvicorn
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

load_dotenv()

from ports.web.fastapi_adapter import app


def run_server(
    host: str = "0.0.0.0",
    port: int = 8000,
    reload: bool = True,
    log_level: str = "info",
):
    """Run the FastAPI server"""
    print("\n" + "=" * 70)
    print("🍽️  RESTAURANT CUSTOMER SUPPORT API")
    print("=" * 70)
    print(f"\n📍 API: http://{host}:{port}")
    print(f"📚 Docs: http://{host}:{port}/docs")
    print("\n" + "=" * 70 + "\n")

    uvicorn.run(
        "ports.web.fastapi_adapter:app",
        host=host,
        port=port,
        reload=reload,
        log_level=log_level,
    )


if __name__ == "__main__":
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    reload = os.getenv("API_RELOAD", "true").lower() == "true"
    log_level = os.getenv("API_LOG_LEVEL", "info")

    run_server(host=host, port=port, reload=reload, log_level=log_level)
