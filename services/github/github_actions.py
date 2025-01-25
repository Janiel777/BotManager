import json
from base64 import b64decode

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




def get_pull_request_details(repo_owner, repo_name, pull_number, token):
    """
    Obtiene los detalles de un Pull Request específico.
    """
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/pulls/{pull_number}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching PR details: {response.status_code}")
        return None



def get_pull_request_files(repo_owner, repo_name, pull_number, token):
    """
    Obtiene los archivos modificados en un Pull Request y su diff.
    """
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/pulls/{pull_number}/files"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching PR files: {response.status_code}")
        return None



def link_issue_to_pr(repo_owner, repo_name, pull_number, issue_number, token):
    """
    Enlaza un Issue a un Pull Request mencionándolo en la descripción del PR.

    Args:
        repo_owner (str): Propietario del repositorio.
        repo_name (str): Nombre del repositorio.
        pull_number (int): Número del Pull Request.
        issue_number (int): Número del Issue a enlazar.
        token (str): Token de acceso personal o de la aplicación.

    Returns:
        bool: True si la operación fue exitosa, False en caso contrario.
    """
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/pulls/{pull_number}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }

    # Obtener la descripción actual del PR
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Error al obtener el PR: {response.status_code}")
        return False

    pr_data = response.json()
    current_body = pr_data.get("body", "")

    # Añadir la referencia al Issue si no está ya presente
    issue_reference = f"Closes #{issue_number}"
    if issue_reference not in current_body:
        new_body = f"{current_body}\n\n{issue_reference}"
        data = {"body": new_body}

        # Actualizar el cuerpo del PR
        response = requests.patch(url, headers=headers, json=data)
        if response.status_code == 200:
            print(f"Issue #{issue_number} enlazado al PR #{pull_number} exitosamente.")
            return True
        else:
            print(f"Error al actualizar el PR: {response.status_code}")
            return False
    else:
        print("El Issue ya está referenciado en el PR.")
        return True



def get_open_issues_by_author(repo_owner, repo_name, author, token):
    """
    Obtiene los títulos y números de los Issues abiertos creados por el autor del Pull Request,
    excluyendo los Pull Requests.
    """
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/issues"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }
    params = {"state": "open", "creator": author}

    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        issues = response.json()
        # Filtrar para excluir los Pull Requests (que tienen el campo "pull_request")
        filtered_issues = [
            f"#{issue['number']}: {issue['title']}"
            for issue in issues
            if "pull_request" not in issue
        ]
        return filtered_issues
    else:
        print(f"Error fetching open issues: {response.status_code}")
        return []


def get_permissions_file(repo_owner, repo_name, token, file_path=".github/permissions.json"):
    """
    Obtiene el archivo JSON de permisos desde el repositorio usando la API de GitHub.
    :param repo_owner: Dueño del repositorio.
    :param repo_name: Nombre del repositorio.
    :param token: Token de autenticación para la GitHub App.
    :param file_path: Ruta del archivo JSON dentro del repositorio.
    :return: Diccionario con los permisos o None si el archivo no existe.
    """
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents/{file_path}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json"
    }

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        content = response.json()
        file_content = b64decode(content["content"]).decode("utf-8")
        return json.loads(file_content)
    else:
        print(f"Error al obtener el archivo de permisos: {response.status_code}")
        return None


def has_permission(username, permissions):
    """
    Verifica si un usuario tiene permisos para cerrar/reabrir issues.
    :param username: Nombre del usuario a verificar.
    :param permissions: Diccionario con los permisos obtenidos del archivo JSON.
    :return: True si el usuario tiene permisos, False en caso contrario.
    """
    if permissions:
        allowed_users = permissions.get("users_allowed_to_close_issues", [])
        return username in allowed_users
    else:
        print("No se pudo cargar el archivo de permisos.")
        return False


def reopen_issue(repo_owner, repo_name, issue_number, token):
    """
    Reabre un issue usando la API de GitHub.
    :param repo_owner: Dueño del repositorio.
    :param repo_name: Nombre del repositorio.
    :param issue_number: Número del issue.
    :param token: Token de autenticación para la GitHub App.
    """
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/issues/{issue_number}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json"
    }
    data = {"state": "open"}
    response = requests.patch(url, headers=headers, json=data)
    if response.status_code == 200:
        print(f"Issue #{issue_number} reabierto exitosamente.")
    else:
        print(f"Error al reabrir el issue #{issue_number}: {response.status_code}")


def close_issue(repo_owner, repo_name, issue_number, token):
    """
    Cierra un issue usando la API de GitHub.
    :param repo_owner: Dueño del repositorio.
    :param repo_name: Nombre del repositorio.
    :param issue_number: Número del issue.
    :param token: Token de autenticación para la GitHub App.
    """
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/issues/{issue_number}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json"
    }
    data = {"state": "closed"}
    response = requests.patch(url, headers=headers, json=data)
    if response.status_code == 200:
        print(f"Issue #{issue_number} cerrado exitosamente.")
    else:
        print(f"Error al cerrar el issue #{issue_number}: {response.status_code}")