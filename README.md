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

## Installation :

Sur Fedora, le RPM `freeboxvm` peut être installé depuis le COPR :

```bash
sudo dnf copr enable lvivier/freebox-failover
sudo dnf install freeboxvm
```

Sinon en utilisant l'environnement PyPI depuis le répertoire source:

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

## Authentification et fichier token

Lors de la première exécution, l’outil suit le flux d’autorisation Freebox et enregistre l’app_token et le track_id dans `~/.config/freeboxvm/freeboxvm_token.json`. Utilisez `--token-file` pour cibler un autre emplacement (utile pour plusieurs Freebox ou comptes) ; le raccourci `~` est accepté.

---

## Utilisation

### Lister les VMs

```bash
freeboxvm list [--long] [--usb-ports] [--disks] [--cloud-init]
```

**Sortie par défaut** : `ID  STATUT  NOM`.

<div>
  <table style="border: none;">
    <tr>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;&#8209;long</strong></td>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;l</strong></td>
      <td>Afficher plus d’informations</td>
    </tr>
    <tr>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;&#8209;usb&#8209;ports</strong></td>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;u</strong></td>
      <td>Lister les ports USB associés</td>
    </tr>
    <tr>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;&#8209;disks</strong></td>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;d</strong></td>
      <td>Lister les images disque</td>
    </tr>
    <tr>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;&#8209;cloud&#8209;init</strong></td>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;c</strong></td>
      <td>Afficher les informations cloud-init</td>
    </tr>
  </table>
</div>

#### Exemples :

##### Vue courte

```bash
$ freeboxvm list
ID  STATUT   NOM
0   running  Debian-11
1   stopped  Ubuntu-22.04
```

##### Vue longue avec ports USB

```bash
$ freeboxvm list --long --usb-ports
ID  STATUT   NOM        OS      MAC               VCPUs  MEMORY  DISPLAY
0   running  Debian-11   debian  aa:bb:cc:dd:ee:ff 2      2048    True
    Ports USB : usb-external-type-a
```

##### Détails disques et cloud-init

```bash
$ freeboxvm list --disks --cloud-init
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

<div>
  <table style="border: none;">
    <tr>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;&#8209;long</strong></td>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;l</strong></td>
      <td>Afficher plus d’informations</td>
    </tr>
    <tr>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;&#8209;usb&#8209;ports</strong></td>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;u</strong></td>
      <td>Lister les ports USB associés</td>
    </tr>
    <tr>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;&#8209;disks</strong></td>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;d</strong></td>
      <td>Lister les images disque</td>
    </tr>
    <tr>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;&#8209;cloud&#8209;init</strong></td>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;c</strong></td>
      <td>Afficher les informations cloud-init</td>
    </tr>
  </table>
</div>

#### Exemples :

```bash
$ freeboxvm show 1
ID    STATUT    NOM
1    stopped    Ubuntu-22.04
```

```bash
$ freeboxvm show Debian-11 --long
ID  STATUT   NOM        OS      MAC               VCPUs  MEMORY  DISPLAY
0   running  Debian-11   debian  aa:bb:cc:dd:ee:ff 2      2048    True
```

```bash
$ freeboxvm show 1 --disks --cloud-init
ID    STATUT    NOM
1    stopped    Ubuntu-22.04
    Image disque : Disque 1/VMs/ubuntu2204.qcow2 (qcow2)
    Aucune image de périphérique CDROM
    Cloud-init hostname : Ubuntu
    Cloud-init user-data :
#cloud-config
system_info:
  default_user:
    name: laurent
  groups:
    - laurent
```

---

### Se connecter à la console d’une VM

```bash
freeboxvm console <id|name>
```

Combinaisons de touches de contrôle de la console:

<div>
<table style="border: none;">
  <tr>
    <td style="border: none"><strong>Ctrl-B D</strong></td><td>Pour Quitter</td></tr>
  <tr>
    <td style="border: none"><strong>Ctrl-B B</strong></td><td>Pour envoyer un <strong>Ctrl-B</strong></td>
  </tr>
  <tr>
    <td style="border: none;"><strong>Ctrl-B R</strong></td><td>Pour Réinitialiser la VM</td>
  </tr>
  <tr>
    <td style="border: none"><strong>Ctrl-B H</strong></td><td>Pour arrêter (Halt) la VM</td>
  </tr>
  <tr>
    <td style="border: none"><strong>Ctrl-B S</strong></td><td>Pour Stopper immédiatement la VM</td>
  </tr>
  <tr>
    <td style="border: none"><strong>Ctrl-B ?</strong></td><td>Pour afficher l'aide concernant les combinaisons de touches</td>
  </tr>
</table>
</div>

#### Exemples :

```bash
freeboxvm console 0
freeboxvm console Debian-11
```

---

### Exposer l’écran d’une VM via proxy VNC

```bash
freeboxvm vnc-proxy [-h] [--listen ADDR] [--port N] [--console] vm
```

Expose l’écran VNC d’une VM sur un port TCP local.

<div>
  <table style="border: none;">
    <tr>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;&#8209;listen ADDR</strong></td>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;l ADDR</strong></td>
      <td>Adresse d’écoute (par défaut 127.0.0.1)</td>
    </tr>
    <tr>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;&#8209;port N</strong></td>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;p N</strong></td>
      <td>Port TCP (par défaut 5901)</td>
    </tr>
    <tr>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;&#8209;console</strong></td>
      <td style="border: none; white-space: nowrap;"><strong> </strong></td>
      <td>Lance la console interactive en parallèle</td>
    </tr>
  </table>
</div>

#### Exemples :

##### Proxy VNC pour la VM 0 sur localhost:5901

```bash
freeboxvm vnc-proxy 0
```

##### Proxy pour la VM 12 sur toutes interfaces, port 5902

```bash
freeboxvm vnc-proxy --listen 0.0.0.0 --port 5902 12
```

##### Proxy et console pour une VM par nom

```bash
freeboxvm vnc-proxy --console Debian-11
```

---

### Gestion des disques

```bash
freeboxvm disk [-h] {create,info,resize,delete} ...
```

Gérer les images disque des VM (création, redimensionnement, inspection, suppression).  
Les tailles acceptent des suffixes binaires `k`, `m`, `g`, `t` (puissances de deux) ; les valeurs en octets bruts sont également acceptées.  

Actions :

- **create**
  
  ```bash
  freeboxvm disk create [-h] [--type TYPE] <path> <size>
  ```
  
  Créer une image disque (par défaut qcow2).

- **resize**
  
  ```bash
  freeboxvm disk resize [-h] [--shrink-allow] <path> <size>
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

#### Exemples :

##### Crée un disque qcow2 de 10 Gio

```bash
freeboxvm disk create "/Disque 1/VMs/disk1.qcow2" 10g
```

##### Redimensione un disque à 20 Gio

```bash
freeboxvm disk resize "/Disque 1/VMs/disk1.qcow2" 20g
```

##### Force un redimensionnement destructif (réduction de la taille)

```bash
freeboxvm disk resize --shrink-allow "/Disque 1/VMs/disk1.qcow2" 8g
```

##### Affiche les informations relatives au disque

```bash
freeboxvm disk info "/Disque 1/VMs/disk1.qcow2"
```

##### Supprime un disque

```bash
freeboxvm disk delete "/Disque 1/VMs/disk1.qcow2"
```

---

### Installer une nouvelle VM

```bash
freeboxvm install [options]
```

Créer et démarrer une VM depuis une image cloud ou un ISO.
Peut aussi attacher console et/ou proxy VNC.

<div>
  <table style="border: none;">
    <tr>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;&#8209;install ID</strong></td>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;i ID</strong></td>
      <td>identifiant de distribution (voir <code>os-list</code>).</td>
    </tr>
    <tr>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;&#8209;name</strong></td>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;n NOM</strong></td>
      <td>nom de la VM.</td>
    </tr>
    <tr>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;&#8209;os</strong></td>
      <td style="border: none; white-space: nowrap;"><strong> </strong></td>
      <td>nom de l’OS (si non détecté).</td>
    </tr>
    <tr>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;&#8209;vcpus</strong></td>
      <td style="border: none; white-space: nowrap;"><strong> </strong></td>
      <td>nombre de CPUs virtuels.</td>
    </tr>
    <tr>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;&#8209;memory</strong></td>
      <td style="border: none; white-space: nowrap;"><strong> </strong></td>
      <td>mémoire (MiB).</td>
    </tr>
    <tr>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;&#8209;disk PATH</strong></td>
      <td style="border: none; white-space: nowrap;"><strong> </strong></td>
      <td>chemin image disque.</td>
    </tr>
    <tr>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;&#8209;disk&#8209;size</strong></td>
      <td style="border: none; white-space: nowrap;"><strong> </strong></td>
      <td>taille disque.</td>
    </tr>
    <tr>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;&#8209;cdrom PATH</strong></td>
      <td style="border: none; white-space: nowrap;"><strong> </strong></td>
      <td>ISO d’installation.</td>
    </tr>
    <tr>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;&#8209;location URL</strong></td>
      <td style="border: none; white-space: nowrap;"><strong> </strong></td>
      <td>URL CD/ISO (exclusif avec <code>--cdrom</code>).</td>
    </tr>
    <tr>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;&#8209;cloud&#8209;init</strong></td>
      <td style="border: none; white-space: nowrap;"><strong> </strong></td>
      <td>activer cloud-init.</td>
    </tr>
    <tr>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;&#8209;cloud&#8209;init&#8209;hostname</strong></td>
      <td style="border: none; white-space: nowrap;"><strong> </strong></td>
      <td>hostname.</td>
    </tr>
    <tr>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;&#8209;cloud&#8209;init&#8209;userdata FILE</strong></td>
      <td style="border: none; white-space: nowrap;"><strong> </strong></td>
      <td>fichier user-data.</td>
    </tr>
    <tr>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;&#8209;enable&#8209;screen</strong></td>
      <td style="border: none; white-space: nowrap;"><strong> </strong></td>
      <td>activer écran (VNC-over-WebSocket).</td>
    </tr>
    <tr>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;&#8209;console</strong></td>
      <td style="border: none; white-space: nowrap;"><strong> </strong></td>
      <td>attacher console après boot.</td>
    </tr>
    <tr>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;&#8209;vnc&#8209;proxy</strong></td>
      <td style="border: none; white-space: nowrap;"><strong> </strong></td>
      <td>démarrer proxy VNC après boot.</td>
    </tr>
    <tr>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;&#8209;listen ADDR</strong></td>
      <td style="border: none; white-space: nowrap;"><strong> </strong></td>
      <td>adresse d’écoute VNC (par défaut 127.0.0.1).</td>
    </tr>
    <tr>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;&#8209;port N</strong></td>
      <td style="border: none; white-space: nowrap;"><strong> </strong></td>
      <td>port TCP VNC (par défaut 5901).</td>
    </tr>
    <tr>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;&#8209;usb&#8209;ports LISTE</strong></td>
      <td style="border: none; white-space: nowrap;"><strong> </strong></td>
      <td>lier des ports USB à la VM (liste séparée par des virgules).</td>
    </tr>
  </table>
</div>

#### Notes :

- Lorsque `--install` ou `--location` est utilisé, l’image est téléchargée via le gestionnaire de téléchargements de la Freebox dans le répertoire par défaut `/Disque 1/VMs/`, avec suivi de progression, vérification de la somme de contrôle et nettoyage en cas d’erreur.
- Pour les images cloud, le fichier téléchargé devient l’image disque de la VM.
- Si `--disk` pointe vers un fichier inexistant, `--disk-size` doit être fourni afin que l’outil puisse créer l’image (le type qcow2/raw est déduit de l’extension).
- Les disques peuvent être redimensionnés automatiquement s’ils sont plus petits que la taille indiquée par `--disk-size`.

#### Exemple :

##### Installer depuis un identifiant de distribution (cloud image), activer cloud-init et attacher la console

```bash
freeboxvm install -n Fedora-cloud --vcpus 1 --memory 512 --console   --cloud-init --cloud-init-hostname Fabulous   --cloud-init-userdata cloud-init-user-data.yaml   -i fedora41 --disk Fabulous.qcow2 --disk-size 10g
```

##### Installer depuis une URL d’ISO CDROM, attacher la console et lancer le proxy VNC

```bash
freeboxvm install -n Fedora-test --os fedora   --location https://download.fedoraproject.org/pub/fedora/linux/releases/41/Everything/aarch64/iso/Fedora-Everything-netinst-aarch64-41-1.4.iso   --disk "/Disque 1/VMs/test.qcow2" --disk-size 20g   --vcpus 2 --memory 2048 --console --vnc-proxy --enable-screen
```

---

### Allumer une VM

```bash
freeboxvm poweron <id|name> [--console|-c] [--vnc-proxy|-v]
                   [--listen|-l ADDR] [--port|-p N]
```

Démarre la VM puis (optionnellement) attache la console et/ou lance le proxy VNC.

<div>
  <table style="border: none;">
    <tr>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;&#8209;console</strong></td>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;c</strong></td>
      <td>attacher une console interactive (détacher avec Ctrl-B D)</td>
    </tr>
    <tr>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;&#8209;vnc&#8209;proxy</strong></td>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;v</strong></td>
      <td>exposer le VNC sur un port TCP local</td>
    </tr>
    <tr>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;&#8209;listen ADDR</strong></td>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;l ADDR</strong></td>
      <td>adresse d’écoute pour le proxy VNC (par défaut 127.0.0.1)</td>
    </tr>
    <tr>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;&#8209;port N</strong></td>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;p N</strong></td>
      <td>port TCP du proxy VNC (par défaut 5901)</td>
    </tr>
  </table>
</div>

#### Exemples :

##### Allume la VM et attache la console

```bash
freeboxvm poweron 12 --console
```

##### Allume la VM et démarre le proxy VNC sur 0.0.0.0:5902

```bash
freeboxvm poweron 12 --vnc-proxy -l 0.0.0.0 -p 5902
```

##### Allume la VM et démarre la console et le proxy VNC

```bash
freeboxvm poweron Debian-11 -c -v
```

---

### Éteindre une VM

```bash
freeboxvm poweroff [-f|--force] <id|name>
```

Demande l’arrêt ACPI de la VM spécifiée.

<div>
  <table style="border: none;">
    <tr>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;&#8209;force</strong></td>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;f</strong></td>
      <td>Envoie un arrêt forcé (hard stop).</td>
    </tr>
  </table>
</div>


#### Exemples :

```bash
freeboxvm poweroff 0
freeboxvm poweroff --force Debian-11
```

---

### Réinitialiser une VM

```bash
freeboxvm reset <id|name>
```

#### Exemples:

```bash
freeboxvm reset 0
freeboxvm reset Debian-11
```

---

### Supprimer une VM

```bash
freeboxvm delete <id|name> [--disk|-d] [--force|-f]
```

Supprime la machine virtuelle spécifiée par son id numérique ou son nom.
Si la suppression échoue, pensez à éteindre la VM au préalable.

<div>
  <table style="border: none;">
    <tr>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;&#8209;disk</strong></td>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;d</strong></td>
      <td>Supprimer également les disques et efivars</td>
    </tr>
    <tr>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;&#8209;force</strong></td>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;f</strong></td>
      <td>Supprimer une VM en cours d’exécution</td>
    </tr>
  </table>
</div>

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
- Chemin du répertoire VMs

#### Exemples:

```bash
$ freeboxvm system
Mémoire totale : 2048    Mémoire utilisée : 0    (0.0 %)
Nombre de CPU : 2    CPU utilisés : 0    (0.0 %)
USB externe alloué : Non
Liste des ports USB disponibles :
   usb-external-type-a
VMs directory path: /Disque 1/VMs
```

---

### Lister distributions installables

```bash
freeboxvm os-list [options]
```

Liste les images de systèmes d’exploitation installables pour les VMs.

<div>
  <table style="border: none;">
    <tr>
      <td style="border: none"><strong>&#8209;&#8209;extra</strong></td><td style="border: none"><strong>&#8209;e</strong></td><td>Interroger des sources externes via libosinfo pour des images cloud-init (aarch64, qcow2/raw).</td>
    </tr>
    <tr>
      <td style="border: none"><strong>&#8209;&#8209;iso</strong></td><td style="border: none"><strong>&#8209;i</strong></td><td>Lister les ISOs installables au lieu des images cloud.</td>
    </tr>
    <tr>
      <td style="border: none"><strong>&#8209;&#8209;long</strong></td><td style="border: none"><strong>&#8209;l</strong></td><td>Afficher les informations détaillées (OS, distribution, URL, somme de contrôle, indicateur live).</td>
    </tr>
    <tr>
      <td style="border: none"><strong>&#8209;&#8209;check</strong></td><td style="border: none"><strong>&#8209;c</strong></td><td>Valider les URLs des images et des sommes de contrôle.</td>
    </tr>
    <tr>
      <td style="border: none"><strong>&#8209;&#8209;os</strong></td><td style="border: none"><strong>&#8209;o</strong></td><td>Filtrer les résultats par nom d’OS (ex. fedora, ubuntu).</td>
    </tr>
  </table>
</div>

#### Exemples:

##### Lister toutes les distributions disponibles

```bash
freeboxvm os-list
```

##### Afficher les informations détaillées

```bash
freeboxvm os-list --long
```

##### Valider les URLs

```bash
freeboxvm os-list --check --long
```

##### Lister les ISOs installables

```bash
freeboxvm os-list --iso
```

##### Filtrer par OS (ex. uniquement Fedora)

```bash
freeboxvm os-list --os fedora
```

---

### Télécharger une image

```bash
freeboxvm download [options] [short-id]
```

Télécharge une image d’installation de VM (disque ou ISO) en utilisant le gestionnaire de téléchargements de la Freebox.

<div>
  <table style="border: none;">
    <tr>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;&#8209;iso</strong></td>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;i</strong></td>
      <td>Sélectionner une ISO d’installation plutôt qu’une image cloud/disque.</td>
    </tr>
    <tr>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;&#8209;url URL</strong></td>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;u URL</strong></td>
      <td>Fournir une URL directe au lieu d’un short-id.</td>
    </tr>
    <tr>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;&#8209;hash HASH</strong></td>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;a HASH</strong></td>
      <td>Fournir l’URL de la somme de contrôle lors de l’utilisation de --url.</td>
    </tr>
    <tr>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;&#8209;filename F</strong></td>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;f F</strong></td>
      <td>Nom de fichier sous lequel enregistrer.</td>
    </tr>
    <tr>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;&#8209;directory D</strong></td>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;d D</strong></td>
      <td>Répertoire Freebox où stocker le fichier (encodé automatiquement en base64).</td>
    </tr>
    <tr>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;&#8209;background</strong></td>
      <td style="border: none; white-space: nowrap;"><strong>&#8209;b</strong></td>
      <td>Lancer le téléchargement en arrière-plan (progression non affichée ; vérifier dans la section "Téléchargements" de la Freebox).</td>
    </tr>
  </table>
</div>

#### Examples:

##### Télécharger une image Fedora cloud-init via short-id

```bash
freeboxvm download fedora40
```

##### Télécharger une ISO Ubuntu au lieu d’une image cloud

```bash
freeboxvm download --iso ubuntu24.04
```

##### Fournir une URL personnalisée et sa somme de contrôle

```bash
freeboxvm download --url https://cloud-images.ubuntu.com/.../disk.qcow2 \
                   --hash https://cloud-images.ubuntu.com/.../SHA256SUMS
```

##### Télécharger en mode arrière-plan

```bash
freeboxvm download --background fedora
```

---

## Licence

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
