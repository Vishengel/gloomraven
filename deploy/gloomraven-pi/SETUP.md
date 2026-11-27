# Gloomraven on the Raspberry Pi

Runs next to the X-Haven server (see `../x-haven-pi/SETUP.md`), on the same Pi. The image is built by GitHub
Actions on every push to master (`ghcr.io/vishengel/gloomraven:latest`), so the Pi only needs this folder's
`compose.yaml` and a `.env`, no clone of the repo.

Both stacks are managed with [Dockge](https://github.com/louislam/dockge) (`http://<pi ip>:5001`, also as an
Android app), which keeps each stack in `/opt/stacks/<name>/`.

## 1. Create the stack

In Dockge: **+ Compose**, name it `gloomraven`, paste this folder's `compose.yaml`, and in the `.env` editor below it:

```
WIZ_BROADCAST_ADDRESS=192.168.178.255
```

- `WIZ_BROADCAST_ADDRESS`: the Pi's LAN broadcast address, shown as `brd` by `ip -4 addr`.
- Keep the name `gloomraven`: the data volume is named after the stack, so another name starts with an empty one.
- Pick the lights in the web UI. `LIGHTS` (see `.env.example`) is only used until a selection is saved there.

Without Dockge, the same by hand:

```bash
sudo mkdir -p /opt/stacks/gloomraven && cd /opt/stacks/gloomraven
sudo curl -fsSLO https://raw.githubusercontent.com/Vishengel/gloomraven/master/deploy/gloomraven-pi/compose.yaml
echo "WIZ_BROADCAST_ADDRESS=192.168.178.255" | sudo tee .env
```

## 2. Start it

**Deploy** in Dockge, or `docker compose pull && docker compose up -d` in `/opt/stacks/gloomraven`. The log is
in Dockge too.

The web UI is on `http://<pi ip>:4568`, from any PC or phone on the LAN. It has no login.

For Hue, change `command` in `compose.yaml` to `--sl_type hue --sl_ip <bridge ip>` and press the bridge's link
button just before the first start. The bridge login is kept in the `gloomraven-data` volume.

## Updating

**Update** in Dockge (pulls the latest image and restarts), or `docker compose pull && docker compose up -d` in
`/opt/stacks/gloomraven`.

To go back to an earlier build, replace `latest` in `compose.yaml` with that commit's full hash. When
`compose.yaml` itself changed in the repo, paste it into Dockge again.

## Things to know

- The container uses the host network: WiZ discovery broadcasts on the LAN, which a bridge network can't reach.
  It also makes the X-Haven server reachable on `127.0.0.1:4567`.
- What you set in the web UI (light selection, names, settings) is saved in the `gloomraven_gloomraven-data`
  volume, as `light_selection.json` and `settings.json`. It survives updates and reboots; only
  `docker compose down -v` deletes it.
- Stopping the stack restores the lights to how they were before the game.
- To see which lights are found, outside the web UI: stop the stack, then in `/opt/stacks/gloomraven`
  `docker compose run --rm gloomraven --list_lights --sl_type wiz`. Both use WiZ's UDP port, so not at the same time.
