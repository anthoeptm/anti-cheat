# Anti-Cheat

Développer un keylogger pour récupérer la saisie clavier des élèves durant les examens

## Serveurs (eleves)

Programme python qui utilise la librairie keyboard notamment la fonction `keyboard.hook(callback)`  https://github.com/boppreh/keyboard#keyboard.hook

### Fonctionnalités

- [x] Récupère toutes les touches pressées par l'utilisateur et les envoie au client
- [x] Démarrer le programme automatiquement au lancement de l'ordinateur et en arrière-plan code inspiré de https://github.com/D4Vinci/PyLoggy/blob/master/PyLoggy.py
- [x] Permettre de configurer le nom du client (constante dans server.py)

- [ ] -> faire un service windows https://thepythoncorner.com/posts/2018-08-01-how-to-create-a-windows-service-in-python/
- [ ] Rajouter que quand il copie ça envoie le presse papier aussi https://pypi.org/project/pyperclip/

### Fichier(s)

- server.exe (pyinstaller)

## Client (prof)

### Tkinter

faire une interface compliquée style comme ça https://github.com/hackaru-app/hackaru/blob/main/docs/images/reports.png

### Fonctionnalités

- [x] pour chaque eleves voir toutes les touches presses depuis le lancement du programme
- [x] voir les eleves connectes (alerte quand déconnexion)
- [x] recherche de mots
- [x] export en json
- [x] import d'un json dans l'interface graphique
- [x] Scan les ip du réseau d'une salle 
- [x] mettre des mots dans une liste noire et être averti quand ils sont pressés

- [x] permettre de customiser le thème de couleur
- [ ] style matrix pour voir les touches
- [ ] rajouter des raccourci clavier pour ouvrir des menus, fermer les fenetres, exporter, importer, ...

- [x] permettre de voir toutes les touches d'un serveur

> Toutes les touches de la base de données sont exportées

### Fichier(s)

- client.exe (pyinstaller)

## Transfert des data du client au server

la librairie socket https://docs.python.org/3/library/socket.html qui envoie des socket tcp mais marche pas dans le navigateur

tutoriel mutltiple client:
- https://www.techwithtim.net/tutorials/python-online-game-tutorial/connecting-multiple-clients
- https://stackoverflow.com/questions/10810249/python-socket-multiple-clients

utiliser select() https://stackoverflow.com/questions/2719017/how-to-set-timeout-on-pythons-socket-recv-method?noredirect=1&lq=1 et https://steelkiwi.com/blog/working-tcp-sockets/ 

detecter les deconnexion des clients : https://stackoverflow.com/questions/21027949/python-tcp-disconnect-detection

### Securite

ssl (https://gist.github.com/marshalhayes/ca9508f97d673b6fb73ba64a67b76ce8) ou ajouter une sum md5 pour etre sur de l'intégrité des infos

JSON envoyé depuis le server: 
```json
{
    "hostname" : "SIOP0201-EDU-11",
    "keys": [
        {
            "time" : "1622447562.2994788",
            "key" : "a"
        },
    ]
}
```

## Idees

- crypter les données envoyées ?
- le serveur ne peut pas être fermé du gestionnaire des taches en utilisant un service windows et topshelf https://www.nuget.org/packages/Topshelf/
- install.bat pour installer le client et faire que ça se lance automatiquement


## Installation

Installer python 3.11
https://www.python.org/downloads/release/python-3110/

Installer les librairies python nécessaire

```sh
pip install -r requirements.txt
```

Installer docker pour la base de données sur le client
https://docs.docker.com/engine/install/

## Lancer

### Serveur

On peut soit double cliquer sur le fichier .py ou l'exécuter dans un terminal

```sh
python3 server.py
```

### Client

Lancer la base de données avec docker

```sh
docker compose up -d
```

et lancer le fichier python en double cliquant dessus ou en l'exécutant dans un terminal

```sh
python3 client.py
```

