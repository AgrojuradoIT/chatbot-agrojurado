import os
from dotenv import load_dotenv
from services.whatsapp_service import get_whatsapp_templates, create_whatsapp_template, send_whatsapp_template
import json

load_dotenv()

def test_templates():
    print("=== Verificando plantillas existentes ===")
    templates = get_whatsapp_templates()
    
    if templates and templates.get('data'):
        print(f"Plantillas encontradas: {len(templates['data'])}")
        for template in templates['data']:
            print(f"- {template['name']} (Estado: {template['status']})")
    else:
        print("No se encontraron plantillas o hay un error con el token")
        
        # Intentar crear una plantilla de prueba
        print("\n=== Creando plantilla de prueba ===")
        result = create_whatsapp_template(
            name="test_bienvenida",
            content="Hola {{1}}, bienvenido a Agrojurado. ¿En qué podemos ayudarte?",
            category="UTILITY",
            language="es"
        )
        
        if result:
            print("Plantilla creada exitosamente:")
            print(json.dumps(result, indent=2))
        else:
            print("Error al crear plantilla")

if __name__ == "__main__":
    test_templates()