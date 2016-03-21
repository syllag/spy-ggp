*** La bibliothèque dynamique ***
Dans cpp:
Un exemple de fake player, avec l'API et un makefile

Compilation de la bibliothèque partagée:
# makefile clean
# makefile - f makefile.linux

faire un lien du .so qq part qui va bien (ex: /usr/local/lib) et mettre le chemin complet dans la variapble DLL_PATH de server.py

*** Lancement du serveur: ***
(Rappel: Sous linux, mettre le chemin COMPLET du .so grace aux options --lib_path et --lib_name (cf. python3 server.py --help))

# python3 --help
usage: python3 server.py [-h|--help] [--lib_path=path] [--lib_name=name] [-i|--interface=ip] [-p|--port=port]

# python3 server.py

# python3 server.py -p 8080 --lib_path=cpp --lib_name=fake_player.so


*** Tests ***
Premier test:
# nc localhost 8080 < tst/info.txt

Deuxième test (tester sur localhost 8080):
http://gamemaster.stanford.edu/playerchecker.php

Deuxième test (tester sur ton IP + port forwardé):
http://gamemaster.stanford.edu/playerchecker.php
