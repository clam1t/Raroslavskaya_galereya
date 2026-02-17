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
					   email      TEXT,
					   password   TEXT
				   )
				''')
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


db = database()

