import sqlite3

class database:
	def __init__(self):
		self.con = sqlite3.connect('database.db')
		with self.con as conn:
			conn.execute(
				'''CREATE TABLE IF NOT EXISTS tickets
				   (
					  id INTEGER PRIMARY KEY AUTOINCREMENT,
					  first_name TEXT,
					  last_name TEXT,
					  email TEXT,
					  date DATETIME,
					  qr_code TEXT
				   )
				''')
			conn.commit()
		with self.con as conn:
			conn.execute(
				'''CREATE TABLE IF NOT EXISTS users
					(
						id INTEGER PRIMARY KEY AUTOINCREMENT,
						first_name TEXT,
						last_name TEXT,
						password TEXT
					)
				''')



db = database()

