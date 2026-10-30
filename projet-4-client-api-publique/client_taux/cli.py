"""Interface en ligne de commande : requêtes, mise en forme lisible, codes de sortie."""

import argparse
import os
import statistics
import sys

from . import api


def formater_nombre(valeur, decimales=2):
    """1234.5 -> « 1'234.50 » (apostrophe pour les milliers, usage suisse)."""
    return f"{valeur:,.{decimales}f}".replace(",", "'")


def tableau(entetes, lignes, alignements):
    largeurs = [max(len(str(x)) for x in col) for col in zip(entetes, *lignes)]
    mise = lambda cellules: "  ".join(  # noqa: E731
        str(c).ljust(w) if a == "l" else str(c).rjust(w) for c, w, a in zip(cellules, largeurs, alignements)
    ).rstrip()
    return "\n".join([mise(entetes), "  ".join("-" * w for w in largeurs), *(mise(l) for l in lignes)])


def afficher_devises(devises, filtre=None):
    lignes = sorted(devises.items())
    if filtre:
        voulu = filtre.casefold()
        lignes = [(c, n) for c, n in lignes if voulu in c.casefold() or voulu in n.casefold()]
    if not lignes:
        print(f"Aucune devise ne correspond à {filtre!r}.")
        return
    print(tableau(["CODE", "NOM"], lignes, "ll"))
    print(f"-- {len(lignes)} devise(s)")


def afficher_taux(resultat, jour_demande=None):
    base = resultat["base"]
    print(f"Taux de change depuis 1 {base} (cours du {resultat['date']})")
    if jour_demande and jour_demande != resultat["date"]:
        print(f"  Remarque : aucun cours publié le {jour_demande} (week-end ou jour férié), "
              f"dernier cours disponible utilisé.")
    lignes = [[code, formater_nombre(v, 4)] for code, v in sorted(resultat["valeurs"].items())]
    print(tableau(["DEVISE", f"POUR 1 {base}"], lignes, "lr"))


def afficher_conversion(resultat, vers, jour_demande=None):
    (code, valeur), = resultat["valeurs"].items()
    taux = valeur / resultat["montant"]
    print(f"{formater_nombre(resultat['montant'])} {resultat['base']} = {formater_nombre(valeur)} {code}")
    print(f"  taux : 1 {resultat['base']} = {taux:.4f} {code}   (cours du {resultat['date']})")
    if jour_demande and jour_demande != resultat["date"]:
        print(f"  Remarque : aucun cours publié le {jour_demande}, dernier cours disponible utilisé.")


def afficher_historique(serie, base, vers):
    print(f"Évolution de 1 {base} en {vers}, {serie[0][0]} au {serie[-1][0]} ({len(serie)} cours)")
    lignes = [[jour, f"{taux:.4f}"] for jour, taux in serie]
    if len(lignes) > 12:  # on garde l'essentiel lisible
        lignes = lignes[:5] + [["...", "..."]] + lignes[-5:]
    print(tableau(["DATE", f"1 {base} EN {vers}"], lignes, "lr"))
    valeurs = [t for _, t in serie]
    premier, dernier = valeurs[0], valeurs[-1]
    print(f"  minimum  : {min(valeurs):.4f}   maximum : {max(valeurs):.4f}   moyenne : {statistics.fmean(valeurs):.4f}")
    print(f"  variation : {(dernier - premier) / premier * 100:+.2f} % ({premier:.4f} -> {dernier:.4f})")


def construire_parseur():
    p = argparse.ArgumentParser(
        prog="python3 -m client_taux",
        description="Taux de change via l'API publique Frankfurter (Banque centrale européenne).",
    )
    p.add_argument("--url", default=os.environ.get("FRANKFURTER_URL", api.URL_PAR_DEFAUT),
                   help="adresse de l'API (défaut : $FRANKFURTER_URL ou %(default)s)")
    p.add_argument("--delai", type=float, default=api.DELAI_PAR_DEFAUT, help="délai maximal par requête, en secondes")
    p.add_argument("--tentatives", type=int, default=api.TENTATIVES_PAR_DEFAUT, help="nombre d'essais en cas d'échec réseau ou 5xx")
    sous = p.add_subparsers(dest="commande", required=True, metavar="commande")

    c = sous.add_parser("devises", help="lister les devises disponibles")
    c.add_argument("--filtre", help="ne garder que les devises dont le code ou le nom contient ce texte")

    c = sous.add_parser("taux", help="taux de change depuis une devise")
    c.add_argument("base", help="devise de départ, ex. CHF")
    c.add_argument("vers", nargs="*", help="devises d'arrivée (toutes si omis)")
    c.add_argument("--date", metavar="AAAA-MM-JJ", help="cours d'un jour passé (défaut : dernier cours)")

    c = sous.add_parser("convertir", help="convertir un montant")
    c.add_argument("montant")
    c.add_argument("base")
    c.add_argument("vers")
    c.add_argument("--date", metavar="AAAA-MM-JJ")

    c = sous.add_parser("historique", help="évolution d'un taux sur une période")
    c.add_argument("base")
    c.add_argument("vers")
    c.add_argument("--du", required=True, metavar="AAAA-MM-JJ", help="date de début")
    c.add_argument("--au", required=True, metavar="AAAA-MM-JJ", help="date de fin")
    return p


def main(argv=None, client=None):
    """Renvoie 0 (succès), 1 (erreur de communication ou de saisie), 2 (usage incorrect)."""
    args = construire_parseur().parse_args(argv)
    client = client or api.ClientTaux(args.url, args.delai, args.tentatives)
    try:
        if args.commande == "devises":
            afficher_devises(client.devises(), args.filtre)
        elif args.commande == "taux":
            resultat = client.taux(args.base, args.vers or None, args.date)
            afficher_taux(resultat, args.date)
        elif args.commande == "convertir":
            montant = api.valider_montant(args.montant)
            resultat = client.taux(args.base, [args.vers], args.date, montant)
            afficher_conversion(resultat, args.vers, args.date)
        else:
            serie = client.historique(args.base, args.vers, args.du, args.au)
            afficher_historique(serie, api.valider_devise(args.base), api.valider_devise(args.vers))
        return 0
    except ValueError as erreur:
        print(f"Erreur de saisie : {erreur}", file=sys.stderr)
        return 1
    except api.ErreurClient as erreur:
        print(f"Erreur : {erreur}", file=sys.stderr)
        return 1
