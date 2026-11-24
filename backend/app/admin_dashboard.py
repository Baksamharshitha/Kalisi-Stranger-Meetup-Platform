from datetime import datetime, timedelta
from fastapi import APIRouter, Form, HTTPException, Depends
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from app.core.config import settings
from app.db.database import SessionLocal
from app.db.models import User, CitySlot, TableGroup, Restaurant, Booking
from app.services.matchmaking import cluster_slot_into_tables

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
        slots = db.query(CitySlot).all()
        tables = db.query(TableGroup).all()
        restaurants = db.query(Restaurant).all()
        bookings = db.query(Booking).all()

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
                "city": u.city,
                "archetype": arch,
                "icebreaker_style": icebreaker,
                "budget_tier": tier,
                "dietary": diet,
                "is_verified": u.is_verified,
                "created_at": u.created_at.strftime("%Y-%m-%d %H:%M") if u.created_at else "Recent",
            })

        # Detailed Tables
        table_list = []
        for t in tables:
            attendees = []
            for b in t.bookings:
                if b.user:
                    u_arch = b.user.personality.archetype if b.user.personality else "Clark Kent"
                    u_tier = b.user.preferences.budget_tier if b.user.preferences else "mid_range"
                    attendees.append({
                        "name": b.user.full_name,
                        "email": b.user.email,
                        "archetype": u_arch,
                        "budget_tier": u_tier,
                        "payment_status": b.payment_status,
                        "attendance_confirmed": b.attendance_confirmed,
                    })

            table_list.append({
                "id": t.id,
                "table_number": t.table_number,
                "slot_id": t.slot_id,
                "date_str": t.slot.date_str if t.slot else "",
                "city": t.slot.city if t.slot else "",
                "time_window": t.slot.time_window if t.slot else "",
                "restaurant_name": t.restaurant.name if t.restaurant else "Unassigned",
                "neighborhood": t.restaurant.neighborhood if t.restaurant else "",
                "reveal_stage": t.reveal_stage,
                "archetype_summary": t.archetype_summary or "Clustering in progress",
                "attendees": attendees,
                "attendee_count": len(attendees),
                "target_size": t.target_size,
                "seats_available": max(0, t.target_size - len(attendees)),
            })

        # Detailed City Slots with Capacity
        slot_list = []
        for s in slots:
            booked_count = len(s.bookings)
            capacity = s.max_capacity or 10
            slot_list.append({
                "id": s.id,
                "city": s.city,
                "date_str": s.date_str,
                "time_window": s.time_window,
                "price_inr": s.price_inr or 499,
                "max_capacity": capacity,
                "bookings_count": booked_count,
                "seats_left": max(0, capacity - booked_count),
                "status": s.status,
                "tables_count": len(s.tables),
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

        # Detailed Bookings & Financial Ledger
        booking_list = []
        total_revenue = 0
        paid_count = 0
        free_trial_count = 0

        for b in bookings:
            amt = b.amount_paid or 0
            total_revenue += amt
            if b.payment_status == "paid":
                paid_count += 1
            else:
                free_trial_count += 1

            booking_list.append({
                "id": b.id,
                "user_name": b.user.full_name if b.user else "Unknown",
                "user_email": b.user.email if b.user else "N/A",
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

        return {
            "metrics": {
                "total_users": len(users),
                "active_slots": len(slots),
                "total_tables": len(tables),
                "total_bookings": len(bookings),
                "total_restaurants": len(restaurants),
                "total_revenue_inr": total_revenue,
                "paid_bookings": paid_count,
                "free_trials": free_trial_count,
            },
            "tables": table_list,
            "slots": slot_list,
            "restaurants": restaurant_list,
            "bookings": booking_list,
            "users": user_list,
        }

@admin_router.post("/admin/api/matchmake")
def admin_trigger_matchmaking():
    with SessionLocal() as db:
        slots = db.query(CitySlot).filter(CitySlot.status == "open").all()
        clustered = 0
        for s in slots:
            cluster_slot_into_tables(db, s.id)
            clustered += 1
        return {"status": "success", "message": f"Matchmaking worker clustered available bookings for {clustered} city slots."}

@admin_router.post("/admin/api/slots/create")
def admin_create_slot(
    city: str = Form(...),
    date_str: str = Form(...),
    time_window: str = Form(...),
    price_inr: int = Form(499),
    max_capacity: int = Form(10)
):
    with SessionLocal() as db:
        new_slot = CitySlot(
            city=city,
            date_str=date_str,
            time_window=time_window,
            price_inr=price_inr,
            max_capacity=max_capacity,
            event_timestamp=datetime.utcnow() + timedelta(days=7),
            status="open",
        )
        db.add(new_slot)
        db.commit()
        return {"status": "success", "slot_id": new_slot.id}

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

@admin_router.post("/admin/api/tables/{table_id}/set-stage")
def admin_set_reveal_stage(table_id: str, stage: str = Form(...)):
    if stage not in ["locked", "area_revealed", "fully_revealed"]:
        raise HTTPException(status_code=400, detail="Invalid reveal stage")
    with SessionLocal() as db:
        table = db.query(TableGroup).filter(TableGroup.id == table_id).first()
        if not table:
            raise HTTPException(status_code=404, detail="Table not found")
        table.reveal_stage = stage
        db.commit()
        return {"status": "success", "table_id": table.id, "new_stage": table.reveal_stage}

# ==============================================================================
# Complete Admin Web UI (HTML + Tailwind + Sidebar + Auth Modal)
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
  <!-- 1. AUTH LOGIN OVERLAY (Shows when not authenticated)                    -->
  <!-- ======================================================================= -->
  <div id="auth-overlay" class="fixed inset-0 bg-black/90 backdrop-blur-md z-[100] flex items-center justify-center p-4">
    <div class="glass-card bg-kalisi-surface max-w-md w-full p-8 rounded-3xl border border-kalisi-border shadow-2xl space-y-6">
      <div class="text-center space-y-2">
        <div class="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-kalisi-gold/20 border border-kalisi-gold/40 text-kalisi-gold text-2xl font-black mb-1">
          K
        </div>
        <h2 class="text-2xl font-black text-white tracking-tight">Kalisi Admin Portal</h2>
        <p class="text-xs text-gray-400">Restricted access for platform organizers & operations.</p>
      </div>

      <div id="login-error" class="hidden p-3 rounded-xl bg-kalisi-crimson/20 border border-kalisi-crimson/50 text-xs font-bold text-red-300"></div>

      <form onsubmit="handleLogin(event)" class="space-y-4">
        <div>
          <label class="block text-xs font-bold text-gray-400 uppercase tracking-wider mb-1.5">Admin Username</label>
          <div class="relative">
            <span class="absolute inset-y-0 left-0 pl-3.5 flex items-center text-gray-400"><i class="fas fa-user-shield text-sm"></i></span>
            <input type="text" id="login-username" value="admin" required class="w-full bg-kalisi-surfaceLight pl-10 pr-4 py-3 rounded-xl border border-kalisi-border text-sm text-white focus:outline-none focus:border-kalisi-gold transition">
          </div>
        </div>
        <div>
          <label class="block text-xs font-bold text-gray-400 uppercase tracking-wider mb-1.5">Password</label>
          <div class="relative">
            <span class="absolute inset-y-0 left-0 pl-3.5 flex items-center text-gray-400"><i class="fas fa-key text-sm"></i></span>
            <input type="password" id="login-password" value="kalisi_admin_2026" required class="w-full bg-kalisi-surfaceLight pl-10 pr-4 py-3 rounded-xl border border-kalisi-border text-sm text-white focus:outline-none focus:border-kalisi-gold transition">
          </div>
          <span class="text-[11px] text-gray-500 mt-1 block">Default: admin / kalisi_admin_2026</span>
        </div>
        <button type="submit" class="w-full py-3.5 rounded-xl bg-kalisi-gold text-black font-extrabold text-sm hover:brightness-110 active:scale-95 transition flex items-center justify-center space-x-2">
          <span>Sign In to Control Center</span>
          <i class="fas fa-arrow-right text-xs"></i>
        </button>
      </form>
    </div>
  </div>

  <!-- ======================================================================= -->
  <!-- 2. SIDEBAR NAVIGATION                                                   -->
  <!-- ======================================================================= -->
  <aside class="w-64 bg-kalisi-sidebar border-r border-kalisi-border flex flex-col justify-between shrink-0 min-h-screen sticky top-0">
    <div class="p-6 space-y-8">
      
      <!-- Brand & Status -->
      <div class="flex items-center justify-between">
        <div class="flex items-center space-x-3">
          <div class="w-9 h-9 rounded-xl bg-kalisi-gold text-black font-black flex items-center justify-center text-lg shadow-md">
            K
          </div>
          <div>
            <h1 class="text-lg font-black tracking-tight text-white leading-none">Kalisi</h1>
            <span class="text-[10px] text-gray-400 font-bold uppercase tracking-wider">Stranger Meetups</span>
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
          <span>Overview & KPIs</span>
        </a>

        <a href="/admin/tables" onclick="return navigateTab('tables', '/admin/tables')" id="nav-btn-tables" class="w-full flex items-center space-x-3 px-3.5 py-2.5 rounded-xl text-sm font-semibold text-gray-400 hover:text-white hover:bg-kalisi-surfaceLight transition">
          <i class="fas fa-users-viewfinder w-5 text-center"></i>
          <span>5-Stranger Tables</span>
        </a>

        <a href="/admin/slots" onclick="return navigateTab('slots', '/admin/slots')" id="nav-btn-slots" class="w-full flex items-center space-x-3 px-3.5 py-2.5 rounded-xl text-sm font-semibold text-gray-400 hover:text-white hover:bg-kalisi-surfaceLight transition">
          <i class="fas fa-calendar-check w-5 text-center"></i>
          <span>Weekend Slots</span>
        </a>

        <a href="/admin/bookings" onclick="return navigateTab('bookings', '/admin/bookings')" id="nav-btn-bookings" class="w-full flex items-center space-x-3 px-3.5 py-2.5 rounded-xl text-sm font-semibold text-gray-400 hover:text-white hover:bg-kalisi-surfaceLight transition">
          <i class="fas fa-ticket w-5 text-center"></i>
          <span>Bookings & Members</span>
        </a>

        <a href="/admin/venues" onclick="return navigateTab('venues', '/admin/venues')" id="nav-btn-venues" class="w-full flex items-center space-x-3 px-3.5 py-2.5 rounded-xl text-sm font-semibold text-gray-400 hover:text-white hover:bg-kalisi-surfaceLight transition">
          <i class="fas fa-utensils w-5 text-center"></i>
          <span>Verified Venues</span>
        </a>

        <a href="/admin/payments" onclick="return navigateTab('payments', '/admin/payments')" id="nav-btn-payments" class="w-full flex items-center space-x-3 px-3.5 py-2.5 rounded-xl text-sm font-semibold text-gray-400 hover:text-white hover:bg-kalisi-surfaceLight transition">
          <i class="fas fa-indian-rupee-sign w-5 text-center"></i>
          <span>Payments & Revenue</span>
        </a>

        <a href="/admin/vibe-dna" onclick="return navigateTab('users', '/admin/vibe-dna')" id="nav-btn-users" class="w-full flex items-center space-x-3 px-3.5 py-2.5 rounded-xl text-sm font-semibold text-gray-400 hover:text-white hover:bg-kalisi-surfaceLight transition">
          <i class="fas fa-fingerprint w-5 text-center"></i>
          <span>User Vibe DNA</span>
        </a>
      </nav>

      <!-- Quick Actions -->
      <div class="pt-4 border-t border-kalisi-border space-y-2">
        <button onclick="triggerMatchmaking()" class="w-full py-2.5 rounded-xl bg-kalisi-gold text-black text-xs font-black hover:brightness-110 active:scale-95 transition flex items-center justify-center space-x-2">
          <i class="fas fa-bolt"></i>
          <span>Run Matchmaker</span>
        </button>
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
  <!-- 3. MAIN DASHBOARD CONTENT AREA                                         -->
  <!-- ======================================================================= -->
  <main class="flex-1 min-w-0 p-8 space-y-8 overflow-y-auto max-h-screen">

    <!-- TAB 1: OVERVIEW & KPIS -->
    <div id="tab-overview" class="space-y-8">
      <div class="flex justify-between items-center">
        <div>
          <h2 class="text-2xl font-black tracking-tight text-white">Mission Control Overview</h2>
          <p class="text-xs text-gray-400 mt-1">Real-time status of strangers, weekend gatherings, and revenue.</p>
        </div>
        <button onclick="loadData()" class="px-3.5 py-1.5 rounded-xl bg-kalisi-surface border border-kalisi-border hover:border-kalisi-gold text-xs font-bold text-gray-300 hover:text-white transition flex items-center space-x-1.5">
          <i class="fas fa-rotate"></i>
          <span>Refresh Data</span>
        </button>
      </div>

      <!-- KPI Bar -->
      <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
        <div class="glass-card p-5 rounded-2xl flex flex-col justify-between">
          <span class="text-[11px] text-gray-400 uppercase font-bold tracking-wider">Total Members</span>
          <span class="text-3xl font-black text-white mt-2" id="kpi-users">-</span>
        </div>
        <div class="glass-card p-5 rounded-2xl flex flex-col justify-between">
          <span class="text-[11px] text-gray-400 uppercase font-bold tracking-wider">Active Slots</span>
          <span class="text-3xl font-black text-kalisi-gold mt-2" id="kpi-slots">-</span>
        </div>
        <div class="glass-card p-5 rounded-2xl flex flex-col justify-between">
          <span class="text-[11px] text-gray-400 uppercase font-bold tracking-wider">5-Stranger Tables</span>
          <span class="text-3xl font-black text-kalisi-purple mt-2" id="kpi-tables">-</span>
        </div>
        <div class="glass-card p-5 rounded-2xl flex flex-col justify-between">
          <span class="text-[11px] text-gray-400 uppercase font-bold tracking-wider">Seat Bookings</span>
          <span class="text-3xl font-black text-kalisi-blue mt-2" id="kpi-bookings">-</span>
        </div>
        <div class="glass-card p-5 rounded-2xl flex flex-col justify-between">
          <span class="text-[11px] text-gray-400 uppercase font-bold tracking-wider">Partner Venues</span>
          <span class="text-3xl font-black text-green-400 mt-2" id="kpi-venues">-</span>
        </div>
        <div class="glass-card p-5 rounded-2xl flex flex-col justify-between">
          <span class="text-[11px] text-gray-400 uppercase font-bold tracking-wider">Total Revenue</span>
          <span class="text-3xl font-black text-kalisi-gold mt-2" id="kpi-revenue">₹0</span>
        </div>
      </div>

      <!-- Quick Glance Grid -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <!-- Recent Tables -->
        <div class="glass-card rounded-2xl p-6 space-y-4">
          <div class="flex justify-between items-center">
            <h3 class="text-base font-black text-white">Active 5-Stranger Tables</h3>
            <button onclick="switchTab('tables')" class="text-xs text-kalisi-gold font-bold hover:underline">View All &rarr;</button>
          </div>
          <div id="overview-tables-summary" class="space-y-3">
            <!-- Rendered by JS -->
          </div>
        </div>

        <!-- Recent Bookings -->
        <div class="glass-card rounded-2xl p-6 space-y-4">
          <div class="flex justify-between items-center">
            <h3 class="text-base font-black text-white">Latest Seat Bookings</h3>
            <button onclick="switchTab('bookings')" class="text-xs text-kalisi-gold font-bold hover:underline">View All &rarr;</button>
          </div>
          <div id="overview-bookings-summary" class="space-y-3">
            <!-- Rendered by JS -->
          </div>
        </div>
      </div>
    </div>

    <!-- TAB 2: 5-STRANGER TABLES & PROGRESSIVE REVEAL -->
    <div id="tab-tables" class="hidden space-y-6">
      <div class="flex justify-between items-center">
        <div>
          <h2 class="text-2xl font-black text-white">5-Stranger Tables & Progressive Reveal</h2>
          <p class="text-xs text-gray-400 mt-1">Control the reveal state: <b>Locked (T > 24h)</b> &rarr; <b>Neighborhood Area (T - 24h)</b> &rarr; <b>Full Reveal (Day-Of)</b></p>
        </div>
        <button onclick="triggerMatchmaking()" class="px-4 py-2 rounded-xl bg-kalisi-gold text-black text-xs font-black hover:brightness-110 transition flex items-center space-x-1.5">
          <i class="fas fa-bolt"></i>
          <span>Re-cluster Tables</span>
        </button>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6" id="tables-full-container">
        <!-- Rendered by JS -->
      </div>
    </div>

    <!-- TAB 3: WEEKEND SLOTS & CAPACITY -->
    <div id="tab-slots" class="hidden space-y-6">
      <div class="flex justify-between items-center">
        <div>
          <h2 class="text-2xl font-black text-white">City Weekend Dinner Slots</h2>
          <p class="text-xs text-gray-400 mt-1">Monitor capacity limits, ticket pricing, and open seat inventories.</p>
        </div>
        <button onclick="document.getElementById('modal-new-slot').classList.remove('hidden')" class="px-4 py-2 rounded-xl bg-kalisi-gold text-black text-xs font-black hover:brightness-110 transition">
          + Schedule Weekend Slot
        </button>
      </div>

      <div class="glass-card rounded-2xl overflow-hidden">
        <table class="min-w-full divide-y divide-kalisi-border text-left text-sm">
          <thead class="bg-kalisi-surfaceLight/60 text-gray-400 text-xs uppercase font-bold">
            <tr>
              <th class="px-6 py-4">City</th>
              <th class="px-6 py-4">Date String</th>
              <th class="px-6 py-4">Time Window</th>
              <th class="px-6 py-4">Slot Price</th>
              <th class="px-6 py-4">Capacity & Filled</th>
              <th class="px-6 py-4">Seats Left</th>
              <th class="px-6 py-4">Status</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-kalisi-border" id="slots-tbody">
            <!-- Rendered by JS -->
          </tbody>
        </table>
      </div>
    </div>

    <!-- TAB 4: BOOKINGS & MEMBER DIRECTORY -->
    <div id="tab-bookings" class="hidden space-y-6">
      <div class="flex justify-between items-center">
        <div>
          <h2 class="text-2xl font-black text-white">Bookings & Member Directory</h2>
          <p class="text-xs text-gray-400 mt-1">Detailed audit of all reserved seats, member contacts, payment methods, and table assignments.</p>
        </div>
      </div>

      <div class="glass-card rounded-2xl overflow-hidden">
        <table class="min-w-full divide-y divide-kalisi-border text-left text-sm">
          <thead class="bg-kalisi-surfaceLight/60 text-gray-400 text-xs uppercase font-bold">
            <tr>
              <th class="px-6 py-4">Member Name</th>
              <th class="px-6 py-4">City & Slot</th>
              <th class="px-6 py-4">Table Assigned</th>
              <th class="px-6 py-4">Price Paid</th>
              <th class="px-6 py-4">Payment Method</th>
              <th class="px-6 py-4">Attendance</th>
              <th class="px-6 py-4">Booking ID</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-kalisi-border" id="bookings-tbody">
            <!-- Rendered by JS -->
          </tbody>
        </table>
      </div>
    </div>

    <!-- TAB 5: VERIFIED VENUES (DEEP DETAILS) -->
    <div id="tab-venues" class="hidden space-y-6">
      <div class="flex justify-between items-center">
        <div>
          <h2 class="text-2xl font-black text-white">Partnered Public Restaurant Venues</h2>
          <p class="text-xs text-gray-400 mt-1">Detailed venue dossiers: activities conducted, occupied duration, and special ambiance highlights.</p>
        </div>
        <button onclick="document.getElementById('modal-new-venue').classList.remove('hidden')" class="px-4 py-2 rounded-xl bg-kalisi-gold text-black text-xs font-black hover:brightness-110 transition">
          + Add Partner Venue
        </button>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6" id="venues-full-container">
        <!-- Rendered by JS -->
      </div>
    </div>

    <!-- TAB 6: PAYMENTS & REVENUE HUB -->
    <div id="tab-payments" class="hidden space-y-6">
      <div class="flex justify-between items-center">
        <div>
          <h2 class="text-2xl font-black text-white">Payments & Revenue Hub</h2>
          <p class="text-xs text-gray-400 mt-1">Track financial conversions, ticket sales, and Razorpay/Stripe transactions.</p>
        </div>
      </div>

      <!-- Financial Metrics -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div class="glass-card p-6 rounded-2xl space-y-2">
          <span class="text-xs text-gray-400 uppercase font-bold">Gross Revenue</span>
          <div class="text-3xl font-black text-kalisi-gold" id="pay-total-revenue">₹0</div>
          <p class="text-[11px] text-gray-500">Collected from ticketed dinner slots & passes.</p>
        </div>
        <div class="glass-card p-6 rounded-2xl space-y-2">
          <span class="text-xs text-gray-400 uppercase font-bold">Paid Seat Conversions</span>
          <div class="text-3xl font-black text-green-400" id="pay-paid-count">0</div>
          <p class="text-[11px] text-gray-500">Members who booked with standard fee.</p>
        </div>
        <div class="glass-card p-6 rounded-2xl space-y-2">
          <span class="text-xs text-gray-400 uppercase font-bold">Free Trial First Dinners</span>
          <div class="text-3xl font-black text-kalisi-purple" id="pay-trial-count">0</div>
          <p class="text-[11px] text-gray-500">First-time members using trial promotion.</p>
        </div>
      </div>

      <!-- Pricing Plans Available in Platform -->
      <div class="glass-card rounded-2xl p-6 space-y-4">
        <h3 class="text-base font-black text-white">Configured Platform Pricing Tiers</h3>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
          <div class="p-4 rounded-xl bg-kalisi-surfaceLight border border-kalisi-border">
            <span class="font-extrabold text-kalisi-gold uppercase block text-[11px]">Free Trial</span>
            <div class="text-xl font-black text-white mt-1">₹0</div>
            <p class="text-gray-400 mt-1">First dinner free per user to eliminate onboarding friction.</p>
          </div>
          <div class="p-4 rounded-xl bg-kalisi-surfaceLight border border-kalisi-border">
            <span class="font-extrabold text-green-400 uppercase block text-[11px]">Single Dinner Pass</span>
            <div class="text-xl font-black text-white mt-1">₹499 / dinner</div>
            <p class="text-gray-400 mt-1">Curated seat reservation, 5-stranger matching, icebreakers.</p>
          </div>
          <div class="p-4 rounded-xl bg-kalisi-surfaceLight border border-kalisi-border">
            <span class="font-extrabold text-kalisi-purple uppercase block text-[11px]">Monthly Vibe Pass</span>
            <div class="text-xl font-black text-white mt-1">₹1,499 / month</div>
            <p class="text-gray-400 mt-1">Unlimited weekend dinners + priority table placement.</p>
          </div>
        </div>
      </div>
    </div>

    <!-- TAB 7: USER VIBE DNA DIRECTORY -->
    <div id="tab-users" class="hidden space-y-6">
      <div class="flex justify-between items-center">
        <div>
          <h2 class="text-2xl font-black text-white">User Vibe DNA & Personality Profiles</h2>
          <p class="text-xs text-gray-400 mt-1">Classified into 4 conversational archetypes: Clark Kent (Anchor), Stark (Spark), Phoebe (Storyteller), Sherlock (Inquirer).</p>
        </div>
      </div>

      <div class="glass-card rounded-2xl overflow-hidden">
        <table class="min-w-full divide-y divide-kalisi-border text-left text-sm">
          <thead class="bg-kalisi-surfaceLight/60 text-gray-400 text-xs uppercase font-bold">
            <tr>
              <th class="px-6 py-4">User</th>
              <th class="px-6 py-4">City</th>
              <th class="px-6 py-4">Conversational Archetype</th>
              <th class="px-6 py-4">Budget Tier</th>
              <th class="px-6 py-4">Dietary Preference</th>
              <th class="px-6 py-4">Verification</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-kalisi-border" id="users-tbody">
            <!-- Rendered by JS -->
          </tbody>
        </table>
      </div>
    </div>

  </main>

  <!-- ======================================================================= -->
  <!-- 4. MODALS (CREATE SLOT & CREATE VENUE)                                   -->
  <!-- ======================================================================= -->

  <!-- Modal: Create Slot -->
  <div id="modal-new-slot" class="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 z-50 hidden">
    <div class="glass-card bg-kalisi-surface p-7 rounded-3xl max-w-md w-full space-y-5 border border-kalisi-border">
      <div class="flex justify-between items-center">
        <h3 class="text-lg font-black text-white">Schedule Weekend Slot</h3>
        <button onclick="document.getElementById('modal-new-slot').classList.add('hidden')" class="text-gray-400 hover:text-white"><i class="fas fa-times"></i></button>
      </div>
      <form onsubmit="handleCreateSlot(event)" class="space-y-4">
        <div>
          <label class="block text-xs font-bold text-gray-400 mb-1">City</label>
          <input type="text" name="city" value="Chennai" required class="w-full bg-kalisi-surfaceLight border border-kalisi-border rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-kalisi-gold">
        </div>
        <div>
          <label class="block text-xs font-bold text-gray-400 mb-1">Date String (e.g. Sat, 12/12/2026)</label>
          <input type="text" name="date_str" placeholder="Sat, 12/12/2026" required class="w-full bg-kalisi-surfaceLight border border-kalisi-border rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-kalisi-gold">
        </div>
        <div>
          <label class="block text-xs font-bold text-gray-400 mb-1">Time Window</label>
          <input type="text" name="time_window" value="19:00 - 22:00" required class="w-full bg-kalisi-surfaceLight border border-kalisi-border rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-kalisi-gold">
        </div>
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block text-xs font-bold text-gray-400 mb-1">Slot Price (₹)</label>
            <input type="number" name="price_inr" value="499" required class="w-full bg-kalisi-surfaceLight border border-kalisi-border rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-kalisi-gold">
          </div>
          <div>
            <label class="block text-xs font-bold text-gray-400 mb-1">Total Capacity</label>
            <input type="number" name="max_capacity" value="10" required class="w-full bg-kalisi-surfaceLight border border-kalisi-border rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-kalisi-gold">
          </div>
        </div>
        <div class="flex justify-end space-x-3 pt-3">
          <button type="button" onclick="document.getElementById('modal-new-slot').classList.add('hidden')" class="px-4 py-2 text-xs font-bold text-gray-400 hover:text-white">Cancel</button>
          <button type="submit" class="px-5 py-2.5 rounded-xl bg-kalisi-gold text-black text-xs font-black hover:brightness-110">Schedule Slot</button>
        </div>
      </form>
    </div>
  </div>

  <!-- Modal: Create Partner Venue (With Rich Activities & Special Features) -->
  <div id="modal-new-venue" class="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 z-50 hidden">
    <div class="glass-card bg-kalisi-surface p-7 rounded-3xl max-w-lg w-full space-y-5 border border-kalisi-border max-h-[90vh] overflow-y-auto">
      <div class="flex justify-between items-center">
        <div>
          <h3 class="text-lg font-black text-white">Add Verified Partner Venue</h3>
          <p class="text-xs text-gray-400">Include activities, occupied time, and special features.</p>
        </div>
        <button onclick="document.getElementById('modal-new-venue').classList.add('hidden')" class="text-gray-400 hover:text-white"><i class="fas fa-times"></i></button>
      </div>

      <form onsubmit="handleCreateVenue(event)" class="space-y-4 text-xs">
        <div>
          <label class="block font-bold text-gray-400 mb-1">Restaurant Name</label>
          <input type="text" name="name" placeholder="e.g. Chamber of Potions" required class="w-full bg-kalisi-surfaceLight border border-kalisi-border rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-kalisi-gold">
        </div>
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block font-bold text-gray-400 mb-1">Neighborhood</label>
            <input type="text" name="neighborhood" placeholder="e.g. Anna Nagar" required class="w-full bg-kalisi-surfaceLight border border-kalisi-border rounded-xl px-4 py-2 text-sm text-white focus:outline-none focus:border-kalisi-gold">
          </div>
          <div>
            <label class="block font-bold text-gray-400 mb-1">City</label>
            <input type="text" name="city" value="Chennai" required class="w-full bg-kalisi-surfaceLight border border-kalisi-border rounded-xl px-4 py-2 text-sm text-white focus:outline-none focus:border-kalisi-gold">
          </div>
        </div>
        <div>
          <label class="block font-bold text-gray-400 mb-1">Full Street Address</label>
          <textarea name="full_address" rows="2" placeholder="Building, Main road, Block, City, Pin..." required class="w-full bg-kalisi-surfaceLight border border-kalisi-border rounded-xl px-4 py-2 text-sm text-white focus:outline-none focus:border-kalisi-gold"></textarea>
        </div>
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block font-bold text-gray-400 mb-1">Cuisine Style</label>
            <input type="text" name="cuisine" placeholder="e.g. Italian / Continental" required class="w-full bg-kalisi-surfaceLight border border-kalisi-border rounded-xl px-4 py-2 text-sm text-white focus:outline-none focus:border-kalisi-gold">
          </div>
          <div>
            <label class="block font-bold text-gray-400 mb-1">Price Tier</label>
            <select name="price_tier" class="w-full bg-kalisi-surfaceLight border border-kalisi-border rounded-xl px-4 py-2 text-sm text-white focus:outline-none focus:border-kalisi-gold">
              <option value="budget">Budget-Friendly (&lt;₹800)</option>
              <option value="mid_range" selected>Mid-Range (₹800-₹1500)</option>
              <option value="premium">Premium (&gt;₹1500)</option>
            </select>
          </div>
        </div>

        <!-- NEW RICH FIELDS REQUESTED BY USER -->
        <div>
          <label class="block font-bold text-kalisi-gold mb-1">Activities Conducted There</label>
          <input type="text" name="activities" value="Table-side icebreaker card deck, rapid vibe trivia, host welcome" required class="w-full bg-kalisi-surfaceLight border border-kalisi-border rounded-xl px-4 py-2 text-sm text-white focus:outline-none focus:border-kalisi-gold">
          <span class="text-[10px] text-gray-500">What social games, icebreakers, or experiences happen at the table?</span>
        </div>

        <div>
          <label class="block font-bold text-kalisi-gold mb-1">Time Occupied / Duration</label>
          <input type="text" name="duration_hours" value="2.5 Hours (19:00 - 21:30)" required class="w-full bg-kalisi-surfaceLight border border-kalisi-border rounded-xl px-4 py-2 text-sm text-white focus:outline-none focus:border-kalisi-gold">
          <span class="text-[10px] text-gray-500">How long will the dinner table be reserved for the strangers?</span>
        </div>

        <div>
          <label class="block font-bold text-kalisi-gold mb-1">What is Special About That Venue? (Highlights)</label>
          <textarea name="special_features" rows="2" required class="w-full bg-kalisi-surfaceLight border border-kalisi-border rounded-xl px-4 py-2 text-sm text-white focus:outline-none focus:border-kalisi-gold">Dedicated 6-person secluded booth, ambient acoustic lighting, complimentary signature mocktail.</textarea>
          <span class="text-[10px] text-gray-500">Unique vibes, secret corners, view, drinks, or ambiance highlights.</span>
        </div>

        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block font-bold text-gray-400 mb-1">Contact Person</label>
            <input type="text" name="contact_person" value="Restaurant Manager" required class="w-full bg-kalisi-surfaceLight border border-kalisi-border rounded-xl px-4 py-2 text-sm text-white focus:outline-none focus:border-kalisi-gold">
          </div>
          <div>
            <label class="block font-bold text-gray-400 mb-1">Contact Phone</label>
            <input type="text" name="contact_phone" value="+91 98400 12345" required class="w-full bg-kalisi-surfaceLight border border-kalisi-border rounded-xl px-4 py-2 text-sm text-white focus:outline-none focus:border-kalisi-gold">
          </div>
        </div>

        <div class="flex justify-end space-x-3 pt-3">
          <button type="button" onclick="document.getElementById('modal-new-venue').classList.add('hidden')" class="px-4 py-2 text-xs font-bold text-gray-400 hover:text-white">Cancel</button>
          <button type="submit" class="px-5 py-2.5 rounded-xl bg-kalisi-gold text-black text-xs font-black hover:brightness-110">Save Verified Venue</button>
        </div>
      </form>
    </div>
  </div>

  <!-- ======================================================================= -->
  <!-- 5. FRONTEND SCRIPTS                                                     -->
  <!-- ======================================================================= -->
  <script>
    let appData = {};

    function checkAuth() {
      const token = localStorage.getItem('kalisi_admin_token');
      if (token) {
        document.getElementById('auth-overlay').classList.add('hidden');
        loadData();
      } else {
        document.getElementById('auth-overlay').classList.remove('hidden');
      }
    }

    async function handleLogin(e) {
      e.preventDefault();
      const username = document.getElementById('login-username').value;
      const password = document.getElementById('login-password').value;
      const errBox = document.getElementById('login-error');

      const formData = new FormData();
      formData.append('username', username);
      formData.append('password', password);

      try {
        const res = await fetch('/admin/api/login', { method: 'POST', body: formData });
        if (res.ok) {
          const data = await res.json();
          localStorage.setItem('kalisi_admin_token', data.token);
          document.getElementById('auth-overlay').classList.add('hidden');
          loadData();
        } else {
          errBox.innerText = 'Invalid username or password. Check .env configuration.';
          errBox.classList.remove('hidden');
        }
      } catch (err) {
        errBox.innerText = 'Server error during login.';
        errBox.classList.remove('hidden');
      }
    }

    function handleLogout() {
      localStorage.removeItem('kalisi_admin_token');
      document.getElementById('auth-overlay').classList.remove('hidden');
    }

    async function loadData() {
      try {
        const res = await fetch('/admin/api/overview');
        appData = await res.json();
        renderKPIs();
        renderTables();
        renderSlots();
        renderBookings();
        renderVenues();
        renderUsers();
      } catch (err) {
        console.error('Failed to load admin data:', err);
      }
    }

    function renderKPIs() {
      const m = appData.metrics;
      document.getElementById('kpi-users').innerText = m.total_users;
      document.getElementById('kpi-slots').innerText = m.active_slots;
      document.getElementById('kpi-tables').innerText = m.total_tables;
      document.getElementById('kpi-bookings').innerText = m.total_bookings;
      document.getElementById('kpi-venues').innerText = m.total_restaurants;
      document.getElementById('kpi-revenue').innerText = '₹' + m.total_revenue_inr.toLocaleString('en-IN');

      // Payments tab KPIs
      document.getElementById('pay-total-revenue').innerText = '₹' + m.total_revenue_inr.toLocaleString('en-IN');
      document.getElementById('pay-paid-count').innerText = m.paid_bookings;
      document.getElementById('pay-trial-count').innerText = m.free_trials;

      // Overview summaries
      const tSummary = document.getElementById('overview-tables-summary');
      tSummary.innerHTML = appData.tables.slice(0, 3).map(t => `
        <div class="flex items-center justify-between p-3 rounded-xl bg-kalisi-surfaceLight/50 border border-kalisi-border text-xs">
          <div>
            <span class="font-bold text-white block">Table #${t.table_number} • ${t.restaurant_name}</span>
            <span class="text-gray-400 text-[11px]">${t.city} • ${t.date_str}</span>
          </div>
          <span class="px-2.5 py-1 rounded-full text-[10px] font-extrabold ${t.reveal_stage === 'fully_revealed' ? 'bg-green-500/20 text-green-400' : 'bg-kalisi-gold/20 text-kalisi-gold'} uppercase">${t.reveal_stage}</span>
        </div>
      `).join('') || '<div class="text-xs text-gray-500">No tables formed yet.</div>';

      const bSummary = document.getElementById('overview-bookings-summary');
      bSummary.innerHTML = appData.bookings.slice(0, 3).map(b => `
        <div class="flex items-center justify-between p-3 rounded-xl bg-kalisi-surfaceLight/50 border border-kalisi-border text-xs">
          <div>
            <span class="font-bold text-white block">${b.user_name}</span>
            <span class="text-gray-400 text-[11px]">${b.slot_city} • ${b.slot_date}</span>
          </div>
          <span class="font-black ${b.amount_paid > 0 ? 'text-green-400' : 'text-kalisi-gold'}">${b.amount_paid > 0 ? '₹' + b.amount_paid : 'Free Trial'}</span>
        </div>
      `).join('') || '<div class="text-xs text-gray-500">No bookings yet.</div>';
    }

    function renderTables() {
      const container = document.getElementById('tables-full-container');
      if (!appData.tables || appData.tables.length === 0) {
        container.innerHTML = `<div class="col-span-full py-12 text-center text-gray-500">No tables formed yet. Click "Run Matchmaker" to cluster bookings.</div>`;
        return;
      }
      container.innerHTML = appData.tables.map(t => {
        let badgeColor = 'bg-gray-800 text-gray-300 border-gray-700';
        let stageLabel = 'Locked (T > 24h)';
        if (t.reveal_stage === 'area_revealed') {
          badgeColor = 'bg-kalisi-gold/20 text-kalisi-gold border-kalisi-gold/40';
          stageLabel = 'Area Revealed (T-24h)';
        } else if (t.reveal_stage === 'fully_revealed') {
          badgeColor = 'bg-green-500/20 text-green-400 border-green-500/40';
          stageLabel = 'Fully Revealed (Day-Of)';
        }

        return `
          <div class="glass-card rounded-2xl p-6 flex flex-col justify-between space-y-4">
            <div>
              <div class="flex items-center justify-between">
                <span class="text-xs font-black text-kalisi-gold uppercase tracking-wider">Table #${t.table_number}</span>
                <span class="text-[11px] px-2.5 py-0.5 rounded-full border font-bold ${badgeColor}">${stageLabel}</span>
              </div>
              <h3 class="text-lg font-black mt-2 text-white">${t.restaurant_name}</h3>
              <p class="text-xs text-gray-400">${t.neighborhood ? t.neighborhood + ', ' : ''}${t.city} • ${t.date_str} (${t.time_window})</p>
              
              <div class="mt-4 p-3 bg-kalisi-surfaceLight/80 rounded-xl border border-kalisi-border">
                <span class="text-[10px] uppercase font-black text-kalisi-purple block mb-1">Group Chemistry</span>
                <p class="text-xs font-semibold text-gray-200">${t.archetype_summary}</p>
              </div>

              <div class="mt-4 space-y-2">
                <div class="flex justify-between items-center text-xs">
                  <span class="font-bold text-gray-400 uppercase text-[10px]">Members (${t.attendee_count}/${t.target_size})</span>
                  <span class="text-[11px] ${t.seats_available === 0 ? 'text-kalisi-gold font-bold' : 'text-gray-400'}">${t.seats_available === 0 ? 'Table Full' : t.seats_available + ' seat(s) open'}</span>
                </div>
                ${t.attendees.map(a => `
                  <div class="flex items-center justify-between text-xs py-1.5 px-3 rounded-lg bg-kalisi-surfaceLight/40 border border-kalisi-border/60">
                    <span class="font-bold text-white">${a.name}</span>
                    <span class="text-[10px] px-2 py-0.5 rounded-full bg-kalisi-border font-bold text-kalisi-gold">${a.archetype}</span>
                  </div>
                `).join('')}
              </div>
            </div>

            <div class="pt-3 border-t border-kalisi-border flex items-center justify-between">
              <span class="text-[11px] font-bold text-gray-400">Advance Stage:</span>
              <div class="flex space-x-1.5">
                <button onclick="setStage('${t.id}', 'locked')" class="px-2.5 py-1 text-[11px] rounded-lg font-bold ${t.reveal_stage === 'locked' ? 'bg-white text-black' : 'bg-kalisi-surfaceLight text-gray-300'}">Lock</button>
                <button onclick="setStage('${t.id}', 'area_revealed')" class="px-2.5 py-1 text-[11px] rounded-lg font-bold ${t.reveal_stage === 'area_revealed' ? 'bg-kalisi-gold text-black' : 'bg-kalisi-surfaceLight text-gray-300'}">Area (24h)</button>
                <button onclick="setStage('${t.id}', 'fully_revealed')" class="px-2.5 py-1 text-[11px] rounded-lg font-bold ${t.reveal_stage === 'fully_revealed' ? 'bg-green-400 text-black' : 'bg-kalisi-surfaceLight text-gray-300'}">Full</button>
              </div>
            </div>
          </div>
        `;
      }).join('');
    }

    function renderSlots() {
      const tbody = document.getElementById('slots-tbody');
      tbody.innerHTML = appData.slots.map(s => `
        <tr class="hover:bg-kalisi-surfaceLight/30 transition">
          <td class="px-6 py-4 font-black text-white">${s.city}</td>
          <td class="px-6 py-4 text-kalisi-gold font-bold">${s.date_str}</td>
          <td class="px-6 py-4 text-gray-300">${s.time_window}</td>
          <td class="px-6 py-4 font-black text-green-400">₹${s.price_inr}</td>
          <td class="px-6 py-4">
            <div class="flex items-center space-x-2">
              <span class="font-bold text-white">${s.bookings_count} / ${s.max_capacity}</span>
              <div class="w-16 bg-kalisi-surfaceLight rounded-full h-1.5">
                <div class="bg-kalisi-gold h-1.5 rounded-full" style="width: ${(s.bookings_count / s.max_capacity) * 100}%"></div>
              </div>
            </div>
          </td>
          <td class="px-6 py-4 font-black ${s.seats_left === 0 ? 'text-red-400' : 'text-kalisi-blue'}">${s.seats_left === 0 ? 'Sold Out' : s.seats_left + ' seats'}</td>
          <td class="px-6 py-4"><span class="px-2.5 py-0.5 text-[10px] rounded-full bg-green-500/20 text-green-400 font-extrabold uppercase">${s.status}</span></td>
        </tr>
      `).join('');
    }

    function renderBookings() {
      const tbody = document.getElementById('bookings-tbody');
      tbody.innerHTML = appData.bookings.map(b => `
        <tr class="hover:bg-kalisi-surfaceLight/30 transition">
          <td class="px-6 py-4">
            <span class="font-black text-white block">${b.user_name}</span>
            <span class="text-xs text-gray-400">${b.user_email}</span>
          </td>
          <td class="px-6 py-4 text-xs">
            <span class="font-bold text-kalisi-gold block">${b.slot_city}</span>
            <span class="text-gray-300">${b.slot_date} (${b.slot_time})</span>
          </td>
          <td class="px-6 py-4 font-bold ${b.table_number ? 'text-kalisi-purple' : 'text-gray-500'}">${b.table_number ? 'Table #' + b.table_number : 'In Clustering Queue'}</td>
          <td class="px-6 py-4 font-black ${b.amount_paid > 0 ? 'text-green-400' : 'text-kalisi-gold'}">${b.amount_paid > 0 ? '₹' + b.amount_paid : '₹0 (Free Trial)'}</td>
          <td class="px-6 py-4 text-xs font-semibold text-gray-300">${b.payment_method}</td>
          <td class="px-6 py-4">
            <span class="px-2 py-0.5 rounded text-[10px] font-bold ${b.attendance_confirmed ? 'bg-green-500/20 text-green-400' : 'bg-gray-800 text-gray-400'}">${b.attendance_confirmed ? 'Confirmed' : 'Pending (T-2h)'}</span>
          </td>
          <td class="px-6 py-4 text-[11px] font-mono text-gray-500">${b.id.substring(0, 8)}...</td>
        </tr>
      `).join('');
    }

    function renderVenues() {
      const container = document.getElementById('venues-full-container');
      container.innerHTML = appData.restaurants.map(r => `
        <div class="glass-card rounded-2xl p-6 flex flex-col justify-between space-y-4">
          <div>
            <div class="flex justify-between items-start">
              <div>
                <h3 class="font-black text-white text-lg">${r.name}</h3>
                <span class="text-xs text-kalisi-gold font-bold">${r.neighborhood}, ${r.city}</span>
              </div>
              <span class="text-[10px] uppercase font-black px-2.5 py-0.5 rounded-full bg-kalisi-gold/20 text-kalisi-gold border border-kalisi-gold/30">${r.price_tier}</span>
            </div>

            <p class="text-xs text-gray-400 mt-2">${r.address}</p>

            <div class="mt-4 space-y-2.5 border-t border-kalisi-border pt-3">
              <div>
                <span class="text-[10px] font-black uppercase text-kalisi-gold block">Activities Conducted There:</span>
                <p class="text-xs text-gray-200 mt-0.5 font-medium">${r.activities}</p>
              </div>

              <div>
                <span class="text-[10px] font-black uppercase text-kalisi-blue block">Time Occupied / Duration:</span>
                <p class="text-xs text-gray-200 mt-0.5 font-medium">${r.duration_hours}</p>
              </div>

              <div>
                <span class="text-[10px] font-black uppercase text-kalisi-purple block">Special About This Venue:</span>
                <p class="text-xs text-gray-200 mt-0.5 font-medium">${r.special_features}</p>
              </div>
            </div>
          </div>

          <div class="pt-3 border-t border-kalisi-border flex justify-between items-center text-[11px] text-gray-400">
            <span>Contact: <b>${r.contact_person}</b></span>
            <span>Tel: <b>${r.contact_phone}</b></span>
          </div>
        </div>
      `).join('');
    }

    function renderUsers() {
      const tbody = document.getElementById('users-tbody');
      tbody.innerHTML = appData.users.map(u => `
        <tr class="hover:bg-kalisi-surfaceLight/30 transition">
          <td class="px-6 py-4">
            <span class="font-black text-white block">${u.name}</span>
            <span class="text-xs text-gray-400">${u.email}</span>
          </td>
          <td class="px-6 py-4 text-gray-300 font-medium">${u.city}</td>
          <td class="px-6 py-4">
            <span class="px-3 py-1 rounded-full text-xs font-black bg-kalisi-purple/20 text-kalisi-purple border border-kalisi-purple/40">${u.archetype}</span>
          </td>
          <td class="px-6 py-4 text-kalisi-gold text-xs font-bold capitalize">${u.budget_tier}</td>
          <td class="px-6 py-4 text-xs text-gray-300">${u.dietary}</td>
          <td class="px-6 py-4"><span class="text-green-400 font-bold text-xs"><i class="fas fa-check-circle mr-1"></i>Verified</span></td>
        </tr>
      `).join('');
    }

    async function setStage(tableId, stage) {
      const formData = new FormData();
      formData.append('stage', stage);
      await fetch(`/admin/api/tables/${tableId}/set-stage`, { method: 'POST', body: formData });
      loadData();
    }

    async function triggerMatchmaking() {
      const res = await fetch('/admin/api/matchmake', { method: 'POST' });
      const data = await res.json();
      alert(data.message || 'Matchmaking complete!');
      loadData();
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

    async function handleCreateVenue(e) {
      e.preventDefault();
      const form = e.target;
      const data = new FormData(form);
      await fetch('/admin/api/restaurants/create', { method: 'POST', body: data });
      document.getElementById('modal-new-venue').classList.add('hidden');
      form.reset();
      loadData();
    }

    function navigateTab(tabId, url) {
      history.pushState({ tab: tabId }, '', url);
      switchTab(tabId);
      return false;
    }

    function detectTabFromPath() {
      const path = window.location.pathname;
      if (path.includes('/tables')) switchTab('tables');
      else if (path.includes('/slots')) switchTab('slots');
      else if (path.includes('/bookings')) switchTab('bookings');
      else if (path.includes('/venues')) switchTab('venues');
      else if (path.includes('/payments')) switchTab('payments');
      else if (path.includes('/vibe-dna') || path.includes('/users')) switchTab('users');
      else switchTab('overview');
    }

    window.onpopstate = function() {
      detectTabFromPath();
    };

    function switchTab(tabId) {
      const tabs = ['overview', 'tables', 'slots', 'bookings', 'venues', 'payments', 'users'];
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
  <script>
    tailwind.config = {
      theme: {
        extend: {
          colors: {
            kalisi: {
              bg: '#121212',
              surface: '#1E1E1E',
              surfaceLight: '#282828',
              gold: '#F5A623',
              crimson: '#D32F2F',
              border: '#2E2E2E'
            }
          }
        }
      }
    }
  </script>
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

@admin_router.get("/admin/login", response_class=HTMLResponse)
def admin_login_page():
    return HTMLResponse(content=ADMIN_LOGIN_HTML)

@admin_router.get("/admin", response_class=HTMLResponse)
def admin_root():
    return RedirectResponse(url="/admin/overview")

@admin_router.get("/admin/overview", response_class=HTMLResponse)
def admin_overview():
    return HTMLResponse(content=get_admin_page_html("overview"))

@admin_router.get("/admin/tables", response_class=HTMLResponse)
def admin_tables():
    return HTMLResponse(content=get_admin_page_html("tables"))

@admin_router.get("/admin/slots", response_class=HTMLResponse)
def admin_slots():
    return HTMLResponse(content=get_admin_page_html("slots"))

@admin_router.get("/admin/bookings", response_class=HTMLResponse)
def admin_bookings():
    return HTMLResponse(content=get_admin_page_html("bookings"))

@admin_router.get("/admin/venues", response_class=HTMLResponse)
def admin_venues():
    return HTMLResponse(content=get_admin_page_html("venues"))

@admin_router.get("/admin/payments", response_class=HTMLResponse)
def admin_payments():
    return HTMLResponse(content=get_admin_page_html("payments"))

@admin_router.get("/admin/vibe-dna", response_class=HTMLResponse)
@admin_router.get("/admin/users", response_class=HTMLResponse)
def admin_users():
    return HTMLResponse(content=get_admin_page_html("users"))

