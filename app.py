import json

from flask import Flask, request, jsonify, render_template
from services.github_auth import get_or_create_installation_token, is_valid_signature
from services.github_events import handle_github_event
import config


app = Flask(__name__)

@app.route('/')
def home():
    return render_template('home.html', title="GitHub App Home", message="Welcome to the GitHub App!")

@app.route('/setup', methods=['GET', 'POST'])
def setup():
    if request.method == 'POST':
        settings = request.form.to_dict()
        return jsonify({"message": "Setup completed", "settings": settings})
    return render_template('setup.html', title="GitHub App Setup")

@app.route('/webhook', methods=['POST'])
def webhook():
    event = request.headers.get("X-GitHub-Event", "ping")
    payload = request.json
    signature = request.headers.get("X-Hub-Signature-256")
    payload_str = json.dumps(payload)

    if not signature:
        return jsonify({"error": "Missing signature header"}), 403

        # Valida la firma del payload
    if not is_valid_signature(payload_str, signature):
        return jsonify({"error": "Invalid signature"}), 403

    if not payload:
        return jsonify({"error": "No payload provided"}), 400

    # Configura tu App ID desde las variables de entorno
    app_id = config.GITHUB_APP_ID
    if not app_id:
        print("Error: GITHUB_APP_ID no está configurada en las variables de entorno.")
        return jsonify({"error": "GITHUB_APP_ID no está configurada"}), 500

    # Obtén el installation_id desde el payload
    installation_id = payload.get("installation", {}).get("id")
    if not installation_id:
        return jsonify({"error": "No installation ID found in payload"}), 400

    # Genera el token de instalación
    token = get_or_create_installation_token(app_id, installation_id)
    if not token:
        return jsonify({"error": "Failed to generate installation token"}), 500

    # Maneja el evento específico
    handle_github_event(event, payload, token)
    return jsonify({"message": f"Webhook received for event: {event}"}), 200

if __name__ == '__main__':
    app.run(debug=True)