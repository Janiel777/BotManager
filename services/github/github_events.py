from services.github.github_actions import comment_on, set_issue_labels, get_pull_request_details, \
    get_pull_request_files, get_open_issues_by_author, link_issue_to_pr, get_permissions_file, has_permission, \
    reopen_issue, close_issue
from services.openaiAPI.requests import generate_pr_prompt, get_pr_review_and_issue


def handle_github_event(event, payload, token):
    if event == "issues":
        handle_issue_event(payload, token)
    elif event == "pull_request":
        handle_pull_request_opened_event(payload, token)

def handle_issue_event(payload, token):
    """
    Maneja eventos relacionados con issues.
    :param payload: Datos del evento.
    :param token: Token de autenticación para la GitHub App.
    """
    action = payload.get("action")
    issue_number = payload.get("issue", {}).get("number")
    repo_owner = payload.get("repository", {}).get("owner", {}).get("login")
    repo_name = payload.get("repository", {}).get("name")
    username = payload.get("sender", {}).get("login")

    if not all([action, issue_number, repo_owner, repo_name, username]):
        print("Faltan datos en el payload para manejar el evento de issue.")
        return

    if action in ["closed", "reopened"]:
        # Manejar permisos para cerrar/reabrir issues
        print(f"Evento detectado: {action} issue #{issue_number} por {username}")
        handle_issue_permissions(repo_owner, repo_name, action, username, issue_number, token)

    elif action == "opened":
        # Etiquetar un issue recién creado
        set_issue_labels(payload, token)


def handle_issue_permissions(repo_owner, repo_name, action, username, issue_number, token):
    """
    Verifica los permisos de un usuario para cerrar o reabrir un issue.
    :param repo_owner: Dueño del repositorio.
    :param repo_name: Nombre del repositorio.
    :param action: Acción realizada (e.g., "closed", "reopened").
    :param username: Usuario que realizó la acción.
    :param issue_number: Número del issue.
    :param token: Token de autenticación para la GitHub App.
    """
    permissions = get_permissions_file(repo_owner, repo_name, token)

    if not permissions:
        print("No se pudo cargar el archivo de permisos. Abortando operación.")
        return

    allowed_users = permissions.get("allowed_users", [])
    allowed_users.append("janiel777-bot-manager[bot]")

    if username not in allowed_users:
        if action == "closed":
            print(f"Usuario {username} no tiene permisos para cerrar el issue #{issue_number}. Reabriendo...")
            reopen_issue(repo_owner, repo_name, issue_number, token)
        elif action == "reopened":
            print(f"Usuario {username} no tiene permisos para reabrir el issue #{issue_number}. Cerrando...")
            close_issue(repo_owner, repo_name, issue_number, token)
        print(f"Usuario {username} no tiene permisos para {action} el issue #{issue_number}.")

def handle_pull_request_opened_event(payload, token):
    """
    Maneja el evento de creación de un Pull Request.
    """
    action = payload.get("action")
    if action != "opened":
        return

    repo_owner = payload["repository"]["owner"]["login"]
    repo_name = payload["repository"]["name"]
    pull_number = payload["pull_request"]["number"]
    author = payload["pull_request"]["user"]["login"]

    # Obtener detalles y archivos del Pull Request
    pr_details = get_pull_request_details(repo_owner, repo_name, pull_number, token)
    pr_files = get_pull_request_files(repo_owner, repo_name, pull_number, token)
    if not pr_details or not pr_files:
        print("Failed to fetch PR details or files.")
        return

    # Obtener títulos de Issues abiertos creados por el autor del PR
    issue_titles = get_open_issues_by_author(repo_owner, repo_name, author, token)

    # Generar prompt para ChatGPT
    prompt = generate_pr_prompt(pr_details, pr_files, issue_titles)

    # Obtener el número del Issue relacionado y el análisis del PR
    related_issue, review_analysis = get_pr_review_and_issue(prompt)

    comment_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/issues/{pull_number}/comments"

    if related_issue:
        # Enlazar el Issue al Pull Request
        success = link_issue_to_pr(repo_owner, repo_name, pull_number, related_issue, token)
        if success:
            issue_linked_warning = (
                f"An issue has been linked to this Pull Request: **closes #{related_issue}**.\n\n"
                "Please verify that this is the correct issue. If it is not, you can:\n"
                "1. Modify the line `closes #{related_issue}` in the Pull Request description to the correct issue number.\n"
                "2. Remove the line entirely and manually link the issue using the menu on the right."
            )
            comment_on(comment_url, issue_linked_warning, token)
        else:
            print(f"Failed to link issue #{related_issue} to PR #{pull_number}.")
    else:
        print("No related issue identified.")
        not_issue_linked_warning = (
            f"Please check if you have any **issues assigned** related to this pull request.\n\n"
            "I looked through all of your open issue titles and it seems that either **I couldn't identify** any that relate to this pull request or **you don't have any issues assigned to you**."
        )
        comment_on(comment_url, not_issue_linked_warning, token)

    if review_analysis:
        # Añadir análisis como comentario
        comment_on(comment_url, review_analysis, token)
