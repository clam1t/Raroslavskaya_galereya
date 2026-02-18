import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import sqlite3
import requests
import json

BOT_TOKEN = "8461726174:AAGXypSgo1Z6oGSwFgL6KsO_hof8DLuF2HY"
ADMIN_CHAT_ID = "1749477245"
SITE_URL = "http://127.0.0.1:5000"


class PaymentBot:
    def __init__(self):
        self.application = Application.builder().token(BOT_TOKEN).build()
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CallbackQueryHandler(self.button_callback))

        self.init_db()

    def init_db(self):
        conn = sqlite3.connect('database.db')
        conn.execute('''
                     CREATE TABLE IF NOT EXISTS payment_responses
                     (
                         payment_id   TEXT PRIMARY KEY,
                         status       TEXT,
                         responded_at DATETIME DEFAULT CURRENT_TIMESTAMP
                     )
                     ''')
        conn.close()

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "Бот для подтверждения платежей запущен!\n"
            "Вы будете получать уведомления о новых платежах."
        )

    async def send_payment_notification(self, payment_data):
        """Отправка уведомления о новом платеже"""
        keyboard = [
            [
                InlineKeyboardButton("✅ Подтвердить", callback_data=f"confirm_{payment_data['id']}"),
                InlineKeyboardButton("❌ Отклонить", callback_data=f"reject_{payment_data['id']}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        message = (
            f"🔔 **Новый платеж**\n\n"
            f"📅 Дата: {payment_data['date']}\n"
            f"🎫 Количество билетов: {payment_data['quantity']}\n"
            f"💰 Сумма: {payment_data['total']} руб.\n"
            f"👤 Пользователь ID: {payment_data['user_id']}\n"
            f"📧 Email: {payment_data['email']}\n"
            f"🆔 Платеж ID: {payment_data['id']}"
        )

        await self.application.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=message,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )

    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик нажатий на кнопки"""
        query = update.callback_query
        await query.answer()

        data = query.data.split('_')
        action = data[0]
        payment_id = data[1]

        status = "confirmed" if action == "confirm" else "rejected"

        # Сохраняем ответ в локальную БД
        conn = sqlite3.connect('database.db')
        conn.execute(
            'INSERT OR REPLACE INTO payment_responses (payment_id, status) VALUES (?, ?)',
            (payment_id, status)
        )
        conn.commit()
        conn.close()

        # Отправляем подтверждение на сайт
        try:
            response = requests.post(
                'http://127.0.0.1:5000/yar_galery/confirm_payment/',
                json={
                    'payment_id': payment_id,
                    'status': status
                }
            )
            if response.ok:
                await query.edit_message_text(
                    text=f"{'✅' if status == 'confirmed' else '❌'} Платеж #{payment_id} {status}!"
                )
            else:
                await query.edit_message_text(
                    text=f"❌ Ошибка при обработке платежа #{payment_id}"
                )
        except Exception as e:
            await query.edit_message_text(
                text=f"❌ Ошибка соединения с сайтом: {str(e)}"
            )

    def run(self):
        """Запуск бота"""
        self.application.run_polling()


# Создаем экземпляр бота
bot = PaymentBot()


def send_payment_to_bot(payment_data):
    """Функция для отправки платежа в бота"""
    asyncio.run(bot.send_payment_notification(payment_data))


def check_payment_response(payment_id):
    """Функция для проверки ответа от бота"""
    conn = sqlite3.connect('bot_responses.db')
    cursor = conn.execute(
        'SELECT status FROM payment_responses WHERE payment_id = ?',
        (payment_id,)
    )
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None


if __name__ == "__main__":
    bot.run()