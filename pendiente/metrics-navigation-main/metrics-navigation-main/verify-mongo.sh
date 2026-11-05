#!/bin/bash
echo "=== Verificando MongoDB ==="

if command -v wslc &> /dev/null; then
    echo "Usando wslc..."
    CONTAINER=$(wslc list 2>/dev/null | grep mongo | awk '{print $1}' || echo "")
    if [ -n "$CONTAINER" ]; then
        echo "Contenedor mongo: $CONTAINER"
        wslc exec "$CONTAINER" bash -c "python3 -c 'import socket; s=socket.create_connection((\"localhost\",27017),timeout=2); print(\"MongoDB puerto 27017 abierto\"); s.close()' 2>/dev/null || echo 'Puerto 27017 no accesible'"
    else
        echo "⚠️ No hay contenedor mongo en wslc"
    fi
fi

echo "=== Verificación completa ==="
