from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3, os

app = Flask(__name__)
app.secret_key = 'student-erp-secret-key'
DB = 'student_erp.db'

def db():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con

def init_db():
    con = db()
    con.executescript('''
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        roll_no TEXT UNIQUE NOT NULL, name TEXT NOT NULL, email TEXT,
        course TEXT, semester TEXT, phone TEXT
    );
    CREATE TABLE IF NOT EXISTS attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER NOT NULL,
        date TEXT NOT NULL, status TEXT NOT NULL,
        FOREIGN KEY(student_id) REFERENCES students(id)
    );
    CREATE TABLE IF NOT EXISTS marks (
        id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER NOT NULL,
        subject TEXT NOT NULL, marks INTEGER NOT NULL,
        FOREIGN KEY(student_id) REFERENCES students(id)
    );
    CREATE TABLE IF NOT EXISTS notices (
        id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL,
        message TEXT NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    ''')
    if con.execute('SELECT COUNT(*) FROM students').fetchone()[0] == 0:
        con.execute("INSERT INTO students(roll_no,name,email,course,semester,phone) VALUES (?,?,?,?,?,?)",
                    ('CSE001','Mahesh Raut','mahesh@example.com','CSE (AI & ML)','2nd','9876543210'))
    if con.execute('SELECT COUNT(*) FROM notices').fetchone()[0] == 0:
        con.execute("INSERT INTO notices(title,message) VALUES (?,?)", ('Welcome','Student ERP is ready to use.'))
    con.commit(); con.close()

@app.route('/')
def dashboard():
    con=db()
    stats={
      'students':con.execute('SELECT COUNT(*) FROM students').fetchone()[0],
      'attendance':con.execute("SELECT COUNT(*) FROM attendance WHERE status='Present'").fetchone()[0],
      'marks':con.execute('SELECT COUNT(*) FROM marks').fetchone()[0],
      'notices':con.execute('SELECT COUNT(*) FROM notices').fetchone()[0]
    }
    notices=con.execute('SELECT * FROM notices ORDER BY id DESC LIMIT 5').fetchall(); con.close()
    return render_template('dashboard.html', stats=stats, notices=notices)

@app.route('/students', methods=['GET','POST'])
def students():
    con=db()
    if request.method=='POST':
        try:
            con.execute('INSERT INTO students(roll_no,name,email,course,semester,phone) VALUES (?,?,?,?,?,?)',
                tuple(request.form.get(k) for k in ['roll_no','name','email','course','semester','phone']))
            con.commit(); flash('Student added successfully.','success')
        except sqlite3.IntegrityError: flash('Roll number already exists.','error')
        con.close(); return redirect(url_for('students'))
    rows=con.execute('SELECT * FROM students ORDER BY id DESC').fetchall(); con.close()
    return render_template('students.html', students=rows)

@app.route('/attendance', methods=['GET','POST'])
def attendance():
    con=db()
    if request.method=='POST':
        con.execute('INSERT INTO attendance(student_id,date,status) VALUES(?,?,?)',
                    (request.form['student_id'],request.form['date'],request.form['status']))
        con.commit(); flash('Attendance saved.','success'); con.close(); return redirect(url_for('attendance'))
    students=con.execute('SELECT * FROM students').fetchall()
    rows=con.execute('''SELECT a.*,s.name,s.roll_no FROM attendance a JOIN students s ON s.id=a.student_id ORDER BY a.date DESC,a.id DESC''').fetchall()
    con.close(); return render_template('attendance.html',students=students,attendance=rows)

@app.route('/marks', methods=['GET','POST'])
def marks():
    con=db()
    if request.method=='POST':
        con.execute('INSERT INTO marks(student_id,subject,marks) VALUES(?,?,?)',
                    (request.form['student_id'],request.form['subject'],request.form['marks']))
        con.commit(); flash('Marks saved.','success'); con.close(); return redirect(url_for('marks'))
    students=con.execute('SELECT * FROM students').fetchall()
    rows=con.execute('SELECT m.*,s.name,s.roll_no FROM marks m JOIN students s ON s.id=m.student_id ORDER BY m.id DESC').fetchall()
    con.close(); return render_template('marks.html',students=students,marks=rows)

@app.route('/notices', methods=['GET','POST'])
def notices():
    con=db()
    if request.method=='POST':
        con.execute('INSERT INTO notices(title,message) VALUES(?,?)',(request.form['title'],request.form['message']))
        con.commit(); flash('Notice published.','success'); con.close(); return redirect(url_for('notices'))
    rows=con.execute('SELECT * FROM notices ORDER BY id DESC').fetchall(); con.close()
    return render_template('notices.html',notices=rows)

if __name__=='__main__':
    init_db(); app.run(debug=True)
