# freeboxvm

[![en](https://img.shields.io/badge/lang-en-blue.svg)](README.en.md)
[![fr](https://img.shields.io/badge/lang-fr-red.svg)](README.md)

Un outil en ligne de commande pour gérer et accéder aux machines virtuelles
d’une Freebox via l’API Freebox OS v8.

---

## Prérequis

- Python 3.8+
- Freebox avec API Freebox OS v8
- Paquets : `requests`, `websockets`, `tqdm`, `humanize`, `PyGObject`
  (pour le support **libosinfo**)

Installation :

```bash
pip install .
```

Pour installer les dépendances sans métadonnées de packaging (développement
ou environnements anciens) :

```bash
pip install -r requirements.txt
```

Sur Fedora, vous pourriez avoir besoin de :

```bash
sudo dnf install python3-gobject gobject-introspection libosinfo osinfo-db
```

Sur Debian/Ubuntu, vous pourriez avoir besoin de :

```bash
sudo apt install python3-gi gir1.2-libosinfo-1.0
```

---

## Utilisation

### Lister les VMs
```bash
freeboxvm list [--long] [--usb-ports] [--disks] [--cloud-init]
```
- **Sortie par défaut** : `ID  STATUS  NAME`.
- **--long** : ajoute les colonnes `OS  MAC  VCPUs  MEMORY  DISPLAY`.
- **--usb-ports** : affiche les ports USB liés (ou "Aucun port USB").
- **--disks** : affiche le chemin/type du disque et éventuel CD.
- **--cloud-init** : affiche l’état cloud-init, hostname et user-data.

Exemples :
```bash
# Vue courte
freeboxvm list
ID  STATUS   NAME
0   running  Debian-11
1   stopped  Ubuntu-22.04

# Vue longue avec ports USB
freeboxvm list --long --usb-ports
ID  STATUS   NAME        OS      MAC               VCPUs  MEMORY  DISPLAY
0   running  Debian-11   debian  aa:bb:cc:dd:ee:ff 2      2048    True
    Ports USB : usb-external-type-a

# Détails disques et cloud-init
freeboxvm list --disks --cloud-init
0   running  Debian-11
    Image disque : Disque 1/VMs/debian.qcow2 (qcow2)
    Image CD : Disque 1/VMs/debian-11.iso
    Cloud-init hostname : debian
    Cloud-init user-data :
#cloud-config
system_info:
default_user:
- name: debian
```

---

### Afficher une VM
```bash
freeboxvm show <id|name> [--long] [--usb-ports] [--disks] [--cloud-init]
```
Affiche les informations d’une VM unique. Supporte les mêmes options que `list`.

- **--long, -l**       : ajouter OS, MAC, vCPUs, mémoire, affichage
- **--usb-ports, -u**  : afficher les ports USB liés
- **--disks, -d**      : afficher le chemin/type de l’image disque et l’image CD
- **--cloud-init, -c** : afficher l’état de cloud-init, le hostname et les user-data

Exemples :
```bash
freeboxvm show 12
freeboxvm show Debian-11 --long
freeboxvm show 12 --disks --cloud-init
```

---

### Se connecter à la console d’une VM
```bash
freeboxvm console <id|name>
```

- Quitter avec **Ctrl-A D**
- Envoyer un **Ctrl-A** : **Ctrl-A A**
- Réinitialiser la VM : **Ctrl-A R**
- Arrêter (halt) la VM : **Ctrl-A H**
- Stopper la VM : **Ctrl-A S**
- Aide Ctrl-A : **Ctrl-A ?**

Exemples :
```bash
freeboxvm console 0
freeboxvm console Debian-11
```

---

### Exposer l’écran d’une VM via proxy VNC
```bash
freeboxvm vnc-proxy [options] <id|name>
```
Expose l’écran VNC-over-WebSocket d’une VM sur un port TCP local.

- `-l, --listen A` : Adresse d’écoute (par défaut `127.0.0.1`).
- `-p, --port P`   : Port TCP (par défaut `5901`).
- `--console`      : Lance la console interactive en parallèle.

Exemples :
```bash
# Proxy VNC pour la VM 0 sur localhost:5901
freeboxvm vnc-proxy 0

# Proxy pour la VM 12 sur toutes interfaces, port 5902
freeboxvm vnc-proxy --listen 0.0.0.0 --port 5902 12

# Proxy et console pour une VM par nom
freeboxvm vnc-proxy --console Debian-11
```

---

### Gestion des disques
```bash
freeboxvm disk <action> [options] <args>
```

Gérer les images disque des VM (création, redimensionnement, inspection, suppression).  
Les tailles acceptent des suffixes binaires `k`, `m`, `g`, `t` (puissances de deux) ; les valeurs en octets bruts sont également acceptées.  

Actions :

- **create**
  ```bash
  freeboxvm disk create [--type qcow2] <path> <size>
  ```

  Créer une image disque (par défaut qcow2).

- **resize**
  ```bash
  freeboxvm disk resize [--shrink-allow] <path> <new-size>
  ```

  Redimensionner une image disque (`--shrink-allow` autorise réduction).

- **info**
  ```bash
  freeboxvm disk info <path>
  ```
  Afficher taille virtuelle, utilisée, type.

- **delete**
  ```bash
  freeboxvm disk delete <path>
  ```
  Supprimer une image disque.

Exemples :
```bash
# Crée un disque qcow2 de 10 Gio
freeboxvm disk create "/Disque 1/VMs/disk1.qcow2" 10g

# Redimensione un disque à 20 Gio
freeboxvm disk resize "/Disque 1/VMs/disk1.qcow2" 20g

# Force un redimensionnement destructif (réduction de la taille)
freeboxvm disk resize --shrink-allow "/Disque 1/VMs/disk1.qcow2" 8g

# Affiche les informations relatives au disque
freeboxvm disk info "/Disque 1/VMs/disk1.qcow2"

# Supprime un disque
freeboxvm disk delete "/Disque 1/VMs/disk1.qcow2"
```

---

### Installer une nouvelle VM
```bash
freeboxvm install [options]
```
Créer et démarrer une VM depuis une image cloud ou un ISO.
Peut aussi attacher console et/ou proxy VNC.

Options :
- `-i, --install ID` : identifiant de distribution (voir `os-list`).
- `-n, --name`       : nom de la VM.
- `--os`             : nom de l’OS (si non détecté).
- `--vcpus`          : nombre de CPUs virtuels.
- `--memory`         : mémoire (MiB).
- `--disk PATH`      : chemin image disque.
- `--disk-size`      : taille disque.
- `--cdrom PATH`     : ISO d’installation.
- `--location URL`   : URL CD/ISO (exclusif avec `--cdrom`).
- `--cloud-init`     : activer cloud-init.
- `--cloud-init-hostname` : hostname.
- `--cloud-init-userdata` : fichier user-data.
- `--enable-screen`  : activer écran (VNC-over-WebSocket).
- `--console`        : attacher console après boot.
- `--vnc-proxy`      : démarrer proxy VNC après boot.
- `--listen`         : adresse d’écoute VNC (par défaut 127.0.0.1).
- `--port`           : port TCP VNC (par défaut 5901).
- `--usb-ports LISTE`: lier des ports USB à la VM (liste séparée par des virgules)

Notes :
- Lorsque `--install` ou `--location` est utilisé, l’image est téléchargée via le gestionnaire de téléchargements de la Freebox dans le répertoire par défaut `/Disque 1/VMs/`, avec suivi de progression, vérification de la somme de contrôle et nettoyage en cas d’erreur.
- Pour les images cloud, le fichier téléchargé devient l’image disque de la VM.
- Si `--disk` pointe vers un fichier inexistant, `--disk-size` doit être fourni afin que l’outil puisse créer l’image (le type qcow2/raw est déduit de l’extension).
- Les disques peuvent être redimensionnés automatiquement s’ils sont plus petits que la taille indiquée par `--disk-size`.

Exemple :
```bash
# Installer depuis un identifiant de distribution (cloud image), activer cloud-init et attacher la console
freeboxvm install -n Fedora-cloud --vcpus 1 --memory 512 --console   --cloud-init --cloud-init-hostname Fabulous   --cloud-init-userdata cloud-init-user-data.yaml   -i fedora41 --disk Fabulous.qcow2 --disk-size 10g

# Installer depuis une URL d’ISO CDROM, attacher la console et lancer le proxy VNC
freeboxvm install -n Fedora-test --os fedora   --location https://download.fedoraproject.org/pub/fedora/linux/releases/41/Everything/aarch64/iso/Fedora-Everything-netinst-aarch64-41-1.4.iso   --disk "/Disque 1/VMs/test.qcow2" --disk-size 20g   --vcpus 2 --memory 2048 --console --vnc-proxy --enable-screen
```

---

### Allumer une VM
```bash
freeboxvm poweron <id|name> [--console|-c] [--vnc-proxy|-v]
                   [--listen|-l ADDR] [--port|-p N]
```

- Démarre la VM puis (optionnellement) attache la console et/ou lance le proxy VNC.
- `--console, -c`     : attacher une console interactive (détacher avec Ctrl-A D)
- `--vnc-proxy, -v`   : exposer le VNC sur un port TCP local
- `--listen, -l ADDR` : adresse d’écoute pour le proxy VNC (par défaut 127.0.0.1)
- `--port, -p N`      : port TCP du proxy VNC (par défaut 5901)

Exemples :
```bash
# Allume la VM et attache la console
freeboxvm poweron 12 --console

# Allume la VM et démarre le proxy VNC sur 0.0.0.0:5902
freeboxvm poweron 12 --vnc-proxy -l 0.0.0.0 -p 5902

# Allume la VM et démarre la console et le proxy VNC
freeboxvm poweron Debian-11 -c -v
```

---

### Éteindre une VM
```bash
freeboxvm poweroff [-f|--force] <id|name>
```

- Demande l’arrêt ACPI de la VM spécifiée.
- Avec -f/--force, envoie à la place un arrêt forcé (hard stop).

Exemples :
```bash
freeboxvm poweroff 0
freeboxvm poweroff --force Debian-11
```

---

### Réinitialiser une VM
```bash
freeboxvm reset <id|name>
```

Exemples:
```bash
freeboxvm reset 0
freeboxvm reset Debian-11
```

---

### Supprimer une VM
```bash
freeboxvm delete <id|name> [--disk|-d] [--force|-f]
- `--disk, -d`     : Supprimer également les disques et efivars
- `--force, -f`    : Supprimer une VM en cours d’exécution
```

Supprime la machine virtuelle spécifiée par son id numérique ou son nom.
Si la suppression échoue, pensez à éteindre la VM au préalable.

---

### Infos système Freebox
```bash
freeboxvm system
```

Affiche les ressources globales de la Freebox :
- Mémoire totale et utilisée
- Processeurs (CPUs) totaux et utilisés
- État d’allocation des ports USB
- Liste des ports USB disponibles

---

### Lister distributions installables
```bash
freeboxvm os-list [options]
```

Liste les images de systèmes d’exploitation installables pour les VMs.

Options:
- `-e, --extra`: Interroger des sources externes via libosinfo pour des images cloud-init (aarch64, qcow2/raw).
- `-i, --iso`  : Lister les ISOs installables au lieu des images cloud.
- `-l, --long` : Afficher les informations détaillées (OS, distribution, URL, somme de contrôle, indicateur live).
- `-c, --check`: Valider les URLs des images et des sommes de contrôle.
- `-o, --os`   : Filtrer les résultats par nom d’OS (ex. fedora, ubuntu).

Exemples:
```bash
# Lister toutes les distributions disponibles
freeboxvm os-list

# Afficher les informations détaillées
freeboxvm os-list --long

# Valider les URLs
freeboxvm os-list --check --long

# Lister les ISOs installables
freeboxvm os-list --iso

# Filtrer par OS (ex. uniquement Fedora)
freeboxvm os-list --os fedora
```

---
### Télécharger une image
```bash
freeboxvm download [options] [short-id]
```

Télécharge une image d’installation de VM (disque ou ISO) en utilisant le gestionnaire de téléchargements de la Freebox.

Options :
- `-i, --iso`        : Sélectionner une ISO d’installation plutôt qu’une image cloud/disque.
- `-u, --url URL`    : Fournir une URL directe au lieu d’un short-id.
- `-a, --hash HASH`  : Fournir l’URL de la somme de contrôle lors de l’utilisation de --url.
- `-f, --filename F` : Nom de fichier sous lequel enregistrer.
- `-d, --directory D`: Répertoire Freebox où stocker le fichier (encodé automatiquement en base64).
- `-b, --background` : Lancer le téléchargement en arrière-plan (progression non affichée ; vérifier dans la section "Téléchargements" de la Freebox).i

Examples:
```bash
# Télécharger une image Fedora cloud-init via short-id
freeboxvm download fedora40

# Télécharger une ISO Ubuntu au lieu d’une image cloud
freeboxvm download --iso ubuntu24.04

# Fournir une URL personnalisée et sa somme de contrôle
freeboxvm download --url https://cloud-images.ubuntu.com/.../disk.qcow2 \
                   --hash https://cloud-images.ubuntu.com/.../SHA256SUMS

# Télécharger en mode arrière-plan
freeboxvm download --background fedora
```
---

## Licence

Ce programme est un logiciel libre : vous pouvez le redistribuer et/ou le modifier
selon les termes de la Licence Publique Générale GNU publiée par la Free Software Foundation,
soit la version 3 de la licence, soit (à votre choix) toute version ultérieure.

Ce programme est distribué sans AUCUNE GARANTIE, ni explicite ni implicite,
y compris sans garantie de COMMERCIALISATION ou d’ADÉQUATION À UN OBJECTIF PARTICULIER.
Voir la Licence Publique Générale GNU pour plus de détails.

Vous devriez avoir reçu une copie de la Licence Publique Générale GNU
avec ce programme. Sinon, consultez <https://www.gnu.org/licenses/>.
