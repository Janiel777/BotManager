from services.github.github_actions import comment_on, set_issue_labels, get_pull_request_details, \
    get_pull_request_files, get_open_issues_by_author, link_issue_to_pr
from services.openaiAPI.requests import generate_pr_prompt, get_pr_review_and_issue


def handle_github_event(event, payload, token):
    if event == "issues":
        handle_issue_event(payload, token)
    elif event == "pull_request":
        handle_pull_request_opened_event(payload, token)

def handle_issue_event(payload, token):
    action = payload.get("action")
    if action == "opened":
        set_issue_labels(payload, token)


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


    if related_issue:
        # Enlazar el Issue al Pull Request
        success = link_issue_to_pr(repo_owner, repo_name, pull_number, related_issue, token)
        if not success:
            print(f"Failed to link issue #{related_issue} to PR #{pull_number}.")
    else:
        print("No related issue identified.")

    if review_analysis:
        # Añadir análisis como comentario
        comment_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/issues/{pull_number}/comments"
        comment_on(comment_url, review_analysis, token)
