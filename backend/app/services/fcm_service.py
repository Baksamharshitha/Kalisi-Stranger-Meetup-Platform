import os
from pathlib import Path
from typing import List, Optional, Dict
import firebase_admin
from firebase_admin import credentials, messaging
from app.db.models import User

# Path to Firebase Service Account JSON
BASE_DIR = Path(__file__).resolve().parent.parent.parent
CRED_PATH = os.getenv("FIREBASE_CREDENTIALS_PATH", "backend/firebase-service-account.json")

_firebase_app = None

def get_firebase_app():
    global _firebase_app
    if _firebase_app is not None:
        return _firebase_app
    
    # Check possible paths
    paths_to_check = [
        Path(CRED_PATH),
        BASE_DIR / CRED_PATH,
        BASE_DIR / "firebase-service-account.json",
        BASE_DIR / "backend" / "firebase-service-account.json",
    ]
    
    cred_file = None
    for p in paths_to_check:
        if p.exists():
            cred_file = p
            break
            
    if cred_file:
        try:
            cred = credentials.Certificate(str(cred_file))
            _firebase_app = firebase_admin.initialize_app(cred)
            print(f"🔥 Firebase Admin SDK initialized successfully with {cred_file}")
            return _firebase_app
        except Exception as e:
            print(f"⚠️ Firebase Admin initialization failed: {e}")
    else:
        print(f"⚠️ Firebase credentials file not found at {CRED_PATH}")
    return None

def send_fcm_notification(
    token: str,
    title: str,
    body: str,
    data: Optional[Dict[str, str]] = None
) -> Dict:
    """Send a push notification to a single device FCM token."""
    app = get_firebase_app()
    if not app:
        return {"success": False, "error": "Firebase Admin SDK not initialized"}

    try:
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            data=data or {},
            token=token,
            android=messaging.AndroidConfig(
                priority="high",
                notification=messaging.AndroidNotification(
                    channel_id="kalisi_high_importance_channel",
                    sound="default",
                ),
            ),
        )
        response = messaging.send(message)
        return {"success": True, "message_id": response}
    except Exception as e:
        return {"success": False, "error": str(e)}

def broadcast_fcm_notification(
    db,
    title: str,
    body: str,
    data: Optional[Dict[str, str]] = None,
    city: Optional[str] = None
) -> Dict:
    """Broadcast a push notification to all users who have an active FCM token."""
    query = db.query(User).filter(User.fcm_token.isnot(None), User.fcm_token != "")
    if city:
        query = query.filter(User.city.ilike(f"%{city}%"))
    
    users = query.all()
    tokens = [u.fcm_token for u in users if u.fcm_token]
    
    if not tokens:
        return {
            "success": True,
            "total_targets": 0,
            "sent_count": 0,
            "failed_count": 0,
            "message": "No registered device tokens found to receive push notification."
        }

    success_count = 0
    fail_count = 0
    errors = []

    for token in tokens:
        res = send_fcm_notification(token, title, body, data)
        if res.get("success"):
            success_count += 1
        else:
            fail_count += 1
            errors.append(res.get("error"))

    return {
        "success": True,
        "total_targets": len(tokens),
        "sent_count": success_count,
        "failed_count": fail_count,
        "errors": errors[:5]
    }
