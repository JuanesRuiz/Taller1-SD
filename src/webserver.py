from flask import Flask, render_template, request
from database import Database
import os
import math

# Definir la ruta correcta de las plantillas
TEMPLATE_DIR = os.path.abspath("C:/Sistemas Distribuidos/DistNews/templates")

app = Flask(__name__, template_folder=TEMPLATE_DIR)

@app.route("/")
def index():
    category = request.args.get("category", "Todos")  # Obtener la categoría seleccionada (default: "Todos")
    page = int(request.args.get("page", 1))  # Obtener el número de página (default: 1)
    per_page = 20  # Máximo de noticias por página

    db = Database()

    # Filtrar noticias por categoría y paginar
    if category == "Todos":
        total_news = db.collection.count_documents({})
        news_cursor = db.collection.find().sort("published", -1).skip((page - 1) * per_page).limit(per_page)
    elif category == "General":
        total_news = db.collection.count_documents({"category": None})
        news_cursor = db.collection.find({"category": None}).sort("published", -1).skip((page - 1) * per_page).limit(per_page)
    else:
        total_news = db.collection.count_documents({"category": category})
        news_cursor = db.collection.find({"category": category}).sort("published", -1).skip((page - 1) * per_page).limit(per_page)

    total_pages = math.ceil(total_news / per_page)  # Calcular total de páginas

    # Convertir cursor a lista
    paginated_news = list(news_cursor)

    db.close()

    return render_template(
        "index.html",
        paginated_news=paginated_news,  # Enviar noticias paginadas
        selected_category=category,
        current_page=page,
        total_pages=total_pages
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

