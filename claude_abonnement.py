"""Appel à Claude par Claude Code (abonnement Claude, sans clé API payante).

Usage personnel sur ce PC : l'abonnement couvre votre propre travail, pas un outil ouvert au public.
"""
import glob
import json
import os
import shutil
import subprocess
import tempfile

MODELE = os.environ.get("DEMEMBREMENT_MODELE", "claude-sonnet-5-5")


def claude_code() -> str | None:
    """Commande « claude », sinon le binaire de l'extension VS Code."""
    if shutil.which("claude"):
        return shutil.which("claude")
    for motif in ("~/.vscode*/extensions/anthropic.claude-code-*/resources/native-binary/claude",
                  "~/.cursor/extensions/anthropic.claude-code-*/resources/native-binary/claude"):
        trouves = sorted(glob.glob(os.path.expanduser(motif)))
        if trouves:
            return trouves[-1]
    return None


def demander(prompt: str, schema: dict, delai: int = 300) -> dict:
    """Envoie le prompt à Claude Code et rend le JSON demandé (conforme au schéma)."""
    exe = claude_code()
    if not exe:
        raise RuntimeError("Claude Code est introuvable sur ce PC (ni commande « claude », ni extension VS Code).")
    # sans clé API dans l'environnement : Claude Code utilise alors l'abonnement
    env = {k: v for k, v in os.environ.items() if k not in ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN")}
    cmd = [exe, "-p", "--output-format", "json", "--no-session-persistence", "--strict-mcp-config",
           "--tools", "", "--permission-mode", "dontAsk", "--model", MODELE, "--json-schema", json.dumps(schema)]
    with tempfile.TemporaryDirectory() as dossier:
        p = subprocess.run(cmd, input=prompt, capture_output=True, text=True, timeout=delai, cwd=dossier, env=env)
    try:
        sortie = json.loads(p.stdout)
    except ValueError:
        raise RuntimeError(f"Réponse illisible de Claude Code : {(p.stderr or p.stdout)[:400]}")
    if sortie.get("is_error") or not isinstance(sortie.get("structured_output"), dict):
        raise RuntimeError(f"Claude Code n'a pas rendu de résultat : {str(sortie.get('result'))[:400]}")
    return sortie["structured_output"]


def _texte_ou_nul():
    return {"type": ["string", "null"]}


def _entier_ou_nul():
    return {"type": ["integer", "null"]}


SCHEMA_EXTRACTION = {
    "type": "object", "additionalProperties": False,
    "required": ["nom_programme", "ville", "departement", "adresse", "region", "type_bien", "neuf_ou_ancien",
                 "prix_minimum", "decote", "duree_demembrement", "date_livraison", "nombre_lots", "promoteur",
                 "bailleur", "description_localisation", "description_programme", "acces_transports"],
    "properties": {
        "nom_programme": _texte_ou_nul(), "ville": _texte_ou_nul(), "departement": _texte_ou_nul(),
        "adresse": _texte_ou_nul(), "region": _texte_ou_nul(),
        "type_bien": {"type": ["string", "null"],
                      "enum": ["Appartement", "Maison", "Résidence de tourisme", "Résidence étudiante", None]},
        "neuf_ou_ancien": {"type": ["string", "null"], "enum": ["Neuf", "Ancien", None]},
        "prix_minimum": _entier_ou_nul(), "decote": _entier_ou_nul(), "duree_demembrement": _entier_ou_nul(),
        "date_livraison": _texte_ou_nul(), "nombre_lots": _entier_ou_nul(), "promoteur": _texte_ou_nul(),
        "bailleur": _texte_ou_nul(), "description_localisation": _texte_ou_nul(),
        "description_programme": _texte_ou_nul(), "acces_transports": _texte_ou_nul(),
    },
}

SCHEMA_FICHE = {
    "type": "object", "additionalProperties": False,
    "required": ["expression_cle", "titre_seo", "meta_description", "html"],
    "properties": {"expression_cle": {"type": "string"}, "titre_seo": {"type": "string"},
                   "meta_description": {"type": "string"}, "html": {"type": "string"}},
}
