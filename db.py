import sqlite3

DB_NAME = "fast_ride.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS viajes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        origen TEXT,
        destino TEXT,
        conductor TEXT,
        precio REAL,
        fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()


def guardar_viaje(user_id, origen, destino, conductor, precio):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
        INSERT INTO viajes (user_id, origen, destino, conductor, precio)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, str(origen), str(destino), conductor, precio))

    conn.commit()
    conn.close()


def obtener_historial(user_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("SELECT origen, destino, conductor, precio, fecha FROM viajes WHERE user_id=? ORDER BY id DESC LIMIT 10", (user_id,))
    rows = c.fetchall()

    conn.close()
    return rows
