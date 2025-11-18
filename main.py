
"""Backward compatible entry point for the Photo Proof API."""

import socket
from app.main import app


def get_network_ip() -> str:
    """Get local network IP address."""
    try:
        # Create a socket connection to determine local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "localhost"


if __name__ == "__main__":
    import uvicorn
    
    network_ip = get_network_ip()
    print("\n🚀 Photo Proof API Server")
    print("=" * 50)
    print(f"📍 Local:   http://localhost:8000")
    print(f"🌐 Network: http://{network_ip}:8000")
    print(f"📚 Docs:    http://localhost:8000/docs")
    print("=" * 50 + "\n")

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
