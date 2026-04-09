from dotenv import load_dotenv
load_dotenv()

from robyn import Robyn
from routes import tokayo, minigame, inventory  # Importación correcta

app = Robyn(__file__)

@app.get("/")
def index():
    return "Hello World!"

# --- REGISTRO DE RUTAS ---
tokayo.register(app)
minigame.register(app)
inventory.register(app)  # <--- ESTA LÍNEA FALTABA

if __name__ == "__main__":
    app.start(host="0.0.0.0", port=9000)