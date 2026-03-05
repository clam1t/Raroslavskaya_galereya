import sqlite3


class database:
    def __init__(self):
        conn = sqlite3.connect('database.db')
        with conn:
            conn.execute(
                '''CREATE TABLE IF NOT EXISTS tickets
                   (
                       id         INTEGER PRIMARY KEY AUTOINCREMENT,
                       first_name TEXT,
                       last_name  TEXT,
                       date       DATETIME,
                       qr_code    TEXT
                   )
				''')

            conn.execute(
                '''CREATE TABLE IF NOT EXISTS users
                   (
                       id         INTEGER PRIMARY KEY AUTOINCREMENT,
                       first_name TEXT,
                       last_name  TEXT,
                       email      TEXT UNIQUE,
                       password   TEXT
                   )
				''')

            conn.execute(
                '''CREATE TABLE IF NOT EXISTS payments
                   (
                       id       TEXT PRIMARY KEY,
                       date     DATETIME,
                       quantity INTEGER,
                       total    INTEGER,
                       user_id  INTEGER,
                       email    TEXT,
                       status   TEXT
                   )
				'''
            )
        conn.close()

    def get_connection(self):
        return sqlite3.connect('database.db')

    def get_user(self, first_name, last_name, password):
        conn = self.get_connection()
        try:
            cursor = conn.execute(
                'SELECT id, first_name, last_name, email '
                'FROM users '
                'WHERE first_name = ? AND last_name = ? AND password = ?',
                (first_name, last_name, password)
            )
            user = cursor.fetchone()
            if user:
                return {
                    'id': user[0],
                    'first_name': user[1],
                    'last_name': user[2],
                    'email': user[3]
                }
            return None
        finally:
            conn.close()

    def get_user_password(self,first_name,last_name,email):
        conn = self.get_connection()
        try:
            cursor = conn.execute(
                'SELECT password FROM users WHERE first_name = ? AND last_name = ? AND email = ?',(first_name,last_name,email)
            )
            password = cursor.fetchone()
            if password:
                return password[0]
            return  None
        finally:
            conn.close()

    def add_user(self, first_name, last_name, email, password):
        conn = self.get_connection()
        try:
            cursor = conn.execute(
                'INSERT INTO users (first_name, last_name, email, password) '
                'VALUES (?, ?, ?, ?)',
                (first_name, last_name, email, password)
            )
            conn.commit()
            return {'id': cursor.lastrowid, 'message': 'Пользователь успешно добавлен'}
        except sqlite3.IntegrityError:
            return {'error': 'Пользователь с таким email уже существует'}
        finally:
            conn.close()

    def add_payment(self, payment_data):
        conn = self.get_connection()
        try:
            cursor = conn.execute(
                'INSERT INTO payments (id, date, quantity, total, user_id, email, status) '
                'VALUES (?, ?, ?, ?, ?, ?, ?)',
                (
                    payment_data['id'],
                    payment_data['date'],
                    payment_data['quantity'],
                    payment_data['total'],
                    payment_data['user_id'],
                    payment_data['email'],
                    payment_data['status']
                )
            )
            conn.commit()
            return {'message': 'Платеж успешно добавлен'}
        except Exception as e:
            print(f"Ошибка добавления платежа: {e}")
            return {'error': str(e)}
        finally:
            conn.close()

    def check_payment(self, payment_id):
        conn = self.get_connection()
        try:
            cursor = conn.execute(
                'SELECT status FROM payments WHERE id = ?',
                (payment_id,)
            )
            result = cursor.fetchone()
            return result[0] if result else None
        except Exception as e:
            print(f"Ошибка проверки платежа: {e}")
            return None
        finally:
            conn.close()

    def update_payment_status(self, payment_id, status):
        conn = self.get_connection()
        try:
            conn.execute(
                'UPDATE payments SET status = ? WHERE id = ?',
                (status, payment_id)
            )
            conn.commit()
            return True
        except Exception as e:
            print(f"Ошибка обновления статуса: {e}")
            return False
        finally:
            conn.close()

    def get_payment(self, payment_id):
        conn = self.get_connection()
        try:
            cursor = conn.execute(
                'SELECT * FROM payments WHERE id = ?',
                (payment_id,)
            )
            payment = cursor.fetchone()
            if payment:
                return {
                    'id': payment[0],
                    'date': payment[1],
                    'quantity': payment[2],
                    'total': payment[3],
                    'user_id': payment[4],
                    'email': payment[5],
                    'status': payment[6]
                }
            return None
        finally:
            conn.close()


db = database()