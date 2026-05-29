from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from database import get_db, init_db
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'presentation_rating_secret_key_2024')

RUBRIC_CRITERIA = [
    {
        'field': 'problem_clarity',
        'criterion': 'Problem Clarity',
        'question': 'Is the problem real, specific, and clearly articulated?',
        'weight': 25
    },
    {
        'field': 'market_potential',
        'criterion': 'Market Potential',
        'question': 'Is the market large enough? Is there willingness to pay?',
        'weight': 20
    },
    {
        'field': 'uniqueness_insight',
        'criterion': 'Uniqueness / Insight',
        'question': 'Is there a fresh angle or founder insight? Not a copy.',
        'weight': 20
    },
    {
        'field': 'feasibility',
        'criterion': 'Feasibility',
        'question': 'Can this be built and tested in 6 weeks with this cohort?',
        'weight': 15
    },
    {
        'field': 'pitch_delivery',
        'criterion': 'Pitch Delivery',
        'question': 'Was it clear, concise, and compelling? (60-sec discipline)',
        'weight': 10
    },
    {
        'field': 'work_interest',
        'criterion': 'Would I Work on This?',
        'question': 'Would you personally join this team for 6 weeks?',
        'weight': 10
    }
]

# ─── Helpers ──────────────────────────────────────────────────────────────────

def get_session_status():
    conn = get_db()
    row = conn.execute('SELECT * FROM session_status WHERE id = 1').fetchone()
    conn.close()
    return row

def require_admin():
    return session.get('role') == 'admin'

def require_student():
    return session.get('role') == 'student'

# ─── Public Routes ─────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        password = request.form.get('password', '').strip()
        conn = get_db()
        user = conn.execute(
            'SELECT * FROM users WHERE name = ? AND password = ? AND role = ?',
            (name, password, 'admin')
        ).fetchone()
        conn.close()
        if user:
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            session['role'] = 'admin'
            return redirect(url_for('admin_dashboard'))
        flash('Invalid admin credentials.', 'error')
    return render_template('admin_login.html')

@app.route('/student_login', methods=['GET', 'POST'])
def student_login():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        password = request.form.get('password', '').strip()
        conn = get_db()
        user = conn.execute(
            'SELECT * FROM users WHERE name = ? AND password = ? AND role = ?',
            (name, password, 'student')
        ).fetchone()
        conn.close()
        if user:
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            session['role'] = 'student'
            return redirect(url_for('student_rating'))
        flash('Invalid student credentials.', 'error')
    return render_template('student_login.html')

@app.route('/student_signup', methods=['GET', 'POST'])
def student_signup():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        role = 'student'

        if len(name) < 3:
            flash('Username must be at least 3 characters long.', 'error')
            return render_template('student_signup.html')
        if len(password) < 4:
            flash('Password must be at least 4 characters long.', 'error')
            return render_template('student_signup.html')
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('student_signup.html')
        conn = get_db()
        existing = conn.execute(
            'SELECT id FROM users WHERE LOWER(name) = LOWER(?)',
            (name,)
        ).fetchone()
        if existing:
            conn.close()
            flash('This username is already registered.', 'error')
            return render_template('student_signup.html')

        conn.execute(
            'INSERT INTO users (name, password, role) VALUES (?, ?, ?)',
            (name, password, role)
        )
        user_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
        conn.commit()
        conn.close()

        session['user_id'] = user_id
        session['user_name'] = name
        session['role'] = role
        flash('Signup successful. You are logged in now.', 'success')
        return redirect(url_for('student_rating'))

    return render_template('student_signup.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# ─── Admin Routes ──────────────────────────────────────────────────────────────

@app.route('/admin_dashboard')
def admin_dashboard():
    if not require_admin():
        return redirect(url_for('admin_login'))
    conn = get_db()
    total_students = conn.execute(
        'SELECT COUNT(*) as cnt FROM users WHERE role = "student"'
    ).fetchone()['cnt']
    completed_presentations = conn.execute(
        'SELECT COUNT(*) as cnt FROM presentations WHERE status = "closed"'
    ).fetchone()['cnt']
    status = conn.execute('SELECT * FROM session_status WHERE id = 1').fetchone()
    active_presentation = 'Yes' if status['is_active'] else 'No'
    pending_presentations = conn.execute('''
        SELECT COUNT(*) as cnt
        FROM users u
        WHERE u.role = 'student'
          AND NOT EXISTS (
              SELECT 1
              FROM presentations p
              WHERE p.presenter_id = u.id
          )
    ''').fetchone()['cnt']
    conn.close()
    return render_template('admin_dashboard.html',
                           user_name=session.get('user_name'),
                           total_students=total_students,
                           completed_presentations=completed_presentations,
                           active_presentation=active_presentation,
                           pending_presentations=pending_presentations)

@app.route('/manage_students')
def manage_students():
    if not require_admin():
        return redirect(url_for('admin_login'))
    conn = get_db()
    students = conn.execute(
        'SELECT id, name, role FROM users WHERE role = "student" ORDER BY name'
    ).fetchall()
    conn.close()
    return render_template('manage_students.html', students=students)

@app.route('/delete_student/<int:student_id>', methods=['POST'])
def delete_student(student_id):
    if not require_admin():
        return redirect(url_for('admin_login'))

    conn = get_db()
    student = conn.execute(
        'SELECT id, name FROM users WHERE id = ? AND role = "student"',
        (student_id,)
    ).fetchone()
    if not student:
        conn.close()
        flash('Student not found.', 'error')
        return redirect(url_for('manage_students'))

    status = conn.execute('SELECT * FROM session_status WHERE id = 1').fetchone()
    if status['is_active'] and status['current_presenter_id'] == student_id:
        conn.close()
        flash('Close this student\'s active presentation before deleting.', 'error')
        return redirect(url_for('manage_students'))

    presentation_ids = [
        row['id']
        for row in conn.execute(
            'SELECT id FROM presentations WHERE presenter_id = ?',
            (student_id,)
        ).fetchall()
    ]

    conn.execute('DELETE FROM ratings WHERE rater_id = ? OR presenter_id = ?', (student_id, student_id))
    if presentation_ids:
        placeholders = ','.join('?' for _ in presentation_ids)
        conn.execute(
            f'DELETE FROM ratings WHERE presentation_id IN ({placeholders})',
            presentation_ids
        )
    conn.execute('DELETE FROM presentations WHERE presenter_id = ?', (student_id,))
    conn.execute('DELETE FROM users WHERE id = ? AND role = "student"', (student_id,))
    conn.commit()
    conn.close()

    flash(f'Student {student["name"]} deleted successfully.', 'success')
    return redirect(url_for('manage_students'))

@app.route('/presentation_control')
def presentation_control():
    if not require_admin():
        return redirect(url_for('admin_login'))
    conn = get_db()
    status = conn.execute('SELECT * FROM session_status WHERE id = 1').fetchone()

    # Get all students with their latest presentation info.
    students = conn.execute('''
        SELECT
            u.id,
            u.name,
            COALESCE(p.status, 'not_presented') as pres_status,
            p.id as pres_id,
            COALESCE((
                SELECT COUNT(*)
                FROM ratings r
                WHERE r.presentation_id = p.id
            ), 0) as ratings_received,
            COALESCE((
                SELECT COUNT(*)
                FROM presentations p_count
                WHERE p_count.presenter_id = u.id
            ), 0) as presentation_count
        FROM users u
        LEFT JOIN presentations p ON p.id = (
            SELECT p_latest.id
            FROM presentations p_latest
            WHERE p_latest.presenter_id = u.id
            ORDER BY p_latest.id DESC
            LIMIT 1
        )
        WHERE u.role = 'student'
        ORDER BY u.name
    ''').fetchall()

    current_presenter = None
    ratings_received = 0
    if status['is_active'] and status['current_presenter_id']:
        current_presenter = conn.execute(
            'SELECT name FROM users WHERE id = ?', (status['current_presenter_id'],)
        ).fetchone()
        ratings_received = conn.execute(
            'SELECT COUNT(*) as cnt FROM ratings WHERE presentation_id = ?',
            (status['current_presentation_id'],)
        ).fetchone()['cnt']

    conn.close()
    return render_template('presentation_control.html',
                           status=status,
                           students=students,
                           current_presenter=current_presenter,
                           ratings_received=ratings_received)

@app.route('/start_presentation/<int:student_id>', methods=['POST'])
def start_presentation(student_id):
    if not require_admin():
        return redirect(url_for('admin_login'))

    conn = get_db()
    status = conn.execute('SELECT * FROM session_status WHERE id = 1').fetchone()

    if status['is_active']:
        flash('A presentation is already active. Close it before starting a new one.', 'error')
        conn.close()
        return redirect(url_for('presentation_control'))

    # Check student exists
    student = conn.execute('SELECT * FROM users WHERE id = ? AND role = "student"', (student_id,)).fetchone()
    if not student:
        flash('Student not found.', 'error')
        conn.close()
        return redirect(url_for('presentation_control'))

    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    conn.execute(
        'INSERT INTO presentations (presenter_id, status, started_at) VALUES (?, ?, ?)',
        (student_id, 'open', now)
    )
    pres_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
    conn.execute('''
        UPDATE session_status SET is_active = 1,
            current_presentation_id = ?,
            current_presenter_id = ?
        WHERE id = 1
    ''', (pres_id, student_id))
    conn.commit()
    conn.close()
    flash(f'Presentation started for {student["name"]}.', 'success')
    return redirect(url_for('presentation_control'))

@app.route('/close_presentation', methods=['POST'])
def close_presentation():
    if not require_admin():
        return redirect(url_for('admin_login'))

    conn = get_db()
    status = conn.execute('SELECT * FROM session_status WHERE id = 1').fetchone()

    if not status['is_active']:
        flash('No active presentation to close.', 'error')
        conn.close()
        return redirect(url_for('presentation_control'))

    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    conn.execute(
        'UPDATE presentations SET status = "closed", closed_at = ? WHERE id = ?',
        (now, status['current_presentation_id'])
    )
    conn.execute('''
        UPDATE session_status SET is_active = 0,
            current_presentation_id = NULL,
            current_presenter_id = NULL
        WHERE id = 1
    ''')
    conn.commit()
    conn.close()
    flash('Presentation closed successfully.', 'success')
    return redirect(url_for('presentation_control'))

@app.route('/admin_results')
def admin_results():
    if not require_admin():
        return redirect(url_for('admin_login'))

    top = request.args.get('top', 'all')

    conn = get_db()
    results = conn.execute('''
        SELECT p.id as presentation_id,
               u.name,
               ROUND(SUM(COALESCE(r.weighted_score, r.rating_score)), 2) as total_score,
               COUNT(r.id) as ratings_received,
               ROUND(CAST(SUM(COALESCE(r.weighted_score, r.rating_score)) AS FLOAT) / NULLIF(COUNT(r.id), 0), 2) as avg_score,
               p.started_at,
               p.closed_at,
               (
                   SELECT COUNT(*)
                   FROM presentations p_attempt
                   WHERE p_attempt.presenter_id = p.presenter_id
                     AND p_attempt.id <= p.id
               ) as attempt_no
        FROM presentations p
        JOIN users u ON u.id = p.presenter_id
        JOIN ratings r ON r.presentation_id = p.id
        WHERE p.status = 'closed'
        GROUP BY p.id, u.name, p.started_at, p.closed_at, p.presenter_id
        ORDER BY avg_score DESC, total_score DESC, u.name ASC
    ''').fetchall()
    conn.close()

    results = [dict(r) for r in results]
    for i, r in enumerate(results):
        r['rank'] = i + 1
        if r['avg_score'] is None:
            r['avg_score'] = 0.0

    if top == '10':
        results = results[:10]
    elif top == '20':
        results = results[:20]
    elif top == '30':
        results = results[:30]

    return render_template('admin_results.html', results=results, top=top)

@app.route('/api/ratings_count')
def ratings_count():
    if not require_admin():
        return jsonify({'error': 'Unauthorized'}), 403
    conn = get_db()
    status = conn.execute('SELECT * FROM session_status WHERE id = 1').fetchone()
    count = 0
    if status['is_active'] and status['current_presentation_id']:
        count = conn.execute(
            'SELECT COUNT(*) as cnt FROM ratings WHERE presentation_id = ?',
            (status['current_presentation_id'],)
        ).fetchone()['cnt']
    conn.close()
    return jsonify({'count': count, 'is_active': status['is_active']})

# ─── Student Routes ────────────────────────────────────────────────────────────

@app.route('/student_rating')
def student_rating():
    if not session.get('user_id'):
        return redirect(url_for('student_login'))
    if session.get('role') == 'admin':
        return redirect(url_for('admin_dashboard'))

    user_id = session['user_id']
    conn = get_db()
    status = conn.execute('SELECT * FROM session_status WHERE id = 1').fetchone()

    # No active presentation
    if not status['is_active']:
        conn.close()
        return render_template('student_waiting.html',
                               message='No active presentation right now. Please wait for the next presenter.',
                               user_name=session.get('user_name'))

    pres_id = status['current_presentation_id']
    presenter_id = status['current_presenter_id']

    # Fetch presentation status
    pres = conn.execute('SELECT * FROM presentations WHERE id = ?', (pres_id,)).fetchone()
    if not pres or pres['status'] != 'open':
        conn.close()
        return render_template('student_waiting.html',
                               message='Rating is closed. Please wait for the next presenter.',
                               user_name=session.get('user_name'))

    # Student is the presenter
    if user_id == presenter_id:
        presenter = conn.execute('SELECT name FROM users WHERE id = ?', (presenter_id,)).fetchone()
        conn.close()
        return render_template('student_waiting.html',
                               message='You are currently presenting. You cannot rate yourself.',
                               user_name=session.get('user_name'))

    # Already rated
    already = conn.execute(
        'SELECT id FROM ratings WHERE presentation_id = ? AND rater_id = ?',
        (pres_id, user_id)
    ).fetchone()
    if already:
        conn.close()
        return render_template('student_waiting.html',
                               message='Your rating has been submitted. Please wait for the next presenter.',
                               user_name=session.get('user_name'))

    presenter = conn.execute('SELECT name FROM users WHERE id = ?', (presenter_id,)).fetchone()
    conn.close()
    return render_template('student_rating.html',
                           presenter_name=presenter['name'],
                           presentation_id=pres_id,
                           user_name=session.get('user_name'),
                           rubric_criteria=RUBRIC_CRITERIA)

@app.route('/submit_rating', methods=['POST'])
def submit_rating():
    if not session.get('user_id'):
        return redirect(url_for('student_login'))
    if session.get('role') == 'admin':
        return redirect(url_for('admin_dashboard'))

    user_id = session['user_id']
    scores = {}
    try:
        for item in RUBRIC_CRITERIA:
            score = int(request.form.get(item['field'], ''))
            if not 1 <= score <= 5:
                raise ValueError
            scores[item['field']] = score
    except (TypeError, ValueError):
        flash('Invalid rating. Please score every rubric criterion from 1 to 5.', 'error')
        return redirect(url_for('student_rating'))

    weighted_score = round(
        sum(scores[item['field']] * item['weight'] for item in RUBRIC_CRITERIA) / 100 * 5,
        2
    )

    conn = get_db()
    status = conn.execute('SELECT * FROM session_status WHERE id = 1').fetchone()

    if not status['is_active']:
        flash('No active presentation.', 'error')
        conn.close()
        return redirect(url_for('student_waiting'))

    pres_id = status['current_presentation_id']
    presenter_id = status['current_presenter_id']

    pres = conn.execute('SELECT * FROM presentations WHERE id = ?', (pres_id,)).fetchone()
    if not pres or pres['status'] != 'open':
        flash('Rating is closed.', 'error')
        conn.close()
        return redirect(url_for('student_waiting'))

    if user_id == presenter_id:
        flash('You cannot rate yourself.', 'error')
        conn.close()
        return redirect(url_for('student_waiting'))

    already = conn.execute(
        'SELECT id FROM ratings WHERE presentation_id = ? AND rater_id = ?',
        (pres_id, user_id)
    ).fetchone()
    if already:
        flash('You have already submitted a rating for this presenter.', 'error')
        conn.close()
        return redirect(url_for('student_waiting'))

    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    conn.execute(
        '''
        INSERT INTO ratings (
            presentation_id,
            presenter_id,
            rater_id,
            rating_score,
            problem_clarity,
            market_potential,
            uniqueness_insight,
            feasibility,
            pitch_delivery,
            work_interest,
            weighted_score,
            submitted_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''',
        (
            pres_id,
            presenter_id,
            user_id,
            weighted_score,
            scores['problem_clarity'],
            scores['market_potential'],
            scores['uniqueness_insight'],
            scores['feasibility'],
            scores['pitch_delivery'],
            scores['work_interest'],
            weighted_score,
            now
        )
    )
    conn.commit()
    conn.close()
    return redirect(url_for('student_waiting', submitted='1'))

@app.route('/student_waiting')
def student_waiting():
    if not session.get('user_id'):
        return redirect(url_for('student_login'))
    if session.get('role') == 'admin':
        return redirect(url_for('admin_dashboard'))
    message = 'Please wait for the next presenter.'
    if request.args.get('submitted') == '1':
        message = 'Your rating has been submitted. Please wait for the next presenter.'
    return render_template('student_waiting.html',
                           message=message,
                           user_name=session.get('user_name'))

if __name__ == '__main__':
    init_db()
    app.run(
        host=os.environ.get('HOST', '0.0.0.0'),
        port=int(os.environ.get('PORT', 5000)),
        debug=os.environ.get('FLASK_DEBUG') == '1'
    )
