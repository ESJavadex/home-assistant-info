# System Monitor Pro - Multi-Architecture Dockerfile
# Supports: amd64, aarch64

ARG BUILD_FROM
FROM ${BUILD_FROM}

# Build arguments
ARG BUILD_ARCH
ARG BUILD_VERSION

# Labels for identification
LABEL \
    io.hass.name="System Monitor Pro" \
    io.hass.description="Comprehensive system monitoring add-on" \
    io.hass.arch="${BUILD_ARCH}" \
    io.hass.type="addon" \
    io.hass.version="${BUILD_VERSION}"

# Install system dependencies
RUN apk add --no-cache \
    python3 \
    py3-pip \
    py3-wheel \
    lm-sensors \
    procps \
    iproute2 \
    && rm -rf /var/cache/apk/*

# Install Python dependencies
COPY requirements.txt /tmp/requirements.txt
RUN pip3 install --no-cache-dir --break-system-packages -r /tmp/requirements.txt \
    && rm /tmp/requirements.txt

# Copy application code
COPY app /app
COPY run.sh /run.sh

# Set permissions
RUN chmod a+x /run.sh

# Set working directory
WORKDIR /app

# Entrypoint
ENTRYPOINT ["/run.sh"]
