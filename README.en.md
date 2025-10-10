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

## Installation

```bash
pip install .
```

To install the dependencies without packaging metadata (for development
or legacy environments):

```bash
pip install -r requirements.txt
```

On Fedora you may need:

```bash
sudo dnf install python3-gobject gobject-introspection libosinfo osinfo-db
```

On Debian/Ubuntu you may need:

```bash
sudo apt install python3-gi gir1.2-libosinfo-1.0
```

---

## Usage

### List VMs

```bash
freeboxvm list [--long] [--usb-ports] [--disks] [--cloud-init]
```

**Default output**: `ID  STATUS  NAME`.

<div>
  <table style="border: none;">
    <tr>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;&#8209;long</strong></td>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;l</strong></td>
      <td>Show more information</td>
    </tr>
    <tr>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;&#8209;usb&#8209;ports</strong></td>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;u</strong></td>
      <td>List associated USB ports</td>
    </tr>
    <tr>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;&#8209;disks</strong></td>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;d</strong></td>
      <td>List disk images</td>
    </tr>
    <tr>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;&#8209;cloud&#8209;init</strong></td>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;c</strong></td>
      <td>Show cloud-init information</td>
    </tr>
  </table>
</div>

#### Examples

##### Short view

```bash
$ freeboxvm list
ID  STATUS   NAME
0   running  Debian-11
1   stopped  Ubuntu-22.04
```

##### Long view with USB ports

```bash
$ freeboxvm list --long --usb-ports
ID  STATUS   NAME        OS      MAC               VCPUs  MEMORY  DISPLAY
0   running  Debian-11   debian  aa:bb:cc:dd:ee:ff 2      2048    True
    USB ports: usb-external-type-a
```

##### Disk and cloud-init details

```bash
$ freeboxvm list --disks --cloud-init
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

### Show a VM

```bash
freeboxvm show <id|name> [--long] [--usb-ports] [--disks] [--cloud-init]
```

Displays information about a single VM. Supports the same options as `list`.

<div>
  <table style="border: none;">
    <tr>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;&#8209;long</strong></td>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;l</strong></td>
      <td>Show more information</td>
    </tr>
    <tr>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;&#8209;usb&#8209;ports</strong></td>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;u</strong></td>
      <td>List associated USB ports</td>
    </tr>
    <tr>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;&#8209;disks</strong></td>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;d</strong></td>
      <td>List disk images</td>
    </tr>
    <tr>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;&#8209;cloud&#8209;init</strong></td>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;c</strong></td>
      <td>Show cloud-init information</td>
    </tr>
  </table>
</div>

#### Examples

```bash
$ freeboxvm show 1
ID    STATUS    NAME
1    stopped    Ubuntu-22.04
```

```bash
$ freeboxvm show Debian-11 --long
ID  STATUS   NAME        OS      MAC               VCPUs  MEMORY  DISPLAY
0   running  Debian-11   debian  aa:bb:cc:dd:ee:ff 2      2048    True
```

```bash
$ freeboxvm show 1 --disks --cloud-init
ID    STATUS    NAME
1    stopped    Ubuntu-22.04
    Disk image: Disque 1/VMs/ubuntu2204.qcow2 (qcow2)
    No CDROM device image
    Cloud-init hostname: Ubuntu
    Cloud-init user-data:
#cloud-config
system_info:
  default_user:
    name: laurent
  groups:
    - laurent
```

---

### Connect to a VM console

```bash
freeboxvm console <id|name>
```

Console control key combinations:

<div>
<table style="border: none;">
  <tr>
    <td style="border: none"><strong>Ctrl-B D</strong></td><td>Quit</td></tr>
  <tr>
    <td style="border: none"><strong>Ctrl-B B</strong></td><td>Send a literal <strong>Ctrl-B</strong></td>
  </tr>
  <tr>
    <td style="border: none;"><strong>Ctrl-B R</strong></td><td>Reset the VM</td>
  </tr>
  <tr>
    <td style="border: none"><strong>Ctrl-B H</strong></td><td>Halt the VM</td>
  </tr>
  <tr>
    <td style="border: none"><strong>Ctrl-B S</strong></td><td>Immediately stop the VM</td>
  </tr>
  <tr>
    <td style="border: none"><strong>Ctrl-B ?</strong></td><td>Show help about key bindings</td>
  </tr>
</table>
</div>

#### Examples

```bash
freeboxvm console 0
freeboxvm console Debian-11
```

---

### Expose a VM screen through a VNC proxy

```bash
freeboxvm vnc-proxy [-h] [--listen ADDR] [--port N] [--console] vm
```

Expose the VM’s VNC screen on a local TCP port.

<div>
  <table style="border: none;">
    <tr>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;&#8209;listen ADDR</strong></td>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;l ADDR</strong></td>
      <td>Listening address (default 127.0.0.1)</td>
    </tr>
    <tr>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;&#8209;port N</strong></td>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;p N</strong></td>
      <td>TCP port (default 5901)</td>
    </tr>
    <tr>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;&#8209;console</strong></td>
      <td style="border: none; white-space: nowrap;"><strong> </strong></td>
      <td>Launch the interactive console in parallel</td>
    </tr>
  </table>
</div>

#### Examples

##### VNC proxy for VM 0 on localhost:5901

```bash
freeboxvm vnc-proxy 0
```

##### Proxy for VM 12 on all interfaces, port 5902

```bash
freeboxvm vnc-proxy --listen 0.0.0.0 --port 5902 12
```

##### Proxy and console for a VM by name

```bash
freeboxvm vnc-proxy --console Debian-11
```

---

### Manage disks

```bash
freeboxvm disk [-h] {create,info,resize,delete} ...
```

Manage VM disk images (creation, resizing, inspection, deletion).
Sizes accept binary suffixes `k`, `m`, `g`, `t` (powers of two); raw
byte values are also accepted.

Actions:

- **create**

  ```bash
  freeboxvm disk create [-h] [--type TYPE] <path> <size>
  ```

  Create a disk image (default qcow2).

- **resize**

  ```bash
  freeboxvm disk resize [-h] [--shrink-allow] <path> <size>
  ```

  Resize a disk image (`--shrink-allow` permits shrinking).

- **info**

  ```bash
  freeboxvm disk info <path>
  ```

  Display virtual size, used size, type.

- **delete**

  ```bash
  freeboxvm disk delete <path>
  ```

  Delete a disk image.

#### Examples

##### Create a 10 GiB qcow2 disk

```bash
freeboxvm disk create "/Disque 1/VMs/disk1.qcow2" 10g
```

##### Resize a disk to 20 GiB

```bash
freeboxvm disk resize "/Disque 1/VMs/disk1.qcow2" 20g
```

##### Force a destructive resize (reduce size)

```bash
freeboxvm disk resize --shrink-allow "/Disque 1/VMs/disk1.qcow2" 8g
```

##### Show disk information

```bash
freeboxvm disk info "/Disque 1/VMs/disk1.qcow2"
```

##### Delete a disk

```bash
freeboxvm disk delete "/Disque 1/VMs/disk1.qcow2"
```

---

### Install a new VM

```bash
freeboxvm install [options]
```

Create and start a VM from a cloud image or an ISO.
Can also attach a console and/or VNC proxy.

<div>
  <table style="border: none;">
    <tr>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;&#8209;install ID</strong></td>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;i ID</strong></td>
      <td>Distribution identifier (see <code>os-list</code>).</td>
    </tr>
    <tr>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;&#8209;name</strong></td>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;n NAME</strong></td>
      <td>VM name.</td>
    </tr>
    <tr>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;&#8209;os</strong></td>
      <td style="border: none; white-space: nowrap;"><strong> </strong></td>
      <td>OS name (if not detected).</td>
    </tr>
    <tr>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;&#8209;vcpus</strong></td>
      <td style="border: none; white-space: nowrap;"><strong> </strong></td>
      <td>Number of virtual CPUs.</td>
    </tr>
    <tr>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;&#8209;memory</strong></td>
      <td style="border: none; white-space: nowrap;"><strong> </strong></td>
      <td>Memory (MiB).</td>
    </tr>
    <tr>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;&#8209;disk PATH</strong></td>
      <td style="border: none; white-space: nowrap;"><strong> </strong></td>
      <td>Disk image path.</td>
    </tr>
    <tr>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;&#8209;disk&#8209;size</strong></td>
      <td style="border: none; white-space: nowrap;"><strong> </strong></td>
      <td>Disk size.</td>
    </tr>
    <tr>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;&#8209;cdrom PATH</strong></td>
      <td style="border: none; white-space: nowrap;"><strong> </strong></td>
      <td>Installation ISO.</td>
    </tr>
    <tr>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;&#8209;location URL</strong></td>
      <td style="border: none; white-space: nowrap;"><strong> </strong></td>
      <td>CD/ISO URL (mutually exclusive with <code>--cdrom</code>).</td>
    </tr>
    <tr>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;&#8209;cloud&#8209;init</strong></td>
      <td style="border: none; white-space: nowrap;"><strong> </strong></td>
      <td>Enable cloud-init.</td>
    </tr>
    <tr>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;&#8209;cloud&#8209;init&#8209;hostname</strong></td>
      <td style="border: none; white-space: nowrap;"><strong> </strong></td>
      <td>Hostname.</td>
    </tr>
    <tr>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;&#8209;cloud&#8209;init&#8209;userdata FILE</strong></td>
      <td style="border: none; white-space: nowrap;"><strong> </strong></td>
      <td>User-data file.</td>
    </tr>
    <tr>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;&#8209;enable&#8209;screen</strong></td>
      <td style="border: none; white-space: nowrap;"><strong> </strong></td>
      <td>Enable screen (VNC-over-WebSocket).</td>
    </tr>
    <tr>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;&#8209;console</strong></td>
      <td style="border: none; white-space: nowrap;"><strong> </strong></td>
      <td>Attach console after boot.</td>
    </tr>
    <tr>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;&#8209;vnc&#8209;proxy</strong></td>
      <td style="border: none; white-space: nowrap;"><strong> </strong></td>
      <td>Start VNC proxy after boot.</td>
    </tr>
    <tr>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;&#8209;listen ADDR</strong></td>
      <td style="border: none; white-space: nowrap;"><strong> </strong></td>
      <td>VNC listen address (default 127.0.0.1).</td>
    </tr>
    <tr>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;&#8209;port N</strong></td>
      <td style="border: none; white-space: nowrap;"><strong> </strong></td>
      <td>VNC TCP port (default 5901).</td>
    </tr>
    <tr>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;&#8209;usb&#8209;ports LIST</strong></td>
      <td style="border: none; white-space: nowrap;"><strong> </strong></td>
      <td>Bind USB ports to the VM (comma-separated list).</td>
    </tr>
  </table>
</div>

#### Notes

- When `--install` or `--location` is used, the image is downloaded via
  the Freebox Download Manager into the default directory
  `/Disque 1/VMs/`, with progress tracking, checksum verification, and
  cleanup on error.
- For cloud images, the downloaded file becomes the VM disk image.
- If `--disk` points to a non-existent file, `--disk-size` must be
  provided so the tool can create the image (qcow2/raw type inferred
  from the extension).
- Disks can be resized automatically if they are smaller than the size
  specified by `--disk-size`.

#### Examples

##### Install from a cloud image short-id and attach the console

```bash
freeboxvm install -n Fedora-cloud --vcpus 1 --memory 512 --console \
  --cloud-init --cloud-init-hostname Fabulous \
  --cloud-init-userdata cloud-init-user-data.yaml \
  -i fedora41 --disk Fabulous.qcow2 --disk-size 10g
```

##### Install from a CDROM URL, attach console and VNC proxy

```bash
freeboxvm install -n Fedora-test --os fedora \
  --location https://download.fedoraproject.org/pub/fedora/linux/releases/41/Everything/aarch64/iso/Fedora-Everything-netinst-aarch64-41-1.4.iso \
  --disk "/Disque 1/VMs/test.qcow2" --disk-size 20g \
  --vcpus 2 --memory 2048 --console --vnc-proxy --enable-screen
```

---

### Power on a VM

```bash
freeboxvm poweron <id|name> [--console|-c] [--vnc-proxy|-v]
                   [--listen|-l ADDR] [--port|-p N]
```

Starts the VM then (optionally) attaches the console and/or launches the VNC proxy.

<div>
  <table style="border: none;">
    <tr>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;&#8209;console</strong></td>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;c</strong></td>
      <td>Attach an interactive console (detach with Ctrl-B D)</td>
    </tr>
    <tr>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;&#8209;vnc&#8209;proxy</strong></td>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;v</strong></td>
      <td>Expose VNC on a local TCP port</td>
    </tr>
    <tr>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;&#8209;listen ADDR</strong></td>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;l ADDR</strong></td>
      <td>Listen address for the VNC proxy (default 127.0.0.1)</td>
    </tr>
    <tr>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;&#8209;port N</strong></td>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;p N</strong></td>
      <td>VNC proxy TCP port (default 5901)</td>
    </tr>
  </table>
</div>

#### Examples

##### Power on and attach the console

```bash
freeboxvm poweron 12 --console
```

##### Power on and start the VNC proxy on 0.0.0.0:5902

```bash
freeboxvm poweron 12 --vnc-proxy -l 0.0.0.0 -p 5902
```

##### Power on and start both console and VNC proxy

```bash
freeboxvm poweron Debian-11 -c -v
```

---

### Power off a VM

```bash
freeboxvm poweroff [-f|--force] <id|name>
```

Requests an ACPI shutdown of the specified VM.

<div>
  <table style="border: none;">
    <tr>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;&#8209;force</strong></td>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;f</strong></td>
      <td>Send a forced stop (hard stop).</td>
    </tr>
  </table>
</div>

#### Examples

```bash
freeboxvm poweroff 0
freeboxvm poweroff --force Debian-11
```

---

### Reset a VM

```bash
freeboxvm reset <id|name>
```

#### Examples

```bash
freeboxvm reset 0
freeboxvm reset Debian-11
```

---

### Delete a VM

```bash
freeboxvm delete <id|name> [--disk|-d] [--force|-f]
```

Delete the virtual machine identified by numeric ID or name.
If deletion fails, try powering off the VM first.

<div>
  <table style="border: none;">
    <tr>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;&#8209;disk</strong></td>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;d</strong></td>
      <td>Also delete disks and efivars</td>
    </tr>
    <tr>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;&#8209;force</strong></td>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;f</strong></td>
      <td>Delete a running VM</td>
    </tr>
  </table>
</div>

---

### Freebox system info

```bash
freeboxvm system
```

Displays global Freebox resources:

- Total and used memory
- Total and used CPUs
- USB allocation state
- List of available USB ports
- Path to the VMs directory

#### Examples

```bash
$ freeboxvm system
Total memory: 2048    Used memory: 0    (0.0 %)
Number of CPU: 2    CPUs used: 0    (0.0 %)
External USB allocated: No
Available USB ports:
   usb-external-type-a
VMs directory path: /Disque 1/VMs
```

---

### List installable distributions

```bash
freeboxvm os-list [options]
```

List operating system images that can be installed for VMs.

<div>
  <table style="border: none;">
    <tr>
      <td style="border: none"><strong>&#8209;&#8209;extra</strong></td><td style="border: none"><strong>&#8209;e</strong></td><td>Query external sources via libosinfo for cloud-init images (aarch64, qcow2/raw).</td>
    </tr>
    <tr>
      <td style="border: none"><strong>&#8209;&#8209;iso</strong></td><td style="border: none"><strong>&#8209;i</strong></td><td>List installable ISOs instead of cloud images.</td>
    </tr>
    <tr>
      <td style="border: none"><strong>&#8209;&#8209;long</strong></td><td style="border: none"><strong>&#8209;l</strong></td><td>Show detailed information (OS, distribution, URL, checksum, live flag).</td>
    </tr>
    <tr>
      <td style="border: none"><strong>&#8209;&#8209;check</strong></td><td style="border: none"><strong>&#8209;c</strong></td><td>Validate image and checksum URLs.</td>
    </tr>
    <tr>
      <td style="border: none"><strong>&#8209;&#8209;os</strong></td><td style="border: none"><strong>&#8209;o</strong></td><td>Filter results by OS name (e.g. fedora, ubuntu).</td>
    </tr>
  </table>
</div>

#### Examples

##### List all available distributions

```bash
freeboxvm os-list
```

##### Show detailed information

```bash
freeboxvm os-list --long
```

##### Validate URLs

```bash
freeboxvm os-list --check --long
```

##### List installable ISOs

```bash
freeboxvm os-list --iso
```

##### Filter by OS (e.g. only Fedora)

```bash
freeboxvm os-list --os fedora
```

---

### Download an image

```bash
freeboxvm download [options] [short-id]
```

Download a VM installation image (disk or ISO) using the Freebox Download Manager.

<div>
  <table style="border: none;">
    <tr>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;&#8209;iso</strong></td>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;i</strong></td>
      <td>Select an installation ISO instead of a cloud/disk image.</td>
    </tr>
    <tr>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;&#8209;url URL</strong></td>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;u URL</strong></td>
      <td>Provide a direct URL instead of a short-id.</td>
    </tr>
    <tr>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;&#8209;hash HASH</strong></td>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;a HASH</strong></td>
      <td>Provide the checksum URL when using --url.</td>
    </tr>
    <tr>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;&#8209;filename F</strong></td>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;f F</strong></td>
      <td>Filename to save as.</td>
    </tr>
    <tr>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;&#8209;directory D</strong></td>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;d D</strong></td>
      <td>Freebox directory to store the file (automatically base64 encoded).</td>
    </tr>
    <tr>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;&#8209;background</strong></td>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;b</strong></td>
      <td>Download in background mode (progress hidden; monitor in the Freebox "Downloads" section).</td>
    </tr>
  </table>
</div>

#### Examples

##### Download a Fedora cloud-init image via short-id

```bash
freeboxvm download fedora40
```

##### Download an Ubuntu ISO instead of a cloud image

```bash
freeboxvm download --iso ubuntu24.04
```

##### Provide a custom URL and checksum

```bash
freeboxvm download --url https://cloud-images.ubuntu.com/.../disk.qcow2 \
                   --hash https://cloud-images.ubuntu.com/.../SHA256SUMS
```

##### Download in background mode

```bash
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
