from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import hashlib
import hmac
import json
import sys
from urllib.parse import parse_qsl

app = Flask(__name__)
CORS(app)

BOT_TOKEN = "8661615931:AAHpeEYDJFpHYkH52aVyWhL0KGktGla3PuQ"
ADMIN_ID = 8592874278

pending_users = {}

def validate_init_data(init_data: str, bot_token: str):
    try:
        pairs = dict(parse_qsl(init_data, strict_parsing=True))
    except ValueError:
        return False, None

    received_hash = pairs.pop("hash", None)
    if not received_hash:
        return False, None

    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(pairs.items()))
    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    computed_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(computed_hash, received_hash):
        return False, None

    user_raw = pairs.get("user")
    user = json.loads(user_raw) if user_raw else None
    return True, user

@app.route('/verify', methods=['POST'])
def verify():
    data = request.get_json()
    init_data = data.get('initData')
    if not init_data:
        return jsonify({"error": "No initData"}), 400

    is_valid, user = validate_init_data(init_data, BOT_TOKEN)
    if not is_valid:
        return jsonify({"error": "Invalid signature"}), 403

    user_id = user.get('id')
    first_name = user.get('first_name', 'Без имени')
    username = user.get('username', 'без_юзернейма')

    pending_users[user_id] = {
    "status": "waiting",
    "first_name": first_name,
    "username": username,
    "user_agent": data.get('userAgent', 'неизвестно'),
    "screen": data.get('screen', 'неизвестно'),
    "timezone": data.get('timezone', 'неизвестно')
}

keyboard = {
    "inline_keyboard": [
        [{"text": "✅ Принять", "callback_data": f"accept_{user_id}"}],
        [{"text": "❌ Отклонить", "callback_data": f"reject_{user_id}"}]
    ]
}

admin_text = (
    f"✅ Новая верификация\n"
    f"👤 Имя: {first_name}\n"
    f"🔗 Username: @{username}\n"
    f"🆔 ID: {user_id}\n"
    f"📱 User-Agent: {pending_users[user_id]['user_agent']}\n"
    f"🖥 Экран: {pending_users[user_id]['screen']}\n"
    f"🌍 Часовой пояс: {pending_users[user_id]['timezone']}"
)

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": ADMIN_ID,
        "text": admin_text,
        "reply_markup": keyboard
    }

    # Логирование
    print("=== ОТПРАВКА АДМИНУ ===", flush=True)
    print(f"ADMIN_ID: {ADMIN_ID}", flush=True)
    print(f"Текст: {admin_text[:50]}...", flush=True)
    print(f"Клавиатура: {keyboard}", flush=True)

    response = requests.post(url, json=payload)

    print("=== ОТВЕТ TELEGRAM ===", flush=True)
    print(f"Статус: {response.status_code}", flush=True)
    print(f"Ответ: {response.text}", flush=True)

    return jsonify({"status": "ok"}), 200

@app.route('/')
def home():
    return "Сервер работает", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
