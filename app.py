from flask import Flask, request, jsonify, render_template, redirect, url_for

app = Flask(__name__)

# Route: Home
@app.route('/')
def home():
    return render_template('home.html', title="GitHub App Home", message="Welcome to the GitHub App!")

# Route: Callback
@app.route('/callback', methods=['GET'])
def callback():
    code = request.args.get('code')
    if not code:
        return jsonify({"error": "No code provided"}), 400
    # Process the OAuth code here (e.g., exchange it for an access token)
    return jsonify({"message": "Callback received", "code": code})

# Route: Setup
@app.route('/setup', methods=['GET', 'POST'])
def setup():
    if request.method == 'POST':
        # Handle setup logic here
        settings = request.form.to_dict()
        return jsonify({"message": "Setup completed", "settings": settings})
    return render_template('setup.html', title="GitHub App Setup")


@app.route('/webhook', methods=['POST'])
def webhook():
    event = request.headers.get("X-GitHub-Event", "ping")
    payload = request.json

    # Log básico para ver qué llega
    print(f"Event received: {event}")
    print(f"Payload: {payload}")

    if not payload:
        return jsonify({"error": "No payload provided"}), 400

    # Manejo de eventos específicos (como issues)
    if event == "issues":
        print("Issue event detected!")
        # Puedes añadir lógica específica aquí

    return jsonify({"message": f"Webhook received for event: {event}"}), 200

if __name__ == '__main__':
    app.run(debug=True)