# CodeScribe
> Un outil CLI open source pour exporter la structure et le contenu de vos projets en format Markdown (ou TXT), optimisé pour l’analyse avec des IA type ChatGPT.  
> **Parce que scroller 300 fichiers, c’est so 2020.**

## Fonctionnalités
- **Analyse récursive** du projet pour générer un rapport complet.
- **Option `--minimal`** pour exclure le bruit (fichiers config, build, etc.).
- **Option `--max-size`** pour tronquer de gros fichiers.
- **Possibilité de générer en Markdown ou en .txt** (ou les deux).
- **Auto-complétion Zsh** incluse !

## Installation
```bash
# Cloner le repo
git clone https://github.com/toncomptegithub/CodeScribe.git
cd CodeScribe

# Rendre exécutable le script
chmod +x codescribe.py
# Lancer l'install
./install.sh
```

## Utilisation
```bash
# Minimal usage
codescribe --source /path/to/myproject --minimal

# Générer un .txt
codescribe --source /path/to/myproject --txt

# Aide complète
codescribe --help
```

## Auto-complétion Zsh
1. Activer compinit dans ~/.zshrc :
```bash
autoload -Uz compinit
compinit
```
2. Placez codescribe-completion.zsh dans un dossier dédié puis sourcez-le :
```bash
source /chemin/vers/codescribe-completion.zsh
```
## Licence
Distribué sous licence MIT. Les contributions sont les bienvenues !
