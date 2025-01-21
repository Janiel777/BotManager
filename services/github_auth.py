import jwt
import time
import requests
from config import GITHUB_APP_ID, PRIVATE_KEY, WEBHOOK_SECRET
import hmac
import hashlib

installation_token = None
token_expiration = 0

def generate_jwt():
    payload = {
        "iat": int(time.time()),
        "exp": int(time.time()) + (10 * 60),
        "iss": GITHUB_APP_ID,
    }
    return jwt.encode(payload, PRIVATE_KEY, algorithm="RS256")

def get_or_create_installation_token(app_id, installation_id):
    global installation_token, token_expiration

    if installation_token and time.time() < token_expiration:
        return installation_token

    jwt_token = generate_jwt()

    url = f"https://api.github.com/app/installations/{installation_id}/access_tokens"
    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Accept": "application/vnd.github+json",
    }

    response = requests.post(url, headers=headers)

    if response.status_code == 201:
        installation_token = response.json().get("token")
        token_expiration = time.time() + 3600
        return installation_token
    else:
        print(f"Error obteniendo el token: {response.status_code}, {response.json()}")
        return None


def is_valid_signature(payload, signature):
    """
    Valida la firma del webhook enviado por GitHub.

    Args:
        payload (bytes): El payload recibido del webhook.
        signature (str): La firma enviada en el encabezado 'X-Hub-Signature-256'.

    Returns:
        bool: True si la firma es válida, False de lo contrario.
    """
    computed_signature = "sha256=" + hmac.new(WEBHOOK_SECRET, payload, hashlib.sha256).hexdigest()

    return hmac.compare_digest(computed_signature, signature)