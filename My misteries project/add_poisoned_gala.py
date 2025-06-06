import sqlite3

conn = sqlite3.connect('mysteries.db')
c = conn.cursor()

# Insert case
title = 'The Poisoned Gala'
background = 'A renowned philanthropist collapses at a charity gala. Poison is suspected, but who among the guests had the motive and means?'
time = '10:05 PM, Charity Gala'
c.execute("INSERT INTO cases (title, background, time) VALUES (?, ?, ?)", (title, background, time))
case_id = c.lastrowid

# Insert clues
clues = [
    ('Wine Glass', 'The victim’s wine glass had traces of a rare toxin.', 'https://images.unsplash.com/photo-1519125323398-675f0ddb6308?auto=format&fit=crop&w=400&q=80'),
    ('Torn Note', 'A torn note in the victim’s pocket reads “Meet me in the garden at 10.”', 'https://images.unsplash.com/photo-1465101046530-73398c7f28ca?auto=format&fit=crop&w=400&q=80'),
    ('Security Footage', 'Footage shows someone entering the kitchen moments before the poisoning.', 'https://images.unsplash.com/photo-1464983953574-0892a716854b?auto=format&fit=crop&w=400&q=80'),
    ('Empty Pill Bottle', 'An empty bottle of sedatives found in the guest bathroom.', 'https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=400&q=80'),
    ('Glove with Stain', 'A single glove with a faint chemical smell was found in the garden.', 'https://images.unsplash.com/photo-1519125323398-675f0ddb6308?auto=format&fit=crop&w=400&q=80'),
    ('Unsent Text', 'The victim’s phone has an unsent text: “I know what you did.”', 'https://images.unsplash.com/photo-1465101046530-73398c7f28ca?auto=format&fit=crop&w=400&q=80'),
]
for t, d, i in clues:
    c.execute("INSERT INTO clues (case_id, title, desc, img) VALUES (?, ?, ?, ?)", (case_id, t, d, i))

# Insert suspects
suspects = [
    ('Dr. Evelyn Collins', 'Family physician', 50, 'Victim was blackmailing her over a malpractice case', 'Claims she was walking the grounds alone for fresh air', 'Medical knowledge makes her capable of using sedatives expertly.', 'https://randomuser.me/api/portraits/women/50.jpg'),
    ('Marcus Reed', 'Business partner', 47, 'Recently cut out of a lucrative deal', 'Was on a phone call in the lobby', 'Financial records show recent losses.', 'https://randomuser.me/api/portraits/men/47.jpg'),
    ('Sophia Lane', 'Event coordinator', 34, 'Victim threatened to expose her affair', 'Setting up the dessert table', 'Had access to all event areas.', 'https://randomuser.me/api/portraits/women/34.jpg'),
    ('Victor Shaw', 'Chef', 41, 'Fired earlier that day', 'Claims he left before the event started', 'Security footage is inconclusive.', 'https://randomuser.me/api/portraits/men/41.jpg'),
    ('Olivia Price', 'Old friend', 52, 'Victim owed her a large sum of money', 'Chatting with guests in the lounge', 'Seen near the kitchen before the incident.', 'https://randomuser.me/api/portraits/women/52.jpg'),
]
for n, r, a, m, al, no, i in suspects:
    c.execute("INSERT INTO suspects (case_id, name, relation, age, motive, alibi, notes, img) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (case_id, n, r, a, m, al, no, i))

# Insert timeline
timeline = [
    '7:00 PM - Guests arrive at the gala.',
    '8:15 PM - Dinner is served.',
    '9:00 PM - Victim gives a speech.',
    '9:45 PM - Victim is seen arguing with Dr. Evelyn Collins.',
    '10:05 PM - Victim collapses.',
    '10:20 PM - Police arrive.'
]
for t in timeline:
    c.execute("INSERT INTO timeline (case_id, event) VALUES (?, ?)", (case_id, t))

# Insert real killer
c.execute("CREATE TABLE IF NOT EXISTS real_killer (case_id INTEGER, name TEXT)")
c.execute("INSERT INTO real_killer (case_id, name) VALUES (?, ?)", (case_id, 'Dr. Evelyn Collins'))

conn.commit()
conn.close()
print('Mystery added!')
