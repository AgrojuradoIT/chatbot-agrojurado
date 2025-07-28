from dotenv import load_dotenv
load_dotenv()

from database import engine, Base
from models.whatsapp_models import WhatsappUser

def init_db():
    print("Eliminando y recreando la tabla de usuarios de WhatsApp...")
    # Esto eliminará la tabla existente y todos sus datos
    WhatsappUser.__table__.drop(engine, checkfirst=True)
    Base.metadata.create_all(bind=engine)
    print("¡Tabla recreada con el nuevo esquema!")

if __name__ == "__main__":
    init_db()