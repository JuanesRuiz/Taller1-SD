import json
import pymongo
import google.generativeai as genai
import time
from concurrent.futures import ThreadPoolExecutor
from database import Database

# Configurar la API de Gemini
GEMINI_API_KEY = "AIzaSyBu6qlVG5w2Fvol6dd7E3VpWutozq64Zfs"
genai.configure(api_key=GEMINI_API_KEY)

# Modelo de Gemini a usar
MODEL_NAME = "gemini-2.0-flash"

# Conectar a MongoDB
db = Database()
news_collection = db.collection

# Definir categorías válidas y prompt fijo
CATEGORIES = ["Política", "Economía", "Deportes", "Tecnología", "Opinión"]
PROMPT_FIJO = """
Clasifica la siguiente noticia en una de estas categorías: Política, Economía, Deportes, Tecnología u Opinión.
Devuelve solo la categoría exacta en formato JSON:
{"category": "Aquí la categoría"}
"""

def classify_news(news, retries=3, delay=5):
    """Clasifica una noticia con reintentos en caso de error."""
    attempt = 0
    while attempt < retries:
        try:
            model = genai.GenerativeModel(MODEL_NAME)
            response = model.generate_content(f"{PROMPT_FIJO}\n\nTítulo: {news['title']}")

            category = json.loads(response.text).get("category", "Opinión")
            if category not in CATEGORIES:
                category = "Opinión"  # Si no es una de las categorías esperadas, asignar "Opinión"

            # Actualizar la base de datos con la categoría asignada
            news_collection.update_one({"_id": news["_id"]}, {"$set": {"category": category}})
            return {"title": news["title"], "category": category, "status": "Success"}

        except Exception as e:
            print(f"⚠️ Error en intento {attempt + 1} al clasificar '{news['title']}': {e}")
            time.sleep(delay)  # Esperar antes de reintentar
            attempt += 1

    return {"title": news["title"], "error": "Fallo después de varios intentos", "status": "Error"}

def classify_news_batch(batch_size=50, max_workers=10):
    """Clasifica noticias cuya categoría es 'null' en paralelo con control de lotes."""
    news_items = list(news_collection.find({"category": None}, {"_id": 1, "title": 1}).limit(batch_size))
    
    if not news_items:
        print("✔ No hay noticias sin categoría para clasificar.")
        return []

    print(f"🔍 Clasificando {len(news_items)} noticias sin categoría...")

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(classify_news, news_items))

    # Contar éxitos y errores
    success_count = sum(1 for r in results if r["status"] == "Success")
    error_count = sum(1 for r in results if r["status"] == "Error")

    print(f"✅ Clasificación completada: {success_count} noticias clasificadas con éxito, {error_count} errores.")
    
    # Agregar mensaje final antes de cerrar la conexión
    print(f"📊 {success_count} Noticias clasificadas correctamente.")

    return results

if __name__ == "__main__":
    report = classify_news_batch()
    print(json.dumps(report, indent=4, ensure_ascii=False))
    db.close()
    print("🔌 Conexión a MongoDB cerrada.")
