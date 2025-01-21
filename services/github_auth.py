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
        payload (str): El payload recibido del webhook como una cadena JSON.
        signature (str): La firma enviada en el encabezado 'X-Hub-Signature-256'.

    Returns:
        bool: True si la firma es válida, False de lo contrario.
    """
    try:
        if not signature or not signature.startswith("sha256="):
            print("Firma ausente o formato inválido.")
            return False

        # Extraer la parte hash de la firma
        received_signature = signature.split("=")[1]

        # Asegúrate de que el secret esté codificado en bytes
        secret = WEBHOOK_SECRET.encode("utf-8")

        # Codifica el payload a bytes si es necesario
        if isinstance(payload, str):
            payload = payload.encode("utf-8")

        # Genera la firma usando HMAC y SHA256
        computed_signature = hmac.new(secret, payload, hashlib.sha256).hexdigest()

        # Imprime ambas firmas para depuración
        print(f"Firma recibida: {received_signature}")
        print(f"Firma calculada: {computed_signature}")
        print(f"Payload recibido: {payload}")
        print(f"WEBHOOK_SECRET: {WEBHOOK_SECRET}")

        # Compara las firmas usando compare_digest para evitar ataques de tiempo
        is_valid = hmac.compare_digest(received_signature, computed_signature)

        if not is_valid:
            print("Firma no válida.")
        return is_valid

    except Exception as e:
        print(f"Error al validar la firma: {e}")
        return False