import os

import openai
import json

from openai import OpenAI

# Inicializa el cliente OpenAI
client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY")  # Asegúrate de que la API Key esté configurada en las variables de entorno
)

def get_suggested_labels(issue_title, issue_body, predefined_labels):
    """
    Envía los detalles de un issue al API de OpenAI para obtener sugerencias de etiquetas.

    Args:
        issue_title (str): Título del issue.
        issue_body (str): Descripción del issue.
        predefined_labels (list): Lista de etiquetas existentes en el repositorio.

    Returns:
        list: Lista de etiquetas sugeridas por el modelo.
    """
    # Define el prompt
    prompt = f"""
    Based on the following issue details, suggest GitHub labels that best describe the issue.
    You may choose from the predefined labels below or suggest new ones if you think they are necessary.

    Title: {issue_title}
    Description: {issue_body}

    Predefined labels: {', '.join(predefined_labels)}

    If you suggest a new label, ensure it is concise, relevant, and follows common GitHub labeling practices.
    Return the labels as a JSON list.
    """

    try:
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a helpful assistant for managing GitHub issues."},
                {"role": "user", "content": prompt}
            ],
            model="gpt-4o",
            max_tokens=500,
            temperature=0.7
        )

        content = response["choices"][0]["message"]["content"]
        suggested_labels = json.loads(content)

        if isinstance(suggested_labels, list):
            return suggested_labels
        else:
            raise ValueError("The response is not a valid JSON list.")

    except Exception as e:
        print(f"Error while getting suggested labels: {e}")
        return []
