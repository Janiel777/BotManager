import requests

from services.github.github_auth import get_or_create_installation_token, generate_jwt
from services.openaiAPI.requests import get_suggested_labels


def get_installations():
    """
    Obtiene todas las instalaciones de la GitHub App y devuelve sus IDs.

    Returns:
        list: Una lista de objetos que contienen detalles de las instalaciones, incluidos los installation IDs.
    """
    try:
        # Genera un token JWT para autenticar la GitHub App

        jwt_token = generate_jwt()

        # Realiza la solicitud para obtener las instalaciones
        url = "https://api.github.com/app/installations"
        headers = {
            "Authorization": f"Bearer {jwt_token}",
            "Accept": "application/vnd.github+json",
        }

        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            installations = response.json()
            return installations
        else:
            print(f"Error al obtener las instalaciones: {response.status_code}, {response.json()}")
            return []

    except Exception as e:
        print(f"Error en la función get_installations: {e}")
        return []

def comment_on(comments_url, message, token):
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json"
    }
    data = {
        "body": message
    }
    response = requests.post(comments_url, json=data, headers=headers)
    if response.status_code == 201:
        print(f"Comentario publicado exitosamente en: {comments_url}")
    else:
        print(f"Error al publicar el comentario: {response.status_code}, {response.json()}")


def get_existing_labels_with_app(repo_owner, repo_name, installation_id):
    """
    Obtiene las etiquetas existentes en un repositorio de GitHub usando una GitHub App.

    Args:
        repo_owner (str): Nombre del propietario del repositorio (usuario u organización).
        repo_name (str): Nombre del repositorio.
        app_id (str): ID de la GitHub App.
        installation_id (str): ID de instalación de la GitHub App.
        private_key (str): Clave privada de la GitHub App.

    Returns:
        list: Lista de etiquetas existentes en el repositorio.
    """
    # Obtén el token de instalación
    token = get_or_create_installation_token(installation_id)

    if not token:
        print("Error: No se pudo obtener el token de instalación.")
        return []

    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/labels"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json"
    }

    try:
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            labels = response.json()
            # Extrae solo los nombres de las etiquetas
            return [label["name"] for label in labels]
        else:
            print(f"Error fetching labels: {response.status_code}, {response.json()}")
            return []
    except Exception as e:
        print(f"Error while fetching labels: {e}")
        return []

def set_labels(labels, url, token):
    """
    Establece etiquetas en un issue a través de la API de GitHub.

    Args:
        labels (list): Lista de etiquetas a establecer.
        url (str): URL para agregar etiquetas al issue.
        token (str): Token de instalación para autenticación.
    """
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json"
    }
    data = {"labels": labels}
    response = requests.post(url, json=data, headers=headers)

    if response.status_code == 200 or response.status_code == 201:
        print(f"Labels successfully added to the issue: {labels}")
    else:
        print(f"Error adding labels: {response.status_code}, {response.json()}")


def set_issue_labels(payload, token):
    """
        Maneja el evento de creación de un issue y realiza las acciones necesarias.

        Args:
            payload (dict): Payload recibido del webhook.
            token (str): Token de instalación para autenticación.
        """
    repo_owner = payload["repository"]["owner"]["login"]
    repo_name = payload["repository"]["name"]
    issue_title = payload["issue"]["title"]
    issue_body = payload["issue"]["body"]
    issue_number = payload["issue"]["number"]
    comments_url = payload["issue"]["comments_url"]

    # Obtén las etiquetas existentes del repositorio
    existing_labels = get_existing_labels_with_app(repo_owner, repo_name, token)

    # Obtén las etiquetas sugeridas de ChatGPT
    suggested_labels = get_suggested_labels(issue_title, issue_body, existing_labels)

    if not suggested_labels:
        message = "No suggested labels were generated for this issue."
        comment_on(comments_url, message, token)
        return

    # Agregar comentario en el issue con las etiquetas sugeridas
    labels_message = f"Suggested labels for this issue: {', '.join(suggested_labels)}"
    comment_on(comments_url, labels_message, token)

    # Envía las etiquetas al nuevo endpoint para establecerlas
    set_labels_endpoint = f"https://api.github.com/repos/{repo_owner}/{repo_name}/issues/{issue_number}/labels"
    set_labels(suggested_labels, set_labels_endpoint, token)