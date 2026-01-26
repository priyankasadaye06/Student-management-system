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
            session['user_id'] = user['id']
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


# ---------------- TEACHER DASHBOARD ----------------
@app.route('/teacher')
def teacher_dashboard():
    if 'role' in session and session['role'] == 'teacher':
        return render_template('teacher.html')
    return redirect(url_for('login'))


# ---------------- STUDENT DASHBOARD ----------------
@app.route('/student')
def student_dashboard():
    if 'role' in session and session['role'] == 'student':
        return render_template('student.html')
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)

