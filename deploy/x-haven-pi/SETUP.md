# X-Haven server on the Raspberry Pi

The X-Haven Assistant project ships an official headless server (a small Dart
program, no GUI) as a Docker image: `ghcr.io/tarmslitaren/x-haven-server`.
It is built for `linux/amd64` and `linux/arm64`, and listens on TCP port 4567.

## 0. Requirements (check these first)

- A 64-bit Pi OS. Run `uname -m` on the Pi: it must print `aarch64`.
  `armv7l` means a 32-bit OS (or an old Pi 2 / Zero), and the published image
  will not run. Pi 3, 4, 5 and Zero 2 W can all run 64-bit Raspberry Pi OS.
- Docker with the compose plugin:
  ```bash
  curl -fsSL https://get.docker.com | sh
  sudo usermod -aG docker $USER   # log out and back in afterwards
  docker compose version
  ```

## 1. Give the Pi a fixed address

Easiest and most robust: a **DHCP reservation** on your router. Find the Pi's
MAC address with `ip link show wlan0` (or `eth0` if wired), then in the
router's admin page reserve an address for it, e.g. `192.168.1.50`.
Reboot the Pi (or `sudo dhclient -r && sudo dhclient`) and check with
`hostname -I`.

Prefer wired Ethernet if possible: fewer drops mid-scenario.

(Alternative: a static IP on the Pi itself via `nmtui` on Bookworm. Then pick
an address outside the router's DHCP range so nothing else gets it.)

## 2. Start the server

```bash
mkdir -p ~/x-haven && cd ~/x-haven
# copy compose.yaml here
docker compose up -d
docker compose logs -f     # expect "Starting Server" / "Server Online"
```

`restart: unless-stopped` brings it back after a reboot.

Quick check from another machine on the wifi:
```bash
nc -vz 192.168.1.50 4567     # or: Test-NetConnection 192.168.1.50 -Port 4567
```

## 3. Connect the players

In the X-Haven app: Settings → connect as client, enter `192.168.1.50`
and port `4567`. Nobody needs to "host" any more; every device is a client.
The first device to connect pushes its game state; others then sync.

## 4. Updating

All players' apps must speak the same protocol as the server. When the app
updates, bump the tag in `compose.yaml` to the same version and run:
```bash
docker compose pull && docker compose up -d
```

## Things to know

- The server keeps the game state in memory only. Restarting the container
  forgets it, but the apps keep their own copy and the next action re-syncs.
- The server log shows an IPv6 address as "connect to" IP; ignore it and use
  the Pi's reserved IPv4 address.
- gloomraven connects the same way:
  `python -m gloomraven.main --gl_ip 192.168.1.50 ...` (port defaults to 4567).
