# HP PhotoSmart B209a-m status to MQTT

## Usage in docker compose

```yaml
version: '3.2'
services:
  hp-to-mqtt:
    container_name: hp
    image: rzarajczyk/hp-to-mqtt:latest
    volumes:
      - ./config/hp-to-mqtt.yaml:/app/config.yaml
    restart: unless-stopped
```

## Configuration

```yaml
mqtt:
  broker: <hostname>
  port: <port>
  username: <username>
  password: <passqord>

fetch-interval-seconds: 600 # How often should the printer be checked 

hp:
  id: printer-scanner # how will the device be identified in MQTT
  url: <printer-ip>
```