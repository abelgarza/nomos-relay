#!/usr/bin/env bash

# Resolve relative directory (handling symlinks)
DIR="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" && pwd)"

PROXY_SCRIPT="$DIR/proxy.js"
PROXY_PORT=11435
OPENCODE_BIN="/home/abelg/.opencode/bin/opencode"

# Función para limpiar el proxy al salir
cleanup() {
    echo -e "\n[Nomos] Deteniendo proxy..."
    pkill -f "node $PROXY_SCRIPT" 2>/dev/null
}

# 1. Comprobar si el proxy ya está activo
if ! lsof -i :$PROXY_PORT > /dev/null 2>&1; then
    echo "[Nomos] Iniciando proxy bajo demanda..."
    node "$PROXY_SCRIPT" > /tmp/nomos_proxy.log 2>&1 &
    
    # Esperar a que el puerto esté listo
    MAX_RETRIES=10
    COUNT=0
    while ! lsof -i :$PROXY_PORT > /dev/null 2>&1; do
        sleep 0.5
        ((COUNT++))
        if [ $COUNT -ge $MAX_RETRIES ]; then
            echo "[Error] El proxy no arrancó a tiempo. Revisa /tmp/nomos_proxy.log"
            exit 1
        fi
    done
    echo "[Nomos] Proxy listo."
    
    # Si nosotros lo arrancamos, nosotros lo cerramos al terminar opencode
    trap cleanup EXIT
else
    echo "[Nomos] El proxy ya estaba corriendo."
fi

# 2. Ejecutar OpenCode con los argumentos pasados
$OPENCODE_BIN "$@"
