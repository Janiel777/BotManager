import requests

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