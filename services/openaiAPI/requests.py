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
        # Realiza la solicitud al modelo
        response = client.chat.completions.create(
            model="gpt-4",  # Asegúrate de que tienes acceso a este modelo
            messages=[
                {"role": "system", "content": "Eres un asistente útil para la gestión de issues en GitHub."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=150,
            temperature=0.7
        )

        # Extrae el contenido de la respuesta
        content = response.choices[0].message.content.strip()

        # Intenta convertir la respuesta a una lista de etiquetas
        suggested_labels = json.loads(content)

        if isinstance(suggested_labels, list):
            return suggested_labels
        else:
            raise ValueError("La respuesta no es una lista JSON válida.")

    except Exception as e:
        print(f"Error al obtener las etiquetas sugeridas: {e}")
        return []




def generate_pr_prompt(pr_details, pr_files, issue_titles):
    print(f"Estos son los issues del author: {issue_titles}")
    """
    Genera un prompt para enviar a ChatGPT basado en los detalles y cambios de un Pull Request
    y los títulos de los issues abiertos del creador del PR.
    """
    title = pr_details["title"]
    body = pr_details["body"]
    changes = ""

    for file in pr_files:
        changes += f"File: {file['filename']}\nDiff:\n{file['patch']}\n\n"

    prompt = f"""
    A Pull Request has been created with the following details:

    Title: {title}
    Description: {body}

    Here are the changes made in this Pull Request:
    {changes}

    Below are the titles of the open issues created by the same author:

    {', '.join(issue_titles)}

    Please perform the following tasks:
    1. Identify the issue to link to this pull request from the list of issues provided. There may be cases where no issues are related to the pull request, in which case null is returned.
    2. Review the changes in this Pull Request and provide a detailed analysis, including any potential improvements or issues.

    Response Format:
    Please make sure your response is valid JSON formatted exactly as below and DO NOT put the json inside a markdown block. But I do want you to use markdown but as part of the review_analysis value which is part of the json and will be treated as a str:
    {{
        "related_issue": <issue_number>,
        "review_analysis": "<your_detailed_analysis>"
    }}
    
    "related_issue" has to be an int or null. It must be one of the issue numbers passed in the list of issues. If the list is empty or the issue numbers are not provided in it, null is returned in related_issue.
    "review_analysis" has to be str.
    
    """
    return prompt



def get_pr_review_and_issue(prompt):
    """
    Envía el prompt a ChatGPT para obtener una revisión del Pull Request
    y determinar el número del Issue relacionado.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert code reviewer and GitHub issue linker."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=1000,
            temperature=0.7
        )

        # Procesar la respuesta de ChatGPT
        content = response.choices[0].message.content.strip()
        print(f"ChatGPT Response: {content}")

        # Detectar y eliminar delimitadores de bloques de código Markdown si están presentes
        if content.startswith("```json") and content.endswith("```"):
            content = content[7:-3].strip()  # Eliminar ```json al inicio y ``` al final
            print("Markdown delimiters detected and removed from response.")

        # Intentar cargar el JSON para extraer los datos necesarios
        response_data = json.loads(content)
        related_issue = response_data.get("related_issue")
        review_analysis = response_data.get("review_analysis")

        print(f"Related issue: {related_issue} isinstance(related_issue, int): {isinstance(related_issue, int)}")
        print(f"Review analysis: {review_analysis}  isinstance(review_analysis, str): {isinstance(review_analysis, str)} ")

        return related_issue if isinstance(related_issue, int) else None, review_analysis

    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        print("Error decoding JSON from ChatGPT response.")
    except Exception as e:
        print(f"Unexpected error: {e}")
    return None, None
