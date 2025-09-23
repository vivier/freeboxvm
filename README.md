# freeboxvm

A command-line tool to manage and access virtual machines on a Freebox
via the Freebox OS API v8.

---

## Requirements

- Python 3.8+
- Freebox with Freebox OS v8 API
- Packages: `requests`, `websockets`, `tqdm`, `humanize`, `pygobject`
  (for **libosinfo** support)

Install with:

```bash
pip install -r requirements.txt
```

---

## Usage

### List VMs
```bash
freeboxvm list
```

Example:
```
ID      STATUS  NAME
0       running Debian-11
1       stopped Ubuntu-22.04
```

---

### Connect to a VM console
```bash
freeboxvm console [id|name]
```

- If no argument is provided, connects to the first running VM (or the first in
  the list).
- Exit with **Ctrl+C** or **Ctrl-A D**.
- Send a literal **Ctrl-A** to the VM with **Ctrl-A A**.

---

### Expose a VM screen via VNC proxy
```bash
freeboxvm vnc-proxy [options][id|name]
```

Exposes the VM’s VNC-over-WebSocket screen on a local TCP port for use
with any standard VNC client.

- If no argument is provided, connects to the first running VM (or the first in
  the list).
- `-l, --listen A` : Bind address (default `127.0.0.1`).
- `-p, --port P`   : Local TCP port (default `5901`).
- `--console`      : Run the interactive console in parallel with the
  VNC proxy.

Examples:
```bash
# Start a VNC proxy for the first running VM on localhost:5901
freeboxvm vnc-proxy

# Start proxy for VM id 12, binding on all interfaces, port 5902
freeboxvm vnc-proxy --listen 0.0.0.0 --port 5902 12

# Run proxy and console together
freeboxvm vnc-proxy --console
```

---

### Manage disk images
```bash
freeboxvm disk <action> [options] <args>
```

Manage VM disk images (create, resize, inspect, delete). Sizes accept
binary suffixes `k`, `m`, `g`, `t` (powers of two); raw bytes are also
accepted.

Actions:

- **create**
  ```bash
  freeboxvm disk create [--type qcow2] <path> <size>
  ```
  Create a new disk image (default type `qcow2`).

- **resize**
  ```bash
  freeboxvm disk resize [--shrink-allow] <path> <new-size>
  ```
  Resize an existing disk image. Use `--shrink-allow` to permit
  shrinking (can be destructive).

- **info**
  ```bash
  freeboxvm disk info <path>
  ```
  Display virtual size, actual space used, and type.

- **delete**
  ```bash
  freeboxvm disk delete <path>
  ```
  Delete a disk image.

Examples:
```bash
# Create a 10 GiB qcow2 image
freeboxvm disk create "/Disque 1/VMs/disk1.qcow2" 10g

# Grow a disk to 20 GiB
freeboxvm disk resize "/Disque 1/VMs/disk1.qcow2" 20g

# Allow destructive shrink to 8 GiB
freeboxvm disk resize --shrink-allow "/Disque 1/VMs/disk1.qcow2" 8g

# Show disk details
freeboxvm disk info "/Disque 1/VMs/disk1.qcow2"

# Delete a disk
freeboxvm disk delete "/Disque 1/VMs/disk1.qcow2"
```

---

### Power on a VM
```bash
freeboxvm poweron [id|name]
```

- Starts the specified VM.
- If no argument is provided, defaults to the first VM in the list.

---

### Power off a VM
```bash
freeboxvm poweroff [-f|--force] [id|name]
```

- Requests ACPI shutdown of the specified VM.
- With `-f`/`--force`, sends a hard stop instead.
- If no argument is provided, defaults to the first VM in the list.

---

### Reset a VM
```bash
freeboxvm reset [id|name]
```

- Restarts the specified VM.
- If no argument is provided, defaults to the first VM in the list.

---

### Display Freebox system info
```bash
freeboxvm system
```

- Shows overall Freebox resources:
  - Total and used memory
  - Total and used CPUs
  - USB allocation status
  - List of available USB ports

---

### List installable distributions
```bash
freeboxvm os-list [options]
```

Lists installable operating system images for VMs.

Options:
- `-e, --extra`: Query external sources via **libosinfo** for cloud-init images
  (aarch64, qcow2/raw).
- `-i, --iso`  : List installable ISOs instead of cloud images.
- `-l, --long` : Show detailed info (OS, distro, URL, checksum, live flag).
- `-c, --check`: Validate image and checksum URLs.
- `-o, --os`   : Filter results by OS name (e.g. `fedora`, `ubuntu`).

Examples:
```bash
# List all available distributions
freeboxvm os-list

# Show detailed info
freeboxvm os-list --long

# Validate URLs
freeboxvm os-list --check --long

# List installable ISOs
freeboxvm os-list --iso

# Filter by OS (e.g. only Fedora)
freeboxvm os-list --os fedora
```

---

### Download an image
```bash
freeboxvm download [options] [short-id]
```

Download a VM installation image (disk or ISO) using the Freebox Download Manager.

Options:
- `-i, --iso`        : Select an install ISO rather than a cloud/disk image.
- `-u, --url URL`    : Provide a direct URL instead of using a `short-id`.
- `-a, --hash HASH`  : Provide checksum URL when using `--url`.
- `-f, --filename F` : Filename to store the file.
- `-d, --directory D`: Freebox directory to store the file (base64 encoded automatically).
- `-b, --background` : Run download in background (progress not shown; check in Freebox "Téléchargements").

Examples:
```bash
# Download a Fedora cloud-init image by short-id
freeboxvm download fedora

# Download an Ubuntu ISO instead of a cloud image
freeboxvm download --iso ubuntu

# Provide a custom URL and checksum
freeboxvm download --url https://cloud-images.ubuntu.com/.../disk.qcow2 \
                   --hash https://cloud-images.ubuntu.com/.../SHA256SUMS

# Download in background mode
freeboxvm download --background fedora
```

---

## License

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <https://www.gnu.org/licenses/>.
