from flask import Flask, render_template, request, redirect ,url_for, flash
import sqlite3
from datetime import date, datetime  # استبدل date بـ datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # مفتاح سري لتأمين الجلسات  

# الصفحة الرئيسية
@app.route('/')
def home():
    return render_template('home.html')

# صفحة إضافة شخص
@app.route('/add', methods=['GET', 'POST'])
def add_person():
    conn = sqlite3.connect('attendance.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # إضافة شخص جديد
    if request.method == 'POST' and 'name' in request.form:
        new_name = request.form['name'].strip()
        gender = request.form['gender']
        grade = request.form['grade']
        if new_name and gender and grade:
            c.execute("INSERT INTO persons (name, gender, grade) VALUES (?, ?, ?)", (new_name, gender, grade))
            conn.commit()
            flash('✅ تم إضافة الشخص بنجاح')

    # جلب كل الأشخاص لعرضهم تحت الفورم
    c.execute("SELECT id, name, gender, grade FROM persons ORDER BY name")
    all_persons = [dict(row) for row in c.fetchall()]
    conn.close()

    return render_template("add_person.html", persons=all_persons)
@app.route('/edit_person/<int:person_id>', methods=['POST'])
def edit_person(person_id):
    new_name = request.form['name'].strip()
    new_gender = request.form['gender']
    new_grade = request.form['grade']

    conn = sqlite3.connect('attendance.db')
    c = conn.cursor()
    c.execute("UPDATE persons SET name = ?, gender = ?, grade = ? WHERE id = ?", 
              (new_name, new_gender, new_grade, person_id))
    conn.commit()
    conn.close()

    flash('✏️ تم تعديل بيانات الشخص بنجاح')
    return redirect(url_for('add_person'))

@app.route('/delete_person/<int:person_id>', methods=['POST'])
def delete_person(person_id):
    conn = sqlite3.connect('attendance.db')
    c = conn.cursor()

    # نحذف من attendance أولًا
    c.execute("DELETE FROM attendance WHERE person_id = ?", (person_id,))
    c.execute("DELETE FROM persons WHERE id = ?", (person_id,))
    conn.commit()
    conn.close()

    flash('🗑 تم حذف الشخص نهائيًا')
    return redirect(url_for('add_person'))

# صفحة تسجيل الحضور
@app.route('/attendance', methods=['GET', 'POST'])
def attendance():
    conn = sqlite3.connect('attendance.db')
    c = conn.cursor()

    today = date.today().isoformat()
    day_name = date.today().strftime('%A')  # اسم اليوم
    
    # تحويل أسماء الأيام إلى العربية
    arabic_days = {
        'Monday': 'الاثنين',
        'Tuesday': 'الثلاثاء', 
        'Wednesday': 'الأربعاء',
        'Thursday': 'الخميس',
        'Friday': 'الجمعة',
        'Saturday': 'السبت',
        'Sunday': 'الأحد'
    }
    arabic_day_name = arabic_days.get(day_name, day_name)

    if request.method == 'POST':
        selected_ids = request.form.getlist('person')  # الأشخاص الذين تم تحديدهم
        selected_ids = [int(person_id) for person_id in selected_ids]  # تحويل القيم إلى أرقام

        # جلب جميع الأشخاص المسجلين في الحضور اليوم
        c.execute("SELECT person_id FROM attendance WHERE date = ?", (today,))
        existing_ids = [row[0] for row in c.fetchall()]

        # الأشخاص الذين يجب إضافتهم
        to_add = set(selected_ids) - set(existing_ids)
        # الأشخاص الذين يجب إزالتهم
        to_remove = set(existing_ids) - set(selected_ids)

        # إضافة الحضور
        for person_id in to_add:
            current_time = datetime.now().strftime('%H:%M:%S')  # الوقت الحالي
            c.execute("INSERT INTO attendance (person_id, date, time) VALUES (?, ?, ?)", (person_id, today, current_time))

        # إزالة الحضور
        for person_id in to_remove:
            c.execute("DELETE FROM attendance WHERE person_id = ? AND date = ?", (person_id, today))

        conn.commit()
        conn.close()

        flash('✅ تم تحديث الحضور بنجاح')
        return redirect(url_for('attendance'))

    # GET: عرض الأشخاص وحالة الحضور
    c.execute("""
        SELECT p.id, p.name, 
               CASE WHEN a.id IS NOT NULL THEN '✅' ELSE '❌' END AS attendance_status,
               a.time, p.grade, p.gender
        FROM persons p
        LEFT JOIN attendance a ON p.id = a.person_id AND a.date = ?
        ORDER BY p.name
    """, (today,))
    persons = c.fetchall()
    conn.close()

    return render_template('attendance.html', persons=persons, current_date=today, 
                         day_name=day_name, arabic_day_name=arabic_day_name)
# صفحة عرض التقارير
@app.route('/report', methods=['GET', 'POST'])
def report():
    conn = sqlite3.connect('attendance.db')
    c = conn.cursor()

    selected_date = None
    start_date = None
    end_date = None
    present_names = []
    absent_names = []

    person_search = ''
    person_result = None

    # كل التواريخ المتاحة
    c.execute("SELECT DISTINCT date FROM attendance ORDER BY date DESC")
    available_dates = [row[0] for row in c.fetchall()]

    # جلب الأشخاص مع ترتيب ديناميكي
    c.execute("SELECT id, name FROM persons ORDER BY name")
    all_persons = c.fetchall()
    persons_with_row_number = {index + 1: person for index, person in enumerate(all_persons)}

    if request.method == 'POST':
        if 'date' in request.form:
            selected_date = request.form['date']

            # كل الأشخاص
            all_persons_dict = {row[0]: row[1] for row in all_persons}

            # الحاضرين في التاريخ
            c.execute("""
                SELECT p.id, p.name FROM attendance a
                JOIN persons p ON a.person_id = p.id
                WHERE a.date = ?
            """, (selected_date,))
            present = {row[0]: row[1] for row in c.fetchall()}

            # الغائبين = الكل - الحضور
            absent = {id: name for id, name in all_persons_dict.items() if id not in present}

            present_names = list(present.values())
            absent_names = list(absent.values())

        elif 'search_id' in request.form and 'start_date' in request.form and 'end_date' in request.form:
            search_row_number = int(request.form['search_id'].strip())
            start_date = request.form['start_date']
            end_date = request.form['end_date']

            if search_row_number in persons_with_row_number:
                person_id, person_name = persons_with_row_number[search_row_number]

                # جلب التواريخ التي حضر فيها الشخص
                c.execute("""
                    SELECT date FROM attendance
                    WHERE person_id = ? AND date BETWEEN ? AND ?
                """, (person_id, start_date, end_date))
                present_dates = [row[0] for row in c.fetchall()]

                # جلب كل التواريخ في النطاق
                c.execute("""
                    SELECT DISTINCT date FROM attendance
                    WHERE date BETWEEN ? AND ?
                """, (start_date, end_date))
                all_dates = [row[0] for row in c.fetchall()]

                # التواريخ التي غاب فيها الشخص
                absent_dates = list(set(all_dates) - set(present_dates))

                person_result = {
                    'name': person_name,
                    'present_count': len(present_dates),
                    'absent_count': len(absent_dates),
                    'present_dates': sorted(present_dates),
                    'absent_dates': sorted(absent_dates)
                }

        elif 'delete_date' in request.form:
            delete_date = request.form['delete_date']
            c.execute("DELETE FROM attendance WHERE date = ?", (delete_date,))
            conn.commit()
            flash(f'🗑️ تم حذف الحضور ليوم {delete_date}')

    conn.close()

    return render_template(
        'report.html',
        available_dates=available_dates,
        selected_date=selected_date,
        present_names=present_names,
        absent_names=absent_names,
        person_search=person_search,
        person_result=person_result,
        start_date=start_date,
        end_date=end_date
    )
if __name__ == '__main__':
    app.run(debug=True)