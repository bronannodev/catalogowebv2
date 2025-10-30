import mysql.connector
from mysql.connector import errorcode

# Datos de conexión extraídos de tu URL de Railway
DB_CONFIG = {
    'user': 'root',
    'password': 'ywJenXppnjeMFeVCTuyaMLFbSyBipCWp',
    'host': 'yamanote.proxy.rlwy.net',
    'port': 38148,
    'database': 'avanti_catalog'
}

def get_db_connection():
    """Crea y devuelve una nueva conexión a la base de datos."""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Error: Usuario o contraseña de MySQL incorrectos")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("Error: La base de datos no existe")
        else:
            print(f"Error de conexión: {err}")
        return None