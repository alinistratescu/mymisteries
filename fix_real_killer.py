import sqlite3

conn = sqlite3.connect('mysteries.db')
c = conn.cursor()
# Set the real killer for the first case to 'John Miller' (who is a suspect)
c.execute("UPDATE real_killer SET name=? WHERE case_id=0", ("John Miller",))
conn.commit()
conn.close()
print("Real killer for case 0 set to 'John Miller'.")
