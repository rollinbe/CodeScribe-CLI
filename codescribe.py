#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CodeScribe
----------
Utilitaire permettant d'exporter la structure et le contenu d'un projet
au format Markdown (et éventuellement en .txt), avec une option --minimal
pour exclure les fichiers "non métier".

Nouveautés / Options :
- --txt : génère uniquement un .txt (pas de .md).
- --export-txt : génère en plus un fichier .txt (si vous souhaitez les deux).
- --ignore-spec : ignore les fichiers .spec.ts.
- --minimal : exclut une liste de fichiers "bruit" (package-lock.json, dist/, *.csproj, etc.)
              afin d'économiser la taille et les tokens pour une analyse IA.

Également :
- On affiche en fin de script la taille globale (Ko) et l'estimation du nombre de tokens.

Auteur : Benjamin ROLLIN
"""

import os
import sys
import argparse
import textwrap

# --------------------------------------------------------------------------
# CONFIGURATION PAR DÉFAUT
# --------------------------------------------------------------------------

__version__ = "1.2.0"

DEFAULT_OUTPUT_MD = "structure_complete.md"
DEFAULT_OUTPUT_TXT = "structure_complete.txt"

EXCLUDED_DIRS = {".git", "node_modules", "__pycache__", ".venv", "bin", "obj", "dist", "build",
                 "out", ".vscode", ".idea", "target", ".pytest_cache", "venv"}

DEFAULT_INCLUDED_EXT = {
    ".cs", ".csproj", ".sln",
    ".ts", ".html", ".scss", ".json",
    ".py", ".txt", ".md"
}

# Mapping extension -> syntaxe pour les blocs de code Markdown
LANGUAGE_MAPPING = {
    ".py": "python",
    ".cs": "csharp",
    ".ts": "typescript",
    ".html": "html",
    ".scss": "scss",
    ".json": "json",
    ".csproj": "xml",
    ".sln": "",  # Pas de coloration spécifique
}


# --------------------------------------------------------------------------
# RÈGLES "MINIMAL" : FICHIERS À EXCLURE
# --------------------------------------------------------------------------
#
# L'option --minimal exclut un certain nombre de fichiers jugés "non métiers".
# Ci-dessous, quelques exemples inspirés de la requête (Angular, .NET, Python).
# Vous pouvez adapter ou étendre la liste selon vos besoins.
#
# Principales exclusions mentionnées :
#   - package-lock.json
#   - tsconfig.json, tsconfig.*.json
#   - angular.json
#   - dist/ (dossier complet)
#   - index.html (dans dist/ ou src/)
#   - environment*.ts
#   - styles.css
#   - .csproj, .sln (pour .NET)
#   - (optionnel) appsettings.json, etc.
#   - (pour Python, on ignore déjà .venv via EXCLUDED_DIRS).
#
# En plus de la liste ci-dessous, on peut ignorer app.config, web.config,
# ou d'autres configurations verbeuses, si on le souhaite.
# --------------------------------------------------------------------------

def is_minimal_excluded(rel_path: str) -> bool:
    """
    Renvoie True si ce fichier doit être exclu en mode --minimal.
    On se base sur le chemin relatif + nom de fichier.
    """

    # Normalisons le chemin en minuscules pour faciliter les comparaisons
    path_lower = rel_path.lower()

    # 1) Exclusions Angular
    if "package-lock.json" in path_lower:
        return True
    # tsconfig.json ou tsconfig.*.json
    if "tsconfig" in path_lower and path_lower.endswith(".json"):
        return True
    # angular.json
    if path_lower.endswith("angular.json"):
        return True
    # dist/
    # Si "dist" apparaît comme segment de dossier, on exclut
    if os.sep + "dist" + os.sep in path_lower:
        return True
    # index.html dans dist/ ou src/
    # => on exclut si c'est index.html ET qu'on voit "dist/" ou "src/" dans le chemin
    if path_lower.endswith("index.html") and (
            os.sep + "dist" + os.sep in path_lower or os.sep + "src" + os.sep in path_lower):
        return True
    # environment*.ts
    # => par ex. environment.ts, environment.prod.ts, ...
    if "environment" in path_lower and path_lower.endswith(".ts"):
        return True
    # styles.css ou global style
    if path_lower.endswith("styles.css"):
        return True

    # 2) Exclusions .NET
    # .csproj, .sln
    if path_lower.endswith(".csproj"):
        return True
    if path_lower.endswith(".sln"):
        return True

    # Exemple : appsettings.json (si vous jugez que c'est verbeux)
    if path_lower.endswith("appsettings.json"):
        return True

    # 3) Exclusions Python ?
    # On ignore déjà __pycache__, .venv, etc. via EXCLUDED_DIRS.
    # On pourrait exclure par ex. "pipfile.lock" ou "poetry.lock" :
    if path_lower.endswith("pipfile.lock") or path_lower.endswith("poetry.lock"):
        return True

    # Sinon, on ne l'exclut pas
    return False


def approximate_token_count(text: str) -> int:
    """
    Estimation simplifiée du nombre de tokens.
    Approche très brute : 1 token ≈ 4 caractères.
    (Vous pouvez affiner selon l'usage GPT / OpenAI.)
    """
    return len(text) // 4


def load_gitignore_patterns(path: str) -> list:
    """Lit le fichier .gitignore et renvoie la liste des motifs."""
    patterns = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                patterns.append(line)
    except Exception:
        pass
    return patterns


def is_gitignored(rel_path: str, patterns: list) -> bool:
    """Retourne True si rel_path correspond à un motif de .gitignore."""
    from fnmatch import fnmatch

    for pat in patterns:
        if pat.endswith("/"):
            if rel_path.startswith(pat.rstrip("/")):
                return True
        if fnmatch(rel_path, pat):
            return True
        if fnmatch(os.path.basename(rel_path), pat):
            return True
    return False


# --------------------------------------------------------------------------
# FONCTIONS PRINCIPALES
# --------------------------------------------------------------------------

def parse_arguments():
    """Analyse les arguments de la ligne de commande."""
    parser = argparse.ArgumentParser(
        description="CodeScribe - Exporte la structure et le contenu d'un projet en Markdown ou en .txt, avec une option --minimal."
    )
    parser.add_argument(
        "--source",
        required=False,
        help=("Chemin vers le dossier source à scanner (obligatoire sauf avec --version ou --default-ext).")
    )
    parser.add_argument(
        "--output",
        default=None,
        help=(
            "Nom du fichier de sortie. "
            "Par défaut : 'structure_complete.md' si sortie MD, ou 'structure_complete.txt' si --txt."
        )
    )
    parser.add_argument(
        "--max-size",
        type=int,
        default=None,
        help="Taille max (en Ko) lue par fichier. Ex: --max-size 50 (limite à 50 Ko)."
    )
    parser.add_argument(
        "--include-ext",
        nargs="+",
        default=[],
        help="Ajouter d'autres extensions à inclure (ex: --include-ext .txt .md)."
    )
    parser.add_argument(
        "--exclude-ext",
        nargs="+",
        default=[],
        help="Exclure certaines extensions (ex: --exclude-ext .log .tmp)."
    )

    parser.add_argument(
        "--version",
        action="store_true",
        help="Affiche la version de CodeScribe et quitte."
    )
    parser.add_argument(
        "--default-ext",
        action="store_true",
        help="Affiche la liste des extensions incluses par défaut et quitte."
    )

    parser.add_argument(
        "--no-logo",
        action="store_true",
        help="Désactive l'affichage du logo ASCII en haut du fichier."
    )
    parser.add_argument(
        "--ignore-spec",
        action="store_true",
        help="Ignore les fichiers .spec.ts (exclut tout fichier terminant par .spec.ts)."
    )
    # Sorties
    parser.add_argument(
        "--txt",
        action="store_true",
        help="Sortie au format .txt uniquement (pas de .md)."
    )
    parser.add_argument(
        "--export-txt",
        action="store_true",
        help="En plus du .md, génère un fichier .txt (si vous souhaitez les deux)."
    )
    parser.add_argument(
        "--git-ignore",
        action="store_true",
        help="Exclut les fichiers listés dans le .gitignore du projet."
    )
    # Option minimal
    parser.add_argument(
        "--minimal",
        action="store_true",
        help="Exclut les fichiers jugés 'non métier' (voir la liste dans le code)."
    )
    return parser.parse_args()


def is_hidden_or_excluded(path: str) -> bool:
    """
    Détermine si un fichier ou un dossier doit être exclu en général (hors --minimal).
    - Exclut les dossiers commençant par '.' ou présents dans EXCLUDED_DIRS.
    - Exclut les fichiers cachés (commençant par '.').
    """
    name = os.path.basename(path)
    # Exclusion si c'est un dossier caché ou dans EXCLUDED_DIRS
    if name.startswith('.') and os.path.isdir(path):
        return True
    if name in EXCLUDED_DIRS and os.path.isdir(path):
        return True
    # Exclusion des fichiers cachés
    if name.startswith('.') and os.path.isfile(path):
        return True
    return False


def gather_project_tree(root_path: str,
                        included_exts: set,
                        ignore_spec: bool = False) -> list:
    """
    Parcourt récursivement le répertoire root_path et retourne la liste
    de tous les fichiers dont l'extension est dans included_exts.
    - ignore_spec=True : exclut les fichiers terminant par '.spec.ts'.

    Retourne une liste de tuples (chemin_relatif, chemin_absolu).
    """
    all_files = []
    for current_root, dirs, files in os.walk(root_path, topdown=True):
        # Filtrer in-place les dossiers exclus
        dirs[:] = [d for d in dirs
                   if not is_hidden_or_excluded(os.path.join(current_root, d))]
        for file_name in files:
            file_path = os.path.join(current_root, file_name)
            if is_hidden_or_excluded(file_path):
                continue

            # Vérifier l'extension
            _, ext = os.path.splitext(file_name)
            if ext.lower() in included_exts:
                # Si --ignore-spec est activé, on ignore les .spec.ts
                if ignore_spec and file_name.lower().endswith(".spec.ts"):
                    continue

                # Construire le chemin relatif pour l'affichage
                rel_path = os.path.relpath(file_path, root_path)
                all_files.append((rel_path, file_path))
    return sorted(all_files)


def build_directory_tree_markdown(root_path: str,
                                  file_list: list) -> str:
    """
    Construit la représentation en arborescence (indentée) de root_path
    sous forme de texte Markdown.
    - file_list est la liste (rel_path, abs_path) des fichiers retenus.
    """
    tree = {}

    for rel_path, _ in file_list:
        parts = rel_path.split(os.sep)
        current_level = tree
        for part in parts[:-1]:
            current_level = current_level.setdefault(part, {})
        current_level.setdefault(parts[-1], None)

    def format_tree(level_dict, indent=0):
        lines = []
        for item in sorted(level_dict):
            if level_dict[item] is None:
                # C'est un fichier
                lines.append("  " * indent + f"- {item}")
            else:
                # C'est un sous-dossier
                lines.append("  " * indent + f"- **{item}/**")
                lines.extend(format_tree(level_dict[item], indent + 1))
        return lines

    tree_markdown_lines = [f"**Arborescence du projet** (racine : `{root_path}`)", ""]
    tree_markdown_lines.extend(format_tree(tree))
    return "\n".join(tree_markdown_lines)


def read_file_content(file_path: str, max_size_kb: int = None) -> str:
    """
    Lit le contenu d'un fichier en UTF-8, avec option de limite en Ko.
    Retourne une chaîne (contenu ou message d'erreur).
    """
    try:
        if max_size_kb is not None:
            max_bytes = max_size_kb * 1024
            with open(file_path, "rb") as f:
                data = f.read(max_bytes)
            return data.decode("utf-8", errors="replace")
        else:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                return f.read()
    except Exception as e:
        return f"**Erreur de lecture** : {e}"


def ext_to_language(ext: str) -> str:
    """
    Retourne la chaîne de langage à utiliser dans le bloc de code markdown
    en fonction de l'extension (pour la coloration syntaxique).
    """
    return LANGUAGE_MAPPING.get(ext.lower(), "")


def generate_markdown_report(root_path: str,
                             files_data: list,
                             no_logo: bool = False) -> str:
    """
    Génère le contenu complet du fichier Markdown, incluant :
    - (Optionnel) Le logo ASCII CodeScribe
    - Section 1 : Arborescence
    - Section 2 : Contenu des fichiers (avec sommaire cliquable)
    """
    lines = []

    # Logo ASCII (si --no-logo n'est pas précisé)
    if not no_logo:
        lines.append(
            r"""```
       _____          _       _____           _ _
      / ____|        | |     / ____|         (_) |
     | |     ___   __| | ___| (___   ___ _ __ _| |__   ___
     | |    / _ \ / _` |/ _ \\___ \ / __| '__| | '_ \ / _ \
     | |___| (_) | (_| |  __/____) | (__| |  | | |_) |  __/
      \_____\___/ \__,_|\___|_____/ \___|_|  |_|_.__/ \___|
    ```"""
        )

    lines.append(f"# Rapport CodeScribe\n")
    lines.append(f"Chemin scanné : `{root_path}`\n")

    # Section 1 : Arborescence
    lines.append("## 1. Arborescence du projet\n")
    directory_tree_str = build_directory_tree_markdown(
        root_path,
        [(f["rel_path"], f["abs_path"]) for f in files_data]
    )
    lines.append(directory_tree_str)
    lines.append("")

    # Section 2 : Contenu des fichiers
    lines.append("## 2. Contenu des fichiers\n")

    # 2.1) Table des matières cliquable
    lines.append("### Sommaire\n")
    for fdata in files_data:
        anchor = fdata["rel_path"].replace(" ", "-").replace("\\", "-").replace("/", "-").lower()
        lines.append(f"- [{fdata['rel_path']}](#{anchor})")
    lines.append("")

    # 2.2) Contenu effectif par fichier
    for fdata in files_data:
        anchor = fdata["rel_path"].replace(" ", "-").replace("\\", "-").replace("/", "-").lower()
        lines.append(f"### {fdata['rel_path']}")
        lines.append(f"<a id='{anchor}'></a>\n")

        lang = fdata["lang"]
        lines.append(f"```{lang}")
        lines.append(fdata["content"])
        lines.append("```\n")

    return "\n".join(lines)


def generate_text_report(markdown_report: str) -> str:
    """
    Transforme le rapport Markdown en version texte simple.
    Pour simplifier, on retire les ``` pour laisser le texte brut.
    """
    text_version = markdown_report.replace("```", "")
    return text_version


def main():
    args = parse_arguments()

    if args.version:
        print(__version__)
        return

    if args.default_ext:
        print(" ".join(sorted(DEFAULT_INCLUDED_EXT)))
        return

    if not args.source:
        print("Erreur : l'argument --source est requis.", file=sys.stderr)
        sys.exit(1)

    source_folder = os.path.abspath(args.source)
    if not os.path.isdir(source_folder):
        print(
            f"Erreur : Le dossier source '{source_folder}' est introuvable ou n'est pas un dossier.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Détermination du mode de sortie (MD ou TXT) et du nom de fichier
    txt_only = args.txt
    output_file = args.output

    if txt_only:
        # Si --txt est spécifié, on ne sort qu'un .txt
        if not output_file:
            output_file = DEFAULT_OUTPUT_TXT
    else:
        # Sinon, sortie principale en .md
        if not output_file:
            output_file = DEFAULT_OUTPUT_MD

    max_size_kb = args.max_size
    no_logo = args.no_logo

    # Construit la liste finale d'extensions
    included_exts = set(DEFAULT_INCLUDED_EXT)
    for e in args.include_ext:
        if not e.startswith("."):
            e = f".{e}"
        included_exts.add(e.lower())
    for e in args.exclude_ext:
        if not e.startswith("."):
            e = f".{e}"
        included_exts.discard(e.lower())


    # 1) Récupérer la liste de tous les fichiers de base
    all_files = gather_project_tree(source_folder, included_exts, ignore_spec=args.ignore_spec)

    # 1bis) Appliquer les règles du .gitignore si demandé
    if args.git_ignore:
        gitignore_path = os.path.join(source_folder, ".gitignore")
        if not os.path.isfile(gitignore_path):
            print(
                "Erreur : l'option --git-ignore est utilisée mais aucun fichier .gitignore n'a été trouvé.",
                file=sys.stderr,
            )
            sys.exit(1)

        patterns = load_gitignore_patterns(gitignore_path)
        filtered = []
        for rel_path, abs_path in all_files:
            if is_gitignored(rel_path, patterns):
                continue
            filtered.append((rel_path, abs_path))
        all_files = filtered

    # 2) Si --minimal, on filtre les fichiers "non métier"
    if args.minimal:
        filtered = []
        for rel_path, abs_path in all_files:
            # Si on juge que le fichier fait partie des exclusions "non métier", on le vire
            if is_minimal_excluded(rel_path):
                continue
            filtered.append((rel_path, abs_path))
        all_files = filtered

    # 3) Lire le contenu de chaque fichier
    files_data = []
    total_chars = 0  # Pour calculer la taille et le nombre de tokens
    for rel_path, abs_path in all_files:
        ext = os.path.splitext(rel_path)[1].lower()
        content = read_file_content(abs_path, max_size_kb)
        files_data.append({
            "rel_path": rel_path,
            "abs_path": abs_path,
            "content": content,
            "lang": ext_to_language(ext),
        })
        total_chars += len(content)

    # 4) Génération du contenu "Markdown"
    markdown_report = generate_markdown_report(source_folder, files_data, no_logo=no_logo)

    # 5) Écriture du fichier principal selon le mode de sortie
    if txt_only:
        text_report = generate_text_report(markdown_report)
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(text_report)
            print(f"Fichier texte généré : {output_file}")
        except Exception as e:
            print(f"Erreur lors de l'écriture du fichier '{output_file}' : {e}")
            sys.exit(1)
    else:
        # Sortie Markdown
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(markdown_report)
            print(f"Fichier Markdown généré : {output_file}")
        except Exception as e:
            print(f"Erreur lors de l'écriture du fichier '{output_file}' : {e}")
            sys.exit(1)

        # Optionnellement, générer un .txt supplémentaire
        if args.export_txt:
            txt_output_file = os.path.splitext(output_file)[0] + ".txt"
            text_report = generate_text_report(markdown_report)
            try:
                with open(txt_output_file, "w", encoding="utf-8") as f:
                    f.write(text_report)
                print(f"Fichier texte (en plus) généré : {txt_output_file}")
            except Exception as e:
                print(f"Erreur lors de l'écriture du fichier texte '{txt_output_file}' : {e}")

    # 6) Afficher la taille estimée et l'estimation de tokens
    total_ko = total_chars / 1024.0
    approx_tokens = sum(approximate_token_count(f["content"]) for f in files_data)
    print(f"\nAnalyse terminée.")
    print(f"Fichiers retenus : {len(files_data)}")
    print(f"Volume total lu : ~{total_ko:.2f} Ko")
    print(f"Estimation tokens : ~{approx_tokens} tokens")


if __name__ == "__main__":
    main()
