from flask import Flask, render_template, request, redirect, url_for, session
from db import db
import qrcode
import jwt
from io import BytesIO
import base64

app = Flask(__name__, template_folder='templates')
app.config['SECRET_KEY'] = 'secret'

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
	return render_template('home.html')



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
		return {'message': 'Вход выполнен'}, 200
	else:
		return {'error': 'Неверные данные'}, 401



if __name__ == '__main__':
	app.run(debug=True)
