# conexion.py
import psycopg2

def conectar_bd():
    try:
        conn = psycopg2.connect(
            dbname="aula_virtual", 
            user="gabriel", 
            password="censorGT", # ¡No subir la clave real!
            host="localhost"
        )
        return conn, conn.cursor()
    except Exception as e:
        print("Error de conexión:", e)
        return None, None