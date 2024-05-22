from flask import Flask, render_template, request, session, redirect, url_for
import os
import mysql.connector

app = Flask(__name__)

# MySQL Configuration
app.config['MYSQL_HOST'] = "localhost"
app.config['MYSQL_PORT'] = 3306
app.config['MYSQL_USER'] = "root"
app.config['MYSQL_PASSWORD'] = "Halo@1109"
app.config['MYSQL_DB'] = "feedback_db"
app.config['SECRET_KEY'] = os.urandom(24)

# Function to get a MySQL connection
def get_mysql_connection():
    return mysql.connector.connect(
        host=app.config['MYSQL_HOST'],
        port=app.config['MYSQL_PORT'],
        user=app.config['MYSQL_USER'],
        password=app.config['MYSQL_PASSWORD'],
        database=app.config['MYSQL_DB']
    )

# Define a decorator for checking if the user is logged in
def login_required(func):
    def wrapper(*args, **kwargs):
        if 'user_id' in session:
            return func(*args, **kwargs)
        else:
            return redirect(url_for('login'))
    return wrapper

@app.route('/')
def login():
    return render_template('loginpage.html')

@app.route('/submit', methods=['POST'])
def submit():
    if request.method == 'POST':
        Student = request.form['Student']
        Student_id = request.form['Student_id']
        Faculty = request.form['Faculty']
        Subject = request.form['Subject']
        rating = request.form['rating']
        comments = request.form['comments']

        if Student == '' or Faculty == '':
            return render_template('index.html', message='Please enter required fields')
        
        conn = get_mysql_connection()
        cur = conn.cursor()
        try:
            cur.execute("SELECT * FROM feedback WHERE Student_id = %s", (Student_id,))
            data = cur.fetchone()
            if data:
                return render_template('login.html', message='You have already submitted feedback')

            cur.execute("INSERT INTO feedback (Student_id, Student, Faculty, Subject, rating, comments) VALUES (%s, %s, %s, %s, %s, %s)", 
                        (Student_id, Student, Faculty, Subject, rating, comments))
            conn.commit()
            return render_template('success.html')
        except Exception as e:
            print(f"Error: {e}")
            conn.rollback()
            return render_template('index.html', message='An error occurred while submitting your feedback')
        finally:
            cur.close()
            conn.close()

@app.route('/admin-page')
@login_required
def admin_page():
    if session.get('user_type') == 'admin':
        conn = get_mysql_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM feedback")
        feedback_data = cur.fetchall()
        cur.close()
        conn.close()
        return render_template('admin.html', feedback=feedback_data)
    else:
        return redirect(url_for('student_page'))

# @app.route('/student-page')
# @login_required
# def student_page():
#     if session.get('user_type') == 'student':
#         return render_template('index.html')
#     else:
#         return redirect(url_for('admin_page'))

@app.route('/authenticate', methods=['GET','POST'])
def authenticate():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user_info = authenticate_user(username, password)

        if user_info:
            session['user_id'] = user_info['user_id']
            session['user_type'] = user_info['user_type']
            if user_info['user_type'] == 'admin':
                return redirect(url_for('admin_page'))
            else:
                return redirect(url_for('student_page'))
        else:
            return render_template('loginpage.html', message='Invalid username or password')

def authenticate_user(username, password):
    conn = get_mysql_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT user_id, user_type, password_hash FROM users WHERE username = %s", (username,))
    user = cur.fetchone()
    cur.close()
    conn.close()

    if user and verify_password(password, user['password_hash']):
        return {'user_id': user['user_id'], 'user_type': user['user_type']}
    return None

def verify_password(password, password_hash):
    import hashlib
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    return hashed_password == password_hash

if __name__ == '__main__':
    app.run(debug=True)
