import os
from dotenv import load_dotenv

# Cargar variables del archivo .env
load_dotenv()

# Variables de entorno necesarias
GITHUB_APP_ID = os.getenv("GITHUB_APP_ID")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")

# Valida que las variables esenciales estén configuradas
if not GITHUB_APP_ID or not PRIVATE_KEY:
    raise EnvironmentError(
        "Asegúrate de configurar GITHUB_APP_ID y PRIVATE_KEY en las variables de entorno."
    )