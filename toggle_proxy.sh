#!/bin/bash

# Configuración del proxy
PROXY_IP="127.0.0.1"
PROXY_PORT="8080"

# Obtener la configuración actual del proxy
CURRENT_PROXY=$(gsettings get org.gnome.system.proxy mode)

if [ "$CURRENT_PROXY" == "'manual'" ]; then
    # Desactivar el proxy
    gsettings set org.gnome.system.proxy mode 'none'
    echo "Proxy desactivado."
else
    # Activar el proxy
    gsettings set org.gnome.system.proxy mode 'manual'
    gsettings set org.gnome.system.proxy.http host "$PROXY_IP"
    gsettings set org.gnome.system.proxy.http port "$PROXY_PORT"
    echo "Proxy activado en $PROXY_IP:$PROXY_PORT."
fi
