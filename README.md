# freeboxvm

A command-line tool to manage and access virtual machines on a Freebox
via the Freebox OS API v8.

---

## Requirements

- Python 3.8+
- Freebox with Freebox OS v8 API
- Packages: requests, websockets

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

### Connect to a VM console
```bash
freeboxvm console [id|name]
```

- If no argument is provided, connects to the first running VM (or the first in
  the list).
- Exit with **Ctrl+C** or **Ctrl-A D**.
- Send a literal **Ctrl-A** to the VM with **Ctrl-A A**.

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
