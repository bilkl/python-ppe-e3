"""Petit serveur HTTP local qui joue le rôle de l'API, pour tester le vrai code réseau
(requests) sans Internet et sans dépendre des taux du jour.

Usage :
    with ServeurFactice({"/v1/latest": (200, {"base": "CHF"})}) as serveur:
        client = ClientTaux(serveur.url)

Une route peut renvoyer une réponse fixe (statut, corps) ou une LISTE de réponses
jouées dans l'ordre (la dernière est répétée). Le corps peut être un dict/list (JSON)
ou une chaîne (envoyée telle quelle). Un 3e élément facultatif = délai en secondes.
"""

import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse


class ServeurFactice:
    def __init__(self, routes):
        self.routes = {chemin: (list(r) if isinstance(r, list) else [r]) for chemin, r in routes.items()}
        self.requetes = []  # (chemin, {param: valeur})
        serveur = self

        class Gestionnaire(BaseHTTPRequestHandler):
            def do_GET(self):
                adresse = urlparse(self.path)
                params = {k: v[0] for k, v in parse_qs(adresse.query).items()}
                serveur.requetes.append((adresse.path, params))
                if adresse.path not in serveur.routes:
                    statut, corps, delai = 404, {"message": "not found"}, 0
                else:
                    liste = serveur.routes[adresse.path]
                    reponse = liste.pop(0) if len(liste) > 1 else liste[0]
                    statut, corps, delai = (*reponse, 0)[:3] if len(reponse) == 2 else reponse
                time.sleep(delai)
                octets = (corps if isinstance(corps, str) else json.dumps(corps)).encode("utf-8")
                try:
                    self.send_response(statut)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Content-Length", str(len(octets)))
                    self.end_headers()
                    self.wfile.write(octets)
                except (BrokenPipeError, ConnectionResetError):
                    pass  # le client a abandonné (test de délai dépassé)

            def log_message(self, *args):
                pass

        self._http = ThreadingHTTPServer(("127.0.0.1", 0), Gestionnaire)
        self._http.daemon_threads = True
        self.url = f"http://127.0.0.1:{self._http.server_address[1]}"

    def __enter__(self):
        threading.Thread(target=self._http.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True).start()
        return self

    def __exit__(self, *exc):
        self._http.shutdown()
        self._http.server_close()
