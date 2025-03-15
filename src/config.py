import os

# Configuración de MongoDB
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DB_NAME = "distnews"

# Configuración de la API de Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyBoFmktBSoGnzTJid99DzID3rPkopK5LFs")

