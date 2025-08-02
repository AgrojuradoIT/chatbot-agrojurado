import requests
import json

def test_create_template():
    """Prueba la creación de una plantilla con formato correcto"""
    
    url = "http://127.0.0.1:8000/api/templates"
    
    # Plantilla de prueba con formato correcto
    template_data = {
        "name": "Bienvenida Agrojurado",
        "content": "¡Hola {{1}}! Bienvenido a Agrojurado. ¿En qué podemos ayudarte hoy?",
        "category": "UTILITY",
        "language": "es",
        "footer": "Agrojurado - Tu aliado en el campo"
    }
    
    print("🔄 Probando creación de plantilla...")
    print(f"URL: {url}")
    print(f"Data: {json.dumps(template_data, indent=2)}")
    
    try:
        response = requests.post(url, json=template_data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 201:
            print("✅ Plantilla creada exitosamente")
        else:
            print("❌ Error al crear plantilla")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def test_get_templates():
    """Prueba obtener las plantillas existentes"""
    
    url = "http://127.0.0.1:8000/api/templates"
    
    print("\n🔄 Obteniendo plantillas existentes...")
    
    try:
        response = requests.get(url)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Plantillas obtenidas exitosamente")
        else:
            print("❌ Error al obtener plantillas")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_create_template()
    test_get_templates() 