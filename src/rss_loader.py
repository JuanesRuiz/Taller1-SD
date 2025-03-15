import json
import os

def load_rss_sources():
    """Loads RSS sources from a JSON file and extracts only the URLs."""
    ruta = os.path.join(os.path.dirname(__file__), "../data/fuentes.json")
    
    with open(ruta, "r", encoding="utf-8") as file:
        sources = json.load(file)  # Load as a list of dictionaries
        return [source["url_rss"] for source in sources]  # Extract only URLs

# Test the function
if __name__ == "__main__":
    urls = load_rss_sources()
    print(urls)  # You should see a list of URLs in the console
