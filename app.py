from flask import Flask, render_template, request, redirect, url_for
from telegram import Bot
import sqlite3
from datetime import datetime
import os

app = Flask(__name__)
bot = Bot(token="8071917672:AAG4R5z7b7w6PrOOLQ7Bi4nafMLy0LOL0I4")

# Chat IDs dos grupos
CHAT_ID_FREE = "-1002508674229"
CHAT_ID_VIP = "-1002600167995"

DATABASE = os.path.join(os.path.dirname(__file__), "database.db")

# Cria o banco de dados se não existir
def init_db():
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS mensagens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                texto TEXT,
                imagem TEXT,
                grupo TEXT,
                data_envio TEXT,
                status TEXT DEFAULT 'pendente'
            )
        ''')
        conn.commit()

init_db()  # Chama isso logo que o app inicia

@app.route('/')
def index():
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM mensagens ORDER BY id DESC")
        mensagens = cursor.fetchall()
    return render_template("index.html", mensagens=mensagens)

@app.route('/enviar', methods=['POST'])
def enviar():
    texto = request.form['texto']
    imagem = request.form['imagem']  # URL ou caminho local
    grupo = request.form['grupo']
    data_envio = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO mensagens (texto, imagem, grupo, data_envio) VALUES (?, ?, ?, ?)",
            (texto, imagem, grupo, data_envio)
        )
        conn.commit()
    return redirect(url_for('index'))

@app.route('/disparar/<int:mensagem_id>')
def disparar(mensagem_id):
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM mensagens WHERE id = ?", (mensagem_id,))
        mensagem = cursor.fetchone()

        if mensagem:
            id, texto, imagem, grupo, data_envio, status = mensagem
            chat_id = CHAT_ID_FREE if grupo == "free" else CHAT_ID_VIP

            try:
                if imagem:
                    if imagem.startswith("http://") or imagem.startswith("https://"):
                        bot.send_photo(chat_id=chat_id, photo=imagem, caption=texto)
                    else:
                        with open(imagem, 'rb') as img:
                            bot.send_photo(chat_id=chat_id, photo=img, caption=texto)
                else:
                    bot.send_message(chat_id=chat_id, text=texto)

                cursor.execute("UPDATE mensagens SET status = 'enviado' WHERE id = ?", (mensagem_id,))
                conn.commit()
            except Exception as e:
                return f"Erro ao enviar mensagem: {e}"

    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
