import sqlite3

# فتح أو إنشاء قاعدة البيانات (ملف)
conn = sqlite3.connect('attendance.db')
c = conn.cursor()

# إنشاء جدول الأشخاص
c.execute('''
    CREATE TABLE IF NOT EXISTS persons (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        gender TEXT NOT NULL,
        grade TEXT NOT NULL
    )
''')

# إنشاء جدول الحضور
c.execute('''
    CREATE TABLE IF NOT EXISTS attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        person_id INTEGER NOT NULL,
        date TEXT NOT NULL,
        FOREIGN KEY (person_id) REFERENCES persons(id)
    )
''')

conn.commit()
conn.close()

print("✅ قاعدة البيانات والجداول اتعملت بنجاح.")