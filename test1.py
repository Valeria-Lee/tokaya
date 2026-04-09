print("paso 1: arrancando")

from dotenv import load_dotenv
print("paso 2: dotenv ok")

load_dotenv()
print("paso 3: env cargado")

import os
print("paso 4: DATABASE_URL =", os.environ.get("DATABASE_URL"))

from database.database import engine
print("paso 5: engine importado")

from database import Base
print("paso 6: Base importado")

print("paso 7: tablas registradas =", list(Base.metadata.tables.keys()))