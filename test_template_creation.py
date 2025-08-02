import requests
import json
import time

def test_template_creation_and_status():
    """Prueba la creación de una plantilla y verifica su estado"""
    
    # URL base
    base_url = "http://localhost:8000"
    
    print("🧪 Probando creación y estado de plantillas...")
    
    # 1. Crear una nueva plantilla
    print("\n1️⃣ Creando nueva plantilla...")
    template_data = {
        "name": "Prueba Estado Plantilla",
        "content": "Esta es una plantilla de prueba para verificar el estado. Hola {{1}}!",
        "category": "UTILITY",
        "language": "es",
        "footer": "Agrojurado - Prueba de Estado"
    }
    
    try:
        create_response = requests.post(
            f"{base_url}/api/templates",
            json=template_data,
            headers={"Content-Type": "application/json"}
        )
        
        if create_response.status_code == 201:
            print("✅ Plantilla creada exitosamente")
            print(f"📄 Respuesta: {create_response.json()}")
        else:
            print(f"❌ Error al crear plantilla: {create_response.status_code}")
            print(f"📄 Respuesta: {create_response.text}")
            return
    except Exception as e:
        print(f"❌ Error en la creación: {e}")
        return
    
    # 2. Esperar un momento para que se procese
    print("\n2️⃣ Esperando 3 segundos para que se procese...")
    time.sleep(3)
    
    # 3. Obtener todas las plantillas para ver el estado
    print("\n3️⃣ Obteniendo plantillas para verificar estado...")
    try:
        templates_response = requests.get(f"{base_url}/api/templates")
        
        if templates_response.status_code == 200:
            templates_data = templates_response.json()
            print("✅ Plantillas obtenidas exitosamente")
            
            # Buscar nuestra plantilla de prueba
            found_template = None
            if 'templates' in templates_data:
                for template in templates_data['templates']:
                    if template.get('name') == "Prueba Estado Plantilla":
                        found_template = template
                        break
            
            if found_template:
                print(f"✅ Plantilla encontrada:")
                print(f"   📝 Nombre: {found_template.get('name')}")
                print(f"   📊 Estado: {found_template.get('status')}")
                print(f"   🏷️  Categoría: {found_template.get('category')}")
                print(f"   📄 Contenido: {found_template.get('content', 'N/A')}")
                
                # Verificar si tiene footer
                if 'components' in found_template:
                    for component in found_template['components']:
                        if component.get('type') == 'FOOTER':
                            print(f"   🦶 Footer: {component.get('text')}")
                            break
                
                # Mostrar todos los estados disponibles
                print(f"\n📊 Estados de todas las plantillas:")
                status_counts = {}
                for template in templates_data['templates']:
                    status = template.get('status', 'UNKNOWN')
                    status_counts[status] = status_counts.get(status, 0) + 1
                
                for status, count in status_counts.items():
                    print(f"   {status}: {count} plantilla(s)")
                    
            else:
                print("❌ No se encontró la plantilla de prueba")
                print("📄 Plantillas disponibles:")
                for template in templates_data.get('templates', []):
                    print(f"   - {template.get('name')} ({template.get('status')})")
        else:
            print(f"❌ Error al obtener plantillas: {templates_response.status_code}")
            print(f"📄 Respuesta: {templates_response.text}")
            
    except Exception as e:
        print(f"❌ Error al obtener plantillas: {e}")

if __name__ == "__main__":
    test_template_creation_and_status() 