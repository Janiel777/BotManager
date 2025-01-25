from services.github.github_actions import comment_on, set_issue_labels, get_pull_request_details, \
    get_pull_request_files
from services.openaiAPI.requests import generate_pr_prompt, get_pr_review


def handle_github_event(event, payload, token):
    if event == "issues":
        handle_issue_event(payload, token)
    elif event == "pull_request":
        handle_pull_request_event(payload, token)

def handle_issue_event(payload, token):
    action = payload.get("action")
    if action == "opened":
        set_issue_labels(payload, token)


def handle_pull_request_event(payload, token):
    """
    Maneja el evento de creación de un Pull Request.
    """
    try:
        # Obtén los detalles del repositorio y del PR desde el payload
        repo_owner = payload["repository"]["owner"]["login"]
        repo_name = payload["repository"]["name"]
        pull_number = payload["pull_request"]["number"]
        comments_url = payload["pull_request"]["comments_url"]

        # Obtén los detalles del Pull Request
        pr_details = get_pull_request_details(repo_owner, repo_name, pull_number, token)
        if not pr_details:
            print("Error: No se pudieron obtener los detalles del Pull Request.")
            return

        # Obtén los archivos modificados en el Pull Request
        pr_files = get_pull_request_files(repo_owner, repo_name, pull_number, token)
        if not pr_files:
            print("Error: No se pudieron obtener los archivos del Pull Request.")
            return

        # Genera el prompt para enviar a ChatGPT
        prompt = generate_pr_prompt(pr_details, pr_files)

        # Envía el prompt a ChatGPT para obtener una revisión
        review = get_pr_review(prompt)

        # Publica un comentario en el Pull Request con la revisión
        comment_on(comments_url, review, token)

    except Exception as e:
        print(f"Error al manejar el evento de Pull Request: {e}")