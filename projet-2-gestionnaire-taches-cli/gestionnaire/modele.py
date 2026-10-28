"""Logique métier : une tâche est un dictionnaire, la liste est une liste de dictionnaires.

Aucune fonction de ce module ne lit le clavier, n'affiche ni n'accède au disque.
Les erreurs sont signalées par ValueError.
"""

from datetime import datetime

PRIORITES = ("basse", "normale", "haute")
STATUTS = ("a_faire", "terminee")
TITRE_MAX = 100


def maintenant():
    """Date et heure courantes au format ISO, à la seconde."""
    return datetime.now().isoformat(timespec="seconds")


def nouvelle_tache(taches, titre, priorite="normale", horodatage=None):
    """Crée une tâche (non ajoutée à la liste) avec le prochain identifiant libre.

    Lève ValueError si le titre est vide ou trop long, ou si la priorité est inconnue.
    """
    titre = " ".join(titre.split())
    if not titre:
        raise ValueError("le titre ne peut pas être vide")
    if len(titre) > TITRE_MAX:
        raise ValueError(f"le titre dépasse {TITRE_MAX} caractères")
    if priorite not in PRIORITES:
        raise ValueError(f"priorité inconnue : {priorite!r} (choix : {', '.join(PRIORITES)})")
    prochain_id = max((t["id"] for t in taches), default=0) + 1
    return {
        "id": prochain_id,
        "titre": titre,
        "statut": "a_faire",
        "priorite": priorite,
        "cree_le": horodatage or maintenant(),
        "terminee_le": None,
    }


def ajouter(taches, titre, priorite="normale", horodatage=None):
    """Ajoute une tâche à la liste et la renvoie."""
    tache = nouvelle_tache(taches, titre, priorite, horodatage)
    taches.append(tache)
    return tache


def trouver(taches, identifiant):
    """Renvoie la tâche portant cet identifiant. Lève ValueError si elle n'existe pas."""
    for tache in taches:
        if tache["id"] == identifiant:
            return tache
    raise ValueError(f"aucune tâche avec l'identifiant {identifiant}")


def terminer(taches, identifiant, horodatage=None):
    """Marque une tâche comme terminée. Lève ValueError si inconnue ou déjà terminée."""
    tache = trouver(taches, identifiant)
    if tache["statut"] == "terminee":
        raise ValueError(f"la tâche {identifiant} est déjà terminée")
    tache["statut"] = "terminee"
    tache["terminee_le"] = horodatage or maintenant()
    return tache


def supprimer(taches, identifiant):
    """Supprime une tâche de la liste et la renvoie. Lève ValueError si inconnue."""
    tache = trouver(taches, identifiant)
    taches.remove(tache)
    return tache


def lister(taches, statut=None, priorite=None):
    """Renvoie les tâches filtrées, triées par priorité décroissante puis par id."""
    if statut is not None and statut not in STATUTS:
        raise ValueError(f"statut inconnu : {statut!r}")
    if priorite is not None and priorite not in PRIORITES:
        raise ValueError(f"priorité inconnue : {priorite!r}")
    retenues = [
        t
        for t in taches
        if (statut is None or t["statut"] == statut)
        and (priorite is None or t["priorite"] == priorite)
    ]
    return sorted(retenues, key=lambda t: (-PRIORITES.index(t["priorite"]), t["id"]))


def valider_tache(tache):
    """Vérifie qu'un dictionnaire chargé du disque a la forme attendue.

    Lève ValueError sinon.
    """
    if not isinstance(tache, dict):
        raise ValueError("une tâche doit être un objet JSON")
    if not isinstance(tache.get("id"), int) or isinstance(tache.get("id"), bool):
        raise ValueError("identifiant manquant ou invalide")
    if not isinstance(tache.get("titre"), str) or not tache["titre"].strip():
        raise ValueError("titre manquant ou invalide")
    if tache.get("statut") not in STATUTS:
        raise ValueError(f"statut invalide : {tache.get('statut')!r}")
    if tache.get("priorite") not in PRIORITES:
        raise ValueError(f"priorité invalide : {tache.get('priorite')!r}")
    return tache
