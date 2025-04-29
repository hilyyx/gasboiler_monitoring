import sqlite3

conn = sqlite3.connect('sensor_data.db')
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS sensor_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    temp_outside REAL,
    temp_back REAL,
    temp_come REAL,
    temp_inside REAL,
    gas REAL,
    timestamp TEXT
);
''')

conn.commit()
conn.close()
