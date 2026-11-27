# Gloomraven on the Raspberry Pi

Runs next to the X-Haven server (see `../x-haven-pi/SETUP.md`), on the same Pi.

## 1. Get the code and configure it

```bash
git clone https://github.com/Vishengel/gloomraven.git ~/gloomraven && cd ~/gloomraven
cp .env.example .env
nano .env
```

- `WIZ_BROADCAST_ADDRESS`: the Pi's LAN broadcast address, shown as `brd` by `ip -4 addr`.
- `LIGHTS`: the lights to control. Leave empty for all of them. To see what is found:
  ```bash
  cd deploy/gloomraven-pi
  docker compose run --rm gloomraven --list_lights --sl_type wiz
  ```

## 2. Start it

```bash
cd ~/gloomraven/deploy/gloomraven-pi
docker compose up -d --build
docker compose logs -f
```

For Hue, change `command` in `compose.yaml` to `--sl_type hue --sl_ip <bridge ip>` and press the bridge's link
button just before the first start. The bridge login is kept in the `gloomraven-data` volume.

## Things to know

- The container uses the host network: WiZ discovery broadcasts on the LAN, which a bridge network can't reach.
  It also makes the X-Haven server reachable on `127.0.0.1:4567`.
- The web UI is on `http://<pi ip>:4568`, from any PC or phone on the LAN. It has no login.
- `docker compose stop` restores the lights to how they were before the game.
- Updating: `git pull && docker compose up -d --build`.
