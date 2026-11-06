"""Codifica una contraseña para usarla dentro de una URI de MongoDB.

Uso:
    $env:MONGO_PASSWORD = "mi contraseña con @ : / ? # %"
    .venv\\Scripts\\python.exe scripts/encode_mongo_password.py

Copia el resultado y úsalo en el lugar de la contraseña dentro de la URI.
No imprime la URI completa.
"""
from __future__ import annotations

import os
import sys
from urllib.parse import quote


def main() -> int:
    password = os.getenv("MONGO_PASSWORD")
    if not password:
        print("Define MONGO_PASSWORD.")
        return 1
    print(quote(password, safe=""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
