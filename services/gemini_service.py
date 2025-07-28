import os
import google.generativeai as genai

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

model = genai.GenerativeModel('gemini-2.0-flash')

def generate_gemini_response(message: str):
    """
    Genera una respuesta utilizando el modelo Gemini.
    """
    try:
        response = model.generate_content(message)
        return response.text
    except Exception as e:
        print(f"Error al contactar la API de Google: {e}")
        return "Error al procesar tu mensaje."