from database import get_db, init_db

def create_dummy_students():
    init_db()
    conn = get_db()
    c = conn.cursor()

    # 10 demo students. Admin accounts should be created through signup.
    created = 0
    skipped = 0
    for i in range(1, 11):
        name = f'Student {i:03d}'
        c.execute('SELECT id FROM users WHERE name = ?', (name,))
        if not c.fetchone():
            c.execute('INSERT INTO users (name, password, role) VALUES (?, ?, ?)',
                      (name, 'student123', 'student'))
            created += 1
        else:
            skipped += 1

    conn.commit()
    conn.close()
    print(f"Students created: {created}, already existed: {skipped}")

if __name__ == '__main__':
    create_dummy_students()
