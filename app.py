import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# 1. Load Root Environment (.env)
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

# 2. Add backend folder to sys.path and remove root so 'app' points to backend/app
backend_dir = str(BASE_DIR / "backend")
root_dir = str(BASE_DIR)
sys.path = [p for p in sys.path if p not in (root_dir, "")]
sys.path.insert(0, backend_dir)

# 3. Import Application
from app.main import app

if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    print(f"==================================================================")
    print(f"🚀 KALISI STRANGER MEETUP PLATFORM")
    print(f"==================================================================")
    print(f"📍 Admin Web Portal:      http://localhost:{port}/admin")
    print(f"📍 Root Redirection:      http://localhost:{port}/")
    print(f"📖 Swagger API Docs:      http://localhost:{port}/api/docs")
    print(f"⚡ Mobile Client Gateway: http://localhost:{port}/api")
    print(f"==================================================================")
    uvicorn.run(app, host=host, port=port)
