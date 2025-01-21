from services.github_actions import comment_on_issue

def handle_github_event(event, payload, token):
    if event == "issues":
        handle_issue_event(payload, token)

def handle_issue_event(payload, token):
    action = payload.get("action")
    if action == "opened":
        issue_title = payload["issue"]["title"]
        comments_url = payload["issue"]["comments_url"]
        message = f"¡Gracias por crear el issue '{issue_title}'! Nuestro bot está aquí para ayudarte. 🚀"
        comment_on_issue(comments_url, message, token)