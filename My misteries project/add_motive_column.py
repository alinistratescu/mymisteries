import sqlite3

conn = sqlite3.connect('mysteries.db')
c = conn.cursor()
c.execute("ALTER TABLE suspects ADD COLUMN motive TEXT")
conn.commit()
conn.close()
print("Added 'motive' column to suspects table.")