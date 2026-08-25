# Installation automatique — Conseil Agropastoral IA

Ce dossier contient un script qui automatise l'installation complète de
l'agent en mode local (avec Ollama), pour un nouvel ordinateur de conseiller.

## Utilisation

1. Télécharger ce dossier `install/` (ou tout le dépôt) sur l'ordinateur cible.
2. Double-cliquer sur **`installer.bat`**.
3. Suivre les instructions à l'écran (le script pose quelques questions :
   activer ou non la synchronisation Supabase, etc.).
4. À la fin, l'agent se lance automatiquement dans le navigateur.

Pour les usages suivants, plus besoin de repasser par l'installateur : un
fichier `lancer_agent.bat` est créé automatiquement dans le dossier de
l'application (`Documents\conseil-agropastoral-ai\lancer_agent.bat`) — il
suffit de double-cliquer dessus.

## Ce que fait le script

- Vérifie et installe si besoin : Python, Git, Ollama (via `winget`, déjà
  intégré à Windows 10/11).
- Récupère le code de l'application depuis GitHub (ou le met à jour s'il est
  déjà installé — relancer le script plus tard applique les mises à jour).
- Crée l'environnement Python et installe les dépendances.
- Télécharge le modèle d'IA local (`llama3.1`).
- Crée le fichier `secrets.toml` de façon interactive (sans avoir besoin
  d'ouvrir le Bloc-notes ni de connaître la syntaxe TOML).
- Crée un raccourci de lancement quotidien.

## Limites connues

- Fonctionne sur **Windows 10/11** uniquement (utilise `winget`).
- Si `winget` n'est pas disponible (rare, sur des versions très anciennes de
  Windows), le script indique comment installer Python/Git/Ollama
  manuellement puis s'arrête proprement — pas de plantage silencieux.
- N'a pas encore été testé en conditions réelles sur un poste Windows vierge
  (développé et vérifié syntaxiquement en environnement Linux). À valider sur
  un premier PC avant diffusion large à toutes les organisations.
