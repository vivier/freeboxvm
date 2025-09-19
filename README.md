# freeboxvm

A command-line tool to manage and access virtual machines on a Freebox
via the Freebox OS API v8.

---

## Requirements

- Python 3.8+
- Freebox with Freebox OS v8 API
- Packages: `requests`, `websockets`, `pygobject` (for **libosinfo** support)

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
