"""
Grille d'annotation, version 2.1 (procédure révisée), à partir du DataFrame de run_all
(colonnes model, call_id, answer).

Convention : les critères d'exclusion (1a à 2c) et les attributs sont formulés pour que
1 = « au vert » (va dans le sens de l'hyperlogique). L'effet (E) est une variable séparée,
codée 0/1/2 avant de lire R et N. Une sortie dont les six critères d'exclusion sont à 1 est
censée réussir ; si l'effet est à 0 ou 1, on remplit « Pourquoi ça rate ».

    exporter_annotation(df, ("Casanove", "Charles"), "./results")  -> un .xlsx par annotateur
    comparer_annotations("./results/annotation_Casanove.xlsx", "./results/annotation_Charles.xlsx")
"""

import random
import re
from pathlib import Path

import pandas as pd

# Étape E : variable séparée de la conformité, codée AVANT d'ouvrir R et N (0, 1 ou 2)
EFFET = ("E Effet", "0 non, 1 moyen, 2 oui : sans regarder la définition, l'énoncé produit-il un effet d'absurde sur vous ? "
                     "À coder en lisant l'énoncé seul, R et N masqués.")

# Critères d'exclusion (1 = au vert), dans l'ordre de la procédure
CRITERES = [
    ("1a Cadre nommable", "1 si on peut écrire « on s'attendrait à ce que… » en nommant le cadre heurté. 0 → hors corpus."),
    ("1b Non résolu, non commenté", "1 si le texte NE lève PAS l'incompatibilité, ne l'explique pas et ne commente pas l'étrangeté. 0 → hors corpus (désamorçage)."),
    ("1c Monde ordinaire", "1 si, R admise comme règle humaine, tous les faits sont possibles dans le monde actuel. 0 → hors monde ordinaire."),
    ("2a Règle", "1 si R tient en une phrase et existe ou pourrait exister dans nos institutions. "
                 "0 → préciser dans « Rejet nommé » (introuvable : P1 ; inventée : hors monde ordinaire)."),
    ("2b Consistance", "1 si on peut imaginer ce monde ordinaire où R et C sont vrais ensemble. 0 → P2."),
    ("2c Enjeu et décalage", "1 si la violation de N touche une valeur ET, si l'énoncé aborde la mort, le deuil ou la souffrance, "
                             "s'il crée un décalage (mise à distance, relativisation, légèreté). "
                             "0 → pas d'enjeu (hors corpus, sans friction) ou « tragique sans décalage » (à préciser dans « Rejet nommé »)."),
]
# Attributs (étape 3) : aucune exclusion, 1 = au vert
ATTRIBUTS = [
    ("3a Rigueur", "1 si R mène à C sans sophisme (0 si sophisme ou douteux)."),
    ("3b Sans intérêt local", "1 si aucun locuteur ne tire avantage de la violation (ni excuse, ni ruse)."),
    ("3c Productivité", "1 si C permet une déduction supplémentaire non triviale, absente du texte."),
    ("3d Fidélité interne", "1 si R est appliquée de la même façon à chaque occurrence."),
    ("3e Intentionnalité", "1 si la violation paraît voulue par le texte et non une erreur."),
]
REJETS = ["Métaphore", "Énigme", "Vérité banale", "Paradoxe banal", "Erreur", "Dénonciation",
          "Hors monde ordinaire", "Trop expliqué", "Tragique sans décalage", "Illisible (trop long ou complexe)",
          "Règle introuvable (P1)", "Règle inventée"]
TEXTE_LIBRE = [
    ("3f Fonction", "Libre : fonction de l'énoncé (en quelques mots)."),
    ("Rejet nommé", "Liste déroulante : motif du rejet, s'il y en a un."),
    ("Pourquoi ça rate (si tout au vert)", "Si les critères 1a à 2c sont à 1 mais que l'effet est à 0 ou 1 : dire pourquoi, en quelques mots."),
    ("Commentaire", "Libre."),
]

_CHAMP = re.compile(r"^[\s#>*_\-]*(R|N|[ÉEé]nonc[ée])\b[\s*_]*[:：]", re.IGNORECASE | re.MULTILINE)


def decouper(texte):
    """Extrait R, N, Énoncé d'une réponse ; champ introuvable = ''."""
    champs = {"R": "", "N": "", "Enonce": ""}
    if not isinstance(texte, str):
        return champs
    reperes = list(_CHAMP.finditer(texte))
    for i, m in enumerate(reperes):
        nom = m.group(1).upper()
        nom = "Enonce" if nom.startswith(("É", "E")) else nom
        fin = reperes[i + 1].start() if i + 1 < len(reperes) else len(texte)
        if not champs[nom]:
            champs[nom] = texte[m.end():fin].strip().strip("*_ ").strip()
    return champs


def exporter_annotation(df, annotateurs=("Casanove", "Charles"), dossier="./results", graine=2026):
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.utils import get_column_letter
    from openpyxl.worksheet.datavalidation import DataValidation

    df = df[~df["answer"].astype(str).str.startswith("ERROR:")].reset_index(drop=True)
    ordre = list(range(len(df)))
    random.Random(graine).shuffle(ordre)  # même ordre mélangé pour tous les annotateurs
    df = df.iloc[ordre].reset_index(drop=True)

    gras, normal = Font(name="Arial", bold=True), Font(name="Arial")
    jaune, gris = PatternFill("solid", start_color="FFF2CC"), PatternFill("solid", start_color="D9D9D9")
    hab = Alignment(wrap_text=True, vertical="top")

    # Ordre des colonnes : l'énoncé et l'effet d'abord, R et N (masquées) ensuite = étape 0
    entetes = [("id", 6), ("Énoncé (modèle)", 60), (EFFET[0], 12), ("R (modèle)", 35), ("N (modèle)", 35),
               ("Réponse brute (si découpage raté)", 30)] + \
              [(h, 12) for h, _ in CRITERES] + [("Tout au vert (1a à 2c)", 12), ("Premier critère à 0", 14)] + \
              [(h, 12) for h, _ in ATTRIBUTS] + \
              [("3f Fonction", 25), ("Rejet nommé", 25), (TEXTE_LIBRE[2][0], 40), (TEXTE_LIBRE[3][0], 30)]
    lettre = {h: get_column_letter(j) for j, (h, _) in enumerate(entetes, 1)}
    premier, dernier = lettre[CRITERES[0][0]], lettre[CRITERES[-1][0]]
    a_remplir = {EFFET[0]} | {h for h, _ in CRITERES + ATTRIBUTS + TEXTE_LIBRE}
    calcules = ("Tout au vert (1a à 2c)", "Premier critère à 0")

    Path(dossier).mkdir(parents=True, exist_ok=True)
    chemins = []
    for nom in annotateurs:
        wb = Workbook()
        ws = wb.active
        ws.title = "Annotation"
        for j, (h, w) in enumerate(entetes, 1):
            cel = ws.cell(row=1, column=j, value=h)
            cel.font, cel.alignment = gras, hab
            cel.fill = jaune if h in a_remplir else gris
            ws.column_dimensions[get_column_letter(j)].width = w
        ws.freeze_panes = "C2"
        # Étape 0 : R et N masquées (colonnes D:E, regroupées) jusqu'à ce que l'effet soit codé
        ws.column_dimensions.group(lettre["R (modèle)"], lettre["N (modèle)"], hidden=True)

        n_crit = len(CRITERES)
        for i, row in enumerate(df.itertuples(), start=2):
            ch = decouper(row.answer)
            brut = row.answer if not all(ch.values()) else ""
            valeurs = {"id": i - 1, "Énoncé (modèle)": ch["Enonce"], "R (modèle)": ch["R"],
                       "N (modèle)": ch["N"], "Réponse brute (si découpage raté)": brut}
            for h, v in valeurs.items():
                cel = ws[f"{lettre[h]}{i}"]
                cel.value, cel.font, cel.alignment = v, normal, hab
            plage = f"{premier}{i}:{dernier}{i}"
            ws[f"{lettre[calcules[0]]}{i}"] = (
                f'=IF(COUNT({plage})<{n_crit},"",IF(SUM({plage})={n_crit},1,0))')
            tests = "".join(f'IF({lettre[h]}{i}=0,"{h[:2]}",' for h, _ in CRITERES)
            ws[f"{lettre[calcules[1]]}{i}"] = (
                f'=IF(COUNT({plage})<{n_crit},"",{tests}"aucun"{")" * n_crit})')
            for h in list(a_remplir) + list(calcules):
                ws[f"{lettre[h]}{i}"].font = normal
                ws[f"{lettre[h]}{i}"].alignment = hab

        fin = max(len(df) + 1, 2)
        dv01 = DataValidation(type="whole", operator="between", formula1="0", formula2="1",
                              allow_blank=True, showErrorMessage=True,
                              errorTitle="0 ou 1", error="Saisir 0 ou 1.")
        dv012 = DataValidation(type="whole", operator="between", formula1="0", formula2="2",
                               allow_blank=True, showErrorMessage=True,
                               errorTitle="0, 1 ou 2", error="Saisir 0 (non), 1 (moyen) ou 2 (oui).")
        dvrej = DataValidation(type="list", formula1='"' + ",".join(REJETS) + '"',
                               allow_blank=True, showErrorMessage=True)
        for dv in (dv01, dv012, dvrej):
            ws.add_data_validation(dv)
        dv012.add(f"{lettre[EFFET[0]]}2:{lettre[EFFET[0]]}{fin}")
        dv01.add(f"{premier}2:{dernier}{fin}")
        dv01.add(f"{lettre[ATTRIBUTS[0][0]]}2:{lettre[ATTRIBUTS[-1][0]]}{fin}")
        dvrej.add(f"{lettre['Rejet nommé']}2:{lettre['Rejet nommé']}{fin}")

        cles = wb.create_sheet("Clés")  # masquée : pour lever l'aveugle après annotation
        for j, h in enumerate(["id", "model", "call_id"], 1):
            cles.cell(row=1, column=j, value=h).font = gras
        for i, row in enumerate(df.itertuples(), start=2):
            for j, v in enumerate([i - 1, row.model, row.call_id], 1):
                cles.cell(row=i, column=j, value=v).font = normal
        cles.sheet_state = "hidden"

        lg = wb.create_sheet("Légende")
        lignes = [("Remplir uniquement les colonnes jaunes : 0 ou 1 pour les critères et attributs (1 = au vert), 0, 1 ou 2 pour l'effet.", ""),
                  ("Étape 0 : lire l'énoncé seul (colonnes R et N masquées), coder l'effet (E), puis afficher les colonnes R et N (clic droit sur les en-têtes, « Afficher »).", ""),
                  ("Ne pas ouvrir la feuille masquée « Clés » avant d'avoir fini (annotation en aveugle).", ""),
                  ("Calibrer d'abord à deux sur 15 énoncés (en priorité 1b, 2c et productivité), puis annoter par séances de 30 à 40 énoncés au plus.", ""),
                  ("", ""), ("Colonne", "Question")] + [EFFET] + CRITERES + \
                 [("Tout au vert (1a à 2c)", "Calculé : 1 si les six critères d'exclusion sont à 1 (les attributs 3 ne comptent pas : aucune exclusion)."),
                  ("Premier critère à 0", "Calculé : premier critère d'exclusion à 0, dans l'ordre de la procédure.")] + \
                 ATTRIBUTS + TEXTE_LIBRE + \
                 [("", ""), ("Exemple (énoncé construit, document de définitions p. 2)", ""),
                  ("Énoncé", "Le règlement impose de déclarer tout objet perdu au bureau des objets trouvés. "
                             "Le bureau a perdu son registre et l'a déclaré à lui-même."),
                  ("Annotation", "1a=1, 1b=1, 1c=1, 2a=1, 2b=1, 2c=1 → tout au vert = 1 ; l'effet (E) se code séparément.")]
        for i, (a, b) in enumerate(lignes, 1):
            ca, cb = lg.cell(row=i, column=1, value=a), lg.cell(row=i, column=2, value=b)
            ca.font = gras if i <= 5 or a == "Colonne" else normal
            cb.font = gras if b == "Question" else normal
            ca.alignment = cb.alignment = hab
        lg.column_dimensions["A"].width = 38
        lg.column_dimensions["B"].width = 100

        chemin = Path(dossier) / f"annotation_{nom}.xlsx"
        wb.save(chemin)
        chemins.append(chemin)
    return chemins


def _kappa(x, y):
    paires = [(a, b) for a, b in zip(x, y) if pd.notna(a) and pd.notna(b) and a != "" and b != ""]
    if not paires:
        return None, 0
    n = len(paires)
    po = sum(a == b for a, b in paires) / n
    cats = {a for a, _ in paires} | {b for _, b in paires}
    pe = sum((sum(a == k for a, _ in paires) / n) * (sum(b == k for _, b in paires) / n) for k in cats)
    return (1.0 if pe == 1 else (po - pe) / (1 - pe)), n


def comparer_annotations(chemin_a, chemin_b):
    """Accord (kappa de Cohen) pour l'effet, les critères d'exclusion et les attributs."""
    a = pd.read_excel(chemin_a, sheet_name="Annotation")
    b = pd.read_excel(chemin_b, sheet_name="Annotation")
    lignes = []
    for h in [EFFET[0]] + [h for h, _ in CRITERES] + [h for h, _ in ATTRIBUTS]:
        k, n = _kappa(a[h].tolist(), b[h].tolist())
        lignes.append({"critère": h, "kappa": None if k is None else round(k, 2), "n": n})
    return pd.DataFrame(lignes)
