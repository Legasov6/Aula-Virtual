# Aula Virtual - Sistema de Gestión Académica

## Requisitos Previos
1. Python 3.10 o superior.
2. PostgreSQL (Servidor local).

## Instalación y Configuración
1. Clona este repositorio: `git clone <url-del-repo>`
2. Crea un entorno virtual y actívalo: `python -m venv venv`
3. Instala las dependencias: `pip install -r requerimientos.txt`
4. En pgAdmin o DBeaver, crea una base de datos llamada `aula_virtual`.
5. Ejecuta el script `db/esquema.sql` para crear las tablas.
6. (Opcional) Ejecuta `db/datos_prueba.sql` para poblar el sistema.
7. Abre `conexion.py` y coloca tu contraseña y usuario de PostgreSQL local.
8. Ejecuta el sistema: `python main.py`