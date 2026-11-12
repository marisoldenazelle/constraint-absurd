"""
Généré par Claude. Prompts de génération en bas de fichier.
Appels multiples à des modèles OpenRouter via le SDK OpenAI,
avec sauvegarde incrémentale locale et reprise après crash.

Dépendances :
    pip install openai pandas

Variable d'environnement requise :
    OPENROUTER_API_KEY
"""

import hashlib
import json
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional, Set, Tuple

import pandas as pd
from openai import OpenAI

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
N_CALLS = 5          # nombre d'appels par modèle
MAX_RETRIES = 2      # nombre de retry après le 1er échec
RETRY_DELAY_S = 2.0  # pause entre deux tentatives
ERROR_PREFIX = "ERROR:"

Task = Tuple[str, int]  # (model, call_number)


# --------------------------------------------------------------------------- #
# Client
# --------------------------------------------------------------------------- #
def get_client(api_key: Optional[str] = None) -> OpenAI:
    """Crée un client OpenAI pointant vers OpenRouter."""
    api_key = api_key or os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("Clé API manquante : définir OPENROUTER_API_KEY.")
    return OpenAI(base_url=OPENROUTER_BASE_URL, api_key=api_key)


# --------------------------------------------------------------------------- #
# Appel unitaire avec retry
# --------------------------------------------------------------------------- #
def call_llm(
    client: OpenAI,
    model: str,
    prompt: str,
    max_retries: int = MAX_RETRIES,
    retry_delay: float = RETRY_DELAY_S,
) -> str:
    """
    Appelle un modèle une fois (+ `max_retries` retry si échec).
    Si toutes les tentatives échouent, retourne le message d'erreur.
    """
    last_error = ""
    for attempt in range(max_retries + 1):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.choices[0].message.content or ""
        except Exception as e:  # noqa: BLE001
            last_error = f"{ERROR_PREFIX} {type(e).__name__}: {e}"
            if attempt < max_retries:
                time.sleep(retry_delay)
    return last_error


def make_call_id(model: str, call_number: int) -> str:
    """Identifiant d'appel : nom du modèle suivi du numéro (1..N)."""
    return f"{model}_{call_number}"


def is_error(answer: str) -> bool:
    return isinstance(answer, str) and answer.startswith(ERROR_PREFIX)


def run_single_call(client: OpenAI, model: str, prompt: str, call_number: int) -> dict:
    """Effectue un appel et retourne la ligne de résultat correspondante."""
    return {
        "model": model,
        "call_id": make_call_id(model, call_number),
        "answer": call_llm(client, model, prompt),
    }


# --------------------------------------------------------------------------- #
# Sauvegarde locale incrémentale (JSONL : une ligne = un appel)
# --------------------------------------------------------------------------- #
class ResultStore:
    """Ajoute chaque résultat dans un fichier JSONL dès qu'il est disponible."""

    def __init__(self, path: str):
        self.path = path
        self._lock = threading.Lock()

    def append(self, row: dict) -> None:
        line = json.dumps(row, ensure_ascii=False)
        with self._lock:
            with open(self.path, "a", encoding="utf-8") as f:
                f.write(line + "\n")
                f.flush()
                os.fsync(f.fileno())

    def load(self) -> Dict[str, dict]:
        """Relit le fichier. En cas de doublon de call_id, la dernière ligne gagne."""
        results: Dict[str, dict] = {}
        if not os.path.exists(self.path):
            return results
        with open(self.path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue  # ligne tronquée par un crash : on l'ignore
                results[row["call_id"]] = row
        return results


def default_save_path(prompt: str) -> str:
    """Nom de fichier dérivé du prompt, pour ne pas mélanger les runs."""
    digest = hashlib.sha1(prompt.encode("utf-8")).hexdigest()[:8]
    return f"results_{digest}.jsonl"


# --------------------------------------------------------------------------- #
# Utilitaires
# --------------------------------------------------------------------------- #
def flatten_models(models_by_category: Dict[str, List[str]]) -> List[str]:
    """Aplatit le dict catégorie -> modèles en liste unique (ordre conservé)."""
    seen: Set[str] = set()
    models: List[str] = []
    for category_models in models_by_category.values():
        for m in category_models:
            if m not in seen:
                seen.add(m)
                models.append(m)
    return models


def build_tasks(models: List[str], n_calls: int, done_ids: Set[str]) -> List[Task]:
    """Liste des appels restant à faire (ceux déjà faits sont ignorés)."""
    return [
        (m, i)
        for m in models
        for i in range(1, n_calls + 1)
        if make_call_id(m, i) not in done_ids
    ]


def results_to_dataframe(
    results: Dict[str, dict], models: List[str], n_calls: int
) -> pd.DataFrame:
    """Construit le DataFrame (model, call_id, answer) dans l'ordre attendu."""
    rows = []
    for m in models:
        for i in range(1, n_calls + 1):
            row = results.get(make_call_id(m, i))
            if row is not None:
                rows.append(row)
    return pd.DataFrame(rows, columns=["model", "call_id", "answer"])


# --------------------------------------------------------------------------- #
# Exécution des appels
# --------------------------------------------------------------------------- #
def execute_tasks(
    client: OpenAI,
    prompt: str,
    tasks: List[Task],
    store: ResultStore,
    results: Dict[str, dict],
    max_workers: int = 1,
) -> None:
    """
    Exécute les appels. Chaque résultat est écrit sur disque (store) puis ajouté
    à `results` dès qu'il est prêt, donc `results` reste exploitable même si
    la fonction lève une exception en cours de route.
    """

    def _work(task: Task) -> dict:
        model, call_number = task
        row = run_single_call(client, model, prompt, call_number)
        store.append(row)
        return row

    if max_workers <= 1:
        for task in tasks:
            row = _work(task)
            results[row["call_id"]] = row
        return

    executor = ThreadPoolExecutor(max_workers=max_workers)
    futures = [executor.submit(_work, t) for t in tasks]
    try:
        for future in as_completed(futures):
            row = future.result()
            results[row["call_id"]] = row
    except BaseException:
        executor.shutdown(wait=False, cancel_futures=True)
        raise
    else:
        executor.shutdown()


# --------------------------------------------------------------------------- #
# Fonction principale
# --------------------------------------------------------------------------- #
def run_all(
    prompt: str,
    models_by_category: Dict[str, List[str]],
    n_calls: int = N_CALLS,
    max_workers: int = 1,
    client: Optional[OpenAI] = None,
    save_path: Optional[str] = None,
    resume: bool = True,
    retry_errors: bool = True,
) -> pd.DataFrame:
    """
    Appelle chaque modèle `n_calls` fois sur le prompt et retourne un DataFrame
    avec les colonnes : model, call_id, answer.

    - Chaque réponse est sauvegardée immédiatement dans `save_path` (JSONL).
      Par défaut : results_<hash du prompt>.jsonl
    - resume=True : les appels déjà présents dans le fichier ne sont pas refaits.
    - retry_errors=True : les appels déjà sauvegardés mais en erreur sont refaits.
    - En cas de crash ou d'interruption (Ctrl+C), le DataFrame des résultats
      obtenus jusque-là est retourné au lieu de lever l'exception.
    """
    models = flatten_models(models_by_category)
    store = ResultStore(save_path or default_save_path(prompt))

    # Reprise : on recharge ce qui existe déjà
    results = store.load() if resume else {}
    if retry_errors:
        results = {k: v for k, v in results.items() if not is_error(v["answer"])}

    try:
        client = client or get_client()
        tasks = build_tasks(models, n_calls, set(results))
        print(f"{len(results)} appel(s) déjà faits, {len(tasks)} à effectuer "
              f"(sauvegarde : {store.path})")
        execute_tasks(client, prompt, tasks, store, results, max_workers)
    except KeyboardInterrupt:
        print("\nInterruption manuelle : retour des résultats partiels.")
    except Exception as e:  # noqa: BLE001
        print(f"Crash ({type(e).__name__}: {e}) : retour des résultats partiels.")

    return results_to_dataframe(results, models, n_calls)


# --------------------------------------------------------------------------- #
# Exemple d'utilisation
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    MODELS = {
        "openai": ["openai/gpt-4o-mini"],
        "anthropic": ["anthropic/claude-3.5-haiku"],
        "open_source": ["meta-llama/llama-3.1-8b-instruct"],
    }
    PROMPT = "Explique en deux phrases ce qu'est un trou noir."

    df = run_all(PROMPT, MODELS, n_calls=5, max_workers=3)
    print(df)
    df.to_csv("results.csv", index=False)

"""
Prompts de génération:
Fais un bout de code python pour appeler openrouter via openai sur python. Je veux un ensemble de fonctions qui permettent de prendre en entrée un prompt et un dictionnaire (Dict[str, List[str]]) de modèles (une liste de modèles pour une catégorie). On appelle 5 fois chaque modèle sur le prompt unique et on stocke la réponse dans un dataframe qui contient les colonnes model, call_id, answer avec call_id un identifiant qui est le nom du modèle suivi du numéro d'appel (de 1 à 5, donc)
La fonction d'appel LLM inclut 2 retry si l'appel échoue. Si les deux retry fail, on met simplement le message d'erreur dans la case associée. 
Crée différentes fonctions de façon à ce que le code soit accessible et modulaire. 
Tu peux créer un fichier .py.
reformule ma demande

mets en place un système d'enregistrmeent successif des réponses en local de manière à ne pas tout perdre dans un crash. Ou alors des try except qui renvoient le df si crash
"""