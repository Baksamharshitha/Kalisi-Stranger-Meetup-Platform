import uuid
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Form, HTTPException, Depends, File, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from app.core.config import settings
from app.db.database import SessionLocal
from app.db.models import User, CitySlot, TableGroup, Restaurant, Booking, VideoReel
from app.services.matchmaking import cluster_slot_into_tables
from app.services.fcm_service import broadcast_fcm_notification, send_fcm_notification

admin_router = APIRouter()

# ==============================================================================
# Admin Auth API
# ==============================================================================

@admin_router.post("/admin/api/login")
def admin_login(username: str = Form(...), password: str = Form(...)):
    if username == settings.ADMIN_USERNAME and password == settings.ADMIN_PASSWORD:
        return {
            "status": "success",
            "token": "kalisi_admin_auth_token_secret_2026",
            "message": "Welcome back to Kalisi Control Center"
        }
    raise HTTPException(status_code=401, detail="Invalid Admin Username or Password")

# ==============================================================================
# Admin Deep Overview API
# ==============================================================================

@admin_router.get("/admin/api/overview")
def admin_get_overview():
    with SessionLocal() as db:
        users = db.query(User).all()
        slots = db.query(CitySlot).order_by(CitySlot.event_timestamp.desc()).all()
        tables = db.query(TableGroup).all()
        restaurants = db.query(Restaurant).all()
        bookings = db.query(Booking).order_by(Booking.created_at.desc()).all()
        videos = db.query(VideoReel).order_by(VideoReel.created_at.desc()).all()

        # Users with Vibe DNA and Preferences
        user_list = []
        for u in users:
            arch = u.personality.archetype if u.personality else "Pending Quiz"
            icebreaker = u.personality.icebreaker_style if u.personality else "N/A"
            tier = u.preferences.budget_tier if u.preferences else "mid_range"
            diet = u.preferences.dietary_requirements if u.preferences else "No restrictions"
            user_list.append({
                "id": u.id,
                "name": u.full_name,
                "email": u.email,
                "phone": u.phone or "N/A",
                "age": u.age or 24,
                "gender": u.gender or "N/A",
                "city": u.city,
                "archetype": arch,
                "icebreaker_style": icebreaker,
                "budget_tier": tier,
                "dietary": diet,
                "bookings_count": len(u.bookings),
                "is_verified": u.is_verified,
                "fcm_token": getattr(u, "fcm_token", None) or "",
                "created_at": u.created_at.strftime("%Y-%m-%d %H:%M") if u.created_at else "Recent",
            })

        # Detailed Slots / Events
        slot_list = []
        active_events_count = 0
        completed_events_count = 0

        for s in slots:
            booked_count = len(s.bookings)
            capacity = s.max_capacity or 10
            is_completed = s.status == "completed"
            if is_completed:
                completed_events_count += 1
            else:
                active_events_count += 1

            slot_list.append({
                "id": s.id,
                "title": getattr(s, "title", None) or f"{s.city} Stranger Dinner Meetup",
                "city": s.city,
                "date_str": s.date_str,
                "time_window": s.time_window,
                "price_inr": s.price_inr or 499,
                "max_capacity": capacity,
                "bookings_count": booked_count,
                "seats_left": max(0, capacity - booked_count),
                "status": s.status,
                "is_enabled": (s.status == "open"),
                "venue_name": getattr(s, "venue_name", None) or "Curated Partner Restaurant",
                "venue_address": getattr(s, "venue_address", None) or f"Central {s.city} Location",
                "about_event": getattr(s, "about_event", None) or "Join 5 curated strangers for an evening of genuine conversations, delicious dining, and icebreaker games.",
                "rules_and_regulations": getattr(s, "rules_and_regulations", None) or "1. Arrive on time.\n2. Equal bill split.\n3. Respectful table talk.\n4. Age 18+ only.",
                "tables_count": len(s.tables),
            })

        # Detailed Bookings & Financial Ledger
        booking_list = []
        total_revenue = 0
        paid_count = 0

        for b in bookings:
            amt = b.amount_paid or 0
            total_revenue += amt
            if b.payment_status == "paid":
                paid_count += 1

            u = b.user
            arch = u.personality.archetype if (u and u.personality) else "Clark Kent"
            diet = u.preferences.dietary_requirements if (u and u.preferences) else "No restrictions"

            booking_list.append({
                "id": b.id,
                "slot_id": b.slot_id,
                "user_id": b.user_id,
                "user_name": u.full_name if u else "Unknown",
                "user_email": u.email if u else "N/A",
                "user_phone": u.phone if u else "N/A",
                "user_age": u.age if u else 24,
                "user_gender": u.gender if u else "N/A",
                "user_archetype": arch,
                "user_dietary": diet,
                "slot_city": b.slot.city if b.slot else "",
                "slot_date": b.slot.date_str if b.slot else "",
                "slot_time": b.slot.time_window if b.slot else "",
                "table_number": b.table.table_number if b.table else None,
                "amount_paid": amt,
                "payment_status": b.payment_status,
                "payment_method": b.payment_method or "Free Trial",
                "payment_id": b.payment_id or "N/A",
                "attendance_confirmed": b.attendance_confirmed,
                "created_at": b.created_at.strftime("%Y-%m-%d %H:%M") if b.created_at else "N/A",
            })

        # Detailed Venues
        restaurant_list = []
        for r in restaurants:
            restaurant_list.append({
                "id": r.id,
                "name": r.name,
                "neighborhood": r.neighborhood,
                "address": r.full_address,
                "cuisine": r.cuisine,
                "price_tier": r.price_tier,
                "city": r.city,
                "activities": r.activities or "Table icebreaker card games, curated conversation starters",
                "duration_hours": r.duration_hours or "2.5 Hours",
                "special_features": r.special_features or "Dedicated private table, welcome drinks",
                "contact_person": r.contact_person or "Manager on Duty",
                "contact_phone": r.contact_phone or "N/A",
            })

        # Detailed Videos
        video_list = []
        for v in videos:
            video_list.append({
                "id": v.id,
                "title": v.title,
                "venue_name": v.venue_name,
                "video_url": v.video_url,
                "thumbnail_url": v.thumbnail_url or "https://images.unsplash.com/photo-1543007630-9710e4a00a20?auto=format&fit=crop&w=800&q=80",
                "views_count": v.views_count,
                "created_at": v.created_at.strftime("%Y-%m-%d") if v.created_at else "Recent",
            })

        return {
            "metrics": {
                "total_users": len(users),
                "event_booked_members": len(bookings),
                "active_events": active_events_count,
                "completed_events": completed_events_count,
                "total_revenue_inr": total_revenue,
                "paid_bookings": paid_count,
                "total_videos": len(videos),
                "total_venues": len(restaurants),
                "active_tables": len(tables),
            },
            "events": slot_list,
            "slots": slot_list,
            "restaurants": restaurant_list,
            "bookings": booking_list,
            "users": user_list,
            "videos": video_list,
        }

@admin_router.post("/admin/api/events/{event_id}/status")
def admin_set_event_status(event_id: str, status: str = Form(...)):
    with SessionLocal() as db:
        slot = db.query(CitySlot).filter(CitySlot.id == event_id).first()
        if not slot:
            raise HTTPException(status_code=404, detail="Event not found")
        slot.status = status
        db.commit()
        return {"status": "success", "event_id": slot.id, "new_status": slot.status}

@admin_router.post("/admin/api/events/{event_id}/toggle-enable")
def admin_toggle_event_enable(event_id: str):
    with SessionLocal() as db:
        slot = db.query(CitySlot).filter(CitySlot.id == event_id).first()
        if not slot:
            raise HTTPException(status_code=404, detail="Event not found")
        # Toggle between open (enabled) and disabled
        if slot.status == "open":
            slot.status = "disabled"
            slot.is_enabled = False
        else:
            slot.status = "open"
            slot.is_enabled = True
        db.commit()
        return {"status": "success", "event_id": slot.id, "new_status": slot.status, "is_enabled": slot.is_enabled}

@admin_router.post("/admin/api/bookings/{booking_id}/toggle-attendance")
def admin_toggle_attendance(booking_id: str):
    with SessionLocal() as db:
        booking = db.query(Booking).filter(Booking.id == booking_id).first()
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")
        booking.attendance_confirmed = not booking.attendance_confirmed
        db.commit()
        return {"status": "success", "booking_id": booking.id, "attended": booking.attendance_confirmed}

@admin_router.post("/admin/api/videos/create")
async def admin_create_video(
    title: str = Form(...),
    venue_name: str = Form(...),
    video_url: Optional[str] = Form(None),
    video_file: Optional[UploadFile] = File(None),
    thumbnail_url: Optional[str] = Form(None),
    thumbnail_file: Optional[UploadFile] = File(None)
):
    upload_base = Path(__file__).resolve().parent.parent / "uploads"
    final_video_url = (video_url or "").strip()
    final_thumbnail_url = (thumbnail_url or "").strip()

    # Save uploaded video file if provided
    if video_file and video_file.filename:
        v_ext = Path(video_file.filename).suffix or ".mp4"
        safe_name = f"{uuid.uuid4().hex[:10]}_{video_file.filename.replace(' ', '_')}"
        v_path = upload_base / "videos" / safe_name
        v_path.parent.mkdir(parents=True, exist_ok=True)
        with open(v_path, "wb") as buffer:
            shutil.copyfileobj(video_file.file, buffer)
        final_video_url = f"/uploads/videos/{safe_name}"

    # Save uploaded thumbnail file if provided
    if thumbnail_file and thumbnail_file.filename:
        safe_t_name = f"{uuid.uuid4().hex[:10]}_{thumbnail_file.filename.replace(' ', '_')}"
        t_path = upload_base / "thumbnails" / safe_t_name
        t_path.parent.mkdir(parents=True, exist_ok=True)
        with open(t_path, "wb") as buffer:
            shutil.copyfileobj(thumbnail_file.file, buffer)
        final_thumbnail_url = f"/uploads/thumbnails/{safe_t_name}"

    if not final_video_url:
        final_video_url = "https://www.w3schools.com/html/mov_bbb.mp4"
    if not final_thumbnail_url:
        final_thumbnail_url = "https://images.unsplash.com/photo-1543007630-9710e4a00a20?auto=format&fit=crop&w=800&q=80"

    with SessionLocal() as db:
        vr = VideoReel(
            title=title,
            venue_name=venue_name,
            video_url=final_video_url,
            thumbnail_url=final_thumbnail_url,
            views_count=1200,
            is_approved=True
        )
        db.add(vr)
        db.commit()
        return {"status": "success", "video_id": vr.id, "video_url": final_video_url, "thumbnail_url": final_thumbnail_url}

@admin_router.delete("/admin/api/videos/{video_id}")
def admin_delete_video(video_id: str):
    with SessionLocal() as db:
        vr = db.query(VideoReel).filter(VideoReel.id == video_id).first()
        if vr:
            db.delete(vr)
            db.commit()
        return {"status": "success"}

@admin_router.post("/admin/api/notifications/send")
def admin_send_push_notification(
    title: str = Form(...),
    body: str = Form(...),
    target_type: str = Form("broadcast"),
    city: Optional[str] = Form(None),
    user_id: Optional[str] = Form(None),
    event_id: Optional[str] = Form(None),
    test_token: Optional[str] = Form(None)
):
    with SessionLocal() as db:
        if target_type == "user":
            if not user_id:
                return {"status": "error", "message": "Please select a user to send the push notification."}
            target_user = db.query(User).filter(User.id == user_id).first()
            if not target_user:
                return {"status": "error", "message": f"User not found with ID {user_id}"}
            
            token = (test_token or "").strip() or target_user.fcm_token
            if not token:
                return {
                    "status": "warning",
                    "message": f"User {target_user.full_name} ({target_user.phone}) has not registered an FCM device token yet. Launch the Kalisi mobile app with this account to automatically register the token, or provide a test token.",
                    "user": {"id": target_user.id, "name": target_user.full_name, "phone": target_user.phone}
                }
            
            res = send_fcm_notification(token=token, title=title, body=body, data={"user_id": target_user.id})
            if res.get("success"):
                return {
                    "status": "success",
                    "message": f"Push notification successfully delivered to {target_user.full_name} ({target_user.phone})! Firebase Message ID: {res.get('message_id')}",
                    "details": res
                }
            else:
                return {
                    "status": "error",
                    "message": f"Firebase FCM delivery failed for {target_user.full_name}: {res.get('error')}",
                    "details": res
                }

        elif target_type == "event_booked":
            if not event_id:
                return {"status": "error", "message": "Please select an event."}
            slot = db.query(CitySlot).filter(CitySlot.id == event_id).first()
            if not slot:
                return {"status": "error", "message": "Event not found."}
            
            bookings = db.query(Booking).filter(Booking.slot_id == event_id).all()
            if not bookings:
                return {
                    "status": "warning",
                    "message": f"No bookings found for '{slot.title}' ({slot.city}).",
                    "total_booked": 0
                }
            
            tokens = []
            users_with_token = []
            users_pending_token = []
            for b in bookings:
                u = b.user
                if u and u.fcm_token:
                    tokens.append((u, u.fcm_token))
                    users_with_token.append(u.full_name)
                elif u:
                    users_pending_token.append(f"{u.full_name} ({u.phone})")
            
            if not tokens:
                return {
                    "status": "warning",
                    "message": f"Found {len(bookings)} booked member(s) for '{slot.title}', but none have registered a device token yet ({', '.join(users_pending_token)}).",
                    "total_booked": len(bookings),
                    "pending_users": users_pending_token
                }
            
            sent_count = 0
            fail_count = 0
            errors = []
            for u, t in tokens:
                res = send_fcm_notification(token=t, title=title, body=body, data={"slot_id": slot.id, "user_id": u.id})
                if res.get("success"):
                    sent_count += 1
                else:
                    fail_count += 1
                    errors.append(res.get("error"))
            
            return {
                "status": "success",
                "message": f"Event notification dispatched! Delivered to {sent_count}/{len(tokens)} active devices across {len(bookings)} booked members for '{slot.title}'.",
                "sent_count": sent_count,
                "total_booked": len(bookings),
                "pending_count": len(users_pending_token),
                "errors": errors[:3]
            }

        elif target_type == "city":
            target_city = city
            res = broadcast_fcm_notification(db, title=title, body=body, city=target_city)
            return {
                "status": "success",
                "message": f"City broadcast dispatched to {target_city}! Sent to {res.get('sent_count', 0)} devices (Targets: {res.get('total_targets', 0)}).",
                "details": res
            }

        else: # broadcast to all
            res = broadcast_fcm_notification(db, title=title, body=body)
            return {
                "status": "success",
                "message": f"Broadcast push notification dispatched! Sent to {res.get('sent_count', 0)} devices (Targets: {res.get('total_targets', 0)}).",
                "details": res
            }

@admin_router.post("/admin/api/slots/create")
def admin_create_slot(
    title: str = Form("Weekend Stranger Dinner Meetup"),
    city: str = Form(...),
    date_str: str = Form(...),
    time_window: str = Form(...),
    price_inr: int = Form(599),
    max_capacity: int = Form(10),
    venue_name: str = Form("Curated Partner Restaurant"),
    venue_address: str = Form("Central City Location"),
    about_event: str = Form("Join 5 curated strangers for an evening of genuine conversations, delicious dining, and icebreaker games."),
    rules_and_regulations: str = Form("1. Arrive within 15 minutes of start time.\n2. Equal bill splitting for food & drinks.\n3. Keep phone away and enjoy real conversations.\n4. Age 18+ verified diners only.")
):
    with SessionLocal() as db:
        new_slot = CitySlot(
            title=title,
            city=city,
            date_str=date_str,
            time_window=time_window,
            price_inr=price_inr,
            max_capacity=max_capacity,
            event_timestamp=datetime.utcnow() + timedelta(days=7),
            status="open",
            is_enabled=True,
            venue_name=venue_name,
            venue_address=venue_address,
            about_event=about_event,
            rules_and_regulations=rules_and_regulations
        )
        db.add(new_slot)
        db.commit()
        return {"status": "success", "slot_id": new_slot.id}

@admin_router.post("/admin/api/events/{event_id}/update")
def admin_update_event(
    event_id: str,
    title: str = Form(...),
    city: str = Form(...),
    date_str: str = Form(...),
    time_window: str = Form(...),
    price_inr: int = Form(...),
    max_capacity: int = Form(...),
    venue_name: str = Form(...),
    venue_address: str = Form(...),
    about_event: str = Form(...),
    rules_and_regulations: str = Form(...),
    status: str = Form("open")
):
    with SessionLocal() as db:
        slot = db.query(CitySlot).filter(CitySlot.id == event_id).first()
        if not slot:
            raise HTTPException(status_code=404, detail="Event not found")
        
        slot.title = title
        slot.city = city
        slot.date_str = date_str
        slot.time_window = time_window
        slot.price_inr = price_inr
        slot.max_capacity = max_capacity
        slot.venue_name = venue_name
        slot.venue_address = venue_address
        slot.about_event = about_event
        slot.rules_and_regulations = rules_and_regulations
        slot.status = status
        slot.is_enabled = (status == "open")
        
        db.commit()
        return {
            "status": "success",
            "event_id": slot.id,
            "message": "Event and venue details updated successfully",
            "is_enabled": slot.is_enabled
        }

@admin_router.post("/admin/api/restaurants/create")
def admin_create_restaurant(
    name: str = Form(...),
    neighborhood: str = Form(...),
    full_address: str = Form(...),
    cuisine: str = Form(...),
    price_tier: str = Form(...),
    city: str = Form(...),
    activities: str = Form("Table icebreakers, conversational trivia"),
    duration_hours: str = Form("2.5 Hours"),
    special_features: str = Form("Dedicated private booth, signature drinks"),
    contact_person: str = Form("Manager on Duty"),
    contact_phone: str = Form("+91 98765 43210")
):
    with SessionLocal() as db:
        restaurant = Restaurant(
            name=name,
            neighborhood=neighborhood,
            full_address=full_address,
            cuisine=cuisine,
            price_tier=price_tier,
            city=city,
            activities=activities,
            duration_hours=duration_hours,
            special_features=special_features,
            contact_person=contact_person,
            contact_phone=contact_phone
        )
        db.add(restaurant)
        db.commit()
        return {"status": "success", "restaurant_id": restaurant.id}

# ==============================================================================
# Complete Admin Web UI (HTML + Tailwind + Sidebar + Dedicated Tab Views)
# ==============================================================================

ADMIN_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Kalisi — Admin Mission Control</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
  <script>
    tailwind.config = {
      theme: {
        extend: {
          colors: {
            kalisi: {
              bg: '#121212',
              sidebar: '#181818',
              surface: '#1E1E1E',
              surfaceLight: '#282828',
              gold: '#F5A623',
              crimson: '#D32F2F',
              purple: '#9C27B0',
              blue: '#64B5F6',
              green: '#4CAF50',
              border: '#2E2E2E'
            }
          }
        }
      }
    }
  </script>
  <style>
    body { background-color: #121212; color: #FFFFFF; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }
    .glass-card { background: #1E1E1E; border: 1px solid #2E2E2E; }
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: #181818; }
    ::-webkit-scrollbar-thumb { background: #333333; border-radius: 3px; }
  </style>
</head>
<body class="min-h-screen flex bg-kalisi-bg overflow-x-hidden">

  <!-- ======================================================================= -->
  <!-- SIDEBAR NAVIGATION                                                      -->
  <!-- ======================================================================= -->
  <aside class="w-64 bg-kalisi-sidebar border-r border-kalisi-border flex flex-col justify-between shrink-0 min-h-screen sticky top-0">
    <div class="p-6 space-y-7">
      
      <!-- Brand & Status -->
      <div class="flex items-center justify-between">
        <div class="flex items-center space-x-3">
          <div class="w-9 h-9 rounded-xl bg-kalisi-gold text-black font-black flex items-center justify-center text-lg shadow-md">
            K
          </div>
          <div>
            <h1 class="text-lg font-black tracking-tight text-white leading-none">Kalisi</h1>
            <span class="text-[10px] text-gray-400 font-bold uppercase tracking-wider">Mission Control</span>
          </div>
        </div>
        <span class="flex h-2.5 w-2.5 relative">
          <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
          <span class="relative inline-flex rounded-full h-2.5 w-2.5 bg-green-500"></span>
        </span>
      </div>

      <!-- Navigation Links with Dedicated URLs -->
      <nav class="space-y-1.5" id="sidebar-nav">
        <a href="/admin/overview" onclick="return navigateTab('overview', '/admin/overview')" id="nav-btn-overview" class="w-full flex items-center space-x-3 px-3.5 py-2.5 rounded-xl text-sm font-bold bg-kalisi-gold/15 text-kalisi-gold border border-kalisi-gold/30 transition">
          <i class="fas fa-chart-pie w-5 text-center"></i>
          <span>Overview</span>
        </a>

        <a href="/admin/users" onclick="return navigateTab('users', '/admin/users')" id="nav-btn-users" class="w-full flex items-center space-x-3 px-3.5 py-2.5 rounded-xl text-sm font-semibold text-gray-400 hover:text-white hover:bg-kalisi-surfaceLight transition">
          <i class="fas fa-users w-5 text-center"></i>
          <span>Users Directory</span>
        </a>

        <a href="/admin/events" onclick="return navigateTab('events', '/admin/events')" id="nav-btn-events" class="w-full flex items-center space-x-3 px-3.5 py-2.5 rounded-xl text-sm font-semibold text-gray-400 hover:text-white hover:bg-kalisi-surfaceLight transition">
          <i class="fas fa-calendar-check w-5 text-center"></i>
          <span>Events List</span>
        </a>

        <a href="/admin/event-bookings" onclick="return navigateTab('event-bookings', '/admin/event-bookings')" id="nav-btn-event-bookings" class="w-full flex items-center space-x-3 px-3.5 py-2.5 rounded-xl text-sm font-semibold text-gray-400 hover:text-white hover:bg-kalisi-surfaceLight transition">
          <i class="fas fa-clipboard-user w-5 text-center"></i>
          <span>Event Bookings</span>
        </a>

        <a href="/admin/payments" onclick="return navigateTab('payments', '/admin/payments')" id="nav-btn-payments" class="w-full flex items-center space-x-3 px-3.5 py-2.5 rounded-xl text-sm font-semibold text-gray-400 hover:text-white hover:bg-kalisi-surfaceLight transition">
          <i class="fas fa-indian-rupee-sign w-5 text-center"></i>
          <span>Payments</span>
        </a>

        <a href="/admin/videos" onclick="return navigateTab('videos', '/admin/videos')" id="nav-btn-videos" class="w-full flex items-center space-x-3 px-3.5 py-2.5 rounded-xl text-sm font-semibold text-gray-400 hover:text-white hover:bg-kalisi-surfaceLight transition">
          <i class="fas fa-play-circle w-5 text-center"></i>
          <span>Videos & Reels</span>
        </a>

        <a href="/admin/notifications" onclick="return navigateTab('notifications', '/admin/notifications')" id="nav-btn-notifications" class="w-full flex items-center space-x-3 px-3.5 py-2.5 rounded-xl text-sm font-semibold text-gray-400 hover:text-white hover:bg-kalisi-surfaceLight transition">
          <i class="fas fa-bell w-5 text-center text-kalisi-gold"></i>
          <span>Push Notifications</span>
        </a>
      </nav>

      <!-- Quick Actions -->
      <div class="pt-4 border-t border-kalisi-border space-y-2">
        <a href="/api/docs" target="_blank" class="w-full py-2 rounded-xl bg-kalisi-surface border border-kalisi-border hover:border-gray-500 text-xs font-bold text-gray-300 hover:text-white text-center block transition">
          <i class="fas fa-code mr-1.5"></i> Swagger API Docs
        </a>
      </div>
    </div>

    <!-- Admin Profile & Logout -->
    <div class="p-4 border-t border-kalisi-border bg-kalisi-surface/40 flex items-center justify-between">
      <div class="flex items-center space-x-2.5">
        <div class="w-8 h-8 rounded-full bg-kalisi-purple/30 border border-kalisi-purple text-kalisi-purple flex items-center justify-center font-black text-xs">
          A
        </div>
        <div>
          <div class="text-xs font-bold text-white">Super Admin</div>
          <div class="text-[10px] text-gray-400">admin@kalisi.app</div>
        </div>
      </div>
      <button onclick="handleLogout()" title="Sign Out" class="p-2 rounded-lg text-gray-400 hover:text-red-400 hover:bg-kalisi-surfaceLight transition">
        <i class="fas fa-arrow-right-from-bracket text-sm"></i>
      </button>
    </div>
  </aside>

  <!-- ======================================================================= -->
  <!-- MAIN CONTENT AREA                                                       -->
  <!-- ======================================================================= -->
  <main class="flex-1 min-w-0 p-8 space-y-8 overflow-y-auto max-h-screen">

    <!-- TAB 1: OVERVIEW & KPIS -->
    <section id="tab-overview" class="space-y-8">
      <div class="flex items-center justify-between">
        <div>
          <h2 class="text-2xl font-black tracking-tight text-white">Platform Overview</h2>
          <p class="text-xs text-gray-400">Real-time pulse of Kalisi dinner meetups across all active cities.</p>
        </div>
        <button onclick="loadData()" class="px-4 py-2 rounded-xl bg-kalisi-surfaceLight border border-kalisi-border text-xs font-bold text-gray-300 hover:text-white hover:border-kalisi-gold transition flex items-center space-x-2">
          <i class="fas fa-arrows-rotate"></i>
          <span>Refresh Live Data</span>
        </button>
      </div>

      <!-- Core Stat Cards -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
        <div class="glass-card p-5 rounded-2xl space-y-2 border-l-4 border-l-kalisi-gold">
          <div class="flex items-center justify-between text-xs font-bold text-gray-400 uppercase tracking-wider">
            <span>Total Users</span>
            <i class="fas fa-users text-kalisi-gold"></i>
          </div>
          <div class="text-3xl font-black text-white" id="stat-total-users">0</div>
          <p class="text-[11px] text-gray-400">Registered on mobile</p>
        </div>

        <div class="glass-card p-5 rounded-2xl space-y-2 border-l-4 border-l-kalisi-purple">
          <div class="flex items-center justify-between text-xs font-bold text-gray-400 uppercase tracking-wider">
            <span>Event Booked Members</span>
            <i class="fas fa-ticket text-kalisi-purple"></i>
          </div>
          <div class="text-3xl font-black text-white" id="stat-booked-members">0</div>
          <p class="text-[11px] text-gray-400">Total seat reservations</p>
        </div>

        <div class="glass-card p-5 rounded-2xl space-y-2 border-l-4 border-l-green-500">
          <div class="flex items-center justify-between text-xs font-bold text-gray-400 uppercase tracking-wider">
            <span>Active Events</span>
            <i class="fas fa-calendar-check text-green-400"></i>
          </div>
          <div class="text-3xl font-black text-white" id="stat-active-events">0</div>
          <p class="text-[11px] text-green-400 font-semibold">Open for booking now</p>
        </div>

        <div class="glass-card p-5 rounded-2xl space-y-2 border-l-4 border-l-blue-400">
          <div class="flex items-center justify-between text-xs font-bold text-gray-400 uppercase tracking-wider">
            <span>Completed Events</span>
            <i class="fas fa-flag-checkered text-blue-400"></i>
          </div>
          <div class="text-3xl font-black text-white" id="stat-completed-events">0</div>
          <p class="text-[11px] text-gray-400">Past successful dinners</p>
        </div>
      </div>

      <!-- Secondary Metrics -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-5">
        <div class="glass-card p-5 rounded-2xl flex items-center justify-between">
          <div>
            <span class="text-xs font-bold text-gray-400 uppercase tracking-wider block mb-1">Total Platform Revenue</span>
            <div class="text-2xl font-black text-kalisi-gold" id="stat-total-revenue">₹0</div>
          </div>
          <div class="w-12 h-12 rounded-xl bg-kalisi-gold/20 flex items-center justify-center text-kalisi-gold text-xl">
            <i class="fas fa-indian-rupee-sign"></i>
          </div>
        </div>

        <div class="glass-card p-5 rounded-2xl flex items-center justify-between">
          <div>
            <span class="text-xs font-bold text-gray-400 uppercase tracking-wider block mb-1">Dinner Reels & Videos</span>
            <div class="text-2xl font-black text-kalisi-purple" id="stat-total-videos">0</div>
          </div>
          <div class="w-12 h-12 rounded-xl bg-kalisi-purple/20 flex items-center justify-center text-kalisi-purple text-xl">
            <i class="fas fa-play-circle"></i>
          </div>
        </div>

        <div class="glass-card p-5 rounded-2xl flex items-center justify-between">
          <div>
            <span class="text-xs font-bold text-gray-400 uppercase tracking-wider block mb-1">Partner Venues</span>
            <div class="text-2xl font-black text-green-400" id="stat-total-venues">0</div>
          </div>
          <div class="w-12 h-12 rounded-xl bg-green-500/20 flex items-center justify-center text-green-400 text-xl">
            <i class="fas fa-utensils"></i>
          </div>
        </div>
      </div>

      <!-- Quick Snapshot: Live Events & Recent Bookings -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 pt-2">
        <!-- Live Upcoming Events Card -->
        <div class="glass-card p-6 rounded-2xl space-y-4">
          <div class="flex items-center justify-between">
            <h3 class="text-sm font-black text-white flex items-center gap-2">
              <i class="fas fa-calendar-check text-kalisi-gold"></i>
              <span>Active Upcoming Dinner Slots</span>
            </h3>
            <a href="/admin/events" onclick="return navigateTab('events', '/admin/events')" class="text-xs text-kalisi-gold hover:underline font-bold">Manage All →</a>
          </div>
          <div class="overflow-x-auto">
            <table class="w-full text-left text-xs">
              <thead class="text-gray-400 uppercase tracking-wider border-b border-kalisi-border bg-kalisi-surfaceLight/50">
                <tr>
                  <th class="px-3 py-2.5">Event</th>
                  <th class="px-3 py-2.5">Date & Time</th>
                  <th class="px-3 py-2.5">Price</th>
                  <th class="px-3 py-2.5">Bookings</th>
                </tr>
              </thead>
              <tbody id="overview-events-tbody" class="divide-y divide-kalisi-border/50 text-gray-300"></tbody>
            </table>
          </div>
        </div>

        <!-- Recent Bookings Feed Card -->
        <div class="glass-card p-6 rounded-2xl space-y-4">
          <div class="flex items-center justify-between">
            <h3 class="text-sm font-black text-white flex items-center gap-2">
              <i class="fas fa-receipt text-kalisi-purple"></i>
              <span>Recent Dinner Bookings Activity</span>
            </h3>
            <a href="/admin/event-bookings" onclick="return navigateTab('event-bookings', '/admin/event-bookings')" class="text-xs text-kalisi-purple hover:underline font-bold">View Ledger →</a>
          </div>
          <div class="overflow-x-auto">
            <table class="w-full text-left text-xs">
              <thead class="text-gray-400 uppercase tracking-wider border-b border-kalisi-border bg-kalisi-surfaceLight/50">
                <tr>
                  <th class="px-3 py-2.5">Member</th>
                  <th class="px-3 py-2.5">Event</th>
                  <th class="px-3 py-2.5">Paid</th>
                  <th class="px-3 py-2.5">Status</th>
                </tr>
              </thead>
              <tbody id="overview-bookings-tbody" class="divide-y divide-kalisi-border/50 text-gray-300"></tbody>
            </table>
          </div>
        </div>
      </div>
    </section>

    <!-- TAB 2: USERS DIRECTORY -->
    <section id="tab-users" class="hidden space-y-6">
      <div class="flex items-center justify-between">
        <div>
          <h2 class="text-2xl font-black text-white">Users Directory</h2>
          <p class="text-xs text-gray-400">All registered attendees with Vibe DNA archetypes, age, gender, and contact info.</p>
        </div>
      </div>

      <div class="glass-card rounded-2xl overflow-hidden">
        <div class="overflow-x-auto">
          <table class="w-full text-left text-sm">
            <thead class="bg-kalisi-surfaceLight text-xs font-bold text-gray-400 uppercase tracking-wider border-b border-kalisi-border">
              <tr>
                <th class="px-6 py-4">User</th>
                <th class="px-6 py-4">Phone</th>
                <th class="px-6 py-4">Age / Gender</th>
                <th class="px-6 py-4">City</th>
                <th class="px-6 py-4">Vibe DNA Archetype</th>
                <th class="px-6 py-4">Bookings</th>
                <th class="px-6 py-4">Status & FCM</th>
                <th class="px-6 py-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody id="users-tbody" class="divide-y divide-kalisi-border text-gray-300"></tbody>
          </table>
        </div>
      </div>
    </section>

    <!-- TAB 3: EVENTS LIST -->
    <section id="tab-events" class="hidden space-y-6">
      <div class="flex items-center justify-between">
        <div>
          <h2 class="text-2xl font-black text-white">Events Management</h2>
          <p class="text-xs text-gray-400">Manage all dinner events, edit titles, venues, rules, price, and toggle availability.</p>
        </div>
        <button onclick="document.getElementById('modal-new-slot').classList.remove('hidden')" class="px-4 py-2.5 rounded-xl bg-kalisi-gold text-black text-xs font-black hover:brightness-110 active:scale-95 transition flex items-center space-x-2">
          <i class="fas fa-plus"></i>
          <span>Schedule New Event</span>
        </button>
      </div>

      <div class="glass-card rounded-2xl overflow-hidden">
        <div class="overflow-x-auto">
          <table class="w-full text-left text-sm">
            <thead class="bg-kalisi-surfaceLight text-xs font-bold text-gray-400 uppercase tracking-wider border-b border-kalisi-border">
              <tr>
                <th class="px-6 py-4">Event Name & City</th>
                <th class="px-6 py-4">Date & Time</th>
                <th class="px-6 py-4">Venue & Address</th>
                <th class="px-6 py-4">Price</th>
                <th class="px-6 py-4">Bookings</th>
                <th class="px-6 py-4">Status</th>
                <th class="px-6 py-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody id="events-tbody" class="divide-y divide-kalisi-border text-gray-300"></tbody>
          </table>
        </div>
      </div>
    </section>

    <!-- TAB 4: PARTICULAR EVENT BOOKINGS -->
    <section id="tab-event-bookings" class="hidden space-y-6">
      <div class="flex items-center justify-between">
        <div>
          <h2 class="text-2xl font-black text-white">Particular Event Bookings</h2>
          <p class="text-xs text-gray-400">Detailed attendee breakdown, dietary requirements & attendance for a specific event.</p>
        </div>
        <!-- Event Switcher Dropdown -->
        <div class="flex items-center space-x-3">
          <label class="text-xs font-bold text-gray-400">Select Event:</label>
          <select id="event-select-dropdown" onchange="onSelectEventFromDropdown()" class="bg-kalisi-surfaceLight border border-kalisi-border rounded-xl px-4 py-2 text-xs font-bold text-white focus:outline-none focus:border-kalisi-gold">
          </select>
        </div>
      </div>

      <!-- Event Header Banner -->
      <div id="event-detail-banner" class="glass-card p-6 rounded-2xl border-l-4 border-l-kalisi-gold space-y-2">
      </div>

      <!-- Attendees Table -->
      <div class="glass-card rounded-2xl overflow-hidden">
        <div class="overflow-x-auto">
          <table class="w-full text-left text-sm">
            <thead class="bg-kalisi-surfaceLight text-xs font-bold text-gray-400 uppercase tracking-wider border-b border-kalisi-border">
              <tr>
                <th class="px-6 py-4">Attendee</th>
                <th class="px-6 py-4">Phone</th>
                <th class="px-6 py-4">Age / Gender</th>
                <th class="px-6 py-4">Archetype</th>
                <th class="px-6 py-4">Dietary</th>
                <th class="px-6 py-4">Payment</th>
                <th class="px-6 py-4">Attendance</th>
                <th class="px-6 py-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody id="event-attendees-tbody" class="divide-y divide-kalisi-border text-gray-300"></tbody>
          </table>
        </div>
      </div>
    </section>

    <!-- TAB 5: PAYMENTS & FINANCIAL LEDGER -->
    <section id="tab-payments" class="hidden space-y-6">
      <div class="flex items-center justify-between">
        <div>
          <h2 class="text-2xl font-black text-white">Payments & Revenue</h2>
          <p class="text-xs text-gray-400">Audit trail of all transaction records, payment methods, and revenue.</p>
        </div>
      </div>

      <div class="glass-card rounded-2xl overflow-hidden">
        <div class="overflow-x-auto">
          <table class="w-full text-left text-sm">
            <thead class="bg-kalisi-surfaceLight text-xs font-bold text-gray-400 uppercase tracking-wider border-b border-kalisi-border">
              <tr>
                <th class="px-6 py-4">Booking ID</th>
                <th class="px-6 py-4">User</th>
                <th class="px-6 py-4">Event Date & City</th>
                <th class="px-6 py-4">Amount</th>
                <th class="px-6 py-4">Method</th>
                <th class="px-6 py-4">Status</th>
                <th class="px-6 py-4">Date</th>
              </tr>
            </thead>
            <tbody id="payments-tbody" class="divide-y divide-kalisi-border text-gray-300"></tbody>
          </table>
        </div>
      </div>
    </section>

    <!-- TAB 6: VIDEOS & REELS -->
    <section id="tab-videos" class="hidden space-y-6">
      <div class="flex items-center justify-between">
        <div>
          <h2 class="text-2xl font-black text-white">Dinner Videos & Reels</h2>
          <p class="text-xs text-gray-400">Manage short community dinner reels displayed on mobile app.</p>
        </div>
        <button onclick="document.getElementById('modal-new-video').classList.remove('hidden')" class="px-4 py-2.5 rounded-xl bg-kalisi-purple text-white text-xs font-black hover:brightness-110 active:scale-95 transition flex items-center space-x-2">
          <i class="fas fa-plus"></i>
          <span>Add New Video</span>
        </button>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6" id="videos-grid">
      </div>
    </section>

    <!-- TAB 7: VERIFIED VENUES -->
    <section id="tab-venues" class="hidden space-y-6">
      <div class="flex items-center justify-between">
        <div>
          <h2 class="text-2xl font-black text-white">Verified Partner Venues</h2>
          <p class="text-xs text-gray-400">Handpicked restaurants with curated private tables, acoustics, and partner perks.</p>
        </div>
        <button onclick="document.getElementById('modal-new-venue').classList.remove('hidden')" class="px-4 py-2.5 rounded-xl bg-kalisi-gold text-black text-xs font-black hover:brightness-110 active:scale-95 transition flex items-center space-x-2">
          <i class="fas fa-plus"></i>
          <span>Add Verified Venue</span>
        </button>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6" id="venues-grid">
      </div>
    </section>

    <!-- TAB 8: PUSH NOTIFICATIONS -->
    <section id="tab-notifications" class="hidden space-y-6">
      <div class="flex items-center justify-between">
        <div>
          <h2 class="text-2xl font-black text-white flex items-center space-x-2">
            <i class="fas fa-bell text-kalisi-gold"></i>
            <span>Firebase Push Notifications</span>
          </h2>
          <p class="text-xs text-gray-400">Broadcast alerts, table reveal updates, and reminders directly to connected mobile devices.</p>
        </div>
        <div class="flex items-center space-x-2 bg-kalisi-surface px-3 py-1.5 rounded-xl border border-kalisi-border text-xs">
          <span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
          <span class="text-gray-300 font-bold">FCM Gateway: Connected</span>
        </div>
      </div>

      <!-- Notification Composer & Presets Grid -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <!-- Composer Form -->
        <div class="lg:col-span-2 bg-kalisi-surface rounded-2xl border border-kalisi-border p-6 shadow-xl">
          <h3 class="text-base font-bold text-white mb-4 flex items-center space-x-2">
            <i class="fas fa-paper-plane text-kalisi-gold text-sm"></i>
            <span>Compose Notification</span>
          </h3>
          <form id="form-push-notification" onsubmit="return handleSendPushNotification(event)" class="space-y-4">
            <div>
              <label class="block text-xs font-bold text-gray-400 uppercase mb-1">Target Audience</label>
              <select name="target_type" id="push-target-type" onchange="togglePushTarget(this.value)" class="w-full bg-kalisi-surfaceLight px-4 py-2.5 rounded-xl border border-kalisi-border text-sm text-white focus:outline-none focus:border-kalisi-gold">
                <option value="broadcast">📢 All Users (Broadcast to All Connected Devices)</option>
                <option value="user">👤 Specific Selected User</option>
                <option value="event_booked">🎟️ Selected Event Booked Members</option>
                <option value="city">📍 Filter by Neighborhood / City</option>
              </select>
            </div>

            <!-- User Select Wrapper -->
            <div id="push-user-select-wrapper" class="hidden">
              <label class="block text-xs font-bold text-gray-400 uppercase mb-1">Select User (By Name or Phone)</label>
              <select name="user_id" id="push-user-select" onchange="onSelectPushUser(this.value)" class="w-full bg-kalisi-surfaceLight px-4 py-2.5 rounded-xl border border-kalisi-border text-sm text-white focus:outline-none focus:border-kalisi-gold">
                <option value="">-- Choose User --</option>
              </select>
            </div>

            <!-- Event Select Wrapper -->
            <div id="push-event-select-wrapper" class="hidden">
              <label class="block text-xs font-bold text-gray-400 uppercase mb-1">Select Event to Notify Booked Members</label>
              <select name="event_id" id="push-event-select" class="w-full bg-kalisi-surfaceLight px-4 py-2.5 rounded-xl border border-kalisi-border text-sm text-white focus:outline-none focus:border-kalisi-gold">
                <option value="">-- Choose Event --</option>
              </select>
            </div>

            <!-- City Select Wrapper -->
            <div id="push-city-select-wrapper" class="hidden">
              <label class="block text-xs font-bold text-gray-400 uppercase mb-1">Target Neighborhood</label>
              <select name="city" id="push-city" class="w-full bg-kalisi-surfaceLight px-4 py-2.5 rounded-xl border border-kalisi-border text-sm text-white focus:outline-none focus:border-kalisi-gold">
                <option value="Central Bangalore">Central Bangalore</option>
                <option value="Indiranagar Bangalore">Indiranagar Bangalore</option>
                <option value="Koramangala Bangalore">Koramangala Bangalore</option>
                <option value="Anna Nagar Chennai">Anna Nagar Chennai</option>
                <option value="South Mumbai">South Mumbai</option>
              </select>
            </div>

            <!-- Optional Device FCM Token Override for testing -->
            <div id="push-test-token-wrapper">
              <div class="flex items-center justify-between mb-1">
                <label class="text-[11px] font-bold text-gray-400 uppercase">Device FCM Token (Auto-synced or Manual Test Override)</label>
                <span id="push-token-status" class="text-[10px]"></span>
              </div>
              <input type="text" name="test_token" id="push-test-token" placeholder="Auto-populated when user has an active token, or paste a test token here..." class="w-full bg-kalisi-surfaceLight px-4 py-2 rounded-xl border border-kalisi-border text-xs text-gray-300 font-mono focus:outline-none focus:border-kalisi-gold">
            </div>

            <div>
              <label class="block text-xs font-bold text-gray-400 uppercase mb-1">Notification Title</label>
              <input type="text" name="title" id="push-title" placeholder="e.g. 🎉 Your Secret Venue Address is Revealed!" required class="w-full bg-kalisi-surfaceLight px-4 py-2.5 rounded-xl border border-kalisi-border text-sm text-white focus:outline-none focus:border-kalisi-gold">
            </div>

            <div>
              <label class="block text-xs font-bold text-gray-400 uppercase mb-1">Message Body</label>
              <textarea name="body" id="push-body" rows="3" placeholder="e.g. Good morning! Your matched table at Lavelle Road is ready. Open Kalisi to see your tablemates." required class="w-full bg-kalisi-surfaceLight px-4 py-2.5 rounded-xl border border-kalisi-border text-sm text-white focus:outline-none focus:border-kalisi-gold"></textarea>
            </div>

            <button type="submit" id="btn-send-push" class="w-full py-3 rounded-xl bg-kalisi-gold text-black font-black text-sm hover:brightness-110 active:scale-95 transition flex items-center justify-center space-x-2">
              <i class="fas fa-paper-plane"></i>
              <span>Send Push Notification to Devices</span>
            </button>
          </form>
          <div id="push-feedback" class="mt-4 hidden p-3 rounded-xl text-xs font-semibold"></div>
        </div>

        <!-- Quick 1-Click Presets -->
        <div class="space-y-4">
          <div class="bg-kalisi-surface rounded-2xl border border-kalisi-border p-5 shadow-xl">
            <h3 class="text-sm font-bold text-white mb-3 flex items-center space-x-2">
              <i class="fas fa-bolt text-kalisi-purple"></i>
              <span>1-Click Event Presets</span>
            </h3>
            <div class="space-y-2.5">
              <button type="button" onclick="applyPushPreset('venue_reveal')" class="w-full text-left p-3 rounded-xl bg-kalisi-surfaceLight hover:bg-kalisi-border border border-kalisi-border transition group">
                <div class="text-xs font-black text-kalisi-gold group-hover:underline">🎉 Table & Venue Reveal</div>
                <div class="text-[11px] text-gray-400 mt-1">"Your mystery table is unlocked! Tap to check your restaurant address."</div>
              </button>
              <button type="button" onclick="applyPushPreset('anti_ghosting')" class="w-full text-left p-3 rounded-xl bg-kalisi-surfaceLight hover:bg-kalisi-border border border-kalisi-border transition group">
                <div class="text-xs font-black text-kalisi-purple group-hover:underline">⏰ T-2 Hours Attendance Check</div>
                <div class="text-[11px] text-gray-400 mt-1">"Dinner starts in 2 hours! Open your ticket to confirm your seat."</div>
              </button>
              <button type="button" onclick="applyPushPreset('weekend_open')" class="w-full text-left p-3 rounded-xl bg-kalisi-surfaceLight hover:bg-kalisi-border border border-kalisi-border transition group">
                <div class="text-xs font-black text-emerald-400 group-hover:underline">✨ Weekend Meetup Slots Live</div>
                <div class="text-[11px] text-gray-400 mt-1">"Fresh stranger dinner slots are open for booking in your neighborhood!"</div>
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Sent Notifications History -->
      <div class="bg-kalisi-surface rounded-2xl border border-kalisi-border overflow-hidden shadow-xl">
        <div class="p-5 border-b border-kalisi-border flex items-center justify-between">
          <h3 class="text-sm font-black text-white">Recent Dispatched Notifications</h3>
          <span class="text-xs text-gray-500">Live Firebase Delivery Status</span>
        </div>
        <div class="overflow-x-auto">
          <table class="w-full text-left border-collapse text-xs">
            <thead>
              <tr class="border-b border-kalisi-border bg-kalisi-surfaceLight/50 text-gray-400 font-bold uppercase">
                <th class="p-3.5">Title</th>
                <th class="p-3.5">Message Body</th>
                <th class="p-3.5">Target</th>
                <th class="p-3.5">Delivered</th>
                <th class="p-3.5">Time</th>
                <th class="p-3.5 text-right">Status</th>
              </tr>
            </thead>
            <tbody id="notifications-table-body" class="divide-y divide-kalisi-border text-gray-300">
              <tr>
                <td class="p-3.5 font-bold text-white">🎉 Welcome to Kalisi</td>
                <td class="p-3.5 text-gray-400">Welcome to Kalisi! Your profile is verified and ready for meetups.</td>
                <td class="p-3.5"><span class="px-2 py-0.5 rounded bg-blue-900/30 text-blue-400 border border-blue-800/40 text-[10px] font-bold">Broadcast</span></td>
                <td class="p-3.5 font-bold text-emerald-400">All Devices</td>
                <td class="p-3.5 text-gray-500">System</td>
                <td class="p-3.5 text-right"><span class="px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400 font-bold text-[10px]">Delivered</span></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </section>

  </main>

  <!-- ======================================================================= -->
  <!-- MODAL: ADD NEW EVENT SLOT & VENUE                                       -->
  <!-- ======================================================================= -->
  <div id="modal-new-slot" class="hidden fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
    <div class="glass-card bg-kalisi-surface max-w-2xl w-full p-6 rounded-3xl border border-kalisi-border space-y-4 max-h-[90vh] overflow-y-auto">
      <div class="flex items-center justify-between pb-3 border-b border-kalisi-border">
        <h3 class="text-lg font-black text-white">Create New Event & Venue</h3>
        <button onclick="document.getElementById('modal-new-slot').classList.add('hidden')" class="text-gray-400 hover:text-white"><i class="fas fa-times"></i></button>
      </div>
      <form onsubmit="handleCreateSlot(event)" class="space-y-4">
        <div>
          <label class="block text-xs font-bold text-gray-400 uppercase mb-1">Event Name / Title</label>
          <input type="text" name="title" required placeholder="e.g. Saturday Rooftop Stranger Dinner" class="w-full bg-kalisi-surfaceLight px-4 py-2.5 rounded-xl border border-kalisi-border text-sm text-white">
        </div>
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block text-xs font-bold text-gray-400 uppercase mb-1">City / Neighborhood</label>
            <input type="text" name="city" required placeholder="e.g. Central Bangalore" class="w-full bg-kalisi-surfaceLight px-4 py-2.5 rounded-xl border border-kalisi-border text-sm text-white">
          </div>
          <div>
            <label class="block text-xs font-bold text-gray-400 uppercase mb-1">Date</label>
            <input type="text" name="date_str" required placeholder="Sat, 11/28/2026" class="w-full bg-kalisi-surfaceLight px-4 py-2.5 rounded-xl border border-kalisi-border text-sm text-white">
          </div>
        </div>
        <div class="grid grid-cols-3 gap-3">
          <div>
            <label class="block text-xs font-bold text-gray-400 uppercase mb-1">Time Window</label>
            <input type="text" name="time_window" required placeholder="19:30 - 22:30" class="w-full bg-kalisi-surfaceLight px-4 py-2.5 rounded-xl border border-kalisi-border text-sm text-white">
          </div>
          <div>
            <label class="block text-xs font-bold text-gray-400 uppercase mb-1">Price (INR)</label>
            <input type="number" name="price_inr" value="599" required class="w-full bg-kalisi-surfaceLight px-4 py-2.5 rounded-xl border border-kalisi-border text-sm text-white">
          </div>
          <div>
            <label class="block text-xs font-bold text-gray-400 uppercase mb-1">Max Seats Capacity</label>
            <input type="number" name="max_capacity" value="10" required class="w-full bg-kalisi-surfaceLight px-4 py-2.5 rounded-xl border border-kalisi-border text-sm text-white">
          </div>
        </div>
        <div class="pt-2 border-t border-kalisi-border">
          <h4 class="text-xs font-black text-kalisi-gold uppercase mb-2">Venue & Restaurant Information</h4>
          <div class="space-y-3">
            <div>
              <label class="block text-xs font-bold text-gray-400 uppercase mb-1">Venue / Restaurant Name</label>
              <input type="text" name="venue_name" required placeholder="e.g. Smoke House Deli Lavelle Road" class="w-full bg-kalisi-surfaceLight px-4 py-2.5 rounded-xl border border-kalisi-border text-sm text-white">
            </div>
            <div>
              <label class="block text-xs font-bold text-gray-400 uppercase mb-1">Venue Full Address</label>
              <textarea name="venue_address" rows="2" required placeholder="Full street address & landmark" class="w-full bg-kalisi-surfaceLight px-4 py-2 rounded-xl border border-kalisi-border text-sm text-white">52, Ground Floor, Lavelle Road, Shanthala Nagar, Ashok Nagar, Bengaluru</textarea>
            </div>
          </div>
        </div>
        <div class="pt-2 border-t border-kalisi-border">
          <h4 class="text-xs font-black text-kalisi-gold uppercase mb-2">Event Details & Guidelines</h4>
          <div class="space-y-3">
            <div>
              <label class="block text-xs font-bold text-gray-400 uppercase mb-1">About the Event</label>
              <textarea name="about_event" rows="2" required class="w-full bg-kalisi-surfaceLight px-4 py-2 rounded-xl border border-kalisi-border text-sm text-white">Join 5 curated strangers for an evening of genuine conversations, delicious dining, and icebreaker games.</textarea>
            </div>
            <div>
              <label class="block text-xs font-bold text-gray-400 uppercase mb-1">Rules & Regulations</label>
              <textarea name="rules_and_regulations" rows="2" required class="w-full bg-kalisi-surfaceLight px-4 py-2 rounded-xl border border-kalisi-border text-sm text-white">1. Arrive within 15 minutes of start time.
2. Equal bill splitting for food & drinks.
3. Keep phone away and enjoy real conversations.
4. Age 18+ verified diners only.</textarea>
            </div>
          </div>
        </div>
        <button type="submit" class="w-full py-3 rounded-xl bg-kalisi-gold text-black font-extrabold text-sm hover:brightness-110 transition mt-2">Publish Event with Venue Details</button>
      </form>
    </div>
  </div>

  <!-- ======================================================================= -->
  <!-- MODAL: EDIT EVENT & VENUE DETAILS                                       -->
  <!-- ======================================================================= -->
  <div id="modal-edit-event" class="hidden fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
    <div class="glass-card bg-kalisi-surface max-w-2xl w-full p-6 rounded-3xl border border-kalisi-border space-y-4 max-h-[90vh] overflow-y-auto">
      <div class="flex items-center justify-between pb-3 border-b border-kalisi-border">
        <div class="flex items-center space-x-2">
          <div class="w-8 h-8 rounded-lg bg-blue-500/20 text-blue-400 flex items-center justify-center text-sm font-bold">
            <i class="fas fa-pen-to-square"></i>
          </div>
          <div>
            <h3 class="text-lg font-black text-white">Edit Event Details</h3>
            <p class="text-xs text-gray-400">Update event schedule, venue, pricing, rules, and publish again.</p>
          </div>
        </div>
        <button onclick="document.getElementById('modal-edit-event').classList.add('hidden')" class="text-gray-400 hover:text-white p-2"><i class="fas fa-times text-lg"></i></button>
      </div>
      <form onsubmit="handleUpdateEvent(event)" class="space-y-4">
        <input type="hidden" name="event_id" id="edit-event-id">
        <div>
          <label class="block text-xs font-bold text-gray-400 uppercase mb-1">Event Name / Title</label>
          <input type="text" name="title" id="edit-title" required class="w-full bg-kalisi-surfaceLight px-4 py-2.5 rounded-xl border border-kalisi-border text-sm text-white focus:outline-none focus:border-blue-400">
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
          <div>
            <label class="block text-xs font-bold text-gray-400 uppercase mb-1">City / Neighborhood</label>
            <input type="text" name="city" id="edit-city" required class="w-full bg-kalisi-surfaceLight px-4 py-2.5 rounded-xl border border-kalisi-border text-sm text-white focus:outline-none focus:border-blue-400">
          </div>
          <div>
            <label class="block text-xs font-bold text-gray-400 uppercase mb-1">Date</label>
            <input type="text" name="date_str" id="edit-date-str" required class="w-full bg-kalisi-surfaceLight px-4 py-2.5 rounded-xl border border-kalisi-border text-sm text-white focus:outline-none focus:border-blue-400">
          </div>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-3">
          <div>
            <label class="block text-xs font-bold text-gray-400 uppercase mb-1">Time Window</label>
            <input type="text" name="time_window" id="edit-time-window" required class="w-full bg-kalisi-surfaceLight px-4 py-2.5 rounded-xl border border-kalisi-border text-sm text-white focus:outline-none focus:border-blue-400">
          </div>
          <div>
            <label class="block text-xs font-bold text-gray-400 uppercase mb-1">Price (INR)</label>
            <input type="number" name="price_inr" id="edit-price-inr" required class="w-full bg-kalisi-surfaceLight px-4 py-2.5 rounded-xl border border-kalisi-border text-sm text-white focus:outline-none focus:border-blue-400">
          </div>
          <div>
            <label class="block text-xs font-bold text-gray-400 uppercase mb-1">Max Capacity</label>
            <input type="number" name="max_capacity" id="edit-max-capacity" required class="w-full bg-kalisi-surfaceLight px-4 py-2.5 rounded-xl border border-kalisi-border text-sm text-white focus:outline-none focus:border-blue-400">
          </div>
        </div>
        <div>
          <label class="block text-xs font-bold text-gray-400 uppercase mb-1">Status</label>
          <select name="status" id="edit-status" class="w-full bg-kalisi-surfaceLight px-4 py-2.5 rounded-xl border border-kalisi-border text-sm text-white focus:outline-none focus:border-blue-400">
            <option value="open">Open (Active & Visible on App)</option>
            <option value="disabled">Disabled (Hidden from App)</option>
            <option value="completed">Completed (Archived)</option>
          </select>
        </div>
        <div class="pt-2 border-t border-kalisi-border">
          <h4 class="text-xs font-black text-kalisi-gold uppercase mb-2">Venue & Restaurant Information</h4>
          <div class="space-y-3">
            <div>
              <label class="block text-xs font-bold text-gray-400 uppercase mb-1">Venue / Restaurant Name</label>
              <input type="text" name="venue_name" id="edit-venue-name" required class="w-full bg-kalisi-surfaceLight px-4 py-2.5 rounded-xl border border-kalisi-border text-sm text-white focus:outline-none focus:border-blue-400">
            </div>
            <div>
              <label class="block text-xs font-bold text-gray-400 uppercase mb-1">Venue Full Address</label>
              <textarea name="venue_address" id="edit-venue-address" rows="2" required class="w-full bg-kalisi-surfaceLight px-4 py-2 rounded-xl border border-kalisi-border text-sm text-white focus:outline-none focus:border-blue-400"></textarea>
            </div>
          </div>
        </div>
        <div class="pt-2 border-t border-kalisi-border">
          <h4 class="text-xs font-black text-kalisi-gold uppercase mb-2">Event Details & Guidelines</h4>
          <div class="space-y-3">
            <div>
              <label class="block text-xs font-bold text-gray-400 uppercase mb-1">About the Event</label>
              <textarea name="about_event" id="edit-about-event" rows="3" required class="w-full bg-kalisi-surfaceLight px-4 py-2 rounded-xl border border-kalisi-border text-sm text-white focus:outline-none focus:border-blue-400"></textarea>
            </div>
            <div>
              <label class="block text-xs font-bold text-gray-400 uppercase mb-1">Rules & Regulations</label>
              <textarea name="rules_and_regulations" id="edit-rules" rows="3" required class="w-full bg-kalisi-surfaceLight px-4 py-2 rounded-xl border border-kalisi-border text-sm text-white focus:outline-none focus:border-blue-400"></textarea>
            </div>
          </div>
        </div>
        <div class="flex items-center space-x-3 pt-2">
          <button type="button" onclick="document.getElementById('modal-edit-event').classList.add('hidden')" class="w-1/3 py-3 rounded-xl bg-gray-700 hover:bg-gray-600 text-white font-bold text-sm transition">Cancel</button>
          <button type="submit" class="w-2/3 py-3 rounded-xl bg-blue-500 hover:bg-blue-400 text-white font-black text-sm transition shadow-lg shadow-blue-500/20"><i class="fas fa-check-double mr-2"></i>Save & Post Event Updates</button>
        </div>
      </form>
    </div>
  </div>

  <!-- ======================================================================= -->
  <!-- MODAL: ADD NEW VIDEO / REEL                                             -->
  <!-- ======================================================================= -->
  <div id="modal-new-video" class="hidden fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
    <div class="glass-card bg-kalisi-surface max-w-lg w-full p-6 rounded-3xl border border-kalisi-border space-y-4">
      <div class="flex items-center justify-between pb-3 border-b border-kalisi-border">
        <h3 class="text-lg font-black text-white">Add New Video Reel</h3>
        <button onclick="document.getElementById('modal-new-video').classList.add('hidden')" class="text-gray-400 hover:text-white"><i class="fas fa-times"></i></button>
      </div>
      <form onsubmit="handleCreateVideo(event)" class="space-y-4" enctype="multipart/form-data">
        <div>
          <label class="block text-xs font-bold text-gray-400 uppercase mb-1">Video Title</label>
          <input type="text" name="title" required placeholder="e.g. When 5 Introverts Dine Together" class="w-full bg-kalisi-surfaceLight px-4 py-2.5 rounded-xl border border-kalisi-border text-sm text-white">
        </div>
        <div>
          <label class="block text-xs font-bold text-gray-400 uppercase mb-1">Venue / Event</label>
          <input type="text" name="venue_name" required placeholder="e.g. Central Bangalore Meetup" class="w-full bg-kalisi-surfaceLight px-4 py-2.5 rounded-xl border border-kalisi-border text-sm text-white">
        </div>

        <!-- Video File Upload & URL -->
        <div class="p-3.5 bg-kalisi-surfaceLight/80 rounded-2xl border border-kalisi-border space-y-2.5">
          <label class="block text-xs font-bold text-kalisi-gold uppercase flex items-center justify-between">
            <span class="flex items-center gap-1.5"><i class="fas fa-video"></i> Upload Video File</span>
            <span class="text-[10px] text-gray-400 font-normal">MP4, WebM, MOV</span>
          </label>
          <input type="file" name="video_file" id="admin-video-file-input" accept="video/*" class="w-full text-xs text-gray-300 file:mr-3 file:py-2 file:px-3.5 file:rounded-xl file:border-0 file:text-xs file:font-bold file:bg-kalisi-gold file:text-black hover:file:brightness-110 cursor-pointer">
          <div class="flex items-center gap-2 pt-1">
            <div class="h-px bg-kalisi-border flex-1"></div>
            <span class="text-[10px] text-gray-500 uppercase font-bold">OR External URL</span>
            <div class="h-px bg-kalisi-border flex-1"></div>
          </div>
          <input type="url" name="video_url" placeholder="https://... (Optional if file is selected above)" class="w-full bg-kalisi-surface px-3 py-2 rounded-xl border border-kalisi-border text-xs text-white">
        </div>

        <!-- Thumbnail Upload & URL -->
        <div class="p-3.5 bg-kalisi-surfaceLight/80 rounded-2xl border border-kalisi-border space-y-2.5">
          <label class="block text-xs font-bold text-kalisi-purple uppercase flex items-center justify-between">
            <span class="flex items-center gap-1.5"><i class="fas fa-image"></i> Thumbnail Image</span>
            <span class="text-[10px] text-gray-400 font-normal">JPG, PNG, WebP</span>
          </label>
          <input type="file" name="thumbnail_file" accept="image/*" class="w-full text-xs text-gray-300 file:mr-3 file:py-2 file:px-3.5 file:rounded-xl file:border-0 file:text-xs file:font-bold file:bg-kalisi-purple file:text-white hover:file:brightness-110 cursor-pointer">
          <input type="url" name="thumbnail_url" placeholder="https://... (Optional preview image URL)" value="https://images.unsplash.com/photo-1543007630-9710e4a00a20?auto=format&fit=crop&w=800&q=80" class="w-full bg-kalisi-surface px-3 py-2 rounded-xl border border-kalisi-border text-xs text-white">
        </div>

        <button type="submit" id="btn-submit-video" class="w-full py-3 rounded-xl bg-kalisi-purple text-white font-extrabold text-sm hover:brightness-110 active:scale-95 transition flex items-center justify-center space-x-2">
          <i class="fas fa-upload mr-1.5"></i>
          <span>Upload & Publish Video Reel</span>
        </button>
      </form>
    </div>
  </div>

  <!-- ======================================================================= -->
  <!-- MODAL: ADD VERIFIED VENUE                                               -->
  <!-- ======================================================================= -->
  <div id="modal-new-venue" class="hidden fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
    <div class="glass-card bg-kalisi-surface max-w-xl w-full p-6 rounded-3xl border border-kalisi-border space-y-4 max-h-[90vh] overflow-y-auto">
      <div class="flex items-center justify-between pb-3 border-b border-kalisi-border">
        <h3 class="text-lg font-black text-white">Add Verified Partner Venue</h3>
        <button onclick="document.getElementById('modal-new-venue').classList.add('hidden')" class="text-gray-400 hover:text-white"><i class="fas fa-times"></i></button>
      </div>
      <form onsubmit="handleCreateVenue(event)" class="space-y-3.5">
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block text-xs font-bold text-gray-400 uppercase mb-1">Venue Name</label>
            <input type="text" name="name" required placeholder="e.g. The Fatty Bao" class="w-full bg-kalisi-surfaceLight px-4 py-2 rounded-xl border border-kalisi-border text-sm text-white">
          </div>
          <div>
            <label class="block text-xs font-bold text-gray-400 uppercase mb-1">City</label>
            <input type="text" name="city" required placeholder="e.g. Bangalore" class="w-full bg-kalisi-surfaceLight px-4 py-2 rounded-xl border border-kalisi-border text-sm text-white">
          </div>
        </div>
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block text-xs font-bold text-gray-400 uppercase mb-1">Neighborhood</label>
            <input type="text" name="neighborhood" required placeholder="e.g. Indiranagar" class="w-full bg-kalisi-surfaceLight px-4 py-2 rounded-xl border border-kalisi-border text-sm text-white">
          </div>
          <div>
            <label class="block text-xs font-bold text-gray-400 uppercase mb-1">Cuisine</label>
            <input type="text" name="cuisine" required placeholder="e.g. Asian / Dim Sum" class="w-full bg-kalisi-surfaceLight px-4 py-2 rounded-xl border border-kalisi-border text-sm text-white">
          </div>
        </div>
        <div>
          <label class="block text-xs font-bold text-gray-400 uppercase mb-1">Full Address</label>
          <input type="text" name="full_address" required placeholder="Complete physical address" class="w-full bg-kalisi-surfaceLight px-4 py-2 rounded-xl border border-kalisi-border text-sm text-white">
        </div>
        <div>
          <label class="block text-xs font-bold text-gray-400 uppercase mb-1">Activities Conducted</label>
          <input type="text" name="activities" value="Table icebreaker card games, curated conversation starters" class="w-full bg-kalisi-surfaceLight px-4 py-2 rounded-xl border border-kalisi-border text-sm text-white">
        </div>
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block text-xs font-bold text-gray-400 uppercase mb-1">Duration Occupied</label>
            <input type="text" name="duration_hours" value="2.5 Hours" class="w-full bg-kalisi-surfaceLight px-4 py-2 rounded-xl border border-kalisi-border text-sm text-white">
          </div>
          <div>
            <label class="block text-xs font-bold text-gray-400 uppercase mb-1">Price Tier</label>
            <select name="price_tier" class="w-full bg-kalisi-surfaceLight px-4 py-2 rounded-xl border border-kalisi-border text-sm text-white">
              <option value="budget">Budget (Under ₹800)</option>
              <option value="mid_range" selected>Mid-Range (₹800 - ₹1500)</option>
              <option value="premium">Premium (₹1500+)</option>
            </select>
          </div>
        </div>
        <div>
          <label class="block text-xs font-bold text-gray-400 uppercase mb-1">Special Highlights & Features</label>
          <input type="text" name="special_features" value="Dedicated private table, welcome drinks" class="w-full bg-kalisi-surfaceLight px-4 py-2 rounded-xl border border-kalisi-border text-sm text-white">
        </div>
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block text-xs font-bold text-gray-400 uppercase mb-1">Manager Contact Person</label>
            <input type="text" name="contact_person" value="Manager on Duty" class="w-full bg-kalisi-surfaceLight px-4 py-2 rounded-xl border border-kalisi-border text-sm text-white">
          </div>
          <div>
            <label class="block text-xs font-bold text-gray-400 uppercase mb-1">Manager Phone</label>
            <input type="text" name="contact_phone" value="+91 98765 43210" class="w-full bg-kalisi-surfaceLight px-4 py-2 rounded-xl border border-kalisi-border text-sm text-white">
          </div>
        </div>
        <button type="submit" class="w-full py-3 rounded-xl bg-kalisi-gold text-black font-extrabold text-sm hover:brightness-110 transition mt-2">Save Venue</button>
      </form>
    </div>
  </div>

  <!-- JAVASCRIPT CONTROLLER -->
  <script>
    let globalData = null;
    let selectedEventId = null;

    function navigateTab(tabId, url) {
      history.pushState({ tab: tabId }, '', url);
      switchTab(tabId);
      return false;
    }

    function detectTabFromPath() {
      const path = window.location.pathname;
      if (path.includes('/users')) switchTab('users');
      else if (path.includes('/event-bookings')) switchTab('event-bookings');
      else if (path.includes('/events') || path.includes('/slots')) switchTab('events');
      else if (path.includes('/payments')) switchTab('payments');
      else if (path.includes('/videos')) switchTab('videos');
      else if (path.includes('/venues')) switchTab('venues');
      else if (path.includes('/notifications')) switchTab('notifications');
      else switchTab('overview');
    }

    window.onpopstate = function() {
      detectTabFromPath();
    };

    function switchTab(tabId) {
      const tabs = ['overview', 'users', 'events', 'event-bookings', 'payments', 'videos', 'venues', 'notifications'];
      tabs.forEach(t => {
        const el = document.getElementById('tab-' + t);
        const btn = document.getElementById('nav-btn-' + t);
        if (el) el.classList.add('hidden');
        if (btn) {
          btn.classList.remove('bg-kalisi-gold/15', 'text-kalisi-gold', 'border', 'border-kalisi-gold/30', 'font-bold');
          btn.classList.add('text-gray-400', 'font-semibold');
        }
      });
      const activeEl = document.getElementById('tab-' + tabId);
      const activeBtn = document.getElementById('nav-btn-' + tabId);
      if (activeEl) activeEl.classList.remove('hidden');
      if (activeBtn) {
        activeBtn.classList.add('bg-kalisi-gold/15', 'text-kalisi-gold', 'border', 'border-kalisi-gold/30', 'font-bold');
        activeBtn.classList.remove('text-gray-400', 'font-semibold');
      }

      // If switching to event-bookings, ensure event dropdown is populated
      if (tabId === 'event-bookings' && globalData) {
        renderEventBookingsPage();
      }
    }

    function checkAuth() {
      const token = localStorage.getItem('kalisi_admin_token');
      if (!token) {
        window.location.href = '/admin/login';
        return;
      }
      detectTabFromPath();
      loadData();
    }

    function handleLogout() {
      localStorage.removeItem('kalisi_admin_token');
      window.location.href = '/admin/login';
    }

    async function loadData() {
      try {
        const res = await fetch('/admin/api/overview');
        const data = await res.json();
        globalData = data;
        renderAll(data);
      } catch (e) {
        console.error('Failed to load overview data', e);
      }
    }

    function renderAll(data) {
      // 1. Overview Stat Cards
      document.getElementById('stat-total-users').innerText = data.metrics.total_users || 0;
      document.getElementById('stat-booked-members').innerText = data.metrics.event_booked_members || 0;
      document.getElementById('stat-active-events').innerText = data.metrics.active_events || 0;
      document.getElementById('stat-completed-events').innerText = data.metrics.completed_events || 0;
      document.getElementById('stat-total-revenue').innerText = '₹' + (data.metrics.total_revenue_inr || 0);
      document.getElementById('stat-total-videos').innerText = data.metrics.total_videos || 0;
      document.getElementById('stat-total-venues').innerText = data.metrics.total_venues || 0;

      // Overview Live Tables
      const ovEvents = document.getElementById('overview-events-tbody');
      if (ovEvents) {
        ovEvents.innerHTML = (data.events || []).slice(0, 5).map(e => `
          <tr class="hover:bg-kalisi-surfaceLight/30">
            <td class="py-2.5 px-3">
              <span class="font-bold text-white block truncate max-w-[140px]">${e.title || 'Dinner Meetup'}</span>
              <span class="text-[10px] text-kalisi-gold">${e.city}</span>
            </td>
            <td class="py-2.5 px-3 font-medium text-gray-300 text-[11px]">${e.date_str}</td>
            <td class="py-2.5 px-3 font-bold text-kalisi-gold text-[11px]">₹${e.price_inr}</td>
            <td class="py-2.5 px-3">
              <span class="px-2 py-0.5 rounded text-[10px] font-bold ${e.bookings_count >= e.max_capacity ? 'bg-red-500/20 text-red-400' : 'bg-green-500/20 text-green-400'}">
                ${e.bookings_count}/${e.max_capacity}
              </span>
            </td>
          </tr>
        `).join('');
      }

      const ovBookings = document.getElementById('overview-bookings-tbody');
      if (ovBookings) {
        ovBookings.innerHTML = (data.bookings || []).slice(0, 5).map(b => `
          <tr class="hover:bg-kalisi-surfaceLight/30">
            <td class="py-2.5 px-3">
              <span class="font-bold text-white block truncate max-w-[120px]">${b.user_name}</span>
              <span class="text-[10px] text-gray-400">${b.user_archetype}</span>
            </td>
            <td class="py-2.5 px-3 font-medium text-gray-300 text-[11px]">${b.slot_city}</td>
            <td class="py-2.5 px-3 font-bold text-kalisi-gold text-[11px]">₹${b.amount_paid}</td>
            <td class="py-2.5 px-3">
              <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-green-500/20 text-green-400 uppercase">Paid</span>
            </td>
          </tr>
        `).join('');
      }

      // 2. Users Directory Table
      const usersTbody = document.getElementById('users-tbody');
      usersTbody.innerHTML = (data.users || []).map(u => {
        const hasToken = !!u.fcm_token;
        const fcmBadge = hasToken 
          ? `<span class="px-2 py-0.5 rounded-full text-[10px] font-black bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 inline-flex items-center"><i class="fas fa-bell mr-1"></i>FCM Active</span>`
          : `<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-gray-500/20 text-gray-400 border border-gray-600/30 inline-flex items-center">No Token</span>`;
        return `
        <tr class="hover:bg-kalisi-surfaceLight/50 transition">
          <td class="px-6 py-4">
            <span class="font-black text-white block">${u.name}</span>
            <span class="text-xs text-gray-400">${u.email}</span>
          </td>
          <td class="px-6 py-4 text-xs font-mono text-gray-300">${u.phone}</td>
          <td class="px-6 py-4 text-xs text-gray-300">${u.age} y/o • ${u.gender}</td>
          <td class="px-6 py-4 text-xs font-bold text-gray-200">${u.city}</td>
          <td class="px-6 py-4">
            <span class="px-2.5 py-1 rounded-full text-xs font-bold bg-kalisi-purple/20 text-kalisi-purple border border-kalisi-purple/30">${u.archetype}</span>
          </td>
          <td class="px-6 py-4 text-xs font-bold text-kalisi-gold">${u.bookings_count} Bookings</td>
          <td class="px-6 py-4 space-y-1">
            <div><span class="text-green-400 font-bold text-xs"><i class="fas fa-check-circle mr-1"></i>Verified</span></div>
            <div>${fcmBadge}</div>
          </td>
          <td class="px-6 py-4 text-right">
            <button onclick="quickPushToUser('${u.id}', '${u.name}')" title="Send push notification to this user" class="px-2.5 py-1 rounded-lg bg-kalisi-gold/20 text-kalisi-gold border border-kalisi-gold/40 text-xs font-bold hover:bg-kalisi-gold hover:text-black transition">
              <i class="fas fa-paper-plane mr-1"></i> Push
            </button>
          </td>
        </tr>
      `}).join('');

      // 3. Events List Table
      const eventsTbody = document.getElementById('events-tbody');
      eventsTbody.innerHTML = (data.events || []).map(e => {
        const isEnabled = e.status === 'open';
        const isCompleted = e.status === 'completed';
        const statusBadge = isEnabled
          ? `<span class="px-2.5 py-1 rounded-full text-xs font-bold bg-green-500/20 text-green-400 border border-green-500/30 uppercase"><i class="fas fa-circle text-[8px] mr-1"></i>Enabled</span>`
          : isCompleted
            ? `<span class="px-2.5 py-1 rounded-full text-xs font-bold bg-blue-500/20 text-blue-400 border border-blue-500/30 uppercase">Completed</span>`
            : `<span class="px-2.5 py-1 rounded-full text-xs font-bold bg-red-500/20 text-red-400 border border-red-500/30 uppercase"><i class="fas fa-ban text-[8px] mr-1"></i>Disabled</span>`;

        return `
          <tr class="hover:bg-kalisi-surfaceLight/50 transition">
            <td class="px-6 py-4">
              <span class="font-black text-white block text-sm">${e.title || 'Dinner Meetup'}</span>
              <span class="text-xs text-kalisi-gold font-bold"><i class="fas fa-map-marker-alt mr-1"></i>${e.city}</span>
            </td>
            <td class="px-6 py-4">
              <span class="font-bold text-gray-200 block text-xs">${e.date_str}</span>
              <span class="text-[11px] text-gray-400">${e.time_window}</span>
            </td>
            <td class="px-6 py-4 max-w-xs">
              <span class="font-bold text-white block text-xs">${e.venue_name || 'Curated Partner Restaurant'}</span>
              <span class="text-[11px] text-gray-400 block truncate" title="${e.venue_address || ''}">${e.venue_address || 'Central Location'}</span>
            </td>
            <td class="px-6 py-4 font-black text-kalisi-gold">₹${e.price_inr}</td>
            <td class="px-6 py-4">
              <div class="flex items-center space-x-2">
                <span class="font-bold text-white text-xs">${e.bookings_count}</span>
                <span class="text-gray-400 text-xs">/ ${e.max_capacity}</span>
              </div>
            </td>
            <td class="px-6 py-4">${statusBadge}</td>
            <td class="px-6 py-4 text-right space-x-2 whitespace-nowrap">
              <button onclick="openEditEventModal('${e.id}')" class="px-2.5 py-1.5 rounded-lg bg-blue-500/20 text-blue-400 border border-blue-500/40 text-xs font-bold hover:bg-blue-500 hover:text-white transition">
                <i class="fas fa-pen-to-square mr-1"></i> Edit
              </button>
              <button onclick="toggleEventEnable('${e.id}')" class="px-2.5 py-1.5 rounded-lg text-xs font-bold transition ${isEnabled ? 'bg-red-500/20 text-red-400 border border-red-500/30 hover:bg-red-500 hover:text-white' : 'bg-green-500/20 text-green-400 border border-green-500/30 hover:bg-green-500 hover:text-white'}">
                <i class="fas ${isEnabled ? 'fa-ban' : 'fa-check'} mr-1"></i> ${isEnabled ? 'Disable' : 'Enable'}
              </button>
              <button onclick="viewParticularEventBookings('${e.id}')" class="px-2.5 py-1.5 rounded-lg bg-kalisi-gold/20 text-kalisi-gold border border-kalisi-gold/40 text-xs font-bold hover:bg-kalisi-gold hover:text-black transition">
                <i class="fas fa-users mr-1"></i> Bookings
              </button>
            </td>
          </tr>
        `;
      }).join('');

      // 4. Payments Table
      const paymentsTbody = document.getElementById('payments-tbody');
      paymentsTbody.innerHTML = (data.bookings || []).map(b => `
        <tr class="hover:bg-kalisi-surfaceLight/50 transition">
          <td class="px-6 py-4 text-xs font-mono text-gray-400">${b.id.substring(0, 8)}...</td>
          <td class="px-6 py-4 font-bold text-white">${b.user_name}</td>
          <td class="px-6 py-4 text-xs text-gray-300">${b.slot_date} • ${b.slot_city}</td>
          <td class="px-6 py-4 font-black text-kalisi-gold">₹${b.amount_paid}</td>
          <td class="px-6 py-4 text-xs font-bold text-gray-300">${b.payment_method}</td>
          <td class="px-6 py-4">
            <span class="px-2 py-0.5 rounded text-[11px] font-black ${b.payment_status === 'paid' ? 'bg-green-500/20 text-green-400 border border-green-500/40' : 'bg-gray-500/20 text-gray-400'} uppercase">
              ${b.payment_status}
            </span>
          </td>
          <td class="px-6 py-4 text-xs text-gray-400">${b.created_at}</td>
        </tr>
      `).join('');

      // 5. Videos Grid
      const videosGrid = document.getElementById('videos-grid');
      videosGrid.innerHTML = (data.videos || []).map(v => `
        <div class="glass-card rounded-2xl overflow-hidden border border-kalisi-border group">
          <div class="h-44 relative bg-cover bg-center" style="background-image: url('${v.thumbnail_url}')">
            <div class="absolute inset-0 bg-black/40 group-hover:bg-black/20 transition"></div>
            <a href="${v.video_url}" target="_blank" class="absolute inset-0 flex items-center justify-center">
              <div class="w-12 h-12 rounded-full bg-white/80 text-black flex items-center justify-center text-xl shadow-lg hover:scale-110 transition">
                <i class="fas fa-play ml-0.5"></i>
              </div>
            </a>
          </div>
          <div class="p-4 space-y-2">
            <h4 class="font-bold text-white text-sm line-clamp-1">${v.title}</h4>
            <div class="flex items-center justify-between text-xs text-gray-400">
              <span><i class="fas fa-location-dot text-kalisi-gold mr-1"></i>${v.venue_name}</span>
              <span><i class="fas fa-eye mr-1"></i>${v.views_count} views</span>
            </div>
            <div class="pt-2 border-t border-kalisi-border flex justify-end">
              <button onclick="handleDeleteVideo('${v.id}')" class="text-xs text-red-400 hover:text-red-300">
                <i class="fas fa-trash mr-1"></i>Delete Video
              </button>
            </div>
          </div>
        </div>
      `).join('');

      // 6. Venues Grid
      const venuesGrid = document.getElementById('venues-grid');
      venuesGrid.innerHTML = (data.restaurants || []).map(r => `
        <div class="glass-card p-6 rounded-2xl border border-kalisi-border space-y-4">
          <div class="flex items-start justify-between">
            <div>
              <h3 class="text-lg font-black text-white">${r.name}</h3>
              <p class="text-xs text-gray-400">${r.neighborhood}, ${r.city}</p>
            </div>
            <span class="px-2.5 py-1 rounded-full text-xs font-bold bg-kalisi-gold/20 text-kalisi-gold border border-kalisi-gold/30 uppercase">${r.price_tier}</span>
          </div>
          <div class="space-y-2 text-xs">
            <div class="p-2.5 rounded-xl bg-kalisi-surfaceLight/80">
              <span class="text-gray-400 block font-semibold mb-0.5">Activities:</span>
              <span class="text-white">${r.activities}</span>
            </div>
            <div class="p-2.5 rounded-xl bg-kalisi-surfaceLight/80">
              <span class="text-gray-400 block font-semibold mb-0.5">Special Features:</span>
              <span class="text-kalisi-gold font-medium">${r.special_features}</span>
            </div>
          </div>
          <div class="flex items-center justify-between pt-3 border-t border-kalisi-border text-xs text-gray-400">
            <span><i class="fas fa-clock mr-1"></i>${r.duration_hours}</span>
            <span><i class="fas fa-phone mr-1"></i>${r.contact_phone}</span>
          </div>
        </div>
      `).join('');

      // Populate Event Dropdown
      const dropdown = document.getElementById('event-select-dropdown');
      if (dropdown && data.events && data.events.length > 0) {
        dropdown.innerHTML = data.events.map(e => `
          <option value="${e.id}" ${selectedEventId === e.id ? 'selected' : ''}>
            ${e.title || 'Dinner Event'} • ${e.city} (${e.date_str}) [${e.bookings_count}/${e.max_capacity} booked]
          </option>
        `).join('');
        if (!selectedEventId) {
          selectedEventId = data.events[0].id;
        }
      }

      // Populate Push Notification User Dropdown
      const pushUserSelect = document.getElementById('push-user-select');
      if (pushUserSelect && data.users) {
        pushUserSelect.innerHTML = '<option value="">-- Choose User to Notify --</option>' + data.users.map(u => {
          const fcmBadge = u.fcm_token ? '🟢 [FCM Token Active]' : '⚪ [No Token Yet]';
          return `<option value="${u.id}">${u.name} (${u.phone || 'No phone'}) — ${u.city || ''} ${fcmBadge}</option>`;
        }).join('');
      }

      // Populate Push Notification Event Dropdown
      const pushEventSelect = document.getElementById('push-event-select');
      if (pushEventSelect && data.events) {
        pushEventSelect.innerHTML = '<option value="">-- Choose Event to Notify Booked Members --</option>' + data.events.map(e => `
          <option value="${e.id}">${e.title || 'Dinner Meetup'} • ${e.city} (${e.date_str}) — [${e.bookings_count} Booked]</option>
        `).join('');
      }
    }

    // =========================================================================
    // PARTICULAR EVENT BOOKINGS PAGE LOGIC
    // =========================================================================
    function viewParticularEventBookings(eventId) {
      selectedEventId = eventId;
      navigateTab('event-bookings', '/admin/event-bookings');
    }

    function onSelectEventFromDropdown() {
      const dropdown = document.getElementById('event-select-dropdown');
      selectedEventId = dropdown.value;
      renderEventBookingsPage();
    }

    function renderEventBookingsPage() {
      if (!globalData || !selectedEventId) return;
      const event = (globalData.events || []).find(e => e.id === selectedEventId) || (globalData.events || [])[0];
      if (!event) return;

      selectedEventId = event.id;
      const dropdown = document.getElementById('event-select-dropdown');
      if (dropdown) dropdown.value = event.id;

      // Event Banner
      const banner = document.getElementById('event-detail-banner');
      banner.innerHTML = `
        <div class="flex flex-wrap items-center justify-between gap-4">
          <div>
            <div class="flex items-center space-x-3 mb-1">
              <h3 class="text-xl font-black text-white">${event.title || 'Dinner Meetup'}</h3>
              <span class="px-2.5 py-0.5 rounded-full text-xs font-bold uppercase ${event.status === 'completed' ? 'bg-blue-500/20 text-blue-400' : event.status === 'open' ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'}">${event.status}</span>
              <button onclick="openEditEventModal('${event.id}')" class="px-2.5 py-1 rounded-lg bg-blue-500/20 text-blue-400 border border-blue-500/40 text-xs font-bold hover:bg-blue-500 hover:text-white transition">
                <i class="fas fa-pen-to-square mr-1"></i>Edit Event
              </button>
            </div>
            <p class="text-xs text-gray-300">
              <span class="text-kalisi-gold font-bold"><i class="fas fa-calendar mr-1"></i>${event.date_str} (${event.time_window})</span> • 
              <span><i class="fas fa-location-dot mr-1"></i>${event.city}</span> • 
              <span>Price: <b class="text-kalisi-gold">₹${event.price_inr}</b></span>
            </p>
            <p class="text-xs text-gray-400 mt-1">
              <i class="fas fa-utensils mr-1 text-gray-500"></i><b>Venue:</b> ${event.venue_name || 'Curated Partner Restaurant'} — <span class="text-gray-400">${event.venue_address || 'Central City Location'}</span>
            </p>
          </div>
          <div class="flex items-center space-x-6">
            <div class="text-center">
              <span class="text-2xl font-black text-white">${event.bookings_count}</span>
              <span class="text-xs text-gray-400 block">Members Booked</span>
            </div>
            <div class="text-center">
              <span class="text-2xl font-black text-green-400">${event.seats_left}</span>
              <span class="text-xs text-gray-400 block">Seats Remaining</span>
            </div>
            <div class="text-center">
              <span class="text-2xl font-black text-kalisi-purple">₹${event.bookings_count * event.price_inr}</span>
              <span class="text-xs text-gray-400 block">Event Total</span>
            </div>
          </div>
        </div>
      `;

      // Filter attendees for this particular event
      const eventAttendees = (globalData.bookings || []).filter(b => b.slot_id === event.id);
      const tbody = document.getElementById('event-attendees-tbody');

      if (eventAttendees.length === 0) {
        tbody.innerHTML = `
          <tr>
            <td colspan="8" class="text-center py-10 text-gray-500 text-sm">
              <i class="fas fa-ticket text-3xl mb-2 block"></i>
              No members have booked for this event yet.
            </td>
          </tr>
        `;
      } else {
        tbody.innerHTML = eventAttendees.map((b, idx) => `
          <tr class="hover:bg-kalisi-surfaceLight/50 transition">
            <td class="px-6 py-4">
              <div class="flex items-center space-x-3">
                <span class="w-6 h-6 rounded-full bg-kalisi-gold/20 text-kalisi-gold font-black text-xs flex items-center justify-center">${idx + 1}</span>
                <div>
                  <span class="font-bold text-white block">${b.user_name}</span>
                  <span class="text-xs text-gray-400">${b.user_email}</span>
                </div>
              </div>
            </td>
            <td class="px-6 py-4 font-mono text-xs text-gray-300">${b.user_phone}</td>
            <td class="px-6 py-4 text-xs text-gray-300">${b.user_age} y/o • ${b.user_gender}</td>
            <td class="px-6 py-4">
              <span class="px-2 py-0.5 rounded-full text-xs font-bold bg-kalisi-purple/20 text-kalisi-purple border border-kalisi-purple/30">${b.user_archetype}</span>
            </td>
            <td class="px-6 py-4 text-xs text-gray-300">${b.user_dietary}</td>
            <td class="px-6 py-4">
              <span class="font-bold text-kalisi-gold">₹${b.amount_paid}</span>
              <span class="text-[11px] text-gray-400 block">${b.payment_method}</span>
            </td>
            <td class="px-6 py-4">
              <span class="px-2.5 py-1 rounded-full text-xs font-bold ${b.attendance_confirmed ? 'bg-green-500/20 text-green-400 border border-green-500/40' : 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/40'}">
                ${b.attendance_confirmed ? '✓ Attended' : 'Confirmed (Booked)'}
              </span>
            </td>
            <td class="px-6 py-4 text-right">
              <button onclick="toggleAttendance('${b.id}')" class="px-3 py-1.5 rounded-lg text-xs font-bold ${b.attendance_confirmed ? 'bg-gray-700 text-gray-300 hover:text-white' : 'bg-green-600 text-white hover:bg-green-500'} transition">
                ${b.attendance_confirmed ? 'Mark Absent' : 'Mark Attended'}
              </button>
            </td>
          </tr>
        `).join('');
      }
    }

    async function toggleAttendance(bookingId) {
      await fetch(`/admin/api/bookings/${bookingId}/toggle-attendance`, { method: 'POST' });
      await loadData();
      renderEventBookingsPage();
    }

    async function toggleEventEnable(eventId) {
      await fetch(`/admin/api/events/${eventId}/toggle-enable`, { method: 'POST' });
      loadData();
    }

    async function toggleEventStatus(eventId, newStatus) {
      const formData = new FormData();
      formData.append('status', newStatus);
      await fetch(`/admin/api/events/${eventId}/status`, { method: 'POST', body: formData });
      loadData();
    }

    async function handleDeleteVideo(videoId) {
      if (!confirm('Are you sure you want to remove this video?')) return;
      await fetch(`/admin/api/videos/${videoId}`, { method: 'DELETE' });
      loadData();
    }

    function openEditEventModal(eventId) {
      if (!globalData || !globalData.events) return;
      const event = globalData.events.find(e => e.id === eventId);
      if (!event) return;

      document.getElementById('edit-event-id').value = event.id;
      document.getElementById('edit-title').value = event.title || '';
      document.getElementById('edit-city').value = event.city || '';
      document.getElementById('edit-date-str').value = event.date_str || '';
      document.getElementById('edit-time-window').value = event.time_window || '';
      document.getElementById('edit-price-inr').value = event.price_inr || 599;
      document.getElementById('edit-max-capacity').value = event.max_capacity || 10;
      document.getElementById('edit-status').value = event.status || 'open';
      document.getElementById('edit-venue-name').value = event.venue_name || '';
      document.getElementById('edit-venue-address').value = event.venue_address || '';
      document.getElementById('edit-about-event').value = event.about_event || '';
      document.getElementById('edit-rules').value = event.rules_and_regulations || '';

      document.getElementById('modal-edit-event').classList.remove('hidden');
    }

    async function handleUpdateEvent(e) {
      e.preventDefault();
      const form = e.target;
      const eventId = document.getElementById('edit-event-id').value;
      const data = new FormData(form);
      const res = await fetch(`/admin/api/events/${eventId}/update`, { method: 'POST', body: data });
      if (res.ok) {
        document.getElementById('modal-edit-event').classList.add('hidden');
        await loadData();
      } else {
        alert('Failed to update event. Please check inputs and try again.');
      }
    }

    async function handleCreateSlot(e) {
      e.preventDefault();
      const form = e.target;
      const data = new FormData(form);
      await fetch('/admin/api/slots/create', { method: 'POST', body: data });
      document.getElementById('modal-new-slot').classList.add('hidden');
      form.reset();
      loadData();
    }

    async function handleCreateVideo(e) {
      e.preventDefault();
      const form = e.target;
      const btn = document.getElementById('btn-submit-video');
      const oldHtml = btn ? btn.innerHTML : '';
      if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i> Uploading & Publishing Video Reel...';
      }

      try {
        const data = new FormData(form);
        const res = await fetch('/admin/api/videos/create', { method: 'POST', body: data });
        if (res.ok) {
          document.getElementById('modal-new-video').classList.add('hidden');
          form.reset();
          await loadData();
        } else {
          alert('Failed to upload video. Please ensure the file is a valid video format.');
        }
      } catch (err) {
        alert('Upload error: ' + err);
      } finally {
        if (btn) {
          btn.disabled = false;
          btn.innerHTML = oldHtml;
        }
      }
    }

    async function handleCreateVenue(e) {
      e.preventDefault();
      const form = e.target;
      const data = new FormData(form);
      await fetch('/admin/api/restaurants/create', { method: 'POST', body: data });
      document.getElementById('modal-new-venue').classList.add('hidden');
      form.reset();
      loadData();
    }

    function togglePushTarget(val) {
      document.getElementById('push-city-select-wrapper').classList.add('hidden');
      document.getElementById('push-user-select-wrapper').classList.add('hidden');
      document.getElementById('push-event-select-wrapper').classList.add('hidden');

      if (val === 'city') {
        document.getElementById('push-city-select-wrapper').classList.remove('hidden');
      } else if (val === 'user') {
        document.getElementById('push-user-select-wrapper').classList.remove('hidden');
      } else if (val === 'event_booked') {
        document.getElementById('push-event-select-wrapper').classList.remove('hidden');
      }
    }

    function onSelectPushUser(userId) {
      const tokenInput = document.getElementById('push-test-token');
      const tokenStatus = document.getElementById('push-token-status');
      if (!userId || !globalData || !globalData.users) {
        if (tokenInput) tokenInput.value = '';
        if (tokenStatus) tokenStatus.innerHTML = '';
        return;
      }
      const u = globalData.users.find(x => x.id === userId);
      if (u && u.fcm_token) {
        if (tokenInput) tokenInput.value = u.fcm_token;
        if (tokenStatus) tokenStatus.innerHTML = '<span class="text-emerald-400 font-bold">✓ Active Device FCM Token</span>';
      } else {
        if (tokenInput) tokenInput.value = '';
        if (tokenStatus) tokenStatus.innerHTML = '<span class="text-amber-400 font-bold">⚠️ No Token (Open app or supply test token)</span>';
      }
    }

    function quickPushToUser(userId, userName) {
      navigateTab('notifications', '/admin/notifications');
      const targetSelect = document.getElementById('push-target-type');
      if (targetSelect) {
        targetSelect.value = 'user';
        togglePushTarget('user');
      }
      const userSelect = document.getElementById('push-user-select');
      if (userSelect) {
        userSelect.value = userId;
        onSelectPushUser(userId);
      }
      const titleInput = document.getElementById('push-title');
      if (titleInput) {
        titleInput.value = `Hey ${userName}! 👋`;
        document.getElementById('push-body').focus();
      }
    }

    function applyPushPreset(preset) {
      const titleInput = document.getElementById('push-title');
      const bodyInput = document.getElementById('push-body');
      if (preset === 'venue_reveal') {
        titleInput.value = '🎉 Table & Venue Revealed!';
        bodyInput.value = 'Good morning! Your mystery dinner table and partner restaurant address are now unlocked. Open Kalisi to view your matched group!';
      } else if (preset === 'anti_ghosting') {
        titleInput.value = '⏰ 2 Hours Until Dinner! Please Confirm';
        bodyInput.value = 'Your dinner meetup begins in 2 hours! Open your ticket to confirm your arrival with your 5 tablemates.';
      } else if (preset === 'weekend_open') {
        titleInput.value = '✨ New Weekend Stranger Dinners Open!';
        bodyInput.value = 'Curated stranger dinner slots for this weekend are live in your neighborhood. Book your seat before slots fill up!';
      }
    }

    async function handleSendPushNotification(e) {
      e.preventDefault();
      const form = e.target;
      const btn = document.getElementById('btn-send-push');
      const feedback = document.getElementById('push-feedback');
      const oldBtnHtml = btn.innerHTML;

      btn.disabled = true;
      btn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i> Dispatching via Firebase FCM...';
      feedback.classList.add('hidden');

      const data = new FormData(form);
      const title = data.get('title');
      const body = data.get('body');
      const targetType = data.get('target_type');
      const city = data.get('city');
      const userId = data.get('user_id');
      const eventId = data.get('event_id');

      let targetLabel = 'Broadcast (All)';
      if (targetType === 'user') {
        const u = (globalData?.users || []).find(x => x.id === userId);
        targetLabel = u ? `User: ${u.name}` : 'Selected User';
      } else if (targetType === 'event_booked') {
        const ev = (globalData?.events || []).find(x => x.id === eventId);
        targetLabel = ev ? `Event: ${ev.title || 'Meetup'}` : 'Event Attendees';
      } else if (targetType === 'city') {
        targetLabel = `City: ${city}`;
      }

      try {
        const res = await fetch('/admin/api/notifications/send', {
          method: 'POST',
          body: data
        });
        const resJson = await res.json();
        
        if (resJson.status === 'success') {
          feedback.className = 'mt-4 p-3 rounded-xl text-xs font-semibold bg-emerald-900/40 border border-emerald-500/50 text-emerald-300';
          feedback.innerHTML = `✅ <b>Success:</b> ${resJson.message || 'Notification dispatched!'}`;
        } else if (resJson.status === 'warning') {
          feedback.className = 'mt-4 p-3 rounded-xl text-xs font-semibold bg-amber-900/40 border border-amber-500/50 text-amber-300';
          feedback.innerHTML = `⚠️ <b>Notice:</b> ${resJson.message || 'Notice occurred during delivery.'}`;
        } else {
          feedback.className = 'mt-4 p-3 rounded-xl text-xs font-semibold bg-red-900/40 border border-red-500/50 text-red-300';
          feedback.innerHTML = `❌ <b>Error:</b> ${resJson.message || 'Failed to dispatch notification.'}`;
        }
        feedback.classList.remove('hidden');

        // Add to history table
        const tbody = document.getElementById('notifications-table-body');
        const isSuccess = resJson.status === 'success';
        const isWarning = resJson.status === 'warning';
        const statusBadge = isSuccess 
          ? '<span class="px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400 font-bold text-[10px]">Delivered</span>'
          : isWarning
            ? '<span class="px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-400 font-bold text-[10px]">Pending Token</span>'
            : '<span class="px-2 py-0.5 rounded-full bg-red-500/20 text-red-400 font-bold text-[10px]">Failed</span>';

        const newRow = document.createElement('tr');
        newRow.className = isSuccess ? 'bg-emerald-950/20' : (isWarning ? 'bg-amber-950/20' : 'bg-red-950/20');
        newRow.innerHTML = `
          <td class="p-3.5 font-bold text-white">${title}</td>
          <td class="p-3.5 text-gray-300">${body}</td>
          <td class="p-3.5"><span class="px-2 py-0.5 rounded bg-amber-900/30 text-amber-400 border border-amber-800/40 text-[10px] font-bold">${targetLabel}</span></td>
          <td class="p-3.5 font-bold ${isSuccess ? 'text-emerald-400' : 'text-amber-400'}">Firebase FCM</td>
          <td class="p-3.5 text-gray-400">Just now</td>
          <td class="p-3.5 text-right">${statusBadge}</td>
        `;
        if (tbody) tbody.insertBefore(newRow, tbody.firstChild);

      } catch (err) {
        feedback.className = 'mt-4 p-3 rounded-xl text-xs font-semibold bg-red-900/40 border border-red-500/50 text-red-300';
        feedback.innerHTML = `❌ <b>Error:</b> Failed to reach server. Please check server logs.`;
        feedback.classList.remove('hidden');
      } finally {
        btn.disabled = false;
        btn.innerHTML = oldBtnHtml;
      }
    }

    // Initialize Auth & Data on Load
    checkAuth();
  </script>
</body>
</html>
"""

ADMIN_LOGIN_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Kalisi — Admin Mission Control Login</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
</head>
<body class="min-h-screen bg-[#121212] flex items-center justify-center p-4">
  <div class="bg-[#1E1E1E] max-w-md w-full p-8 rounded-3xl border border-[#2E2E2E] shadow-2xl space-y-6">
    <div class="text-center space-y-2">
      <div class="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-amber-500/20 border border-amber-500/40 text-amber-400 text-2xl font-black mb-1">
        K
      </div>
      <h2 class="text-2xl font-black text-white tracking-tight">Kalisi Admin Portal</h2>
      <p class="text-xs text-gray-400">Restricted access for platform organizers & operations.</p>
    </div>

    <div id="login-error" class="hidden p-3 rounded-xl bg-red-900/30 border border-red-500/50 text-xs font-bold text-red-300"></div>

    <form onsubmit="handleLogin(event)" class="space-y-4">
      <div>
        <label class="block text-xs font-bold text-gray-400 uppercase tracking-wider mb-1.5">Admin Username</label>
        <div class="relative">
          <span class="absolute inset-y-0 left-0 pl-3.5 flex items-center text-gray-400"><i class="fas fa-user-shield text-sm"></i></span>
          <input type="text" id="login-username" value="admin" required class="w-full bg-[#282828] pl-10 pr-4 py-3 rounded-xl border border-[#2E2E2E] text-sm text-white focus:outline-none focus:border-amber-400 transition">
        </div>
      </div>
      <div>
        <label class="block text-xs font-bold text-gray-400 uppercase tracking-wider mb-1.5">Admin Password</label>
        <div class="relative">
          <span class="absolute inset-y-0 left-0 pl-3.5 flex items-center text-gray-400"><i class="fas fa-key text-sm"></i></span>
          <input type="password" id="login-password" value="kalisi_admin_2026" required class="w-full bg-[#282828] pl-10 pr-4 py-3 rounded-xl border border-[#2E2E2E] text-sm text-white focus:outline-none focus:border-amber-400 transition">
        </div>
      </div>
      <button type="submit" class="w-full py-3.5 rounded-xl bg-amber-500 text-black font-black text-sm hover:brightness-110 active:scale-[0.98] transition shadow-lg shadow-amber-500/20 mt-2">
        Unlock Mission Control
      </button>
    </form>
    <div class="text-center text-[11px] text-gray-400">
      Default credentials pre-filled for local operations (<code class="text-amber-400">admin</code> / <code class="text-amber-400">kalisi_admin_2026</code>)
    </div>
  </div>

  <script>
    if (localStorage.getItem('kalisi_admin_token')) {
      window.location.href = '/admin/overview';
    }
    async function handleLogin(e) {
      e.preventDefault();
      const u = document.getElementById('login-username').value;
      const p = document.getElementById('login-password').value;
      const err = document.getElementById('login-error');
      err.classList.add('hidden');
      const formData = new FormData();
      formData.append('username', u);
      formData.append('password', p);
      try {
        const res = await fetch('/admin/api/login', { method: 'POST', body: formData });
        const data = await res.json();
        if (res.ok && data.status === 'success') {
          localStorage.setItem('kalisi_admin_token', data.token);
          window.location.href = '/admin/overview';
        } else {
          err.innerText = data.detail || 'Invalid admin credentials';
          err.classList.remove('hidden');
        }
      } catch (ex) {
        err.innerText = 'Connection error reaching admin auth API';
        err.classList.remove('hidden');
      }
    }
  </script>
</body>
</html>
"""

def get_admin_page_html(initial_tab: str = "overview") -> str:
    return ADMIN_HTML.replace("checkAuth();", f"checkAuth(); switchTab('{initial_tab}');")

# Dedicated URLs for Admin Pages
@admin_router.get("/admin/login", response_class=HTMLResponse)
def admin_login_page():
    return HTMLResponse(content=ADMIN_LOGIN_HTML)

@admin_router.get("/admin", response_class=HTMLResponse)
def admin_root():
    return RedirectResponse(url="/admin/overview")

@admin_router.get("/admin/overview", response_class=HTMLResponse)
def admin_overview():
    return HTMLResponse(content=get_admin_page_html("overview"))

@admin_router.get("/admin/users", response_class=HTMLResponse)
@admin_router.get("/admin/vibe-dna", response_class=HTMLResponse)
def admin_users():
    return HTMLResponse(content=get_admin_page_html("users"))

@admin_router.get("/admin/events", response_class=HTMLResponse)
@admin_router.get("/admin/slots", response_class=HTMLResponse)
@admin_router.get("/admin/tables", response_class=HTMLResponse)
def admin_events():
    return HTMLResponse(content=get_admin_page_html("events"))

@admin_router.get("/admin/event-bookings", response_class=HTMLResponse)
@admin_router.get("/admin/bookings", response_class=HTMLResponse)
def admin_event_bookings():
    return HTMLResponse(content=get_admin_page_html("event-bookings"))

@admin_router.get("/admin/payments", response_class=HTMLResponse)
def admin_payments():
    return HTMLResponse(content=get_admin_page_html("payments"))

@admin_router.get("/admin/videos", response_class=HTMLResponse)
def admin_videos():
    return HTMLResponse(content=get_admin_page_html("videos"))

@admin_router.get("/admin/venues", response_class=HTMLResponse)
def admin_venues():
    return HTMLResponse(content=get_admin_page_html("venues"))

@admin_router.get("/admin/notifications", response_class=HTMLResponse)
def admin_notifications():
    return HTMLResponse(content=get_admin_page_html("notifications"))
