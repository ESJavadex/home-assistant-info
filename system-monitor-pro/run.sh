#!/usr/bin/env bashio

# System Monitor Pro - Entrypoint Script

bashio::log.info "Starting System Monitor Pro..."

# Export MQTT configuration from Supervisor
if bashio::services.available "mqtt"; then
    export MQTT_HOST=$(bashio::services "mqtt" "host")
    export MQTT_PORT=$(bashio::services "mqtt" "port")
    export MQTT_USERNAME=$(bashio::services "mqtt" "username")
    export MQTT_PASSWORD=$(bashio::services "mqtt" "password")
    bashio::log.info "MQTT broker configured: ${MQTT_HOST}:${MQTT_PORT}"
else
    bashio::log.error "MQTT service not available! Please install and configure the Mosquitto broker add-on."
    exit 1
fi

# Export hostname for unique identifiers
export SYSTEM_HOSTNAME=$(hostname)
bashio::log.info "System hostname: ${SYSTEM_HOSTNAME}"

# Start the Python application
bashio::log.info "Launching monitoring service..."
exec python3 /app/main.py
