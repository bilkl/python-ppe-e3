"""Démonstration : python3 -m banque. Seul module qui affiche quelque chose."""

from . import Banque, ErreurBancaire, formater_releve


def main():
    banque = Banque()
    courant = banque.ouvrir_compte("Alice Martin", "1500", decouvert_autorise=500)
    epargne = banque.ouvrir_compte("Alice Martin", "10000", taux_epargne="0.015")
    courant.deposer("250.50", "Salaire (acompte)")
    courant.retirer(80)
    banque.virement(courant.numero, epargne.numero, "300")
    epargne.appliquer_interets()
    for compte in banque.comptes():
        print(formater_releve(compte), end="\n\n")
    print("Tentative de retrait de 5 000 :")
    try:
        courant.retirer(5000)
    except ErreurBancaire as erreur:
        print(f"  refusé -> {erreur}")


if __name__ == "__main__":
    main()
