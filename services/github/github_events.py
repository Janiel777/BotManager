from services.github.github_actions import comment_on, set_issue_labels


def handle_github_event(event, payload, token):
    if event == "issues":
        handle_issue_event(payload, token)

def handle_issue_event(payload, token):
    action = payload.get("action")
    if action == "opened":
        set_issue_labels(payload, token)