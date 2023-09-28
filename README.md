# Anti-Cheat

Développer un keylogger pour récupérer la saise clavier des élèves durant les examens

## Serveurs (eleves)

Récupère toutes les touches pressées par l'utilisateur et les envoie au client

Programme python qui utilise
- la librairie keyboard notamment la fonction `keyboard.hook(callback)`  https://github.com/boppreh/keyboard#keyboard.hook

Démarrer le programme automatiquement au lancement de l'ordinateur et en arrière-plan https://stackoverflow.com/questions/1689015/run-python-script-without-windows-console-appearing et https://github.com/D4Vinci/PyLoggy/blob/master/PyLoggy.py

-> faire un service windows https://thepythoncorner.com/posts/2018-08-01-how-to-create-a-windows-service-in-python/ ou utliser nssm http://nssm.cc/ (plus simple)

Permettre de configurer le nom du client et le numéro de la salle dans un fichier de config (json, xml, ...)

Rajouter que quand il copie ça envoie le presse papier aussi

### Fichier(s)

- anti-cheat-serveur.py
- anti-cheat-config.json  

## Client (prof)

### DearPyGui

Interface python avec DearPyGui https://github.com/hoffstadt/DearPyGui

render loop pour metttre du code qui s'execute chaque frame : https://dearpygui.readthedocs.io/en/latest/documentation/render-loop.html

faire une interface compliquée https://github.com/hackaru-app/hackaru/blob/main/docs/images/reports.png

icons (tkinter) https://pypi.org/project/tkfontawesome/

### Fonctionnalités

- Scan les ip du réseau d'une salle 
- voir les eleves connectes (alerte quand déconnexion)
- pour chaque eleves voir toutes les touches presses depuis le lancement du programme
- mettre des mots dans une liste noire et être averti quand ils sont pressés
- recherche de mots
- export en csv ou txt ou json (a voir) ou sauvegarde automatique en txt

### Fichier(s)

anti-cheat-client.exe (pyinstaller)

## Transfert des data du client au server

la librairie socket https://docs.python.org/3/library/socket.html qui envoie des socket tcp mais marche pas dans le navigateur

tutoriel mutltiple client:
- https://www.techwithtim.net/tutorials/python-online-game-tutorial/connecting-multiple-clients
- https://stackoverflow.com/questions/10810249/python-socket-multiple-clients

utiliser select() https://stackoverflow.com/questions/2719017/how-to-set-timeout-on-pythons-socket-recv-method?noredirect=1&lq=1 et https://steelkiwi.com/blog/working-tcp-sockets/ 

detecter les deconnexion des clients : https://stackoverflow.com/questions/21027949/python-tcp-disconnect-detection

### Securite

ssl (https://gist.github.com/marshalhayes/ca9508f97d673b6fb73ba64a67b76ce8) ou ajouter une sum md5 pour etre sur de l'intégrité des infos

```json
{
    "hostname" : "SIOP-EDU 3213",
    "ip" : "192.168.205.211",
    "time" : "1622447562.2994788",
    "key" : "a"
}
```

## Idees

- crypter les données envoyées ?
- faire que les touches sont pas de suite envoyés mais que quand le client demande avec un cache chez le serveur -> le serveur demande une update et le serveur envoie son cache
- le serveur ne peut pas être fermé du gestionnaire des taches en utilisant un service windows et topshelf https://www.nuget.org/packages/Topshelf/
- style matrix pour le prof ?
- envoyer aussi le timestamp pour faire des stats ?
- programme pour config le serveur
- install.bat pour installer le client et faire que ça se lance automatiquement


## A trier

ip prof : 10.204.129.201