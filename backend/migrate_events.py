import sqlite3

def migrate_db(path):
    print("Migrating", path)
    conn = sqlite3.connect(path)
    c = conn.cursor()
    c.execute("PRAGMA table_info(city_slots)")
    existing = [col[1] for col in c.fetchall()]
    
    new_cols = [
        ("title", "TEXT DEFAULT 'Weekend Stranger Dinner Meetup'"),
        ("is_enabled", "BOOLEAN DEFAULT 1"),
        ("venue_name", "TEXT DEFAULT 'Curated Partner Restaurant'"),
        ("venue_address", "TEXT DEFAULT 'Central City Location'"),
        ("about_event", "TEXT DEFAULT 'Join 5 curated strangers for an evening of genuine conversations, delicious dining, and icebreaker games.'"),
        ("rules_and_regulations", "TEXT DEFAULT '1. Arrive within 15 minutes of start time.\n2. Equal bill splitting for food and drinks.\n3. Keep phone away and enjoy real conversations.\n4. Age 18+ verified diners only.'")
    ]
    for col_name, col_type in new_cols:
        if col_name not in existing:
            c.execute(f"ALTER TABLE city_slots ADD COLUMN {col_name} {col_type}")
            print(f"Added column {col_name} to {path}")
    
    # Update existing slots with rich data based on city/date
    c.execute("""
        UPDATE city_slots
        SET title = 'Saturday Sunset Stranger Dinner',
            venue_name = 'Smoke House Deli Lavelle Road',
            venue_address = '52, Ground Floor, Lavelle Road, Shanthala Nagar, Ashok Nagar, Bengaluru 560001',
            about_event = 'Spend Saturday evening sharing a warm dinner table with 5 curious strangers. Features chef comfort specials, illustrative aesthetics, and our signature Kalisi icebreaker dilemma cards.',
            rules_and_regulations = '1. Arrive by 19:30 PM (15 mins buffer).\n2. Food and beverages are split equally among tablemates at the end.\n3. Respectful table talk — phone scrolling is discouraged.\n4. Age 18+ verified members only.'
        WHERE city LIKE '%Central Bangalore%' AND date_str LIKE '%Nov 28%'
    """)

    c.execute("""
        UPDATE city_slots
        SET title = 'Sunday Rooftop Skyline Dinner',
            venue_name = 'The Fatty Bao Indiranagar',
            venue_address = '610, 12th Main Rd, HAL 2nd Stage, Indiranagar, Bengaluru 560038',
            about_event = 'A relaxed Sunday evening Asian dining experience with panoramic skyline views. Enjoy mystery dim sum tastings and rapid-fire vibe match conversations with 5 fellow diners.',
            rules_and_regulations = '1. Arrive by 20:00 PM.\n2. Food bill is shared equally among diners.\n3. Maintain an open, welcoming table vibe.\n4. Casual chic / smart casual attire recommended.'
        WHERE city LIKE '%Central Bangalore%' AND date_str LIKE '%Nov 29%'
    """)

    c.execute("""
        UPDATE city_slots
        SET title = 'Saturday Pan-Asian Craft Dinner',
            venue_name = 'The Fatty Bao Indiranagar',
            venue_address = '610, 12th Main Rd, HAL 2nd Stage, Indiranagar, Bengaluru 560038',
            about_event = 'Unwind after a busy week with delicious craft cuisine, artisan cocktails, and an energetic table of 5 dynamic conversationalists.',
            rules_and_regulations = '1. Punctuality is appreciated (starts 20:00 PM).\n2. Equal bill splitting at meal conclusion.\n3. Age 18+ verified platform members.'
        WHERE city LIKE '%Indiranagar%'
    """)

    c.execute("""
        UPDATE city_slots
        SET title = 'Saturday Cozy Bistro Meetup',
            venue_name = 'The Bier Library Koramangala',
            venue_address = '14, Patel Narayana Reddy Layout, 80 Feet Main Rd, Koramangala 6th Block, Bengaluru 560095',
            about_event = 'A warm, open-air bistro atmosphere with craft bites and lively trivia conversation cards with 5 strangers.',
            rules_and_regulations = '1. Arrive within 15 minutes of 19:00 PM.\n2. Bill is split evenly among table participants.\n3. Friendly, respectful social atmosphere.'
        WHERE city LIKE '%Koramangala%'
    """)

    c.execute("""
        UPDATE city_slots
        SET title = 'Saturday Mystery Potion Dinner',
            venue_name = 'Chamber of Potions Anna Nagar',
            venue_address = 'C10, Ravilla Towers, Anna Nagar 3rd Main Rd, Chennai 600040',
            about_event = 'An enchanting fantasy-themed dinner experience with atmospheric lighting and table-side connection games.',
            rules_and_regulations = '1. Arrive by 19:00 PM.\n2. Bill split equally.\n3. Phone-free table focus.'
        WHERE city LIKE '%Chennai%'
    """)

    c.execute("""
        UPDATE city_slots
        SET title = 'Saturday Heritage Cafe Meetup',
            venue_name = 'Subko Specialty Coffee & Craftery',
            venue_address = '2 John Baptist Rd, Bandra West / Colaba Arts Precinct, Mumbai 400050',
            about_event = 'Craft sourdoughs, single-origin pour-overs, and thoughtful conversations in a restored heritage bungalow with 5 strangers.',
            rules_and_regulations = '1. Arrive by 20:00 PM.\n2. Bill split equally.\n3. Age 18+ verified diners.'
        WHERE city LIKE '%Mumbai%'
    """)

    conn.commit()
    conn.close()
    print("Completed migration for", path)

if __name__ == "__main__":
    migrate_db("kalisi.db")
    migrate_db("backend/kalisi.db")
