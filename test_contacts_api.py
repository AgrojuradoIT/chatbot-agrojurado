import requests
import json
import time

def test_contacts_crud():
    """Prueba todas las operaciones CRUD de contactos"""
    
    base_url = "http://localhost:8000/api"
    
    print("🧪 Probando operaciones CRUD de contactos...")
    
    # Datos de prueba
    test_contact = {
        "phone_number": "573001234567",
        "name": "Juan Pérez"
    }
    
    updated_contact = {
        "name": "Juan Carlos Pérez",
        "is_active": False
    }
    
    # 1. Crear contacto
    print("\n1️⃣ Creando contacto de prueba...")
    try:
        create_response = requests.post(
            f"{base_url}/contacts",
            json=test_contact,
            headers={"Content-Type": "application/json"}
        )
        
        if create_response.status_code == 201:
            created_contact = create_response.json()
            print("✅ Contacto creado exitosamente")
            print(f"📄 Datos: {created_contact}")
        else:
            print(f"❌ Error al crear contacto: {create_response.status_code}")
            print(f"📄 Respuesta: {create_response.text}")
            return
    except Exception as e:
        print(f"❌ Error en la creación: {e}")
        return
    
    # 2. Obtener todos los contactos
    print("\n2️⃣ Obteniendo todos los contactos...")
    try:
        contacts_response = requests.get(f"{base_url}/contacts")
        
        if contacts_response.status_code == 200:
            contacts_data = contacts_response.json()
            print("✅ Contactos obtenidos exitosamente")
            print(f"📊 Total de contactos: {len(contacts_data.get('contacts', []))}")
            
            for contact in contacts_data.get('contacts', []):
                print(f"   - {contact['name']} ({contact['phone_number']}) - {'Activo' if contact['is_active'] else 'Inactivo'}")
        else:
            print(f"❌ Error al obtener contactos: {contacts_response.status_code}")
            print(f"📄 Respuesta: {contacts_response.text}")
    except Exception as e:
        print(f"❌ Error al obtener contactos: {e}")
    
    # 3. Obtener contacto específico
    print(f"\n3️⃣ Obteniendo contacto específico: {test_contact['phone_number']}")
    try:
        contact_response = requests.get(f"{base_url}/contacts/{test_contact['phone_number']}")
        
        if contact_response.status_code == 200:
            contact_data = contact_response.json()
            print("✅ Contacto específico obtenido exitosamente")
            print(f"📄 Datos: {contact_data}")
        else:
            print(f"❌ Error al obtener contacto específico: {contact_response.status_code}")
            print(f"📄 Respuesta: {contact_response.text}")
    except Exception as e:
        print(f"❌ Error al obtener contacto específico: {e}")
    
    # 4. Actualizar contacto
    print(f"\n4️⃣ Actualizando contacto: {test_contact['phone_number']}")
    try:
        update_response = requests.put(
            f"{base_url}/contacts/{test_contact['phone_number']}",
            json=updated_contact,
            headers={"Content-Type": "application/json"}
        )
        
        if update_response.status_code == 200:
            updated_data = update_response.json()
            print("✅ Contacto actualizado exitosamente")
            print(f"📄 Datos actualizados: {updated_data}")
        else:
            print(f"❌ Error al actualizar contacto: {update_response.status_code}")
            print(f"📄 Respuesta: {update_response.text}")
    except Exception as e:
        print(f"❌ Error al actualizar contacto: {e}")
    
    # 5. Verificar que se actualizó correctamente
    print(f"\n5️⃣ Verificando actualización...")
    try:
        verify_response = requests.get(f"{base_url}/contacts/{test_contact['phone_number']}")
        
        if verify_response.status_code == 200:
            verify_data = verify_response.json()
            print("✅ Verificación exitosa")
            print(f"📄 Datos verificados: {verify_data}")
            
            if verify_data['name'] == updated_contact['name'] and verify_data['is_active'] == updated_contact['is_active']:
                print("✅ Los datos se actualizaron correctamente")
            else:
                print("❌ Los datos no se actualizaron correctamente")
        else:
            print(f"❌ Error en la verificación: {verify_response.status_code}")
    except Exception as e:
        print(f"❌ Error en la verificación: {e}")
    
    # 6. Eliminar contacto
    print(f"\n6️⃣ Eliminando contacto: {test_contact['phone_number']}")
    try:
        delete_response = requests.delete(f"{base_url}/contacts/{test_contact['phone_number']}")
        
        if delete_response.status_code == 200:
            print("✅ Contacto eliminado exitosamente")
        else:
            print(f"❌ Error al eliminar contacto: {delete_response.status_code}")
            print(f"📄 Respuesta: {delete_response.text}")
    except Exception as e:
        print(f"❌ Error al eliminar contacto: {e}")
    
    # 7. Verificar que se eliminó
    print(f"\n7️⃣ Verificando eliminación...")
    try:
        final_response = requests.get(f"{base_url}/contacts/{test_contact['phone_number']}")
        
        if final_response.status_code == 404:
            print("✅ Contacto eliminado correctamente (no encontrado)")
        else:
            print(f"❌ El contacto aún existe: {final_response.status_code}")
    except Exception as e:
        print(f"❌ Error en la verificación final: {e}")
    
    print("\n🎉 Prueba de contactos completada!")

if __name__ == "__main__":
    test_contacts_crud() 