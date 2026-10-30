"""Mise en forme d'un relevé de compte (texte). Aucune règle métier ici."""


def chf(montant):
    """1234.5 -> « 1'234.50 » (apostrophe pour les milliers, usage suisse)."""
    return f"{montant:,.2f}".replace(",", "'")


def formater_releve(compte):
    """Renvoie le relevé d'un compte sous forme de texte."""
    lignes = [
        f"Compte {compte.numero} : {compte.titulaire}" + (" (CLÔTURÉ)" if compte.ferme else ""),
        f"{'DATE':<19}  {'OPÉRATION':<14}  {'MONTANT':>14}  {'SOLDE':>14}",
    ]
    signes = {"retrait": "-", "virement_emis": "-"}
    for op in compte.historique:
        montant = signes.get(op.type, "+") + chf(op.montant)
        lignes.append(f"{op.horodatage:<19}  {op.type:<14}  {montant:>14}  {chf(op.solde_apres):>14}")
    if not compte.historique:
        lignes.append("(aucune opération)")
    lignes.append(f"Solde : CHF {chf(compte.solde)}   Disponible : CHF {chf(compte.disponible)}")
    return "\n".join(lignes)
