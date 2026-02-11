import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session




app = Flask(__name__, template_folder='templates')
app.config['SECRET_KEY'] = 'secret'


DATABASE = 'database.db'
PASSWORD = 'Yarik228'

def init_db():
	with sqlite3.connect(DATABASE) as conn:
		conn.execute(
			'''CREATE TABLE IF NOT EXISTS qr_codes (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			title TEXT,
			signer TEXT,
			date TEXT,
			qr_code TEXT,
			file_hash TEXT,
			insert_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
			status_id INTEGER,
			note TEXT
			)
			''')
		conn.commit()

def save_qr_code(title, signer, date, qr_code_base64, note):
	with sqlite3.connect(DATABASE) as conn:
		conn.execute(
			'INSERT INTO qr_codes (title, signer, date, qr_code, note, status_id) VALUES (?, ?, ?, ?, ?, 1)',
			(title, signer, date, qr_code_base64, note)
		)
		conn.commit()