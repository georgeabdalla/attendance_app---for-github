import os
import sqlite3

# اسم ملف قاعدة البيانات
db_file = 'attendance.db'

# حذف قاعدة البيانات القديمة إذا كانت موجودة
if os.path.exists(db_file):
    os.remove(db_file)
    print(f"🗑️ تم حذف قاعدة البيانات القديمة: {db_file}")

# إنشاء قاعدة بيانات جديدة
conn = sqlite3.connect(db_file)
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
        time TEXT NOT NULL,
        FOREIGN KEY (person_id) REFERENCES persons (id)
    )
''')

conn.commit()
conn.close()

print("✅ تم إنشاء قاعدة البيانات والجداول بنجاح.")