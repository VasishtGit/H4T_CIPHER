#comment this out cutie pie
import psycopg2
from datetime import datetime

class DatabaseManager:
    def __init__(self):
        # Database credentials - update these after installing PostgreSQL
        self.params = {
            "dbname": "graph_solver",
            "user": "postgres",
            "password": "yourpassword",
            "host": "localhost"
        }

    def save_query(self, result_json):
        try:
            conn = psycopg2.connect(**self.params)
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO history (timestamp, solution) VALUES (%s, %s)",
                (datetime.now(), str(result_json))
            )
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            print(f"Database Error: {e}")