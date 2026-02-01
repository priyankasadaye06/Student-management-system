from datetime import date
import os
from werkzeug.utils import secure_filename


from flask import Flask, render_template, request, redirect, session, url_for
from db import get_db_connection

app = Flask(__name__)
UPLOAD_FOLDER = 'static/assignments'
ALLOWED_EXTENSIONS = {'pdf'}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'assignments')

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER



app.secret_key = "secret_key_123"   # required for session

# ------helper funtion for events and notices ---------

def get_notices(limit=5):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM notices ORDER BY posted_on DESC LIMIT %s",
        (limit,)
    )
    notices = cursor.fetchall()

    cursor.close()
    conn.close()
    return notices


def get_events(limit=5):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM events ORDER BY event_date ASC LIMIT %s",
        (limit,)
    )
    events = cursor.fetchall()

    cursor.close()
    conn.close()
    return events





# for avoid file not found error
os.makedirs('static/assignments', exist_ok=True)
os.makedirs('static/submissions', exist_ok=True)



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
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))   
    

# --------NOTICE AND EVENTS -------------

    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # total students
    cursor.execute("SELECT COUNT(*) AS total_students FROM user WHERE role='student'")
    total_students = cursor.fetchone()['total_students']

    # total teachers
    cursor.execute("SELECT COUNT(*) AS total_teachers FROM user WHERE role='teacher'")
    total_teachers = cursor.fetchone()['total_teachers']

    

    cursor.close()
    conn.close()

    notices = get_notices()
    events = get_events()
    return render_template(
        'admin.html',
        total_students=total_students,
        total_teachers=total_teachers,
        notices=notices,
        events=events
    )

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



@app.route('/admin/add-class', methods=['GET', 'POST'])
def add_class():
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))

    if request.method == 'POST':
        class_name = request.form['class_name']
        section = request.form['section']

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO classes (class_name, section) VALUES (%s, %s)",
            (class_name, section)
        )

        conn.commit()
        cursor.close()
        conn.close()

        return redirect(url_for('admin_dashboard'))

    return render_template('add_class.html')


# ------notice ------

@app.route('/admin/add-notice', methods=['GET', 'POST'])
def add_notice():
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))

    if request.method == 'POST':
        title = request.form['title']
        message = request.form['message']
        posted_by = 'admin'
        posted_on = date.today()

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO notices (title, message, posted_by, posted_on)
            VALUES (%s, %s, %s, %s)
            """,
            (title, message, posted_by, posted_on)
        )

        conn.commit()
        cursor.close()
        conn.close()

        return redirect(url_for('admin_dashboard'))

    return render_template('add_notice.html')


# -------------- Event ------------

@app.route('/admin/add-event', methods=['GET', 'POST'])
def add_event():
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        event_date = request.form['event_date']
        posted_on = date.today()

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO events (title, description, event_date, posted_on)
            VALUES (%s, %s, %s, %s)
            """,
            (title, description, event_date, posted_on)
        )

        conn.commit()
        cursor.close()
        conn.close()

        return redirect(url_for('admin_dashboard'))

    return render_template('add_event.html')


# ------------------ VIEW STUDENTS --------------------

@app.route('/admin/view-students')
def admin_view_students():
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Get all classes
    cursor.execute("SELECT * FROM classes")
    classes = cursor.fetchall()

    class_students = []

    for cls in classes:
        cursor.execute("""
            SELECT u.name, u.email, s.roll_no
            FROM student s
            JOIN user u ON s.user_id = u.user_id
            WHERE s.class_id = %s
        """, (cls['class_id'],))

        students = cursor.fetchall()

        class_students.append({
            'class_name': cls['class_name'],
            'section': cls['section'],
            'students': students
        })

    cursor.close()
    conn.close()

    return render_template(
        'admin_view_students.html',
        class_students=class_students
    )


# --------------------- VIEW TEACHER ------------------


@app.route('/admin/teachers')
def view_teachers():
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT name, email FROM user WHERE role='teacher'")
    teachers = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('view_teachers.html', teachers=teachers)


# ---------------- TEACHER DASHBOARD ----------------
@app.route('/teacher')
def teacher_dashboard():
    if 'role' not in session or session['role'] != 'teacher':
        return redirect(url_for('login'))

    notices = get_notices()
    events = get_events()

    return render_template(
        'teacher.html',
        notices=notices,
        events=events
    )
    #return render_template('teacher.html')


# ---------------- ADD ASSIGNMENT ----------------
@app.route('/teacher/add-assignment', methods=['GET', 'POST'])
def add_assignment():
    if 'role' not in session or session['role'] != 'teacher':
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM classes")
    classes = cursor.fetchall()

    if request.method == 'POST':
        class_id = request.form['class_id']
        title = request.form['title']
        description = request.form['description']
        due_date = request.form['due_date']
        file = request.files['assignment_file']

        filename = None
        if file and file.filename.endswith('.pdf'):
            filename = file.filename
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        cursor.execute(
            """
            INSERT INTO assignment (class_id, title, description, due_date, file_path)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (class_id, title, description, due_date, filename)
        )
        conn.commit()

        cursor.close()
        conn.close()
        return redirect(url_for('teacher_dashboard'))

    cursor.close()
    conn.close()
    return render_template('add_assignment.html', classes=classes)

# ----------helper function --------------

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ---------------- VIEW STUDENTS ----------------
@app.route('/teacher/view-students')
def teacher_view_students():
    if 'role' not in session or session['role'] != 'teacher':
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # get all classes
    cursor.execute("SELECT * FROM classes")
    classes = cursor.fetchall()

    class_students = []

    for cls in classes:
        cursor.execute("""
            SELECT u.name, u.email, s.roll_no
            FROM student s
            JOIN user u ON s.user_id = u.user_id
            WHERE s.class_id = %s
        """, (cls['class_id'],))

        students = cursor.fetchall()

        class_students.append({
            'class_name': cls['class_name'],
            'section': cls['section'],
            'students': students
        })

    cursor.close()
    conn.close()

    return render_template(
        'teacher_view_students.html',
        class_students=class_students
    )


# ---------------- STUDENT DASHBOARD ----------------

# ----------------- Submission -------------------

@app.route('/student/submit/<int:assignment_id>', methods=['GET', 'POST'])
def submit_assignment(assignment_id):
    if 'role' not in session or session['role'] != 'student':
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Get student_id
    cursor.execute("""
        SELECT student_id FROM student WHERE user_id = %s
    """, (session['user_id'],))
    student = cursor.fetchone()

    if not student:
        cursor.close()
        conn.close()
        return "Student record not found"

    student_id = student['student_id']

    if request.method == 'POST':
        file = request.files['submission_file']
        filename = secure_filename(file.filename)
        file.save(os.path.join('static/submissions', filename))

        cursor.execute("""
            INSERT INTO submission
            (assignment_id, student_id, submitted_on, file_path)
            VALUES (%s, %s, %s, %s)
        """, (assignment_id, student_id, date.today(), filename))

        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for('student_dashboard'))

    cursor.close()
    conn.close()
    return render_template('submit_assignment.html')



# ----------------VIEW ASSIGNMENT ---------------s


@app.route('/student')
def student_dashboard():
    if 'role' not in session or session['role'] != 'student':
        return redirect(url_for('login'))

    # --- Notices & Events (helper functions) ---
    notices = get_notices()
    events = get_events()

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # --- Get student_id and class_id ---
    cursor.execute("""
        SELECT student_id, class_id
        FROM student
        WHERE user_id = %s
    """, (session['user_id'],))
    student = cursor.fetchone()

    if not student:
        cursor.close()
        conn.close()
        return "Student not assigned to any class"

    student_id = student['student_id']
    class_id = student['class_id']

    # --- Get assignments + submission status ---
    cursor.execute("""
        SELECT 
            a.assignment_id,
            a.title,
            a.description,
            a.due_date,
            a.file_path,
            s.submission_id
        FROM assignment a
        LEFT JOIN submission s
        ON a.assignment_id = s.assignment_id
        AND s.student_id = %s
        WHERE a.class_id = %s
    """, (student_id, class_id))

    assignments = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        'student.html',
        notices=notices,
        events=events,
        assignments=assignments
    )

    

if __name__ == '__main__':
    app.run(debug=True)



