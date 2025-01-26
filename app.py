

import requests
from flask import Flask, request, jsonify, render_template

from services.github.github_actions import get_installations
from services.github.github_auth import get_or_create_installation_token, is_valid_signature
from services.github.github_events import handle_github_event
from config import CLIENT_ID, CLIENT_SECRET, db_handler, BASE_URL

callback_uri = f"{BASE_URL}/github/callback"

app = Flask(__name__)


def verificar_token(token):
    url = "https://api.github.com/user"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json"
    }
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        print("El token es válido.")
        print("Información del usuario:", response.json())
    else:
        print("El token no es válido o ha expirado.")
        print("Código de estado:", response.status_code)
        print("Respuesta:", response.json())


@app.route('/')
def home():
    return render_template('home.html', title="GitHub App Home", message="Welcome to the GitHub App!", redirect_uri=callback_uri, client_id=CLIENT_ID)

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
    # app_id = config.GITHUB_APP_ID
    # if not app_id:
    #     print("Error: GITHUB_APP_ID no está configurada en las variables de entorno.")
    #     return jsonify({"error": "GITHUB_APP_ID no está configurada"}), 500

    # Obtén el installation_id desde el payload
    installation_id = payload.get("installation", {}).get("id")
    # print("Installation id: ",installation_id)
    if not installation_id:
        return jsonify({"error": "No installation ID found in payload"}), 400

    # Genera el token de instalación
    token = get_or_create_installation_token(installation_id)
    if not token:
        return jsonify({"error": "Failed to generate installation token"}), 500

    # Maneja el evento específico
    handle_github_event(event, payload, token)
    return jsonify({"message": f"Webhook received for event: {event}"}), 200


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


@app.route("/github/callback", methods=["GET"])
def github_callback():
    # Obtener el código de autorización
    code = request.args.get("code")
    if not code:
        return jsonify({"error": "No se proporcionó un código de autorización."}), 400

    # Intercambiar el código por un token de acceso
    token_url = "https://github.com/login/oauth/access_token"
    headers = {"Accept": "application/json"}
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": code
    }
    response = requests.post(token_url, headers=headers, data=data)

    if response.status_code == 200:
        token_data = response.json()
        access_token = token_data.get("access_token")
        if access_token:
            # Obtener información del usuario con el token
            user_info_url = "https://api.github.com/user"
            user_headers = {
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json"
            }
            user_response = requests.get(user_info_url, headers=user_headers)

            if user_response.status_code == 200:
                user_info = user_response.json()
                username = user_info.get("login")
                if username:
                    # Guardar el token en la base de datos
                    db_handler.save_user_token(username, access_token)
                    return render_template("callback.html",
                                           message="Token received and saved successfully.",
                                           status_class="success",
                                           year=2025), 200
                else:
                    return render_template("callback.html",
                                       message="Could not get the user's username.",
                                       status_class="error",
                                       year=2025), 400
            else:
                return render_template("callback.html",
                                   message="Failed to get user information.",
                                   status_class="error",
                                   year=2025), 400
        else:
            return render_template("callback.html",
                               message="Access token not received.",
                               status_class="error",
                               year=2025), 400
    else:
        return render_template("callback.html",
                               message="Error getting access token.",
                               status_class="error",
                               year=2025), 400





if __name__ == '__main__':
    app.run(debug=True)