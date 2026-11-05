"""Configuración global de las pruebas.

Se ejecuta antes de importar `app.main`, así la app de módulo (`app.main:app`)
no crea un archivo `data/devblog.db` durante pytest.
"""
import os

os.environ["CMS_DB_PATH"] = ":memory:"
