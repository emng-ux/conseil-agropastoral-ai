"""Contexte multi-organisations.

Principe de rétrocompatibilité : tant que la variable d'environnement
ORGANIZATION_ID n'est pas définie (cas de tous les déploiements existants,
dont celui d'origine), le comportement de l'application reste strictement
inchangé -- current_organization_id() renvoie None, et les fonctions de
storage/hierarchy qui l'utilisent l'ignorent (comme avant cette migration).

Ce n'est qu'à partir du moment où une organisation cliente est explicitement
configurée (ORGANIZATION_ID="efa_moungo" par exemple, dans les secrets de son
propre déploiement) que le cloisonnement s'active pour elle.
"""
import os


def current_organization_id() -> str | None:
    org_id = os.environ.get("ORGANIZATION_ID", "").strip()
    return org_id or None


def multi_org_enabled() -> bool:
    return current_organization_id() is not None


def tag_with_org(payload: dict) -> dict:
    """Ajoute organization_id à un enregistrement avant sauvegarde, si le
    mode multi-organisations est actif. Ne modifie rien sinon (compatibilité
    avec les déploiements existants qui n'ont pas cette colonne en tête)."""
    org_id = current_organization_id()
    if org_id is not None:
        payload = dict(payload)
        payload["organization_id"] = org_id
    return payload


def org_filter_params() -> dict:
    """Paramètres de requête Supabase (PostgREST) à ajouter pour ne lire que
    les données de l'organisation courante. Dict vide si mode mono-organisation
    (comportement historique, aucun filtre supplémentaire)."""
    org_id = current_organization_id()
    if org_id is None:
        return {}
    return {"organization_id": f"eq.{org_id}"}
