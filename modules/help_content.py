"""Contenu de la page d'aide : un guide intégré (statique, FR/EN) expliquant
l'utilisation générale de l'agent, complété par des entrées personnalisées
que l'administrateur peut ajouter (ex. définitions de termes propres à
l'organisation). Les entrées personnalisées suivent le même mode hybride que
le reste de l'app (Supabase si configuré, sinon fichier JSON local).
"""
import json
import os

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_LOCAL_PATH = os.path.join(_BASE_DIR, "storage", "_help_entries.json")


def _supabase_configured() -> bool:
    return bool(os.environ.get("SUPABASE_URL")) and bool(os.environ.get("SUPABASE_KEY"))


def _headers() -> dict:
    key = os.environ["SUPABASE_KEY"]
    return {"apikey": key, "Authorization": f"Bearer {key}", "Content-Type": "application/json"}


def _base_url() -> str:
    return os.environ["SUPABASE_URL"].rstrip("/") + "/rest/v1/help_entries"


def list_custom_help_entries() -> list:
    if _supabase_configured():
        try:
            import requests
            resp = requests.get(_base_url(), headers=_headers(),
                                 params={"select": "*", "order": "created_at.asc"}, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except Exception:
            return []
    if os.path.exists(_LOCAL_PATH):
        with open(_LOCAL_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def add_custom_help_entry(titre: str, contenu: str) -> None:
    from datetime import datetime
    entry = {"titre": titre, "contenu": contenu, "created_at": datetime.utcnow().isoformat()}
    if _supabase_configured():
        import requests
        resp = requests.post(_base_url(), headers=_headers(), json=entry, timeout=10)
        resp.raise_for_status()
    else:
        entries = list_custom_help_entries()
        entry["id"] = len(entries) + 1
        entries.append(entry)
        with open(_LOCAL_PATH, "w", encoding="utf-8") as f:
            json.dump(entries, f, ensure_ascii=False, indent=2)


def delete_custom_help_entry(entry_id) -> None:
    if _supabase_configured():
        import requests
        resp = requests.delete(_base_url(), headers=_headers(),
                                params={"id": f"eq.{entry_id}"}, timeout=10)
        resp.raise_for_status()
    else:
        entries = [e for e in list_custom_help_entries() if e.get("id") != entry_id]
        with open(_LOCAL_PATH, "w", encoding="utf-8") as f:
            json.dump(entries, f, ensure_ascii=False, indent=2)


# Guide intégré, statique — les sections principales de l'agent.
BUILTIN_GUIDE_FR = [
    ("🏠 Tableau de bord", (
        "C'est ta page d'accueil. Tu y crées un nouveau diagnostic (nom, type "
        "de structure, conseiller), ou tu en importes un existant (Excel, "
        "Word, ou KoboToolbox). La liste de tes diagnostics déjà créés "
        "s'affiche à gauche, avec un bouton pour les ouvrir ou les supprimer."
    )),
    ("📝 Collecte du diagnostic", (
        "Renseigne l'identification (village, localisation, contact) et les "
        "6 branches de l'étoile du conseil (Politiques publiques, Marchés/"
        "Filières, Milieu local, Finances, Moyens de production, Activités). "
        "Un chat IA peut t'aider à remplir le formulaire — décris la "
        "situation en langage naturel, l'agent complète les champs. Ce chat "
        "est limité à 12 échanges par diagnostic (garde-fou budgétaire) ; "
        "au-delà, complète le formulaire manuellement."
    )),
    ("🏢 Entreprise", (
        "Section détaillée : histoire, environnement, plan de localisation "
        "(parcelles, siège, bâtiments), calendrier, description de chaque "
        "activité avec calcul automatique des marges, diagnostic financier "
        "global, immobilisations et amortissements, bilan comptable (FDR, "
        "BFR, tableau de financement), et plan de financement (10 "
        "indicateurs + qualification automatique)."
    )),
    ("📥 Importer un diagnostic", (
        "Trois façons d'importer des données déjà collectées : Excel/CSV "
        "(modèle strict, remappage direct), Word (extraction par IA, à "
        "relire attentivement), ou KoboToolbox (collecte terrain sur "
        "mobile, remappage direct sans IA — le plus fiable pour la collecte "
        "de terrain)."
    )),
    ("🧭 Analyse stratégique", (
        "Une fois le diagnostic rempli, cette page génère automatiquement "
        "le PESTEL, les 5 forces de Porter, la matrice BCG, la matrice "
        "d'Ansoff, et un SWOT qui croise les analyses précédentes."
    )),
    ("📋 Plan stratégique", (
        "Génère un plan d'actions à partir des analyses. Le conseiller doit "
        "valider explicitement le plan (horodaté) avant de pouvoir "
        "l'exporter en PDF ou Word — aucun export n'est possible sans "
        "validation humaine."
    )),
    ("⚙️ Administration", (
        "Réservé aux comptes administrateurs : création et gestion des "
        "comptes (National/Régional/Départemental), logo et devise de "
        "l'organisation, suivi estimé des coûts API, et journal d'activité."
    )),
    ("💬 Messagerie", (
        "Envoie un message à l'ensemble de ton périmètre (diffusion) ou à "
        "un compte précis. Les messages remontent et descendent selon la "
        "hiérarchie : un message national atteint tout le monde, un message "
        "régional reste dans sa région."
    )),
]

BUILTIN_GUIDE_EN = [
    ("🏠 Dashboard", (
        "Your home page. Create a new diagnostic (name, structure type, "
        "advisor), or import an existing one (Excel, Word, or KoboToolbox). "
        "Your existing diagnostics are listed on the left, with buttons to "
        "open or delete them."
    )),
    ("📝 Diagnostic collection", (
        "Fill in identification (village, location, contact) and the 6 "
        "branches of the advisory star (Public policies, Markets/Value "
        "chains, Local environment, Finance, Production resources, "
        "Activities). An AI chat can help fill the form — describe the "
        "situation in plain language, the agent fills in fields. This chat "
        "is capped at 12 exchanges per diagnostic (budget safeguard); "
        "beyond that, complete the form manually."
    )),
    ("🏢 Business", (
        "Detailed section: history, environment, site plan (plots, "
        "headquarters, buildings), calendar, description of each activity "
        "with automatic margin calculation, overall financial diagnosis, "
        "assets and depreciation, balance sheet (FDR, BFR, funding "
        "statement), and funding plan (10 indicators + automatic "
        "assessment)."
    )),
    ("📥 Import a diagnostic", (
        "Three ways to import already-collected data: Excel/CSV (strict "
        "template, direct remapping), Word (AI extraction, review "
        "carefully), or KoboToolbox (mobile field collection, direct "
        "remapping without AI — most reliable for field data)."
    )),
    ("🧭 Strategic analysis", (
        "Once the diagnostic is filled in, this page automatically "
        "generates PESTEL, Porter's 5 forces, the BCG matrix, the Ansoff "
        "matrix, and a SWOT crossing the previous analyses."
    )),
    ("📋 Strategic plan", (
        "Generates an action plan from the analyses. The advisor must "
        "explicitly validate the plan (timestamped) before it can be "
        "exported as PDF or Word — no export is possible without human "
        "validation."
    )),
    ("⚙️ Administration", (
        "Restricted to administrator accounts: account creation and "
        "management (National/Regional/Departmental), organization logo and "
        "currency, estimated API cost tracking, and activity log."
    )),
    ("💬 Messaging", (
        "Send a message to your entire scope (broadcast) or to a specific "
        "account. Messages flow up and down the hierarchy: a national "
        "message reaches everyone, a regional message stays within its "
        "region."
    )),
]


def builtin_guide(lang: str) -> list:
    return BUILTIN_GUIDE_FR if lang == "fr" else BUILTIN_GUIDE_EN
