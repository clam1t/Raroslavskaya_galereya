from flask import Flask, render_template, request, redirect, url_for, session
from db import db
import qrcode
import jwt
import threading
import asyncio
from telegramm_bot import *
from io import BytesIO
import base64
import uuid
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__, template_folder='templates')
app.config['SECRET_KEY'] = 'secret'

def send_password_email(to_email, login_password):
	smtp_server = 'smtp.gmail.com'
	port = 587
	sender_email = "egorskurenkov391@gmail.com"
	password = "sgvf tpfb nxop lqbh"

	message = f"""
	Ваш пароль!
	{login_password}
	"""
	msg = MIMEMultipart()
	msg['From'] = sender_email
	msg['To'] = to_email
	msg['Subject'] = "Пароль от вашего аккаунта"

	msg.attach(MIMEText(message, 'plain'))

	try:
		server = smtplib.SMTP(smtp_server, port)
		server.starttls()
		server.login(sender_email, password)
		server.send_message(msg)
		server.quit()
		return True
	except Exception as e:
		print(f"Ошибка отправки email: {e}")
		return False

def send_ticket_email(to_email, payment_data):
	smtp_server = "smtp.gmail.com"
	port = 587
	sender_email = "egorskurenkov391@gmail.com"
	password = "sgvf tpfb nxop lqbh"

	message = f"""
    Благодарим за покупку!

    Ваши билеты:
    Дата посещения: {payment_data['date']}
    Количество билетов: {payment_data['quantity']}
    Сумма: {payment_data['total']} руб.

    Ваш QR-код для входа:
    """

	qr_data = {
		'text': f"Билет в галерею\nДата: {payment_data['date']}\nID: {payment_data['id']}",
	}
	qr_code = generate_qr_code(qr_data)

	msg = MIMEMultipart()
	msg['From'] = sender_email
	msg['To'] = to_email
	msg['Subject'] = "Ваши билеты в галерею"

	msg.attach(MIMEText(message, 'plain'))

	try:
		server = smtplib.SMTP(smtp_server, port)
		server.starttls()
		server.login(sender_email, password)
		server.send_message(msg)
		server.quit()
		return True
	except Exception as e:
		print(f"Ошибка отправки email: {e}")
		return False


def generate_qr_code(data):
	try:
		text = data.get('text', '')
		error_correction = data.get('error_correction', qrcode.constants.ERROR_CORRECT_L)
		box_size = data.get('box_size', 10)
		border = data.get('border', 4)

		qr = qrcode.QRCode(
			version=None,
			error_correction=error_correction,
			box_size=box_size,
			border=border,
		)
		qr.add_data(text)
		qr.make(fit=True)

		img = qr.make_image(fill_color=data.get('fill_color', 'black'), back_color=data.get('back_color', 'white'))

		buffered = BytesIO()
		img.save(buffered, format="PNG")
		img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")

		return img_str
	except Exception as e:
		return str(e)


@app.route('/')
@app.route('/yar_galery/')
@app.route('/yar_galery/home/')
def home():
	return render_template('home.html')

@app.route('/yar_galery/logout/')
def logout():
	session.clear()
	return redirect(url_for('home'))

@app.route('/yar_galery/buy_ticket/')
def buy_ticket():
	return render_template('buy_ticket.html')

@app.route('/yar_galery/process_payment/', methods=['POST'])
def process_payment():
	data = request.get_json()
	if not data:
		return {'error': 'Нет данных'}, 400

	payment_id = str(uuid.uuid4())[:8]
	user_email = session.get('user_email')

	if not user_email:
		return {'error': 'Пользователь не авторизован'}, 401

	payment_data = {
		'id': payment_id,
		'date': data['date'],
		'quantity': data['quantity'],
		'total': data['total'],
		'user_id': session.get('user_id'),
		'email': user_email,
		'status': 'pending'
	}

	result = db.add_payment(payment_data)
	if 'error' in result:
		return {'error': result['error']}, 500

	threading.Thread(target=send_payment_to_bot, args=(payment_data,)).start()

	return {'payment_id': payment_id, 'message': 'Платеж создан'}, 200


@app.route('/yar_galery/confirm_payment/', methods=['POST'])
def confirm_payment():
	data = request.get_json()
	payment_id = data.get('payment_id')
	status = data.get('status')

	current_status = db.check_payment(payment_id)

	if current_status and current_status == 'pending':
		db.update_payment_status(payment_id, status)

		if status == 'confirmed':
			payment = db.get_payment(payment_id)
			if payment:
				send_ticket_email(payment['email'], payment)
		return {'message': f'Платеж {status}'}, 200
	else:
		return {'error': 'Платеж не найден или уже обработан'}, 404


@app.route('/yar_galery/payment_status/<payment_id>')
def payment_status(payment_id):
	status = db.check_payment(payment_id)
	if status:
		return {'status': status}
	return {'status': 'pending'}

@app.route('/yar_galery/resetPassword/', methods=['GET','POST'])
def reset_Password():
	data = request.get_json()
	if not data:
		return {'error': 'Нет данных'}, 400
	first_name = data.get('first_name')
	second_name = data.get('last_name')
	email = data.get('email')
	if not all([first_name, second_name, email]):
		return {'error': 'Заполните все поля'}, 400
	password = db.get_user_password(first_name,second_name,email)
	if password:
		if send_password_email(email, password):
			return {'message': 'Пароль отправлен на почту'}, 200
		else:
			return {'error': 'Ошибка отправки письма'}, 500
	else:
		return {'error': 'Пользователь не найден'}, 404


@app.route('/yar_galery/register/', methods=['POST'])
def register():
	data = request.get_json()
	if not data:
		return {'error': 'Нет данных'}, 400
	first_name = data.get('first_name')
	second_name = data.get('last_name')
	password = data.get('password')
	email = data.get('email')
	if not all([first_name, second_name, password, email]):
		return {'error': 'Заполните все поля'}, 400
	result = db.add_user(first_name, second_name, email, password)

	if 'error' in result:
		return result, 400

	session['username'] = f"{first_name} {second_name}"
	session['user_id'] = result['id']
	session['user_email'] = email

	return {'message': 'Регистрация успешна'}, 200

@app.route('/yar_galery/login/', methods=['POST'])
def login():
	data = request.get_json()
	if not data:
		return {'error': 'Нет данных'}, 400
	first_name = data.get('first_name')
	second_name = data.get('last_name')
	password = data.get('password')
	if not all([first_name, second_name, password]):
		return {'error': 'Заполните все поля'}, 400

	user = db.get_user(first_name, second_name, password)
	if user:
		session['username'] = f"{first_name} {second_name}"
		session['user_id'] = user['id']
		session['user_email'] = user['email']
		return {'message': 'Вход выполнен'}, 200
	else:
		return {'error': 'Неверные данные'}, 401

def run_telegram_bot():
	bot.run()


if __name__ == '__main__':
	app.run(debug=True)
