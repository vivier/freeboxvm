# freeboxvm

[![en](https://img.shields.io/badge/lang-en-blue.svg)](README.en.md)
[![fr](https://img.shields.io/badge/lang-fr-red.svg)](README.md)

A command-line tool to manage and access virtual machines on a Freebox
via the Freebox OS API v8.

---

## Requirements

- Python 3.8+
- Freebox with Freebox OS v8 API
- Packages: `requests`, `websockets`, `tqdm`, `humanize`, `PyGObject`
  (for **libosinfo** support)

Install with:

```bash
pip install .
```

To install dependencies without packaging metadata (for development or
legacy environments), use:


```bash
pip install -r requirements.txt
```

On Fedora you may also need:

```bash
sudo dnf install python3-gobject gobject-introspection libosinfo osinfo-db
```

On Debian/Ubuntu you may also need:

```bash
sudo apt install python3-gi gir1.2-libosinfo-1.0
```

---

## Usage

### List VMs
```bash
freeboxvm list [--long] [--usb-ports] [--disks] [--cloud-init]
```
- **Default output** shows: `ID  STATUS  NAME`.
- **--long** adds columns: `OS  MAC  VCPUs  MEMORY  DISPLAY`.
- **--usb-ports** prints bound USB ports (or "No USB ports").
- **--disks** prints disk image path/type and optional CD image path.
- **--cloud-init** prints cloud-init status, hostname and user-data.

Examples:
```bash
# Short view
freeboxvm list
ID  STATUS   NAME
0   running  Debian-11
1   stopped  Ubuntu-22.04

# Long view with USB ports
freeboxvm list --long --usb-ports
ID  STATUS   NAME        OS      MAC               VCPUs  MEMORY  DISPLAY
0   running  Debian-11   debian  aa:bb:cc:dd:ee:ff 2      2048    True
    USB ports: usb-external-type-a

# Disk and cloud-init details
freeboxvm list --disks --cloud-init
0   running  Debian-11
    Disk image: Disque 1/VMs/debian.qcow2 (qcow2)
    CD image: Disque 1/VMs/debian-11.iso
    Cloud-init hostname: debian
    Cloud-init user-data:
#cloud-config
system_info:
default_user:
- name: debian
```

---

### Show a single VM
```bash
freeboxvm show <id|name> [--long] [--usb-ports] [--disks] [--cloud-init]
```
Display information for a single VM. Supports the same optional flags as
`list`:

- **--long, -l**       : add OS, MAC, vCPUs, memory, display flag
- **--usb-ports, -u**  : show bound USB ports
- **--disks, -d**      : show disk image path/type and CD image
- **--cloud-init, -c** : show cloud-init status, hostname and user-data

Examples:
```bash
freeboxvm show 12
freeboxvm show Debian-11 --long
freeboxvm show 12 --disks --cloud-init
```

---

### Connect to a VM console
```bash
freeboxvm console <id|name>
```

- Exit with **Ctrl-A D**.
- Send a literal **Ctrl-A** to the VM with **Ctrl-A A**.
- Reset the VM with **Ctrl-A R**
- Halt the VM with **Ctrl-A H**
- Stop the VM with **Ctrl-A S**
- Display Ctrl-A help with **Ctrl-A ?**

Examples:
```bash
freeboxvm console 0
freeboxvm console Debian-11
```

---

### Expose a VM screen via VNC proxy
```bash
freeboxvm vnc-proxy [options] <id|name>
```

Exposes the VM’s VNC-over-WebSocket screen on a local TCP port for use
with any standard VNC client.

- `-l, --listen A` : Bind address (default `127.0.0.1`).
- `-p, --port P`   : Local TCP port (default `5901`).
- `--console`      : Run the interactive console in parallel with the
  VNC proxy.

Examples:
```bash
# Start a VNC proxy for VM id 0 on localhost:5901
freeboxvm vnc-proxy 0

# Start proxy for VM id 12, binding on all interfaces, port 5902
freeboxvm vnc-proxy --listen 0.0.0.0 --port 5902 12

# Run proxy and console together for a VM by name
freeboxvm vnc-proxy --console Debian-11
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

### Install a new VM
```bash
freeboxvm install [options]
```
Create and boot a new VM from either a cloud image or an install ISO.
Optionally attach the console and/or start a local VNC proxy.

Options:
- `-i, --install ID`             : distro short-id (see `os-list` or `--extra` for cloud-init images, `--iso` for ISOs)
- `-n, --name NAME`              : VM name
- `--os NAME`                    : OS name (if not inferred)
- `--vcpus N`                    : number of virtual CPUs
- `--memory N`                   : memory size in MiB
- `--disk PATH`                  : disk image path
- `--disk-size SIZE`             : disk size (accepts k/m/g/t suffixes or raw bytes)
- `--cdrom PATH`                 : ISO path (for installs from ISO)
- `--location URL`               : boot CD/image URL (mutually exclusive with `--cdrom`)
- `--cloud-init`                 : enable cloud-init
- `--cloud-init-hostname NAME`   : cloud-init hostname
- `--cloud-init-userdata FILE`   : cloud-init user-data file
- `--enable-screen`              : enable VM screen (VNC-over-WebSocket on Freebox)
- `-c, --console`                : attach console after boot
- `-v, --vnc-proxy`              : start VNC proxy after boot (requires `--enable-screen`)
- `-l, --listen ADDR`            : bind address for VNC proxy (default `127.0.0.1`)
- `-p, --port N`                 : TCP port for VNC proxy (default `5901`)
- `--usb-ports LIST`             : bind USB ports to the VM (comma-separated)

Notes:
- When `--install` or `--location` is provided, the image is downloaded
  via the Freebox Download Manager to the default directory `/Disque 1/VMs/`,
  with progress, checksum verification, and cleanup on error.
- For cloud images, the downloaded file becomes the VM disk image.
- If `--disk` points to a non-existent file, `--disk-size` must be provided
  so the tool can create the image (qcow2/raw type inferred by extension).
- Disks can be resized automatically if smaller than `--disk-size`.

Flow:
1. Resolve short-id or URL and download image if needed.
2. Create or resize the VM disk as required.
3. Configure VM properties (`--name`, `--os`, `--vcpus`, `--memory`).
4. Apply cloud-init if enabled.
5. POST `/vm/` to create, then `/vm/<id>/start` to boot.
6. Optionally attach console and/or start VNC proxy.

Examples:
```bash
# Install from a distro short-id as a cloud image, enable cloud-init, attach console
freeboxvm install -n Fedora-cloud --vcpus 1 --memory 512 --console   --cloud-init --cloud-init-hostname Fabulous   --cloud-init-userdata cloud-init-user-data.yaml   -i fedora41 --disk Fabulous.qcow2 --disk-size 10g

# Install from a CDROM install URL, attach console and vnc-proxy
freeboxvm install -n Fedora-test --os fedora   --location https://download.fedoraproject.org/pub/fedora/linux/releases/41/Everything/aarch64/iso/Fedora-Everything-netinst-aarch64-41-1.4.iso   --disk "/Disque 1/VMs/test.qcow2" --disk-size 20g   --vcpus 2 --memory 2048 --console --vnc-proxy --enable-screen
```


### Power on a VM
```bash
freeboxvm poweron <id|name> [--console|-c] [--vnc-proxy|-v]
                   [--listen|-l ADDR] [--port|-p N]
```
- Boots the VM, then (optionally) attaches the console and/or starts the
  VNC proxy.
- `--console, -c`     : attach interactive console (detach Ctrl-A D)
- `--vnc-proxy, -v`   : expose VNC over a local TCP port
- `--listen, -l ADDR` : bind address for VNC proxy (default 127.0.0.1)
- `--port, -p N`      : TCP port for VNC proxy (default 5901)

Examples:
```bash
# Power on and attach console
freeboxvm poweron 12 --console

# Power on and start VNC proxy on 0.0.0.0:5902
freeboxvm poweron 12 --vnc-proxy -l 0.0.0.0 -p 5902

# Power on, attach console and run VNC proxy together
freeboxvm poweron Debian-11 -c -v
```

---

### Power off a VM
```bash
freeboxvm poweroff [-f|--force] <id|name>
```

- Requests ACPI shutdown of the specified VM.
- With `-f`/`--force`, sends a hard stop instead.

Examples:
```bash
freeboxvm poweroff 0
freeboxvm poweroff --force Debian-11
```

---

### Reset a VM
```bash
freeboxvm reset <id|name>
```

Examples:
```bash
freeboxvm reset 0
freeboxvm reset Debian-11
```

---

### Delete a VM
```bash
freeboxvm delete <id|name>
- `--disk, -d`     : Also delete disks and efivars
- `--force, -f`    : Delete a running VM
```
Remove the specified virtual machine by its numeric **id** or **name**.
Consider powering off the VM first if deletion fails.

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
