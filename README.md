# 🌿 Conseil Agropastoral IA

Agent IA d'aide aux conseillers agropastoraux : collecte de diagnostics selon
**l'étoile du conseil** (6 branches : moyens de production, performances
technico-économiques, finances, milieu local, marché, politiques publiques) et
analyse stratégique automatisée (**PESTEL, 5 forces de Porter, Matrice BCG,
Matrice d'Ansoff**), avec génération d'un **plan stratégique** et d'un **plan
d'actions** téléchargeables (PDF / Word), **validés par le conseiller** avant tout
export.

Interface **bilingue français / anglais**. Fonctionnement **hybride** :
le socle (collecte, stockage, analyse, export) fonctionne 100% hors connexion
(edge computing) ; le chat IA conversationnel et la transcription audio en ligne
s'activent uniquement si une connexion Internet est disponible.

## Fonctionnalités (V1)

- ✅ Formulaire guidé multi-branches (étoile du conseil), visualisation radar de complétude
- ✅ Import de diagnostics existants (Excel/CSV, modèle strict) + modèle téléchargeable
- ✅ Import de diagnostics **Word à structure libre** (une ou plusieurs parties), extraction assistée par IA vers l'étoile du conseil et le SWOT, toujours relu avant sauvegarde
- ✅ 5 moteurs d'analyse stratégique 100% locaux (PESTEL, Porter, BCG, Ansoff, **SWOT/FFOM**)
- ✅ Génération d'un plan stratégique + plan d'actions éditable
- ✅ **Validation obligatoire du conseiller** avant tout téléchargement
- ✅ Export PDF et Word
- ✅ Interface bilingue FR/EN
- ✅ Stockage 100% local (JSON), aucune dépendance réseau pour l'usage de base
- ✅ Agent conversationnel **multi-tours avec tool-calling réel** — actif si `ANTHROPIC_API_KEY` est configurée et une connexion est détectée. Il enregistre les informations mentionnées, relance sur les branches manquantes, et signale lui-même quand le diagnostic est prêt pour l'analyse
- ✅ Squelette transcription audio en ligne et hors-ligne (voir `audio/`)

## Roadmap (V3)

- Enregistrement audio direct dans le navigateur (`st.audio_input`) + transcription → pré-remplissage
  automatique du formulaire via le même agent conversationnel, avec validation humaine systématique
- Synchronisation optionnelle vers un espace cloud partagé entre conseillers

## Démo en ligne

Une démo est déployée sur Streamlit Community Cloud : https://conseil-agropastoral-ia.streamlit.app
(usage de démonstration uniquement — évite d'y saisir de vraies données de producteurs).

## Installation

```bash
git clone https://github.com/emng-ux/conseil-agropastoral-ai.git
cd conseil-agropastoral-ai
python -m venv venv
source venv/bin/activate  # Windows : venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

L'application s'ouvre dans le navigateur (par défaut http://localhost:8501) et
fonctionne sans connexion Internet.

### Activer les fonctionnalités en ligne (optionnel)

```bash
pip install anthropic openai   # décommenter dans requirements.txt
export ANTHROPIC_API_KEY="..."       # pour le chat IA de collecte
export TRANSCRIPTION_API_KEY="..."   # pour la transcription audio en ligne
```

### Activer la transcription audio hors-ligne (optionnel)

```bash
pip install openai-whisper
```

## Structure du projet

```
app.py                    Point d'entrée Streamlit (navigation, pages)
data/schema_etoile_conseil.json   Schéma des 6 branches de l'étoile du conseil
i18n/                      Traductions FR/EN
modules/
  collecte.py              Rendu dynamique du formulaire
  import_data.py           Import Excel/CSV + modèle
  import_word.py            Import Word à structure libre (extraction IA)
  analyse_pestel.py         Moteur PESTEL
  analyse_porter.py         Moteur 5 forces de Porter
  analyse_bcg.py             Moteur Matrice BCG
  analyse_ansoff.py          Moteur Matrice d'Ansoff
  analyse_swot.py             Moteur SWOT (FFOM), recoupé avec PESTEL et Porter
  plan_strategique.py       Génération du plan + validation conseiller
  export.py                  Export PDF / Word (bloqué si non validé)
agent/orchestrator.py      Agent conversationnel (actif en ligne uniquement)
audio/                      Transcription en ligne / hors-ligne
utils/                      i18n, stockage local, détection de connectivité
storage/                    Diagnostics enregistrés localement (JSON)
```

## Licence

Projet interne — à adapter selon les besoins de l'organisation.
