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