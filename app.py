import requests
from flask import Flask, request, jsonify, render_template

from services.github.github_actions import get_installations
from services.github.github_auth import get_or_create_installation_token, is_valid_signature
from services.github.github_events import handle_github_event
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
    payload_raw = request.get_data()  # Obtén el payload en su forma cruda

    if not signature:
        return jsonify({"error": "Missing signature header"}), 403

        # Valida la firma del payload
    if not is_valid_signature(payload_raw, signature):
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
    print("Installation id: ",installation_id)
    if not installation_id:
        return jsonify({"error": "No installation ID found in payload"}), 400

    # Genera el token de instalación
    token = get_or_create_installation_token(app_id, installation_id)
    if not token:
        return jsonify({"error": "Failed to generate installation token"}), 500

    # Maneja el evento específico
    handle_github_event(event, payload, token)
    return jsonify({"message": f"Webhook received for event: {event}"}), 200



@app.route('/labels', methods=['GET'])
def get_labels():
    # Obtén el token de instalación
    app_id = config.GITHUB_APP_ID
    installation_id = request.args.get("installation_id")  # Espera el ID de instalación como parámetro
    repo = request.args.get("repo")  # Espera el nombre del repo como parámetro (formato: owner/repo)

    if not installation_id or not repo:
        return jsonify({"error": "Missing 'installation_id' or 'repo' parameter"}), 400

    token = get_or_create_installation_token(app_id, installation_id)
    if not token:
        return jsonify({"error": "Failed to generate installation token"}), 500

    # Llama al endpoint de GitHub para obtener los labels
    url = f"https://api.github.com/repos/{repo}/labels"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return jsonify(response.json()), 200
    else:
        return jsonify({
            "error": f"Failed to fetch labels: {response.status_code}",
            "details": response.json()
        }), response.status_code



@app.route('/installations', methods=['GET'])
def get_installations_endpoint():
    """
    Endpoint para devolver todos los installation IDs.
    """
    try:
        installations = get_installations()
        if installations:
            installations_list = [
                {"id": installation["id"], "account": installation["account"]["login"]}
                for installation in installations
            ]
            return jsonify({"installations": installations_list}), 200
        else:
            return jsonify({"error": "No installations found or an error occurred."}), 404
    except Exception as e:
        return jsonify({"error": f"An error occurred: {e}"}), 500



if __name__ == '__main__':
    app.run(debug=True)