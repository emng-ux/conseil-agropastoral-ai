# =============================================================================
# Installation automatique - Conseil Agropastoral IA
# =============================================================================
# Ce script installe tout ce qui est necessaire pour faire tourner l'agent en
# local sur un nouvel ordinateur : Python, Git, Ollama, le code de l'app, et
# la configuration de base (secrets.toml). Il est concu pour etre relance sans
# risque (il detecte ce qui est deja installe et passe les etapes inutiles).
#
# Usage : double-cliquer sur "installer.bat" (qui appelle ce script), ou
# executer directement : powershell -ExecutionPolicy Bypass -File install.ps1
# =============================================================================

$ErrorActionPreference = "Stop"
$RepoUrl = "https://github.com/emng-ux/conseil-agropastoral-ai.git"
$InstallDir = Join-Path $env:USERPROFILE "Documents\conseil-agropastoral-ai"
$OllamaModel = "llama3.1"

function Write-Step($text) {
    Write-Host ""
    Write-Host "==> $text" -ForegroundColor Green
}

function Write-Info($text) {
    Write-Host "    $text" -ForegroundColor DarkGray
}

function Write-Warn($text) {
    Write-Host "    ! $text" -ForegroundColor Yellow
}

function Test-Command($name) {
    return [bool](Get-Command $name -ErrorAction SilentlyContinue)
}

Write-Host ""
Write-Host "=========================================================" -ForegroundColor DarkGreen
Write-Host "  Installation - Conseil Agropastoral IA (mode local)" -ForegroundColor DarkGreen
Write-Host "=========================================================" -ForegroundColor DarkGreen

# -----------------------------------------------------------------------------
# 1. Python
# -----------------------------------------------------------------------------
Write-Step "Verification de Python"
if (Test-Command "python") {
    Write-Info "Python deja installe : $(python --version)"
} else {
    Write-Info "Python non trouve, installation via winget..."
    if (-not (Test-Command "winget")) {
        Write-Warn "winget n'est pas disponible sur cet ordinateur."
        Write-Warn "Installez Python manuellement depuis https://www.python.org/downloads/"
        Write-Warn "(cochez bien 'Add python.exe to PATH'), puis relancez ce script."
        Read-Host "Appuyez sur Entree pour quitter"
        exit 1
    }
    winget install -e --id Python.Python.3.12 --accept-source-agreements --accept-package-agreements
    Write-Warn "Python vient d'etre installe. Fermez cette fenetre et relancez"
    Write-Warn "le script une fois (le PATH doit se recharger)."
    Read-Host "Appuyez sur Entree pour quitter"
    exit 0
}

# -----------------------------------------------------------------------------
# 2. Git
# -----------------------------------------------------------------------------
Write-Step "Verification de Git"
if (Test-Command "git") {
    Write-Info "Git deja installe : $(git --version)"
} else {
    Write-Info "Git non trouve, installation via winget..."
    winget install -e --id Git.Git --accept-source-agreements --accept-package-agreements
    Write-Warn "Git vient d'etre installe. Fermez cette fenetre et relancez le script."
    Read-Host "Appuyez sur Entree pour quitter"
    exit 0
}

# -----------------------------------------------------------------------------
# 3. Recuperation du code (clone ou mise a jour si deja present)
# -----------------------------------------------------------------------------
Write-Step "Recuperation du code de l'application"
if (Test-Path (Join-Path $InstallDir ".git")) {
    Write-Info "Le dossier existe deja, mise a jour (git pull)..."
    Push-Location $InstallDir
    git pull
    Pop-Location
} else {
    Write-Info "Clonage dans $InstallDir ..."
    git clone $RepoUrl $InstallDir
}

# -----------------------------------------------------------------------------
# 4. Environnement virtuel et dependances Python
# -----------------------------------------------------------------------------
Write-Step "Preparation de l'environnement Python"
Push-Location $InstallDir

if (-not (Test-Path "venv")) {
    Write-Info "Creation de l'environnement virtuel..."
    python -m venv venv
} else {
    Write-Info "Environnement virtuel deja present."
}

Write-Info "Installation des dependances (peut prendre quelques minutes)..."
& ".\venv\Scripts\pip.exe" install -r requirements.txt --quiet

# -----------------------------------------------------------------------------
# 5. Ollama et modele local
# -----------------------------------------------------------------------------
Write-Step "Verification d'Ollama"
if (Test-Command "ollama") {
    Write-Info "Ollama deja installe."
} else {
    Write-Info "Ollama non trouve, installation via winget..."
    if (Test-Command "winget") {
        winget install -e --id Ollama.Ollama --accept-source-agreements --accept-package-agreements
        Write-Warn "Ollama vient d'etre installe. Fermez cette fenetre et relancez le script."
        Read-Host "Appuyez sur Entree pour quitter"
        exit 0
    } else {
        Write-Warn "Installez Ollama manuellement depuis https://ollama.com puis relancez ce script."
        Read-Host "Appuyez sur Entree pour quitter"
        exit 1
    }
}

Write-Step "Telechargement du modele local ($OllamaModel)"
$modelsInstalled = & ollama list 2>$null
if ($modelsInstalled -match [regex]::Escape($OllamaModel)) {
    Write-Info "Le modele $OllamaModel est deja telecharge."
} else {
    Write-Info "Telechargement en cours (environ 4,7 Go, selon la connexion)..."
    ollama pull $OllamaModel
}

# -----------------------------------------------------------------------------
# 6. Fichier de configuration secrets.toml
# -----------------------------------------------------------------------------
Write-Step "Configuration (secrets.toml)"
$streamlitDir = Join-Path $InstallDir ".streamlit"
$secretsPath = Join-Path $streamlitDir "secrets.toml"

if (Test-Path $secretsPath) {
    Write-Info "secrets.toml existe deja, il n'est pas modifie."
} else {
    New-Item -ItemType Directory -Path $streamlitDir -Force | Out-Null

    Write-Host ""
    Write-Host "    Quelques questions pour finaliser la configuration :" -ForegroundColor Cyan
    $wantSync = Read-Host "    Activer la synchronisation avec la base partagee Supabase ? (o/N)"

    $lines = @(
        'LLM_PROVIDER = "ollama"',
        'OLLAMA_HOST = "http://localhost:11434"',
        "OLLAMA_MODEL = `"$OllamaModel`""
    )

    if ($wantSync -match '^[oOyY]') {
        $supabaseUrl = Read-Host "    SUPABASE_URL (fourni par l'administrateur du projet)"
        $supabaseKey = Read-Host "    SUPABASE_KEY (fourni par l'administrateur du projet)"
        $orgId = Read-Host "    Identifiant d'organisation (laisser vide si non applicable)"

        $lines += "SUPABASE_URL = `"$supabaseUrl`""
        $lines += "SUPABASE_KEY = `"$supabaseKey`""
        $lines += 'SYNC_LOCAL_TO_SUPABASE = "true"'
        if ($orgId.Trim() -ne "") {
            $lines += "ORGANIZATION_ID = `"$($orgId.Trim())`""
        }
    } else {
        Write-Info "Synchronisation non activee : l'agent fonctionnera en local uniquement."
        Write-Info "(on pourra l'activer plus tard en relancant ce script apres avoir supprime secrets.toml)"
    }

    $lines | Set-Content -Path $secretsPath -Encoding UTF8
    Write-Info "secrets.toml cree."
}

# -----------------------------------------------------------------------------
# 7. Lanceur quotidien (pour ne plus avoir a retaper les commandes)
# -----------------------------------------------------------------------------
Write-Step "Creation du lanceur quotidien"
$launcherPath = Join-Path $InstallDir "lancer_agent.bat"
@"
@echo off
cd /d "%~dp0"
call venv\Scripts\activate.bat
streamlit run app.py
"@ | Set-Content -Path $launcherPath -Encoding ASCII
Write-Info "Cree : $launcherPath"
Write-Info "Double-cliquez sur ce fichier pour relancer l'agent a l'avenir."

Pop-Location

# -----------------------------------------------------------------------------
# 8. Lancement immediat
# -----------------------------------------------------------------------------
Write-Host ""
Write-Host "=========================================================" -ForegroundColor DarkGreen
Write-Host "  Installation terminee !" -ForegroundColor DarkGreen
Write-Host "=========================================================" -ForegroundColor DarkGreen
Write-Host ""
$launchNow = Read-Host "Lancer l'agent maintenant ? (O/n)"
if ($launchNow -notmatch '^[nN]') {
    Push-Location $InstallDir
    & ".\venv\Scripts\streamlit.exe" run app.py
    Pop-Location
} else {
    Write-Host "Vous pourrez le lancer plus tard via : $launcherPath"
}
