# CodeScribe
> Un outil CLI open source pour exporter la structure et le contenu de vos projets en format Markdown (ou TXT), optimisé pour l’analyse avec des IA type ChatGPT.  
> **Parce que scroller 300 fichiers, c’est so 2020.**

## Fonctionnalités
- **Analyse récursive** du projet pour générer un rapport complet.
- **Option `--minimal`** pour exclure les fichiers de configuration ou de build.
- **Option `--max-size`** pour limiter la lecture des fichiers volumineux.
- **Option `--ignore-spec`** pour ignorer les tests `*.spec.ts`.
- **Option `--include-ext`** pour ajouter d'autres extensions à analyser.
- **Option `--exclude-ext`** pour exclure des extensions spécifiques.
- **Option `--exclude-dir`** pour ignorer certains répertoires.
- **Option `--version`** pour afficher la version actuelle.
- **Option `--default-ext`** pour lister les extensions incluses par défaut.
- **Option `--git-ignore`** pour exclure les fichiers ignorés par Git.
- **Option `--no-logo`** pour retirer le logo ASCII dans la sortie.
- **Mode `--txt` ou `--export-txt`** pour obtenir un rapport texte.
- **Paramètre `--output`** pour choisir le nom du fichier généré.

## Installation
```bash
# Cloner le repo
git clone https://github.com/rollinbe/CodeScribe-CLI.git
cd CodeScribe-CLI

# Rendre exécutable le script
chmod +x codescribe.py
chmod +x install.sh
# Lancer l'installation (copie dans /usr/local/bin)
sudo ./install.sh
```

## Utilisation
```bash
# Minimal usage
codescribe --source /path/to/myproject --minimal

# Générer uniquement un fichier texte
codescribe --source /path/to/myproject --txt

# Exporter en Markdown et en texte
codescribe --source /path/to/myproject --export-txt

# Choisir le nom du fichier de sortie
codescribe --source /path/to/myproject --output monrapport.md

# Ignorer les fichiers de test Angular
codescribe --source /path/to/myproject --ignore-spec

# Exclure certaines extensions
codescribe --source /path/to/myproject --exclude-ext .log .tmp

# Exclure des dossiers
codescribe --source /path/to/myproject --exclude-dir cache build

# Afficher la version
codescribe --version
# Respecter le .gitignore
codescribe --source /path/to/myproject --git-ignore


# Lister les extensions par défaut
codescribe --default-ext

# Aide complète
codescribe --help
```

## Tests
Les tests unitaires s'exécutent avec `pytest` :

```bash
pytest -q
```
## Licence
Distribué sous licence MIT. Les contributions sont les bienvenues !
