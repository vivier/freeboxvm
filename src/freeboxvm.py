#!/usr/bin/env python3
import os, sys
import requests, json, argparse
import hashlib, hmac
import time
import platform
from contextlib import contextmanager
import asyncio
from websockets.asyncio.client import connect
import ssl
from urllib.parse import urljoin, urlparse
import re
import base64
from tqdm import tqdm
import signal
from websockets.exceptions import ConnectionClosed
import humanize
from freeboxvm_version import __version__

APP_ID		= "freeboxvm"
APP_NAME	= "Freebox VM manager"
DEVICE_NAME	= platform.node()

API_URL		= f"http://mafreebox.freebox.fr/api/v8"

TOKEN_FILE = "freeboxvm_token.json"

def load_app_token():
    """Load persisted Freebox application token and track_id from disk.

    Returns
    -------
    tuple[str|None, str|None]
        (app_token, track_id) if present; (None, None) otherwise.
    """
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "r") as file:
            data = json.load(file)
            return data["app_token"], data["track_id"]
    return None, None

def save_app_token(app_token, track_id):
    """Persist Freebox application token and track_id to disk.

    Parameters
    ----------
    app_token : str
        Token issued by the Freebox authorization step.
    track_id : str
        Tracking identifier returned by the authorization API.
    """
    with open(TOKEN_FILE, "w") as file:
        json.dump({"app_token": app_token, "track_id": track_id}, file)

def api_request(method, endpoint, session_token=None, **kwargs):
    """Call a Freebox OS API endpoint and return its `result` payload.

    Parameters
    ----------
    method : str
        HTTP verb, e.g. 'get', 'post'.
    endpoint : str
        API path beginning with '/'.
    session_token : str | None
        Optional session token to send as 'X-Fbx-App-Auth'.
    **kwargs : dict
        Extra arguments forwarded to `requests.request` (json=data, params, etc.).

    Returns
    -------
    Any | str | None
        The `result` field on success; the string 'forbidden' on HTTP 403;
        or None on network/JSON errors.

    Side Effects
    ------------
    Logs API/network/JSON errors to journald.
    """
    headers = {}
    if session_token:
        headers["X-Fbx-App-Auth"] = session_token

    try:
        response = requests.request(method, f"{API_URL}{endpoint}", headers=headers,
                                    timeout=5, **kwargs)
        response.raise_for_status()
        data = response.json()
        if data.get('success'):
            return data.get('result')
        else:
            print(f"{endpoint}: {data.get('msg')}")
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 403:
            return "forbidden" # Return a special string for 403 errors
        else:
            print(f"Erreur HTTP sur {endpoint}: {e}")
    except requests.exceptions.RequestException as e:
        print(f"Erreur de réseau sur {endpoint}: {e}")
    except json.JSONDecodeError:
        print(f"Erreur de décodage JSON sur {endpoint}")
    return None

def freebox_connect():
    """Establish a Freebox OS API session token.

    1) Load stored app token/track_id; otherwise request authorization and poll
       until the user approves the app on the Freebox.
    2) Compute HMAC-SHA1 password from challenge and app_token.
    3) Open a login session and return the session token.

    Returns
    -------
    str | None
        A valid session token, or None if the flow fails.

    Side Effects
    ------------
    May persist the app token to disk. Logs status messages to journald.
    """
    # Charger le token depuis le fichier ou obtenir une nouvelle autorisation
    app_token, track_id = load_app_token()
    if not app_token or not track_id:
        auth_data = api_request("post", "/login/authorize/", json={
            "app_id": APP_ID, "app_name": APP_NAME,
            "app_version": __version__, "device_name": DEVICE_NAME
        })
        if not auth_data: return None
        track_id, app_token = auth_data['track_id'], auth_data['app_token']
        save_app_token(app_token, track_id)
        print("Veuillez accepter l'application sur la Freebox")
        max_retries = 24
        for i in range(max_retries):
            status_data = api_request("get", f"/login/authorize/{track_id}")
            status = status_data.get('status') if status_data else None
            if status == 'granted':
                print("Autorisation approuvée.")
                break
            elif status == 'pending':
                print("En attente d'autorisation...")
                time.sleep(5)
            else:
                print(f"Échec d'autorisation avec le statut : {status}")
                return None
        else:
            print("Épuisement du délai d'attente d'autorisation après 2 minutes.")
            return None

    challenge_data = api_request("get", f"/login/authorize/{track_id}")
    if not challenge_data or not isinstance(challenge_data, dict):
        print("Échec pour obtenir le challenge, le token doit être invalide.")
        return None
    challenge = challenge_data['challenge']
    password = hmac.new(app_token.encode(), challenge.encode(), hashlib.sha1).hexdigest()

    login_data = api_request("post", "/login/session/", json={"app_id": APP_ID, "password": password})
    if login_data == "forbidden":
        print(f"Fichier token invalide {TOKEN_FILE}")
        return None
    return login_data['session_token'] if login_data else None

def search_VMs(session_token, path):
    path_b64 = base64.b64encode(path.encode("utf-8")).decode("ascii")
    res = api_request("get", f"/fs/ls/{path_b64}", session_token, data = { 'onlyFolder': True, 'removeHidden': True })
    for entry in res:
        if entry['hidden'] or not entry['mimetype'] == 'inode/directory' or entry['name'] == '.' or entry['name'] == '..':
            continue
        path = base64.b64decode(entry['path']).decode('utf-8')
        if entry['name'] == 'VMs':
            return path
        res = search_VMs(session_token, path)
        if res != None:
            return res
    return None

async def console_link(session_token, vm_id):
    url = f"wss://mafreebox.freebox.fr/api/v8/vm/{vm_id}/console"

    # TLS verification
    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE
    async with connect(
        url,
        additional_headers={"X-Fbx-App-Auth": session_token},
        subprotocols=['binary'],
        ssl=ssl_ctx
    ) as ws:
        loop = asyncio.get_running_loop()

        CTRL_B = b"\x02"              # Ctrl-B
        HELP_KEYS = { b"?" } # Ctrl-B ?
        DETACH_KEYS = { b"d", b"D" } # Ctrl-B D
        PASSTHRU_KEYS = { b"b", b"B" } # Ctrl-B B
        HALT_KEYS = { b"h", b"H" } # Ctrl-B H
        RESET_KEYS = { b"r", b"R" } # Ctrl-B R
        STOP_KEYS = { b"s", b"S" } # Ctrl-B S

        async def rx():
            async for msg in ws:
                if isinstance(msg, str):
                    sys.stdout.write(msg)
                else:
                    sys.stdout.buffer.write(msg)
                sys.stdout.flush()

        async def tx():
            waiting_cmd = False
            while True:
                data = await loop.run_in_executor(None, sys.stdin.buffer.read, 1)
                if not data:
                    break
                if waiting_cmd:
                    waiting_cmd = False
                    if data in DETACH_KEYS:
                        await ws.close()
                        return
                    elif data in HELP_KEYS:
                        print("\r")
                        print("    Ctrl-B ? : Affiche l'aide\r")
                        print("    Ctrl-B D : Détache la console\r")
                        print("    Ctrl-B H : Arrête la VM\r")
                        print("    Ctrl-B S : Force l'arrêt de la VM\r")
                        print("    Ctrl-B R : Redémarre la VM\r")
                        print("    Ctrl-B B : Envoie Ctrl-B a la console\r")
                    elif data in HALT_KEYS:
                        api_request("post", f"/vm/{vm_id}/powerbutton", session_token)
                    elif data in STOP_KEYS:
                        api_request("post", f"/vm/{vm_id}/stop", session_token)
                    elif data in RESET_KEYS:
                        api_request("post", f"/vm/{vm_id}/restart", session_token)
                    elif data in PASSTHRU_KEYS:
                        await ws.send(CTRL_B)
                    else:
                        await ws.send(CTRL_B + data)
                    continue

                if data == CTRL_B:
                    waiting_cmd = True
                else:
                    await ws.send(data)

        try:
            await asyncio.gather(rx(), tx())
        except ConnectionClosed:
            return

def system_info(session_token):
    info = api_request("get", "/vm/info/", session_token)
    print(f"Mémoire totale : {info['total_memory']}\tMémoire utilisée : {info['used_memory']}\t({info['used_memory'] * 100 / info['total_memory']} %)")
    print(f"Nombre de CPU : {info['total_cpus']}\tCPU utilisés : {info['used_cpus']}\t({info['used_cpus'] * 100 / info['total_cpus']} %)")
    print(f"USB externe alloué : {'Oui' if info['usb_used'] else 'Non'}")
    print("Liste des ports USB disponibles :")
    for usb in info['usb_ports']:
        print(f"   {usb}")
    print(f"VMs directory path: {search_VMs(session_token, '/')}")

def get_vm_list(session_token):
    vm_list = api_request("get", "/vm/", session_token)
    return vm_list

def display_info(vm, args):
    if not args.long:
        print(f"{vm['id']}\t{vm.get('status')}\t{vm.get('name')}")
    else:
        print(f"{vm['id']}\t{vm.get('status')}\t{vm.get('name')}\t{vm.get('os')}\t{vm.get('mac')}\t{vm.get('vcpus')}\t{vm.get('memory')}\t{vm.get('enable_screen')}")

    if args.usb_ports:
        if vm.get('bind_usb_ports'):
            print(f"\tPorts USB : {', '.join(port for port in vm.get('bind_usb_ports'))}")
        else:
            print("\tAucun port USB")

    if args.disks:
        disc_path = vm.get('disk_path')
        print(f"\tImage disque : {base64.b64decode(vm.get('disk_path')).decode('utf-8')} ({vm.get('disk_type')})")
        if vm.get('cd_path'):
            print(f"\tImage CD : {base64.b64decode(vm.get('cd_path')).decode('utf-8')}")
        else:
            print("\tAucune image de périphérique CDROM")

    if args.cloud_init:
        if vm.get('enable_cloudinit'):
            print(f"\tCloud-init hostname : {vm.get('cloudinit_hostname')}")
            print("\tCloud-init user-data :")
            print(vm.get('cloudinit_userdata'))
        else:
            print("\tCloud-init est désactivé")

def human_size(hsize):
    # size will be number of kilibytes
    tens = dict(k=2**0, m=2**10, b=2**20, g=2**30, t=2**40)

    try:
        return int(int(hsize) / 2**10)
    except:
        number, unit = hsize[0:-1], hsize[-1].lower()

        if unit in tens.keys():
            return int(float(number) * tens[unit])

        return None

def list(session_token, args):
    vm_list = get_vm_list(session_token)
    if not vm_list:
        print("Pas de VM disponible", file=sys.stderr)
        return

    if not args.long:
        print("ID\tSTATUT\tNOM")
    else:
        print("ID\tSTATUT\tNOM\tOS\tMAC             \tvCPU\tMÉMOIRE\tAFFICHAGE")

    for vm in vm_list:
        display_info(vm, args)

def distro_check(url, hash):
    try:
        r = requests.head(url, allow_redirects=True, timeout=5)
        if not r.status_code == 200:
            return False
    except requests.RequestException:
        return False

    if not hash:
        return True

    try:
        r = requests.head(hash, allow_redirects=True, timeout=5)
        if not r.status_code == 200:
            return False
    except requests.RequestException:
        return False

    return True

def distro_get_hash(os_name, url):
    base_url = url.rsplit("/", 1)[0] + "/"
    if os_name == "ubuntu":
        sha_url = urljoin(base_url, "SHA256SUMS")
    if os_name == "alt" :
        sha_url = urljoin(base_url, "SHA256SUM")
    elif os_name == "debian":
        sha_url = urljoin(base_url, "SHA512SUMS")
    elif os_name in [ "almalinux", "centos", "rocky" ] :
        # format not supported by Freebox download manager
        #sha_url = urljoin(base_url, "CHECKSUM")
        sha_url = None
    elif os_name == "opensuse":
        sha_url = url + ".sha256"
    elif os_name == "fedora":
        m = re.match(r".*-(\d+)-([\d.]+)\.aarch64\.qcow2", os.path.basename(urlparse(url).path))
        if not m:
            m = re.match(r".*\.aarch64-(\d+)-([\d.]+)\.qcow2", os.path.basename(urlparse(url).path))

        if m:
            release, version = m.groups()
            sha_url = urljoin(base_url, f"Fedora-Cloud-{release}-{version}-aarch64-CHECKSUM")
        else:
            m = re.match(r"^Fedora-(\w+)-ostree-aarch64-(\d+)-([\d.]+)\.iso$", os.path.basename(urlparse(url).path))

            if m:
                codename, release, version = m.groups()
                sha_url = urljoin(base_url, f"Fedora-{codename}-{release}-{version}-aarch64-CHECKSUM")
            else:
                return None
    else:
        sha_url = None

    return sha_url

def get_list_iso():
    import gi
    gi.require_version('Libosinfo', '1.0')
    from gi.repository import Libosinfo
    distro_list = [ ]

    loader = Libosinfo.Loader()
    loader.process_default_path()
    db = loader.get_db()

    os_list = db.get_os_list()
    num_oses = os_list.get_length()

    for i in range(num_oses):
        os_obj = os_list.get_nth(i)

        media_list = os_obj.get_media_list()
        medias = [ media_list.get_nth(i) for i in range(media_list.get_length()) ]

        distro_os = os_obj.get_distro()
        distro_name = os_obj.get_name()
        distro_version = os_obj.get_version()

        for media in medias:
            distro_url = media.get_param_value('url')
            if not distro_url or not media.get_architecture() == 'aarch64':
                continue

            distro_hash = distro_get_hash(distro_os, distro_url)
            entry = {
                'name': distro_name,
                'short-id': os_obj.get_short_id(),
                'os': distro_os,
                'url': distro_url,
                'hash': distro_get_hash(distro_os, distro_url),
                'live': media.get_live()
            }
            distro_list.append(entry)
    return distro_list

def get_list_distro(session_token):
    distro_list = [ ]

    freebox_list = api_request("get", "/vm/distros/", session_token)

    for distro in freebox_list:
        entry = {
            'name': distro['name'],
            'os': distro['os'],
            'url': distro['url'],
        }
        m = re.search(r"\d+(?:\.\d+)?", distro['name'])
        if m:
            relver = m.group()
            entry['short-id'] = f"{distro['os']}{relver}"
        else:
            if distro['os'] == 'jeedom':
                entry['short-id'] = 'jeedom'
            elif distro['name'] == "Debian Unstable (sid)":
                entry['short-id'] = 'debian-sid'

        if distro.get('hash'):
            entry['hash'] = distro.get('hash')
        distro_list.append(entry)
    return distro_list

def get_list_extra_distro():
    import gi
    gi.require_version('Libosinfo', '1.0')
    from gi.repository import Libosinfo
    distro_list = [ ]

    loader = Libosinfo.Loader()
    loader.process_default_path()
    db = loader.get_db()

    os_list = db.get_os_list()
    num_oses = os_list.get_length()

    for i in range(num_oses):
        os_obj = os_list.get_nth(i)

        distro_os = os_obj.get_distro()

        img_list = os_obj.get_image_list()
        images = [ img_list.get_nth(i) for i in range(img_list.get_length()) ]

        ci_images = [ img for img in images
                        if img.get_param_value("cloud-init") == 'true' and
                           img.get_architecture() == 'aarch64' and
                           img.get_param_value('format') in [ 'qcow2', 'raw' ] ]

        if not ci_images:
            continue

        distro_name = os_obj.get_name()
        for img in ci_images:
            distro_url = img.get_param_value('url')
            entry = {
                'name': distro_name,
                'short-id': os_obj.get_short_id(),
                'os': distro_os,
                'url': distro_url,
                'hash': distro_get_hash(distro_os, distro_url),
                'variant': img.get_param_value("variant"),
            }
            distro_list.append(entry)

    return distro_list

def list_distro(session_token, args):

    if args.extra:
        distro_list = get_list_extra_distro()
    elif args.iso:
        distro_list = get_list_iso()
    else:
        distro_list = get_list_distro(session_token)

    if not distro_list:
        print("Pas de distribution disponible", file=sys.stderr)
        return

    for distro in distro_list:
        distro_os = distro['os']

        if args.os and not distro_os in args.os:
            continue

        distro_url = distro['url']
        distro_name = distro['name']
        distro_hash = distro.get('hash')

        print(f"{distro_name} ({distro.get('short-id')}{f', {distro.get('variant')}' if distro.get('variant') else ''}){' [Live CD]' if distro.get('live') else ''}")
        if not distro_hash:
            distro_hash = distro_get_hash(distro_os, distro_url)
        if args.check and not distro_check(distro_url, distro_hash):
            print(f"\t-> URL/HASH invalide")

        if args.long:
            print(f"\t{distro_os}")
            print(f"\t{distro_url}")
            print(f"\t{distro_hash if distro_hash else 'Aucune URL de hash/somme de contrôle'}")

def select_vm(session_token, selector):
    vm_list = get_vm_list(session_token)
    if not vm_list:
        return None

    try:
        wanted_id = int(selector)
        match = next((vm for vm in vm_list if int(vm["id"]) == wanted_id), None)
        if match:
            return match
    except ValueError:
        pass

    matches = [ vm for vm in vm_list if selector == vm["name"]]
    if len(matches) == 1:
        return matches[0]

    if len(matches) > 1:
        print("Plusieurs correspondances :", file=sys.stderr)
        for vm in matches:
            print(f"  {vm['id']}: {vm['name']} {vm.get('status')}", file=sys.stderr)
        return None

    return None

def show(session_token, args):
    vm = select_vm(session_token, args.vm)
    if not vm:
        print("VM non trouvée. Utilisez 'freeboxvm list' pour voir la liste.", file=sys.stderr)
        sys.exit(1)

    if not args.long:
        print("ID\tSTATUT\tNOM")
    else:
        print("ID\tSTATUT\tNOM\tOS\tMAC             \tvCPU\tMÉMOIRE\tAFFICHAGE")

    display_info(vm, args)

def delete(session_token, args):
    vm = select_vm(session_token, args.vm)
    if not vm:
        print("VM non trouvée. Utilisez 'freeboxvm list' pour voir la liste.", file=sys.stderr)
        sys.exit(1)

    if vm['status'] != 'stopped':
        if args.force:
            print("La VM est allumée, destruction forcée")
            api_request("post", f"/vm/{vm['id']}/stop", session_token)
            while vm['status'] != 'stopped':
                time.sleep(0.2)
                vm = api_request("get", f"/vm/{vm['id']}", session_token)
        else:
            print(f"La VM est allumée ({vm['status']}), annulation de l'effacement")
            return

    disk_path_b64 = vm['disk_path']
    api_request("delete", f"/vm/{vm['id']}", session_token)
    if disk_path_b64:
        efivars_path = base64.b64decode(disk_path_b64).decode('utf-8') + '.efivars'
        efivars_path_b64 = base64.b64encode(efivars_path.encode("utf-8")).decode("ascii")
        api_request("post", "/fs/rm/", session_token, json={ 'files': [ efivars_path_b64 ] })
        api_request("post", "/fs/rm/", session_token, json={ 'files': [ disk_path_b64 ] })

def get_file(session_token, request, background):
    resp = api_request("post", "/downloads/add", session_token, data=request)
    if not resp:
       print("Échec")
       return

    if background:
        print("Téléchargement démarré sur la Freebox, consultez l'utilitaire « Téléchargements »")
        return None

    task_id = resp['id']
    try:
        filesize = 0
        while not filesize:
            time.sleep(0.1)
            task = api_request("get", f"/downloads/{task_id}", session_token)
            if task['status'] != 'downloading':
                break
            filesize = task['size']

        rxsize = 0
        lastrxsize = 0
        t = tqdm(total=filesize,unit_scale=True,unit='o')

        while rxsize != filesize:
            task = api_request("get", f"/downloads/{task_id}", session_token)
            if task['status'] != 'downloading':
                break
            rxsize = task['rx_bytes']
            t.update(rxsize - lastrxsize)
            lastrxsize = rxsize
            time.sleep(0.1)
        t.close()
        task = api_request("get", f"/downloads/{task_id}", session_token)
        if task['status'] == 'checking':
            print("Vérification du SHA")
        while True:
            task = api_request("get", f"/downloads/{task_id}", session_token)
            if task['status'] != 'checking':
                break
            time.sleep(0.5)
        print(task['status'])
    except KeyboardInterrupt:
        t.close()
        # On Ctrl-C remove the task and the file
        task = api_request("delete", f"/downloads/{task_id}/erase", session_token)
        print("Interrompu... fichier effacé")
        return None
    # On success remove the task but keep the file
    if task['status'] != 'done':
        print("Erreur de téléchargement... fichier effacé")
        task = api_request("delete", f"/downloads/{task_id}/erase", session_token)
        return None
    else:
        destdir = base64.b64decode(task['download_dir']).decode('utf-8')
        filepath = os.path.join(destdir, task['name'])
        task = api_request("delete", f"/downloads/{task_id}", session_token)
        return filepath

def install(session_token, args):
    download_dir = search_VMs(session_token, "/")
    download_dir_b64 = base64.b64encode(download_dir.encode("utf-8")).decode("ascii")

    vm = { }

    if args.vnc_proxy and not args.enable_screen:
        print("--enable-screen est nécessaire pour utiliser --vnc-proxy")
        return

    os_name = args.os

    cdrom_path = args.cdrom
    disk_path = args.disk

    if args.name:
        vm['name'] = args.name

    if args.disk_size:
        disk_size = human_size(args.disk_size)

    if args.vcpus:
        vm['vcpus'] = args.vcpus

    if args.memory:
        vm['memory'] = args.memory

    if args.usb_ports:
        vm['bind_usb_ports'] = args.usb_ports

    hash = None
    location = None
    if args.install:
        if args.cloud_init:
            distro_list = get_list_distro(session_token)
            distro = next((item for item in distro_list if item['short-id'] == args.install), None)
            if not distro:
                distro_list = get_list_extra_distro()
                distro = next((item for item in distro_list if item['short-id'] == args.install), None)
        else:
            distro_list = get_list_iso()
            distro = next((item for item in distro_list if item['short-id'] == args.install), None)

        if not distro:
            print(f"Distribution inconnue : {args.install}")
            return

        location = distro['url']
        hash = distro['hash']
        os_name = distro['os']

    if args.location:
        location = args.location

    if location:
        print(f"URL : {location}")
        if hash:
            print(f"Hash : {hash}")
        if args.cdrom:
            print("--location et --cdrom sont mutuellement exclusifs")
            return

        request = {
           'download_url': location,
           'download_dir': download_dir_b64,
           'hash': hash,
        }
        if args.cloud_init and args.disk:
            request['filename'] = os.path.basename(args.disk)

        print(f"Téléchargement de {location}")
        filepath = get_file(session_token, request, False)
        if not filepath:
            return
        print(f"Le fichier {filepath} a été téléchargé")

        if args.cloud_init:
            disk_path = filepath
        else:
            cdrom_path = filepath

    if os_name:
        vm['os'] = os_name
        print(f"OS : {os_name}")

    if cdrom_path:
        cd_path_b64 = base64.b64encode(cdrom_path.encode("utf-8")).decode("ascii")
        vm['cd_path'] = cd_path_b64

    if disk_path:
        disk_path_b64 = base64.b64encode(disk_path.encode("utf-8")).decode("ascii")

        info = api_request("post", f"/vm/disk/info", session_token, json={ 'disk_path': disk_path_b64 })
        if not info:
            if not args.disk_size:
                print(f"Le disque {disk_path} n'existe pas, et la taille n'a pas été spécifiée pour sa création")
                return
            if disk_path.lower().endswith(".qcow2"):
                disk_type = "qcow2"
            elif disk_path.lower().endswith((".img", ".raw")):
                disk_type = "raw"
            else:
                print(f"Le type du fichier {disk_path} n'a pas pu être déterminé.")
                return
            asyncio.run(disk_execute(session_token, disk_create, {
                'path_b64': disk_path_b64,
                'size': disk_size,
                'type': disk_type
            }))
            info = api_request("post", f"/vm/disk/info", session_token, json={ 'disk_path': disk_path_b64 })
            print(f"Disque créé à {disk_path} de taille {info['virtual_size']}, type {disk_type}")

        if info['virtual_size'] < disk_size:
            asyncio.run(disk_execute(session_token, disk_resize, {
                'path_b64': disk_path_b64,
                'size': disk_size,
                'shrink_allow': False
            }))
            info = api_request("post", f"/vm/disk/info", session_token, json={ 'disk_path': disk_path_b64 })
            print(f"Disque redimensionné à {info['virtual_size']}")

        vm['disk_path'] = disk_path_b64
        vm['disk_type'] = info['type']

    if args.cloud_init:
        vm['enable_cloudinit'] = True
        vm['cloudinit_hostname'] = args.cloud_init_hostname
        with args.cloud_init_userdata as file:
                vm['cloudinit_userdata'] = file.read()

    vm['enable_screen'] = args.enable_screen;

    res = api_request("post", "/vm/", session_token, json = vm )
    if not res:
        return

    vm_id = res['id']
    vm_name = res['name']

    res = api_request("post", f"/vm/{vm_id}/start", session_token)

    if args.console and args.vnc_proxy:
        print(f"Proxy VNC pour {vm_name} (VM #{vm_id}) sur {args.listen}:{args.port}")
        asyncio.run(run_vnc_and_console(session_token, vm_id, args.listen, args.port))
    elif args.console:
        with raw_terminal():
            try:
                asyncio.run(console_link(session_token, vm_id))
            except KeyboardInterrupt:
                pass
    elif args.vnc_proxy:
        print(f"Proxy VNC pour {vm_name} (VM #{vm_id}) sur {args.listen}:{args.port}")
        asyncio.run(run_vnc_proxy(session_token, vm_id, args.listen, args.port))

@contextmanager
def raw_terminal():
    import termios, tty

    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        yield
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)

def console(session_token, args):

    vm = select_vm(session_token, args.vm)
    if not vm:
        print("VM non trouvée. Utilisez 'freeboxvm list' pour voir la liste.", file=sys.stderr)
        sys.exit(1)

    vm_id, vm_name = vm["id"], vm["name"]

    print(f"Connexion à la console de '{vm_name}' (VM #{vm_id}), Ctrl-B D pour sortir...",
          file=sys.stderr)

    with raw_terminal():
        try:
            asyncio.run(console_link(session_token, vm_id))
        except KeyboardInterrupt:
            pass

async def vnc_proxy_once(session_token, vm_id, reader, writer, prefer_base64=False):
    """
    Bridge one TCP client <-> Freebox VNC-over-WebSocket connection.
    """
    url = f"wss://mafreebox.freebox.fr/api/v8/vm/{vm_id}/vnc"

    # TLS verification disabled (Freebox local cert); change if you pinned certs.
    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE

    # Try to negotiate 'binary' first; some QEMU endpoints accept 'base64' only.
    subprotocols = ['binary', 'base64'] if not prefer_base64 else ['base64', 'binary']

    async with connect(
        url,
        additional_headers={"X-Fbx-App-Auth": session_token},
        subprotocols=subprotocols,
        ssl=ssl_ctx,
        open_timeout=10,
        close_timeout=5,
        max_size=None,  # do not cap frame size
    ) as ws:
        mode = ws.subprotocol or 'binary'
        use_base64 = (mode == 'base64')

        async def ws_to_tcp():
            try:
                async for msg in ws:
                    if isinstance(msg, str):
                        # text frames: either base64 data or shouldn't happen
                        data = base64.b64decode(msg) if use_base64 else msg.encode()
                    else:
                        data = msg
                    writer.write(data)
                    await writer.drain()
            except ConnectionClosed:
                pass
            finally:
                try:
                    writer.close()
                    await writer.wait_closed()
                except Exception:
                    pass

        async def tcp_to_ws():
            try:
                while True:
                    data = await reader.read(65536)
                    if not data:
                        break
                    if use_base64:
                        await ws.send(base64.b64encode(data).decode('ascii'))
                    else:
                        await ws.send(data)
            finally:
                try:
                    await ws.close()
                except Exception:
                    pass

        await asyncio.gather(ws_to_tcp(), tcp_to_ws())


async def run_vnc_proxy(session_token, vm_id, host="127.0.0.1", port=5901):
    """
    Start TCP server that forwards to Freebox VNC WS for the given VM.
    """
    loop = asyncio.get_running_loop()
    stop = loop.create_future()

    def _handle_sig():
        if not stop.done():
            stop.set_result(True)

    # Graceful Ctrl-C
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, _handle_sig)

    async def handler(reader, writer):
        peer = writer.get_extra_info("peername")
        print(f"Client connecté depuis {peer}")
        try:
            await vnc_proxy_once(session_token, vm_id, reader, writer)
        except Exception as e:
            print(f"Erreur de tunnel : {e}")
            try:
                writer.close()
                await writer.wait_closed()
            except Exception:
                pass
        finally:
            print(f"Client déconnecté de {peer}")

    server = await asyncio.start_server(handler, host, port)
    sockets = ", ".join(str(s.getsockname()) for s in server.sockets or [])
    async with server:
        await stop
    print("Arrêt du proxy VNC...")

async def run_vnc_and_console(session_token, vm_id, host, port):
    """
    Run the VNC proxy and the interactive console concurrently.
    The console ends on Ctrl-B D (your existing behavior); we then stop the proxy.
    """
    proxy_task = asyncio.create_task(run_vnc_proxy(session_token, vm_id, host, port))

    async def _console_task():
        with raw_terminal():
            try:
                await console_link(session_token, vm_id)
            except KeyboardInterrupt:
                pass

    try:
        await _console_task()        # waits until user detaches or Ctrl-C
    finally:
        # Stop the proxy when console ends (or on Ctrl-C)
        proxy_task.cancel()
        try:
            await proxy_task
        except asyncio.CancelledError:
            pass


def vnc_proxy(session_token, args):
    vm = select_vm(session_token, args.vm)
    if not vm:
        print("VM non trouvée. Utilisez 'freeboxvm list' pour voir la liste.", file=sys.stderr)
        sys.exit(1)
    vm_id, vm_name = vm["id"], vm["name"]
    print(f"Proxy VNC pour '{vm_name}' (VM #{vm_id}) sur {args.listen}:{args.port}")

    if args.console:
        asyncio.run(run_vnc_and_console(session_token, vm_id, args.listen, args.port))
    else:
        asyncio.run(run_vnc_proxy(session_token, vm_id, args.listen, args.port))

def poweron(session_token, args):

    vm = select_vm(session_token, args.vm)
    if not vm:
        print("VM non trouvée. Utilisez 'freeboxvm list' pour voir la liste.", file=sys.stderr)
        sys.exit(1)

    vm_id, vm_name = vm["id"], vm["name"]

    print(f"Démarrage de '{vm_name}' (VM #{vm_id})",
          file=sys.stderr)

    api_request("post", f"/vm/{vm_id}/start", session_token)

    if args.console and args.vnc_proxy:
        asyncio.run(run_vnc_and_console(session_token, vm_id, args.listen, args.port))
    elif args.console:
        with raw_terminal():
            try:
                asyncio.run(console_link(session_token, vm_id))
            except KeyboardInterrupt:
                pass
    elif args.vnc_proxy:
        asyncio.run(run_vnc_proxy(session_token, vm_id, args.listen, args.port))

def poweroff(session_token, args):
    vm = select_vm(session_token, args.vm)
    if not vm:
        print("VM non trouvée. Utilisez 'freeboxvm list' pour voir la liste.", file=sys.stderr)
        sys.exit(1)

    vm_id, vm_name = vm["id"], vm["name"]

    print(f"Extinction de '{vm_name}' (VM #{vm_id})",
          file=sys.stderr)

    if args.force:
        api_request("post", f"/vm/{vm_id}/stop", session_token)
    else:
        api_request("post", f"/vm/{vm_id}/powerbutton", session_token)

def reset(session_token, args):

    vm = select_vm(session_token, args.vm)
    if not vm:
        print("VM non trouvée. Utilisez 'freeboxvm list' pour voir la liste.", file=sys.stderr)
        sys.exit(1)

    vm_id, vm_name = vm["id"], vm["name"]

    print(f"Redémarrage de '{vm_name}' (VM #{vm_id})",
          file=sys.stderr)

    api_request("post", f"/vm/{vm_id}/restart", session_token)

def download(session_token, args):
    if not args.short_id and not args.url:
        print("L'un des paramètres short-id ou --url est nécessaire")
        return

    if args.directory:
        download_dir_b64 = base64.b64encode(args.directory.encode("utf-8")).decode("ascii")
    else:
        download_dir_b64 = None

    if args.filename:
        filename = args.filename
    else:
        filename = None

    if args.short_id:
        short_id = args.short_id
        if args.iso:
            distro_list = get_list_iso()
            entry = next((item for item in distro_list if item['short-id'] == short_id), None)
        else:
            distro_list = get_list_distro(session_token)
            entry = next((item for item in distro_list if item['short-id'] == short_id), None)
            if not entry:
                distro_list = get_list_extra_distro()
                entry = next((item for item in distro_list if item['short-id'] == short_id), None)
        if entry:
            request = {
               'download_url': entry['url'],
               'download_dir': download_dir_b64,
               'filename': filename,
                'hash': entry.get('hash')
            }
        else:
            print(f"short-id {short_id} introuvable")
            return
    else:
            request = {
               'download_url': args.url,
               'download_dir': download_dir_b64,
               'filename': filename,
                'hash': args.hash
            }

    filepath = get_file(session_token, request, args.background)
    if filepath:
        print(f"{filepath} a été téléchargé")

def disk_create(session_token, args):
    task_id = api_request("post", '/vm/disk/create', session_token, json={
        'disk_path': args['path_b64'],
        'size': args['size'],
        'disk_type': args['type'],
    })
    return task_id

def disk_resize(session_token, args):
    task_id = api_request("post", '/vm/disk/resize', session_token, json={
        'disk_path': args['path_b64'],
        'size': args['size'],
        'shrink_allow': args['shrink_allow'],
    })
    return task_id

async def disk_execute(session_token, action, args):
    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE

    async with connect("wss://mafreebox.freebox.fr/api/v8/ws/event/",
                       additional_headers={"X-Fbx-App-Auth": session_token},
                       ssl=ssl_ctx) as ws:
        await ws.send(json.dumps({
            "action": "register",
            "events": [ "vm_disk_task_done"],
        }))
        task_id = action(session_token, args)
        if not task_id:
            return False
        async for msg in ws:
            try:
                data = json.loads(msg)
            except Exception:
                continue
            if data.get("action") == "register":
                if not data.get("success"):
                    return False
                continue
            if data.get("action") == "notification" and data.get("source") == "vm" and data.get("event") == "disk_task_done":
                result = data.get("result", {})
                if result.get("id") == task_id["id"]:
                    break
    api_request("delete", f"/vm/disk/task/{task_id['id']}", session_token)

def disk(session_token, args):

    if args.path:
        disk_path_b64 = base64.b64encode(args.path.encode("utf-8")).decode("ascii")

    if hasattr(args, "size"):
        disk_size = human_size(args.size)

    if args.action == 'create':
        asyncio.run(disk_execute(session_token, disk_create, {
            'path_b64': disk_path_b64,
            'size': disk_size,
            'type': args.type
        }))
    elif args.action == 'resize':
        asyncio.run(disk_execute(session_token, disk_resize, {
            'path_b64': disk_path_b64,
            'size': disk_size,
            'shrink_allow': args.shrink_allow
        }))
    elif args.action == 'delete':
        info = api_request("post", f"/vm/disk/info", session_token, json={ 'disk_path': disk_path_b64 })
        if not info:
            print("Ce n'est pas un disque de VM")
        rm = api_request("post", "/fs/rm/", session_token, json={ 'files': [ disk_path_b64 ] })
    elif args.action == 'info':
        info = api_request("post", f"/vm/disk/info", session_token, json={ 'disk_path': disk_path_b64 })
        if not info:
            return
        print(f"Fichier : {args.path}")
        print(f"Taille virtuelle : {humanize.naturalsize(info['virtual_size'], binary=True)} Espace occupé : {humanize.naturalsize(info['actual_size'], binary=True)} type : {info['type']}")

def parse_args():
    p = argparse.ArgumentParser(prog="freeboxvm",
                                description="Gestionnaire de VM Freebox")

    p.add_argument("--version", action="version",
                   version=f"%(prog)s {__version__}")

    sub = p.add_subparsers(dest="cmd", required=True)

    # system
    sp_system = sub.add_parser("system",
                               help="Afficher les informations système de la Freebox")

    # os-list
    sp_list_os = sub.add_parser("os-list",
                                help="Lister les distributions installables")
    sp_list_os.add_argument("--long", "-l", action='store_true',
                            help="Afficher plus d'informations")
    sp_list_os.add_argument("--extra", "-e", action='store_true',
                    help="Lister les distributions disponibles depuis des sources externes")
    sp_list_os.add_argument("--check", "-c", action='store_true',
                            help="Vérifier la validité de l'URL")
    sp_list_os.add_argument("--iso", "-i", action='store_true',
                            help="Lister les images ISO d'installation disponibles")
    sp_list_os.add_argument("--os", "-o", type=str,
                        help="Filtrer la liste par nom d'OS (fedora, ubuntu, ...)")

    # list
    sp_list = sub.add_parser("list", help="Lister les VM")
    sp_list.add_argument("--long", "-l", action='store_true',
                         help="Afficher plus d'informations")
    sp_list.add_argument("--usb-ports", "-u", action='store_true',
                         help="Lister les ports USB associés")
    sp_list.add_argument("--disks", "-d", action='store_true',
                         help="Lister les images disque")
    sp_list.add_argument("--cloud-init", "-c", action='store_true',
                         help="Afficher les informations cloud-init")

    # show
    sp_show = sub.add_parser("show", help="Afficher les informations d'une VM")
    sp_show.add_argument("--long", "-l", action='store_true',
                         help="Afficher plus d'informations")
    sp_show.add_argument("--usb-ports", "-u", action='store_true',
                         help="Lister les ports USB associés")
    sp_show.add_argument("--disks", "-d", action='store_true',
                         help="Lister les images disque")
    sp_show.add_argument("--cloud-init", "-c", action='store_true',
                         help="Afficher les informations cloud-init")
    sp_show.add_argument("vm", help="ID ou nom de la VM")

    # delete
    sp_delete = sub.add_parser("delete", help="Supprimer une VM")
    sp_delete.add_argument("--disk", "-d", action='store_true',
                           help="Supprimer l'image disque")
    sp_delete.add_argument("--force", "-f", action='store_true',
                           help="Supprimer même si la VM est en cours d'exécution")
    sp_delete.add_argument("vm", help="ID ou nom de la VM")

    # console
    sp_console = sub.add_parser("console", help="Ouvrir la console de la VM")
    sp_console.add_argument("vm", help="ID ou nom de la VM")

    # install
    sp_install = sub.add_parser("install", help="Installer une nouvelle VM")
    sp_install.add_argument("--console", "-c", action="store_true",
                            help="Attacher la console de la VM au démarrage")
    sp_install.add_argument("--vnc-proxy", "-v", action="store_true",
                            help="Exposer le VNC de la VM sur un port TCP local au démarrage")
    sp_install.add_argument("--listen", "-l", default="127.0.0.1",
                            help="Adresse d'écoute (défaut 127.0.0.1)")
    sp_install.add_argument("--port", "-p", type=int, default=5901,
                            help="Port TCP local (défaut 5901)")
    sp_install.add_argument("--install", "-i",
                            help="Identifiant court de la distribution à installer (voir os-list)")
    sp_install.add_argument("--name", "-n", help="Nom de la VM")
    sp_install.add_argument("--memory", help="Taille mémoire de la VM")
    sp_install.add_argument("--vcpus", help="Nombre de vCPU")
    sp_install.add_argument("--cdrom", help="Chemin de l'image CDROM")
    sp_install.add_argument("--location", help="URL du CD de démarrage")
    sp_install.add_argument("--disk", help="Image disque")
    sp_install.add_argument("--disk-size", help="Taille de l'image disque")
    sp_install.add_argument("--cloud-init", action="store_true",
                            help="Activer cloud-init")
    sp_install.add_argument("--cloud-init-hostname",
                            help="Définir le nom d'hôte cloud-init")
    sp_install.add_argument("--cloud-init-userdata",
                            type=argparse.FileType("r"),
                            help="Charger le user-data cloud-init depuis ce fichier")
    sp_install.add_argument("--enable-screen", action="store_true",
                            help="Activer l'écran")
    sp_install.add_argument("--os", help="Nom de l'OS")

    def comma_separated_list(ports):
        return [ x for x in ports.split(",") ]

    sp_install.add_argument("--usb-ports", type=comma_separated_list,
                            help="Ports USB à associer à la VM (séparés par des virgules)")

    # vnx-proxy
    sp_vnc = sub.add_parser("vnc-proxy",
                            help="Exposer le VNC de la VM sur un port TCP local")
    sp_vnc.add_argument("vm", help="ID ou nom de la VM")
    sp_vnc.add_argument("--listen", "-l", default="127.0.0.1",
                        help="Adresse d'écoute (défaut 127.0.0.1)")
    sp_vnc.add_argument("--port", "-p", type=int, default=5901,
                        help="Port TCP local (défaut 5901)")
    sp_vnc.add_argument("--console", action="store_true",
                        help="Attacher également la console de la VM")

    # poweron
    sp_poweron = sub.add_parser("poweron", help="Allumer une VM")
    sp_poweron.add_argument("vm", help="ID ou nom de la VM")
    sp_poweron.add_argument("--console", "-c", action="store_true",
                            help="Attacher également la console de la VM")
    sp_poweron.add_argument("--vnc-proxy", "-v", action="store_true",
                            help="Exposer également le VNC de la VM sur un port TCP local")
    sp_poweron.add_argument("--listen", "-l", default="127.0.0.1",
                            help="Adresse d'écoute (défaut 127.0.0.1)")
    sp_poweron.add_argument("--port", "-p", type=int, default=5901,
                            help="Port TCP local (défaut 5901)")

    # poweroff
    sp_poweroff = sub.add_parser("poweroff",
                                 help="Éteindre une VM")
    sp_poweroff.add_argument("--force", "-f", action='store_true',
                            help="Forcer l'arrêt de la VM")
    sp_poweroff.add_argument("vm", help="ID ou nom de la VM")

    # reset
    sp_reset = sub.add_parser("reset", help="Redémarrer une VM")
    sp_reset.add_argument("vm", help="ID ou nom de la VM")

    # download
    sp_download = sub.add_parser("download", help="Télécharger une image disque/CDROM")
    sp_download.add_argument("--iso", "-i", action='store_true',
                             help="Sélectionner une ISO plutôt qu'une image disque")
    sp_download.add_argument("short_id", metavar="short-id", nargs="?",
                             type=str, help="Identifiant court de la distribution")
    sp_download.add_argument("--background", "-b", action='store_true',
                             help="Télécharger en arrière-plan")
    sp_download.add_argument("--url", "-u", type=str,
                             help="Ne pas utiliser l'identifiant court ; fournir l'URL")
    sp_download.add_argument("--hash", "-a", type=str,
                             help="Ne pas utiliser l'identifiant court ; fournir le hash")
    sp_download.add_argument("--filename", "-f", type=str,
                             help="Nom de fichier à utiliser")
    sp_download.add_argument("--directory", "-d", type=str,
                             help="Dossier Freebox où stocker le fichier")

    # disk
    sp_disk = sub.add_parser("disk", help="Gérer les images disque")
    sp_disk_action = sp_disk.add_subparsers(dest="action", required=True)

    # disk create
    sp_disk_create = sp_disk_action.add_parser("create",
                                               help="Créer une nouvelle image disque")
    sp_disk_create.add_argument("--type", "-t", type=str, default='qcow2',
                                help="Type de disque")
    sp_disk_create.add_argument("path", help="Chemin de l'image disque")
    sp_disk_create.add_argument("size", help="Taille de l'image disque")

    # disk info
    sp_disk_info = sp_disk_action.add_parser("info",
                                        help="Obtenir des informations sur une image disque")
    sp_disk_info.add_argument("path", help="Chemin de l'image disque")

    # disk resize
    sp_disk_resize = sp_disk_action.add_parser("resize",
                                               help="Redimensionner une image disque")
    sp_disk_resize.add_argument("--shrink-allow", "-a", action='store_true',
                    help="Réduction du disque autorisée (peut être destructif)")
    sp_disk_resize.add_argument("path", help="Chemin de l'image disque")
    sp_disk_resize.add_argument("size", help="Nouvelle taille de l'image disque")

    # disk delete
    sp_disk_delete = sp_disk_action.add_parser("delete",
                                               help="Supprimer une image disque")
    sp_disk_delete.add_argument("path", help="Chemin de l'image disque")

    return p.parse_args()

def main():

    args = parse_args()

    session_token = freebox_connect()
    if not session_token:
        print("Freebox inaccessible.")
        return

    if args.cmd == "system":
        system_info(session_token)

    if args.cmd == "os-list":
        list_distro(session_token, args)

    if args.cmd == "download":
        download(session_token, args)

    if args.cmd == "list":
        list(session_token, args)

    if args.cmd == "show":
        show(session_token, args)

    if args.cmd == "delete":
        delete(session_token, args)

    if args.cmd == "install":
        install(session_token, args)

    if args.cmd == "console":
        console(session_token, args)

    if args.cmd == "poweron":
        poweron(session_token, args)

    if args.cmd == "poweroff":
        poweroff(session_token, args)

    if args.cmd == "reset":
        reset(session_token, args)

    if args.cmd == "vnc-proxy":
        vnc_proxy(session_token, args)

    if args.cmd == "disk":
        disk(session_token, args)

if __name__ == "__main__":
    main()
