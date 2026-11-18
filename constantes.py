PROMPT = """
Produis un énoncé absurde de type hyperlogique, en trois champs.

R : une règle explicite, formulable en une phrase (logique, grammaticale ou littérale).

N : la norme de sens commun ou pragmatique que la conséquence va heurter (« on s’attendrait à ce que... »).

Énoncé : un texte court qui applique R sans erreur jusqu’à une conséquence C qui viole N.
Contraintes : (1) R et C doivent être compatibles : on doit pouvoir imaginer un monde où les deux sont vrais. (2) Le lien entre R
et C doit tenir par le contenu, pas par des connecteurs logiques ou une mise en scène du raisonnement (« donc », « or »,
syllogisme apparent). (3) Aucun locuteur ne tire avantage de la violation (ni excuse, ni ruse). (4) C doit permettre au moins
une déduction supplémentaire non triviale, sans que tu l’énonces. (5) N’explique pas la chute.
"""

PROMPT2 = f"""
Produis un énoncé absurde de type hyperlogique, en trois champs.

R : une règle explicite, en une phrase, qui existe ou pourrait exister dans nos institutions, nos
procédures ou nos conventions (règlement, usage, formule juridique). Pas de loi physique inventée.

N : la norme de sens commun que la conséquence va heurter (« on s'attendrait à ce que… »). Elle
engage quelque chose qui compte (justice, identité, mort, propriété, autorité, vérité, soin), pas une
simple habitude pratique. v2.1 La mort, le deuil ou la souffrance peuvent être montrés ; dans ce cas,
l'application de R doit créer un décalage qui met le fait grave à distance, le relativise ou y introduit de la
légèreté, au lieu de le décrire tel qu'il est.

Énoncé : un texte court où des personnes ordinaires appliquent R à la lettre, sans
erreur, jusqu'à une conséquence C qui viole N. v2.1 Privilégie une conséquence exagérée mais concrète,
que le lecteur se représente comme une scène.
Contraintes. (1) Monde ordinaire : aucune magie, aucune loi physique modifiée, aucune entité ou
propriété impossible ; n'ouvre pas de monde à part (« dans ce monde… »). (2) R et C doivent être
compatibles dans ce monde ordinaire, et C résulte uniquement de l'application littérale de R. (3) R peut
apparaître comme texte du monde (plaque, règlement, statuts) ; sinon le lecteur doit pouvoir la
reconstituer à partir des faits. (4) Ni le narrateur ni un personnage ne commente, ne s'étonne, ne justifie
ni n'explique ; pas de morale, pas de chute explicative. (5) La violation passe par un fait concret (lieu,
objet, personne, chiffre), vrai au sens littéral : ni métaphore, ni analogie. (6) R est appliquée de la même
façon à chaque occurrence. (7) C permet au moins une déduction supplémentaire non triviale, que tu
n'énonces pas. (8) La violation se voit sans calcul : pas d'énigme à résoudre. (9) Le passage de R à C est
valide : aucune erreur de raisonnement. (10) Aucun locuteur ne tire avantage de la violation.
Sortie : uniquement les trois champs R, N, Énoncé. Aucun commentaire, aucune note, aucune
vérification des contraintes.
"""

PROMPT3 = """
Produis un énoncé absurde de type hyperlogique.

R : une règle explicite, simple, en une phrase, qui existe ou pourrait exister dans nos institutions, nos procédures ou nos conventions (règlement, usage, formule juridique). Pas de loi physique inventée.

N : la norme de sens commun que la conséquence va heurter (« on s'attendrait à ce que… »).
Elle peut être logique, pragmatique, encyclopédique ou morale : ce qu'une personne, un objet ou une institution est, peut faire ou doit faire. Une indignation morale suffit, pourvu que N engage quelque chose qui compte (morale, justice, identité, propriété, autorité, vérité, soin), pas une simple habitude pratique. Si N touche un sujet grave, l'application de R doit créer un décalage qui met le fait à distance, le relativise ou y introduit de la légèreté.
Énoncé : un texte court (une à trois phrases), qui peut être une simple affirmation, déclaration ou constat. R y est appliquée à la lettre, sincèrement et sans erreur, et sa logique est déroulée jusqu'à ses limites : par extension, répétition ou combinaison, R fait exister quelque chose de nouveau, que personne n'a voulu et que R ne prévoit pas, et la conclusion C viole N. La conclusion doit créer un sens nouveau et renverser la perspective du lecteur : il ne suffit pas qu'elle soit exacte (pas de « d'accord, et alors ? »). Privilégie une conséquence exagérée mais concrète, que le lecteur se représente aisément. La conséquence doit défier la logique par la logique, pas seulement choquer ou attrister.
Contraintes. (1) R et C doivent être compatibles, et C résulte uniquement de l'application littérale de R, sans fraude, sans erreur ni mauvaise foi. (2) R peut apparaître comme texte du monde (plaque, règlement, statuts) ; sinon le lecteur doit pouvoir la reconstituer à partir des faits. (3) Le texte ne commente pas, ne s'étonne pas, ne justifie ni n'explique ; pas de morale, pas de chute explicative. (4) La violation passe par un fait concret (lieu, objet, personne, chiffre), vrai au sens littéral : ni métaphore, ni analogie. (5) R est appliquée de la même façon à chaque occurrence. (6) C permet au moins une déduction supplémentaire non triviale, que tu n'énonces pas. (7) La violation se voit sans calcul : pas d'énigme à résoudre. (8) Le passage de R à C est valide : aucune erreur de raisonnement. (9) Le texte est sincère : aucune personne ni aucune institution ne tire avantage de la violation. (10) Le texte se comprend à la première lecture : peu d'éléments (entités, lieux), aucune procédure à suivre en plusieurs étapes. (11) La logique tient par le rapport entre les notions elles-mêmes, sans connecteurs d'apparat (« donc », « ainsi », « or ») ni forme de syllogisme : liens secs, souvent implicites.
Sortie : uniquement les trois champs R, N, Énoncé. Aucun commentaire, aucune note, aucune vérification des contraintes.

"""

MODELES = {
    "PairesHybrides": ["deepseek/deepseek-v4.1-flash-1017", "mistralai/mistral-small-2603", 
                       "qwen/qwen3.6-27b", "google/gemma-4-31b-it", "anthropic/claude-sonnet-5.5"],
    "PetitsModeles": ["nvidia/nemotron-3-nano-30b-a3b", "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free",
                      "liquid/lfm-3-1.7b"],
    "GrosSansThinking": ["mistralai/mistral-large-2512", "meta-llama/llama-4-maverick", 
                         "qwen/qwen3-next-80b-a3b-instruct"],
    "ThinkingSansCode": ["google/gemini-4-argon", "openai/gpt-6-astra",
                        "qwen/qwen3.8-max", "anthropic/claude-fable-5.2"],
    "ThinkingAvecCode": ["deepseek/deepseek-v4-pro", "z-ai/glm-5.3", "moonshotai/kimi-k3.1-pro",
                          "minimax/minimax-m3.1-flash", "tencent/hy4"],
    "BudgetHautVolume": ["openai/gpt-6-luna", "stepfun/step-5-preview", "z-ai/glm-5.3-flash",
                         "deepseek/deepseek-v4.1-flash-1017"],
    "ReferencesHistoriques": ["deepseek/deepseek-r1-0528", "openai/o3"]
}
