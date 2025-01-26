import os
from urllib.parse import quote_plus

from dotenv import load_dotenv

from services.mongoDB.db import MongoDBHandler

# Cargar variables del archivo .env
load_dotenv()

# Variables de entorno necesarias
GITHUB_APP_ID = os.getenv("GITHUB_APP_ID")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
WEBHOOK_SECRET=os.getenv("WEBHOOK_SECRET")
DB_USERNAME=os.getenv("DB_USERNAME")
DB_PASSWORD=os.getenv("DB_PASSWORD")
ENCRYPTION_KEY=os.getenv("ENCRYPTION_KEY")
CLIENT_ID=os.getenv("CLIENT_ID")
CLIENT_SECRET=os.getenv("CLIENT_SECRET")
ENV=os.getenv("ENV")
BASE_URL = "http://127.0.0.1:5000" if ENV == "local" else "https://git-app-bot-manager-00be1ee6bf4e.herokuapp.com/"

# Codificar el nombre de usuario y la contraseña
encoded_username = quote_plus(DB_USERNAME)
encoded_password = quote_plus(DB_PASSWORD)
# Configuración
uri = f"mongodb+srv://{encoded_username}:{encoded_password}@cluster0.2gvpcdl.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
database_name = "github-app-bot-manager"
encryption_key = ENCRYPTION_KEY
# Crear instancia de MongoDBHandler
db_handler = MongoDBHandler(uri, database_name, encryption_key)

# Valida que las variables esenciales estén configuradas
if not GITHUB_APP_ID or not PRIVATE_KEY:
    raise EnvironmentError(
        "Asegúrate de configurar GITHUB_APP_ID y PRIVATE_KEY en las variables de entorno."
    )