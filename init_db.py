import asyncio
import sys
from dotenv import load_dotenv
load_dotenv()

print("INICIO", flush=True)
sys.stdout.flush()

from database.database import engine
from database import Base

print("Tablas registradas:", list(Base.metadata.tables.keys()), flush=True)


async def main():
    print("Conectando...", flush=True)
    async with engine.begin() as conn:
        print("Conectado, creando tablas...", flush=True)
        await conn.run_sync(Base.metadata.create_all)
        print("create_all terminó", flush=True)
    print("✅ Tablas creadas", flush=True)
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())