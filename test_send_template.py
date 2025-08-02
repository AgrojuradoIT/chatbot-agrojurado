import os
from dotenv import load_dotenv
from services.whatsapp_service import send_whatsapp_template
import json

load_dotenv()

def test_send_template():
    # Número de prueba (reemplaza con un número real)
    test_number = "573016472138"  # Asegúrate de que este número esté en tu lista de contactos
    
    print(f"Enviando plantilla 'testeo' a {test_number}")
    
    result = send_whatsapp_template(
        to=test_number,
        template_name="testeo",
        parameters={}
    )
    
    if result:
        print("✅ Plantilla enviada exitosamente")
        print(json.dumps(result, indent=2))
    else:
        print("❌ Error al enviar plantilla")

if __name__ == "__main__":
    test_send_template() 