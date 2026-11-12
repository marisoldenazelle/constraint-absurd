"""
Grille d'annotation 0/1 à partir du DataFrame de run_all (colonnes model, call_id, answer).

Convention : chaque critère est formulé pour que 1 = « au vert » (va dans le sens de
l'hyperlogique). Une sortie dont tous les critères sont à 1 est censée réussir ;
si elle rate quand même, on remplit « Pourquoi ça rate ».

    exporter_annotation(df, ("Casanove", "Charles"), "./results")  -> un .xlsx par annotateur
    comparer_annotations("./results/annotation_Casanove.xlsx", "./results/annotation_Charles.xlsx")
"""

import random
import re
from pathlib import Path

import pandas as pd

# (en-tête, question posée à l'annotateur) ; 1 = au vert
CRITERES = [
    ("1a Cadre nommable", "1 si on peut écrire « on s'attendrait à ce que… » en nommant le cadre heurté (logique, pragmatique, encyclopédique)."),
    ("1b Non résolu", "1 si le texte NE lève PAS l'incompatibilité (pas de correction ni d'explication de la chute)."),
    ("2a Règle formulable", "1 si on peut formuler en une phrase la règle R qui engendre la conséquence C."),
    ("2b Monde consistant", "1 si on peut imaginer un monde où R et C sont vrais ensemble."),
    ("3a Rigueur valide", "1 si R mène à C sans sophisme (0 si sophisme ou douteux)."),
    ("3b Sans intérêt local", "1 si aucun locuteur ne tire avantage de la violation (ni excuse, ni ruse)."),
    ("3c Productif", "1 si C permet une déduction supplémentaire non triviale, absente du texte."),
]
TEXTE_LIBRE = [
    ("Pourquoi ça rate (si tout au vert)", "Si tous les critères sont à 1 mais que la sortie ne fonctionne pas : dire pourquoi, en quelques mots."),
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

    fixes = [("id", 6), ("R (modèle)", 35), ("N (modèle)", 35), ("Énoncé (modèle)", 60),
             ("Réponse brute (si découpage raté)", 30)]
    a_remplir = [(h, 12) for h, _ in CRITERES] + [("Tout au vert", 10)] + \
                [(TEXTE_LIBRE[0][0], 40), (TEXTE_LIBRE[1][0], 30)]
    entetes = fixes + a_remplir
    lettre = {h: get_column_letter(j) for j, (h, _) in enumerate(entetes, 1)}
    premier, dernier = lettre[CRITERES[0][0]], lettre[CRITERES[-1][0]]

    Path(dossier).mkdir(parents=True, exist_ok=True)
    chemins = []
    for nom in annotateurs:
        wb = Workbook()
        ws = wb.active
        ws.title = "Annotation"
        for j, (h, w) in enumerate(entetes, 1):
            cel = ws.cell(row=1, column=j, value=h)
            cel.font, cel.alignment = gras, hab
            cel.fill = jaune if h in dict(CRITERES) or h in dict(TEXTE_LIBRE) else gris
            ws.column_dimensions[get_column_letter(j)].width = w
        ws.freeze_panes = "B2"

        for i, row in enumerate(df.itertuples(), start=2):
            ch = decouper(row.answer)
            brut = row.answer if not all(ch.values()) else ""
            for j, v in enumerate([i - 1, ch["R"], ch["N"], ch["Enonce"], brut], 1):
                cel = ws.cell(row=i, column=j, value=v)
                cel.font, cel.alignment = normal, hab
            plage = f"{premier}{i}:{dernier}{i}"
            ws[f"{lettre['Tout au vert']}{i}"] = (
                f'=IF(COUNT({plage})<{len(CRITERES)},"",IF(SUM({plage})={len(CRITERES)},1,0))')
            for h, _ in a_remplir:
                ws[f"{lettre[h]}{i}"].font = normal
                ws[f"{lettre[h]}{i}"].alignment = hab

        fin = max(len(df) + 1, 2)
        dv = DataValidation(type="whole", operator="between", formula1="0", formula2="1",
                            allow_blank=True, showErrorMessage=True,
                            errorTitle="0 ou 1", error="Saisir 0 ou 1.")
        ws.add_data_validation(dv)
        dv.add(f"{premier}2:{dernier}{fin}")

        cles = wb.create_sheet("Clés")  # masquée : pour lever l'aveugle après annotation
        for j, h in enumerate(["id", "model", "call_id"], 1):
            cles.cell(row=1, column=j, value=h).font = gras
        for i, row in enumerate(df.itertuples(), start=2):
            for j, v in enumerate([i - 1, row.model, row.call_id], 1):
                cles.cell(row=i, column=j, value=v).font = normal
        cles.sheet_state = "hidden"

        lg = wb.create_sheet("Légende")
        lignes = [("Remplir uniquement les colonnes jaunes, en 0 ou 1 pour les critères (1 = au vert).", ""),
                  ("Ne pas ouvrir la feuille masquée « Clés » avant d'avoir fini (annotation en aveugle).", ""),
                  ("", ""), ("Colonne", "Question")] + CRITERES + \
                 [("Tout au vert", "Calculé : 1 si tous les critères sont à 1.")] + TEXTE_LIBRE + \
                 [("", ""), ("Exemple (énoncé construit, document de définitions p. 2)", ""),
                  ("Énoncé", "Le règlement impose de déclarer tout objet perdu au bureau des objets trouvés. "
                             "Le bureau a perdu son registre et l'a déclaré à lui-même."),
                  ("Annotation", "1a=1, 1b=1, 2a=1, 2b=1, 3a=1, 3b=1, 3c=1 → tout au vert = 1")]
        for i, (a, b) in enumerate(lignes, 1):
            ca, cb = lg.cell(row=i, column=1, value=a), lg.cell(row=i, column=2, value=b)
            ca.font = gras if i <= 4 else normal
            cb.font = gras if i == 4 else normal
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
    """Accord (kappa de Cohen) critère par critère."""
    a = pd.read_excel(chemin_a, sheet_name="Annotation")
    b = pd.read_excel(chemin_b, sheet_name="Annotation")
    lignes = []
    for h, _ in CRITERES:
        k, n = _kappa(a[h].tolist(), b[h].tolist())
        lignes.append({"critère": h, "kappa": None if k is None else round(k, 2), "n": n})
    return pd.DataFrame(lignes)
