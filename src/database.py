from pymongo import MongoClient

class Database:
    def __init__(self):
        """ Conectar a la base de datos MongoDB """
        try:
            self.client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=5000)
            self.db = self.client["news_db"]
            self.collection = self.db["news"]
            self.client.admin.command('ping')  
            print("✅ Conexión a MongoDB establecida correctamente.")
        except Exception as e:
            print(f"❌ Error de conexión a MongoDB: {e}")
            self.client = None

    def insert_news(self, news):
        """ Inserta noticias en la base de datos evitando duplicados """
        if not self.client:
            print("⚠️ No hay conexión a MongoDB. No se pueden insertar noticias.")
            return

        if not news:
            print("⚠️ No hay noticias para insertar.")
            return

        inserted_count = 0  # Contador de inserciones
        for new in news:
            if not self.collection.find_one({"link": new["link"]}):  # Evita duplicados
                self.collection.insert_one(new)
                inserted_count += 1

        print(f"✅ Se insertaron {inserted_count} noticias en la base de datos.")

    def get_news(self, category=None):
        """ Obtiene todas las noticias sin límite """
        if not self.client:
            print("⚠️ No hay conexión a MongoDB.")
            return []

        query = {}
        if category:
            query["category"] = category

        try:
            news_list = list(self.collection.find(query).sort("published", -1))
            print(f"🔍 Total de noticias encontradas en BD: {len(news_list)}")
            return news_list
        except Exception as e:
            print(f"❌ Error al obtener noticias de MongoDB: {e}")
            return []

    def close(self):
        """ Cierra la conexión con la base de datos """
        if self.client:
            self.client.close()
            print("🔌 Conexión a MongoDB cerrada.")
