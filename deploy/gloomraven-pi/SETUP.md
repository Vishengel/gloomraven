# Gloomraven on the Raspberry Pi

Runs next to the X-Haven server (see `../x-haven-pi/SETUP.md`), on the same Pi. The image is built by GitHub
Actions on every push to master (`ghcr.io/vishengel/gloomraven:latest`), so the Pi only needs this folder's
`compose.yaml` and a `.env`, no clone of the repo.

## 1. Get the compose file and configure it

```bash
mkdir -p ~/gloomraven && cd ~/gloomraven
curl -fsSLO https://raw.githubusercontent.com/Vishengel/gloomraven/master/deploy/gloomraven-pi/compose.yaml
echo "WIZ_BROADCAST_ADDRESS=192.168.178.255" > .env
```

- `WIZ_BROADCAST_ADDRESS`: the Pi's LAN broadcast address, shown as `brd` by `ip -4 addr`.
- Pick the lights in the web UI. `LIGHTS` (see `.env.example`) is only used until a selection is saved there.

## 2. Start it

```bash
cd ~/gloomraven
docker compose pull && docker compose up -d
docker compose logs -f
```

The web UI is on `http://<pi ip>:4568`, from any PC or phone on the LAN. It has no login.

For Hue, change `command` in `compose.yaml` to `--sl_type hue --sl_ip <bridge ip>` and press the bridge's link
button just before the first start. The bridge login is kept in the `gloomraven-data` volume.

## Updating

```bash
cd ~/gloomraven
docker compose pull && docker compose up -d
```

To go back to an earlier build, replace `latest` in `compose.yaml` with that commit's full hash. When
`compose.yaml` itself changed, download it again with the `curl` command above.

## Things to know

- The container uses the host network: WiZ discovery broadcasts on the LAN, which a bridge network can't reach.
  It also makes the X-Haven server reachable on `127.0.0.1:4567`.
- What you set in the web UI (light selection, names, settings) is saved in the `gloomraven_gloomraven-data`
  volume, as `light_selection.json` and `settings.json`. It survives updates and reboots; only
  `docker compose down -v` deletes it.
- `docker compose stop` restores the lights to how they were before the game.
- To see which lights are found, outside the web UI: `docker compose stop`, then
  `docker compose run --rm gloomraven --list_lights --sl_type wiz`. Both use WiZ's UDP port, so not at the same time.
