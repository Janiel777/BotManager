import requests

from services.github.github_auth import get_or_create_installation_token


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


def get_existing_labels_with_app(repo_owner, repo_name, app_id, installation_id, private_key):
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
    token = get_or_create_installation_token(app_id, installation_id)

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