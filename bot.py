import telebot                        # бот телеграмм
from flask import Flask, request      # сервер для приема webhook
import os                             # обработка запроса
import smtplib                        # почта
from smtplib import SMTPException     # обработка ошибок
import logging                        # лог
import config                         # конфиг с токеном, почтами

from email.mime.text import MIMEText  # для корректности типа переменной письма
from email.header import Header       # для темы письма

bot = telebot.TeleBot(token=config.TOKEN)  # инициализация бота, передаем токен бота телеги
server = Flask(__name__, static_folder='')  # инициализация сервера Flask

logging.basicConfig(filename="bot.log",  # настройка лога
                    format='%(asctime)s: %(levelname)s - %(module)s - %(funcName)s - %(lineno)d - %(message)s',
                    level=logging.INFO)


@bot.message_handler(func=lambda message: message.text != '')  # обработчик любого сообщения
def handler(message):
    logging.info("Got \"" + message.text + "\" from " + message.from_user.id)  # лог сообщения
    if not (message.from_user.id in config.FROM_TG):  # проверка на пользователя
        return
    try:  # try except на ошибки smtp: соединение, логин, отправка
        s = smtplib.SMTP('smtp.gmail.com', 587)  # соединение с smtp сервером google
        s.starttls()  # запуск tls
        s.login(config.FROM_EMAIL, config.FROM_EMAIL_PASSWORD)  # логин с данными конфига

        msg = MIMEText(message.text, 'plain', 'utf-8')  # собираем тело письма - текст сообщения
        msg['Subject'] = Header(message.from_user.id, 'utf-8')  # тема письма - id пользователя telegram

        s.sendmail(config.FROM_EMAIL, config.TO_EMAIL, msg.as_string())  # отправка письма. Адресаты - согласно конфигу
        s.quit()  # выход из сессии
    except SMTPException as err:  # обработка ошибки, лог
        logging.error(err)


@server.route("/" + config.TOKEN, methods=["POST"])  # обработчик установленного хука в def setter():
def get_hook():  # распарсим запрос от бота. Сначала строку в utf, затем из json в нужный тип
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "!", 200


@server.route("/setter")  # установка webhook url для бота. Обращаемся по адрессу единожды.
def setter():
    logging.info("WEBHOOK SETUP")
    bot.remove_webhook()  # удалить
    bot.set_webhook(url=config.APP_URL + config.TOKEN)  # поставить хук
    return "!", 200


if __name__ == "__main__":  # в главной функции..
    logging.info("BOT STARTED")  # запишем в лог и запустим сервер на Flask
    server.run(host="0.0.0.0", port=int(os.environ.get('PORT', 8443)))
