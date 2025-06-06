import sqlite3

conn = sqlite3.connect('mysteries.db')
c = conn.cursor()

# Create tables
c.execute('''CREATE TABLE IF NOT EXISTS cases (
    id INTEGER PRIMARY KEY,
    title TEXT,
    background TEXT,
    time TEXT
)''')
c.execute('''CREATE TABLE IF NOT EXISTS clues (
    id INTEGER PRIMARY KEY,
    case_id INTEGER,
    img TEXT,
    title TEXT,
    desc TEXT
)''')
c.execute('''CREATE TABLE IF NOT EXISTS suspects (
    id INTEGER PRIMARY KEY,
    case_id INTEGER,
    img TEXT,
    name TEXT,
    age INTEGER,
    relation TEXT,
    alibi TEXT,
    notes TEXT
)''')
c.execute('''CREATE TABLE IF NOT EXISTS timeline (
    id INTEGER PRIMARY KEY,
    case_id INTEGER,
    event TEXT
)''')

# Insert sample data for one case (extend as needed)
c.execute("INSERT OR REPLACE INTO cases VALUES (0, 'The Case of the Missing Painting', 'A priceless painting vanished from the city museum during a stormy night. The alarm never sounded, and only three people were present: the night guard, the curator, and a visiting art critic.', '2:15 AM, City Museum, Main Gallery')")
c.executemany("INSERT INTO clues (case_id, img, title, desc) VALUES (?, ?, ?, ?)", [
    (0, 'https://images.unsplash.com/photo-1519125323398-675f0ddb6308?auto=format&fit=crop&w=400&q=80', 'Blood-stained Glove', 'A left-handed glove with a faint blood stain was found near the window.'),
    (0, 'https://images.unsplash.com/photo-1465101046530-73398c7f28ca?auto=format&fit=crop&w=400&q=80', 'Broken Watch', 'A watch stopped at 2:15 AM was found under the display case.')
])
c.executemany("INSERT INTO suspects (case_id, img, name, age, relation, alibi, notes) VALUES (?, ?, ?, ?, ?, ?, ?)", [
    (0, 'https://randomuser.me/api/portraits/men/32.jpg', 'John Miller', 45, 'Night Guard', 'Claims to have been making rounds in the basement.', 'Veteran guard, but recently in debt.'),
    (0, 'https://randomuser.me/api/portraits/women/44.jpg', 'Elena Rossi', 38, 'Curator', 'Was in her office preparing paperwork.', 'Had access to all security codes.'),
    (0, 'https://randomuser.me/api/portraits/men/65.jpg', 'Victor Lane', 52, 'Visiting Art Critic', 'Claims to have been asleep in the guest room.', 'Known for controversial reviews.')
])
c.executemany("INSERT INTO timeline (case_id, event) VALUES (?, ?)", [
    (0, '1:45 AM - Night guard checks main gallery, all clear.'),
    (0, '2:00 AM - Storm intensifies, power flickers.'),
    (0, '2:15 AM - Painting last seen, watch breaks.'),
    (0, '2:30 AM - Curator discovers missing painting.')
])

conn.commit()
conn.close()
