from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import hashlib
import hmac
import json
from urllib.parse import parse_qsl

app = Flask(__name__)
CORS(app)  # Разрешает запросы из любого источника

BOT_TOKEN = "8661615931:AAHpeEYDJFpHYkH52aVyWhL0KGktGla3PuQ"
ADMIN_ID = 8592874278

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

    admin_text = (
        f"✅ Новая верификация\n"
        f"👤 Имя: {user.get('first_name', '')}\n"
        f"🔗 Username: @{user.get('username', '')}\n"
        f"🆔 ID: {user.get('id')}\n"
        f"📱 User-Agent: {data.get('userAgent', 'неизвестно')}\n"
        f"🖥 Экран: {data.get('screen', 'неизвестно')}\n"
        f"🌍 Часовой пояс: {data.get('timezone', 'неизвестно')}"
        f"🌐 IP-адрес: {data.get('ip', 'неизвестно')}"
    )

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": ADMIN_ID, "text": admin_text})

    return jsonify({"status": "ok"}), 200

@app.route('/')
def home():
    return "Сервер работает", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
