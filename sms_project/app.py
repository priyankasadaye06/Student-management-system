from flask import Flask, render_template, request, redirect, session, url_for
from db import get_db_connection

app = Flask(__name__)
app.secret_key = "secret_key_123"   # required for session

# ---------------- LOGIN ----------------
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            "SELECT * FROM user WHERE email=%s AND password=%s",
            (email, password)
        )
        user = cursor.fetchone()

        cursor.close()
        conn.close()

        if user:
            session['user_id'] = user['user_id']
            session['role'] = user['role']

            if user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            elif user['role'] == 'teacher':
                return redirect(url_for('teacher_dashboard'))
            else:
                return redirect(url_for('student_dashboard'))
        else:
            return "Invalid email or password"

    return render_template('login.html')


# ---------------- LOGOUT ----------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


# ---------------- ADMIN DASHBOARD ----------------
@app.route('/admin')
def admin_dashboard():
    if 'role' in session and session['role'] == 'admin':
        return render_template('admin.html')
    return redirect(url_for('login'))

@app.route('/admin/add-user', methods=['GET', 'POST'])
def add_user():
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))

    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO `user` (name, email, password, role) VALUES (%s, %s, %s, %s)",
            (name, email, password, role)
        )

        conn.commit()
        cursor.close()
        conn.close()

        return redirect(url_for('admin_dashboard'))

    return render_template('add_user.html')




@app.route('/admin/assign-student', methods=['GET', 'POST'])
def assign_student():
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Get users who are students and not yet assigned
    cursor.execute("""
        SELECT user_id, name 
        FROM user 
        WHERE role = 'student'
        AND user_id NOT IN (SELECT user_id FROM student)
    """)
    students = cursor.fetchall()

    # Get all classes
    cursor.execute("SELECT * FROM classes")
    classes = cursor.fetchall()

    if request.method == 'POST':
        user_id = request.form['user_id']
        roll_no = request.form['roll_no']
        class_id = request.form['class_id']

        cursor.execute(
            "INSERT INTO student (user_id, roll_no, class_id) VALUES (%s, %s, %s)",
            (user_id, roll_no, class_id)
        )
        conn.commit()

        cursor.close()
        conn.close()
        return redirect(url_for('admin_dashboard'))

    cursor.close()
    conn.close()
    return render_template(
        'assign_student.html',
        students=students,
        classes=classes
    )




# ---------------- TEACHER DASHBOARD ----------------
@app.route('/teacher')
def teacher_dashboard():
    if 'role' not in session or session['role'] != 'teacher':
        return redirect(url_for('login'))

    return render_template('teacher.html')


# ---------------- ADD ASSIGNMENT ----------------
@app.route('/teacher/add-assignment', methods=['GET', 'POST'])
def add_assignment():
    if 'role' not in session or session['role'] != 'teacher':
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Get all classes
    cursor.execute("SELECT * FROM classes")
    classes = cursor.fetchall()

    if request.method == 'POST':
        class_id = request.form['class_id']
        title = request.form['title']
        description = request.form['description']
        due_date = request.form['due_date']

        cursor.execute(
            "INSERT INTO assignment (class_id, title, description, due_date) VALUES (%s, %s, %s, %s)",
            (class_id, title, description, due_date)
        )
        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for('teacher_dashboard'))

    cursor.close()
    conn.close()
    return render_template('add_assignment.html', classes=classes)


# ---------------- VIEW STUDENTS ----------------
@app.route('/teacher/view-students')
def view_students():
    if 'role' not in session or session['role'] != 'teacher':
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT s.student_id, u.name AS student_name, s.roll_no, c.class_name, c.section
        FROM student s
        JOIN user u ON s.user_id = u.user_id
        JOIN classes c ON s.class_id = c.class_id
    """)
    students = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('view_students.html', students=students)

# ---------------- STUDENT DASHBOARD ----------------
@app.route('/student')
def student_dashboard():
    if 'role' in session and session['role'] == 'student':
        return render_template('student.html')
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)



