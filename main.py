import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session
from db import db

app = Flask(__name__, template_folder='templates')
app.config['SECRET_KEY'] = 'secret'

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
