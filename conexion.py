# conexion.py
import psycopg2

def conectar_bd():
    try:
        conn = psycopg2.connect(
            dbname="aula_virtual", 
            user="postgres", 
            password="PON_TU_PASSWORD_AQUI", # ¡No subir la clave real!
            host="localhost"
        )
        return conn, conn.cursor()
    except Exception as e:
        print("Error de conexión:", e)
        return None, None