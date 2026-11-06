"""Diagnóstico seguro de una cadena de MongoDB Atlas.

No imprime la contraseña. Uso:

    $env:CMS_MONGO_URI = "mongodb+srv://usuario:password@cluster.../..."
    .venv\\Scripts\\python.exe scripts/test_mongo_uri.py

También acepta MONGO_URI.
"""
from __future__ import annotations

import os
import sys

from pymongo import MongoClient
from pymongo.errors import ConfigurationError, OperationFailure, ServerSelectionTimeoutError
from pymongo.uri_parser import parse_uri


def main() -> int:
    uri = os.getenv("CMS_MONGO_URI") or os.getenv("MONGO_URI")
    if not uri:
        print("Define CMS_MONGO_URI o MONGO_URI.")
        return 1

    try:
        parsed = parse_uri(uri)
    except Exception as exc:
        print(f"URI mal formada: {exc}")
        return 1

    print("Usuario:", parsed.get("username"))
    print("Hosts:", parsed.get("nodelist"))
    print("Base de datos:", parsed.get("database"))
    options = {
        key: value
        for key, value in (parsed.get("options") or {}).items()
        if "password" not in key.lower()
    }
    print("Opciones:", options)

    client = None
    try:
        client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        print("Ping admin:", client.admin.command("ping"))

        for db_name in ("devblog_cms", "metrics"):
            try:
                client[db_name].command("dbstats")
                print(f"Base {db_name}: OK")
            except Exception as exc:
                print(f"Base {db_name}: ERROR -> {exc}")

        print("Conexión correcta.")
        return 0
    except OperationFailure as exc:
        print(f"OperationFailure: {exc}")
        if getattr(exc, "code", None) == 8000:
            print("=> bad auth: usuario/contraseña incorrectos o contraseña sin codificar.")
            print("   Codifica la contraseña con scripts/encode_mongo_password.py")
        return 1
    except ServerSelectionTimeoutError as exc:
        print(f"ServerSelectionTimeout: {exc}")
        print("=> Revisa Network Access (0.0.0.0/0), el hostname y que el clúster esté activo.")
        return 1
    except ConfigurationError as exc:
        print(f"ConfigurationError: {exc}")
        print("=> Revisa que la URI empiece con mongodb+srv:// y no tenga espacios ni comillas.")
        return 1
    finally:
        if client is not None:
            client.close()


if __name__ == "__main__":
    raise SystemExit(main())
