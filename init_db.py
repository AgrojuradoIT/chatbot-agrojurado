from dotenv import load_dotenv
load_dotenv()

from database import engine, Base
from models.whatsapp_models import WhatsappUser, Template

def init_db():
    print("Eliminando y recreando las tablas de la base de datos...")
    # Esto eliminará las tablas existentes y todos sus datos
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("¡Tablas recreadas con el nuevo esquema!")

if __name__ == "__main__":
    init_db()