from pymongo import MongoClient
from cryptography.fernet import Fernet
from config import DB_USERNAME, DB_PASSWORD, ENCRYPTION_KEY
from urllib.parse import quote_plus

class MongoDBHandler:
    def __init__(self, uri, database_name, encryption_key):
        """
        Inicializa el manejador para conectarse a MongoDB y manejar tokens encriptados.
        """
        self.uri = uri
        self.database_name = database_name
        self.encryption_key = encryption_key
        self.cipher = Fernet(self.encryption_key)

    def _open_connection(self):
        """
        Abre la conexión a la base de datos.
        """
        self.client = MongoClient(self.uri)
        self.db = self.client[self.database_name]

    def _close_connection(self):
        """
        Cierra la conexión a la base de datos.
        """
        if hasattr(self, 'client'):
            self.client.close()

    def save_user_token(self, username, token):
        """
        Guarda un token de usuario en la base de datos, encriptado.
        """
        try:
            self._open_connection()
            encrypted_token = self.cipher.encrypt(token.encode())
            collection = self.db["user_tokens"]
            collection.update_one(
                {"username": username},
                {"$set": {"token": encrypted_token.decode()}},
                upsert=True
            )
        finally:
            self._close_connection()

    def get_user_token(self, username):
        """
        Recupera un token de usuario por su username, desencriptado.
        """
        try:
            self._open_connection()
            collection = self.db["user_tokens"]
            user_data = collection.find_one({"username": username})
            if user_data and "token" in user_data:
                user_data["token"] = self.cipher.decrypt(user_data["token"].encode()).decode()
            return user_data
        finally:
            self._close_connection()

    def delete_user_token(self, username):
        """
        Elimina el token de un usuario por su username.
        """
        try:
            self._open_connection()
            collection = self.db["user_tokens"]
            collection.delete_one({"username": username})
        finally:
            self._close_connection()


if __name__ == "__main__":
    # Codificar el nombre de usuario y la contraseña
    encoded_username = quote_plus(DB_USERNAME)
    encoded_password = quote_plus(DB_PASSWORD)
    # Configuración
    uri = f"mongodb+srv://{encoded_username}:{encoded_password}@cluster0.2gvpcdl.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
    database_name = "github-app-bot-manager"
    encryption_key = ENCRYPTION_KEY  # Genera una clave para pruebas. Usa una fija en producción.

    # Crear instancia de MongoDBHandler
    db_handler = MongoDBHandler(uri, database_name, encryption_key)

    # Probar guardado de token
    user_id = "12345"
    username = "test_user"
    token = "sample_token_abc123"
    print("Guardando token...")
    db_handler.save_user_token(user_id, username, token)
    print("Token guardado correctamente.")

    # Probar recuperación de token
    print("Recuperando token...")
    user_data = db_handler.get_user_token(user_id)
    if user_data:
        print(f"Datos recuperados: {user_data}")
    else:
        print("No se encontró el token del usuario.")

    # Probar eliminación de token
    print("Eliminando token...")
    db_handler.delete_user_token(user_id)
    print("Token eliminado correctamente.")

    # Verificar que el token fue eliminado
    print("Verificando eliminación...")
    user_data = db_handler.get_user_token(user_id)
    if not user_data:
        print("El token fue eliminado exitosamente.")
    else:
        print(f"Error: El token sigue existiendo: {user_data}")