import feedparser
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
from database import Database
from rss_loader import load_rss_sources
import multiprocessing
from urllib.parse import urlparse

DEFAULT_IMAGE = "https://via.placeholder.com/300x200?text=No+Image"

# Diccionario de logos de fuentes RSS conocidas
KNOWN_SITES_LOGOS = {
    "nytimes.com": "https://static01.nyt.com/images/icons/t_logo_291_black.png",
    "bbc.co.uk": "https://ichef.bbci.co.uk/images/ic/1200x675/p01tqv8z.jpg",
    "cnn.com": "https://cdn.cnn.com/cnn/.e/img/3.0/global/misc/cnn-logo.png",
    "elpais.com": "https://ep00.epimg.net/favicon/ep-favicon.ico",
}

def extract_image_from_html(news_url):
    """Extrae la imagen principal de una noticia desde su página HTML."""
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"}
        response = requests.get(news_url, headers=headers, timeout=5)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, "html.parser")

        # Método 1: OpenGraph (meta property="og:image")
        og_image = soup.find("meta", property="og:image")
        if og_image and og_image.get("content"):
            return og_image["content"]

        # Método 2: Buscar primera imagen en la página
        img_tag = soup.find("img")
        if img_tag and "src" in img_tag.attrs:
            return img_tag["src"]

    except requests.exceptions.RequestException as e:
        print(f"⚠️ Error extrayendo imagen de {news_url}: {e}")

    return None  # Retornar None si no se encontró imagen

def get_site_logo(rss_url):
    """Obtiene el logo del sitio de noticias basado en su dominio."""
    parsed_url = urlparse(rss_url)
    base_domain = parsed_url.netloc.replace("www.", "")

    # Si el sitio ya está en la lista de logos conocidos, usarlo
    if base_domain in KNOWN_SITES_LOGOS:
        return KNOWN_SITES_LOGOS[base_domain]

    # Intentar obtener el favicon del sitio
    favicon_url = f"{parsed_url.scheme}://{parsed_url.netloc}/favicon.ico"
    try:
        response = requests.get(favicon_url, timeout=5)
        if response.status_code == 200:
            return favicon_url  # Retornar el favicon si está disponible
    except requests.exceptions.RequestException:
        pass

    return DEFAULT_IMAGE  # Si todo falla, usar imagen por defecto

def fetch_news(rss_url):
    """Descarga y extrae noticias de una fuente RSS."""
    print(f"📡 Extrayendo noticias desde: {rss_url}")
    try:
        feed = feedparser.parse(rss_url)
        
        if not feed.entries:
            print(f"⚠️ Advertencia: No se encontraron noticias en {rss_url}")
            return []

        news = []
        site_logo = get_site_logo(rss_url)

        for entry in feed.entries:
            image_url = extract_image_from_html(entry.link) or site_logo  # Si no hay imagen, usar logo del sitio
            description = entry.summary if hasattr(entry, 'summary') else "Descripción no disponible."
            published = entry.published if hasattr(entry, 'published') else "Fecha desconocida"

            # Evitar almacenar noticias sin información importante
            if not entry.title or not description:
                print(f"⚠️ Noticia ignorada (incompleta) en {rss_url}")
                continue

            news.append({
                "title": entry.title,
                "published": published,
                "link": entry.link,
                "image": image_url,
                "description": description,
                "category": None  # No asignamos categoría aquí
            })

        print(f"✅ Extraídas {len(news)} noticias desde {rss_url}")
        return news

    except Exception as e:
        print(f"❌ Error al procesar {rss_url}: {e}")
        return []

def scrape_rss():
    """Ejecuta la extracción concurrente de noticias de todas las fuentes disponibles."""
    print("🚀 Cargando fuentes RSS...")
    sources = load_rss_sources()
    print(f"🌐 Se han cargado {len(sources)} fuentes")

    num_threads = max(2, multiprocessing.cpu_count() - 1)  # No usar menos de 2 hilos
    # num_threads = 5  # O cualquier número deseado

    print(f"🔄 Usando {num_threads} hilos para la extracción")

    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        results = executor.map(fetch_news, sources)

    news_list = [news for sublist in results for news in sublist]
    print(f"📊 Total de noticias extraídas: {len(news_list)}")

    if news_list:
        db = Database()
        db.insert_news(news_list)  # Insertar en la base de datos
        db.close()
        print("✅ Noticias almacenadas en la base de datos")
    else:
        print("⚠️ No se almacenaron noticias, revisa los feeds.")

if __name__ == "__main__":
    scrape_rss()
