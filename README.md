# Kalisi — Stranger Meetup Platform

> **"Five Strangers, One Unforgettable Meal."**  
> A curated offline social dining and micro-meetup platform inspired by the proven design and mechanics of *Together: Dinners That Connect*.

---

## 📌 Architecture & Team Documentation

* 👉 **[Product Requirements & Technical Specification (REQUIREMENTS.md)](./REQUIREMENTS.md)**
* ⚙️ **[Root Environment Configuration (.env)](./.env)**
* 🚀 **[Unified App & Admin Control Server (app.py)](./app.py)**

---

## 🚀 Quick Start Guide

### 1. Launch the Unified Platform & Admin Web Control
To start the backend server, database, and the **Admin Web Dashboard**:

```bash
python app.py
```

Once running, access:
* 📍 **Admin Web Portal:** [http://localhost:8000/admin](http://localhost:8000/admin)
* 📖 **Interactive Swagger API Docs:** [http://localhost:8000/api/docs](http://localhost:8000/api/docs)
* ⚡ **Mobile API Gateway:** `http://localhost:8000/api`

---

## 🖥️ Admin Web Dashboard Features (`/admin`)

The Admin Web Dashboard gives you real-time visibility and control over the platform:
1. **Live KPI Bar:** Real-time metrics for Total Users, Active City Slots, 5-Stranger Tables, Confirmed Bookings, and Verified Venues.
2. **5-Stranger Tables & Progressive Reveal Controller:**
   * View matched tables with group chemistry breakdown (e.g. *Clark Kent (2), Stark (1), Phoebe (1)*).
   * Advance the progressive reveal state for any table: **Locked (T > 24h)** $\to$ **Area Revealed (T - 24h)** $\to$ **Fully Revealed (Day of Event)**.
   * **1-Click "Run Matchmaker" button** to cluster unassigned attendees into optimal 5-person tables.
3. **City Slots Manager:** Create and schedule weekend dinner slots for any city (Chennai, Bangalore, Mumbai, Delhi).
4. **Verified Venues:** Add and manage partnered public restaurants with neighborhood, address, cuisine, and price tiers.
5. **User DNA Directory:** Inspect users, their conversational archetypes (*Clark Kent*, *Stark*, *Phoebe*, *Sherlock*), budget tiers, and verification badges.

---

## 📱 Mobile App (Flutter)

The mobile client is built with Flutter in `frontend/`, reproducing the exact dark-theme aesthetic (`#121212`, Gold `#F5A623`, Crimson `#D32F2F`) from the reference app:

```bash
cd frontend
flutter pub get
flutter run
```

### Mobile Screens Implemented:
* `welcome_screen.dart`: "Five Strangers, One Unforgettable Meal" with high-contrast pill actions.
* `onboarding_quiz_screen.dart`: Vibe DNA quiz with neon-glow selection buttons (*Humor*, *Observation*, *Listening*, *Asking questions*).
* `customization_screen.dart`: 3-step setup with Budget Tiers (Budget-Friendly <₹800, Mid-Range ₹800–₹1,500, Premium >₹1,500), dietary requirements, and language.
* `city_slots_screen.dart`: "Hey Gautham! Ready to Hang Out??", city selector, weekend slot cards, and "Book my seat".
* `progressive_reveal_screen.dart`: Table #1, Venue details, and Group Summary teaser.
* `character_insight_modal.dart`: "+ View Character Insights" modal with table icebreaker prompts.
