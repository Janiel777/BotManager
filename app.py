from flask import Flask, request, jsonify, render_template, redirect, url_for
import requests
import jwt
import time
import os

# Variables globales para el token y su expiración
installation_token = None
token_expiration = 0

def generate_jwt(app_id, private_key):
    """
    Genera un JWT para autenticar la GitHub App.

    Args:
        app_id (str): El ID de la GitHub App.
        private_key (str): La clave privada de la GitHub App en formato PEM.

    Returns:
        str: El JWT generado.
    """
    payload = {
        "iat": int(time.time()),
        "exp": int(time.time()) + (10 * 60),  # Expira en 10 minutos
        "iss": app_id,
    }

    return jwt.encode(payload, private_key, algorithm="RS256")

def get_or_create_installation_token(app_id, installation_id):
    """
    Obtiene un Installation Access Token, reutilizándolo si aún es válido.

    Args:
        app_id (str): El ID de la GitHub App.
        installation_id (int): El ID de la instalación.

    Returns:
        str: Un Installation Access Token válido.
    """
    global installation_token, token_expiration

    # Si el token aún es válido, lo reutilizamos
    if installation_token and time.time() < token_expiration:
        return installation_token

    # Obtén la Private Key desde las variables de entorno
    private_key = os.getenv("PRIVATE_KEY")
    if not private_key:
        print("Error: PRIVATE_KEY no está configurada en las variables de entorno.")
        return None

    # Genera un nuevo JWT
    jwt_token = generate_jwt(app_id, private_key)

    # Solicita el Installation Access Token
    url = f"https://api.github.com/app/installations/{installation_id}/access_tokens"
    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Accept": "application/vnd.github+json",
    }

    response = requests.post(url, headers=headers)

    if response.status_code == 201:
        installation_token = response.json().get("token")
        token_expiration = time.time() + 3600  # El token dura 1 hora
        return installation_token
    else:
        print(f"Error obteniendo el token: {response.status_code}, {response.json()}")
        return None

app = Flask(__name__)

# Route: Home
@app.route('/')
def home():
    return render_template('home.html', title="GitHub App Home", message="Welcome to the GitHub App!")

# Route: Callback
@app.route('/callback', methods=['GET'])
def callback():
    code = request.args.get('code')
    if not code:
        return jsonify({"error": "No code provided"}), 400
    # Process the OAuth code here (e.g., exchange it for an access token)
    return jsonify({"message": "Callback received", "code": code})

# Route: Setup
@app.route('/setup', methods=['GET', 'POST'])
def setup():
    if request.method == 'POST':
        # Handle setup logic here
        settings = request.form.to_dict()
        return jsonify({"message": "Setup completed", "settings": settings})
    return render_template('setup.html', title="GitHub App Setup")


def comment_on_issue(comments_url, message, token):
    """
    Publica un comentario en un issue.

    Args:
        comments_url (str): La URL de comentarios del issue.
        message (str): El mensaje a publicar como comentario.
        token (str): El token de instalación de la GitHub App.
    """
    # Configura los encabezados con el token de instalación
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json"
    }

    # Cuerpo de la solicitud
    data = {
        "body": message
    }

    # Realiza la solicitud POST para comentar en el issue
    response = requests.post(comments_url, json=data, headers=headers)

    # Verifica si el comentario fue exitoso
    if response.status_code == 201:
        print(f"Comentario publicado exitosamente en el issue: {comments_url}")
    else:
        print(f"Error al publicar el comentario: {response.status_code}, {response.json()}")

def handle_issue_event(payload, token):
    """
    Maneja el evento 'issues' para casos cuando un issue es creado.

    Args:
        payload (dict): El payload recibido del evento 'issues' de GitHub.
        token (str): El token de instalación de la GitHub App.
    """
    action = payload.get("action")
    if action == "opened":
        # Extraer información del issue
        issue_title = payload["issue"]["title"]
        comments_url = payload["issue"]["comments_url"]

        # Mensaje a comentar
        message = f"¡Gracias por crear el issue '{issue_title}'! Nuestro bot está aquí para ayudarte. 🚀"

        # Comentar en el issue usando la función `comment_on_issue`
        comment_on_issue(comments_url, message, token)


@app.route('/webhook', methods=['POST'])
def webhook():
    event = request.headers.get("X-GitHub-Event", "ping")
    payload = request.json

    # Verifica si hay payload
    if not payload:
        return jsonify({"error": "No payload provided"}), 400

    # Configura tu App ID (asegúrate de configurarla como variable de entorno también)
    app_id = os.getenv("GITHUB_APP_ID")
    if not app_id:
        print("Error: GITHUB_APP_ID no está configurada en las variables de entorno.")
        return jsonify({"error": "GITHUB_APP_ID no está configurada"}), 500

    installation_id = payload.get("installation", {}).get("id")

    # Obtén un token de instalación válido
    token = get_or_create_installation_token(app_id, installation_id)

    if not token:
        return jsonify({"error": "Failed to generate installation token"}), 500

    # Manejo de eventos específicos
    if event == "issues":
        print("Issue event detected!")
        handle_issue_event(payload, token)

    return jsonify({"message": f"Webhook received for event: {event}"}), 200

if __name__ == '__main__':
    app.run(debug=True)