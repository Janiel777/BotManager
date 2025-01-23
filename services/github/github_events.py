from services.github.github_actions import comment_on, set_issue_labels


def handle_github_event(event, payload, token, installation_id):
    if event == "issues":
        handle_issue_event(payload, token, installation_id)

def handle_issue_event(payload, token, installation_id):
    action = payload.get("action")
    if action == "opened":
        # issue_title = payload["issue"]["title"]
        # comments_url = payload["issue"]["comments_url"]
        set_issue_labels(payload, token)
        # message = f"¡Gracias por crear el issue '{issue_title}'! Nuestro bot está aquí para ayudarte. 🚀"
        # comment_on(comments_url, message, token)