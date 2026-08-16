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
- ✅ Section **Identification & localisation** : village, arrondissement, département, région, pays, code administratif, année, GPS, contact (adresse/téléphone/email) — contact masquable comme le nom
- ✅ Section **Entreprise** : histoire, environnement externe, plan de localisation (parcelles), calendrier annuel des activités, description détaillée de chaque activité (avec calcul automatique de la marge brute et de la marge directe), diagnostic économique et financier global (marge brute globale, EBE, marge de sécurité — calculés automatiquement), tableau des immobilisations, bilan (actif/passif)
- ✅ Import de diagnostics existants (Excel/CSV, modèle strict) + modèle téléchargeable
- ✅ Import de diagnostics **Word à structure libre** (une ou plusieurs parties), extraction assistée par IA vers l'étoile du conseil et le SWOT, toujours relu avant sauvegarde
- ✅ 5 moteurs d'analyse stratégique 100% locaux (PESTEL, Porter, BCG, Ansoff, **SWOT/FFOM**)
- ✅ Génération d'un plan stratégique + plan d'actions éditable
- ✅ **Validation obligatoire du conseiller** avant tout téléchargement
- ✅ Export PDF et Word
- ✅ **Persistance en ligne** : bascule automatique vers Supabase (base de données partagée) quand configuré, sinon fichiers locaux
- ✅ **Authentification** : écran de connexion nom d'utilisateur/mot de passe, activable via les secrets
- ✅ **Protection des données** : code d'identifiant unique par diagnostic ; masquage du nom réel de l'EFA/OP par défaut dans l'interface et les exports
- ✅ Interface bilingue FR/EN
- ✅ Stockage 100% local (JSON), aucune dépendance réseau pour l'usage de base
- ✅ Agent conversationnel **multi-tours avec tool-calling réel** — actif si `ANTHROPIC_API_KEY` est configurée et une connexion est détectée. Il enregistre les informations mentionnées, relance sur les branches manquantes, et signale lui-même quand le diagnostic est prêt pour l'analyse
- ✅ **Capture audio dans le navigateur** (`st.audio_input`) : transcription automatique puis alimentation du même agent conversationnel, avec relecture obligatoire avant sauvegarde
- ✅ **Assistant de configuration de mot de passe intégré** : génère le secret à coller dans Streamlit Cloud, sans ligne de commande
- ✅ Section Entreprise incluse dans les exports PDF/Word du diagnostic

## Roadmap (V3)

- Enregistrement audio direct dans le navigateur (`st.audio_input`) + transcription → pré-remplissage
  automatique du formulaire via le même agent conversationnel, avec validation humaine systématique
- Synchronisation optionnelle vers un espace cloud partagé entre conseillers

## Démo en ligne

Une démo est déployée sur Streamlit Community Cloud : https://conseil-agropastoral-ia.streamlit.app
(usage de démonstration uniquement — évite d'y saisir de vraies données de producteurs).

## Persistance en ligne (Supabase) et authentification

Par défaut, l'app stocke les diagnostics dans des fichiers JSON locaux (dossier
`storage/`) — parfait pour un usage local, mais **le système de fichiers d'un
déploiement Streamlit Cloud est éphémère** : sans base de données externe, les
diagnostics créés sur la version en ligne peuvent être perdus au redémarrage.

### 1. Créer la base Supabase (gratuit pour démarrer)

1. Crée un compte sur [supabase.com](https://supabase.com) et un nouveau projet.
2. Dans l'éditeur SQL du projet, exécute :
   ```sql
   create table diagnostics (
     id text primary key,
     code text,
     data jsonb not null,
     updated_at timestamptz not null default now()
   );
   ```
3. Dans Project Settings → API, récupère l'URL du projet et la clé **service_role**
   (jamais la clé `anon` publique — la `service_role` doit rester strictement secrète).

### 2. Configurer les secrets (Streamlit Cloud ou local)

```toml
SUPABASE_URL = "https://xxxx.supabase.co"
SUPABASE_KEY = "eyJ..."   # la clé service_role, jamais exposée côté navigateur
```

Dès que ces deux valeurs sont présentes, l'app bascule automatiquement sur
Supabase — visible dans la barre latérale ("💾 Supabase (base partagée en ligne)").
Sans elles, elle continue à fonctionner en local comme avant.

### 3. Activer l'authentification (nom d'utilisateur / mot de passe)

Génère un hash pour chaque mot de passe choisi :
```bash
python -c "import hashlib; print(hashlib.sha256('mot_de_passe_ici'.encode()).hexdigest())"
```

Puis ajoute dans les secrets :
```toml
[auth_users]
emmanuel = "le_hash_généré_ci-dessus"
conseiller2 = "un_autre_hash"
```

Dès qu'au moins un compte est configuré, un écran de connexion apparaît avant
tout accès à l'app. Sans cette section, l'accès reste ouvert (comportement
adapté à un usage local individuel).

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
  identification.py         Village, localisation, contact, GPS (données sensibles, masquables)
  entreprise.py              Histoire, environnement, parcelles, calendrier, activités, finances, bilan
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
