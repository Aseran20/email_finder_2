# Script d'installation des dépendances frontend
# Usage: .\install-deps.ps1

Write-Host "=== Installation des dépendances frontend ===" -ForegroundColor Cyan

# Vérifier que nous sommes dans le bon répertoire
if (!(Test-Path "package.json")) {
    Write-Host "Erreur: package.json non trouvé. Êtes-vous dans le dossier frontend?" -ForegroundColor Red
    exit 1
}

# Nettoyer l'installation existante
Write-Host "`nNettoyage des fichiers existants..." -ForegroundColor Yellow
if (Test-Path "node_modules") {
    Remove-Item -Recurse -Force node_modules
    Write-Host "  - node_modules supprimé" -ForegroundColor Green
}
if (Test-Path "package-lock.json") {
    Remove-Item package-lock.json
    Write-Host "  - package-lock.json supprimé" -ForegroundColor Green
}

# Nettoyer le cache npm
Write-Host "`nNettoyage du cache npm..." -ForegroundColor Yellow
npm cache clean --force
Write-Host "  - Cache npm nettoyé" -ForegroundColor Green

# Installer les dépendances
Write-Host "`nInstallation des dépendances..." -ForegroundColor Yellow
npm install

# Vérifier que vite est installé
Write-Host "`nVérification de l'installation..." -ForegroundColor Yellow
if (Test-Path "node_modules/.bin/vite.cmd") {
    Write-Host "  ✓ Vite installé avec succès" -ForegroundColor Green
} else {
    Write-Host "  ✗ Vite n'a pas été installé correctement" -ForegroundColor Red
    exit 1
}

# Vérifier les composants shadcn
$components = @("button", "input", "label", "card", "badge", "tabs", "collapsible")
Write-Host "`nVérification des composants shadcn:" -ForegroundColor Yellow
foreach ($component in $components) {
    if (Test-Path "src/components/ui/$component.tsx") {
        Write-Host "  ✓ $component.tsx" -ForegroundColor Green
    } else {
        Write-Host "  ✗ $component.tsx manquant" -ForegroundColor Red
    }
}

Write-Host "`n=== Installation terminée ===" -ForegroundColor Cyan
Write-Host "`nPour démarrer le serveur de développement:" -ForegroundColor Yellow
Write-Host "  npm run dev" -ForegroundColor White
Write-Host "`nOuvrir ensuite: http://localhost:5173" -ForegroundColor Cyan
