import os
import subprocess
import pytest
import shutil

@pytest.fixture
def sample_project(tmp_path):
    """
    Crée un dossier temporaire avec plusieurs fichiers
    pour simuler un petit projet à analyser.
    Retourne le chemin de ce dossier.
    """
    # Exemple de structure
    # tmp_path/
    #   - main.py
    #   - useless.spec.ts
    #   - package-lock.json
    #   - dist/ (dossier, à ignorer si --minimal)
    #   - bigfile.txt (pour tester --max-size)
    #   etc.

    proj_dir = tmp_path / "sample_project"
    proj_dir.mkdir()

    # Fichier Python "métier"
    (proj_dir / "main.py").write_text("#!/usr/bin/env python3\nprint('Hello World')\n")

    # Fichiers spec.ts (devraient être ignorés si --ignore-spec)
    (proj_dir / "useless.spec.ts").write_text("describe('Useless', () => {});\n")
    (proj_dir / "AnotherFile.SPEC.ts").write_text("describe('Upper', () => {});\n")

    # Un package-lock.json, par ex. (à ignorer si --minimal)
    (proj_dir / "package-lock.json").write_text("{}")

    # Dossier dist/ (à ignorer si --minimal)
    dist_dir = proj_dir / "dist"
    dist_dir.mkdir()
    (dist_dir / "bundle.js").write_text("// Some compiled output")

    # Un gros fichier pour tester --max-size
    big_file = proj_dir / "bigfile.py"
    big_file_contents = "print('a'*50000)\n"  # ~50 KB en ASCII
    big_file.write_text(big_file_contents)

    # Un fichier normal .cs
    (proj_dir / "Program.cs").write_text("namespace Test { class Program { static void Main() {} } }")

    return proj_dir


def test_codescribe_help():
    """
    Vérifie que l'appel 'python codescribe.py --help' retourne un code 0
    et contient le mot 'CodeScribe'.
    """
    result = subprocess.run(["python", "codescribe.py", "--help"], capture_output=True)
    assert result.returncode == 0, "Le script devrait se terminer normalement (--help)."
    assert b"CodeScribe" in result.stdout, "La sortie d'aide devrait mentionner CodeScribe."


def test_codescribe_nonexistent():
    """
    Vérifie le comportement si on passe un --source inexistant.
    On s'attend à un code de retour != 0 et un message d'erreur.
    """
    result = subprocess.run(["python", "codescribe.py", "--source", "chemin/inexistant"], capture_output=True)
    assert result.returncode != 0, "Le script doit échouer si le dossier source est introuvable."
    assert b"introuvable" in result.stderr or b"Erreur" in result.stderr


def test_codescribe_minimal(sample_project, tmp_path):
    """
    Teste l'option --minimal, qui doit exclure package-lock.json, dist/, etc.
    On vérifie que le rapport Markdown ne contient pas ces fichiers.
    """
    output_md = tmp_path / "export_minimal.md"

    cmd = [
        "python", "codescribe.py",
        "--source", str(sample_project),
        "--minimal",
        "--output", str(output_md)
    ]
    result = subprocess.run(cmd, capture_output=True)
    assert result.returncode == 0, f"Echec: {result.stderr.decode()}"

    # Lire le rapport généré
    report_content = output_md.read_text(encoding="utf-8")

    # 'dist/' ne doit pas apparaître
    assert "dist" not in report_content, "Le dossier dist/ ne devrait pas être listé en --minimal"
    # package-lock.json ne doit pas apparaître
    assert "package-lock.json" not in report_content, "package-lock.json ne devrait pas être listé en --minimal"

    # Par contre, Program.cs, main.py devraient être là
    assert "Program.cs" in report_content
    assert "main.py" in report_content


def test_codescribe_ignore_spec(sample_project, tmp_path):
    """
    Vérifie que l'option --ignore-spec exclut les *.spec.ts.
    """
    output_md = tmp_path / "export_ignore_spec.md"

    cmd = [
        "python", "codescribe.py",
        "--source", str(sample_project),
        "--ignore-spec",
        "--output", str(output_md)
    ]
    result = subprocess.run(cmd, capture_output=True)
    assert result.returncode == 0

    content = output_md.read_text(encoding="utf-8")
    # Les fichiers .spec.ts ne doivent pas être présents
    assert "useless.spec.ts" not in content, "Le fichier .spec.ts doit être exclu en --ignore-spec"
    assert "AnotherFile.SPEC.ts" not in content, "La vérification doit être insensible à la casse"


def test_codescribe_max_size(sample_project, tmp_path):
    """
    Vérifie que l'option --max-size tronque le contenu des fichiers volumineux.
    On met --max-size=10 Ko, alors bigfile.py (~50 Ko) sera tronqué.
    """
    output_md = tmp_path / "export_maxsize.md"
    cmd = [
        "python", "codescribe.py",
        "--source", str(sample_project),
        "--max-size", "10",  # 10 Ko
        "--output", str(output_md)
    ]
    result = subprocess.run(cmd, capture_output=True)
    assert result.returncode == 0

    report_content = output_md.read_text(encoding="utf-8")
    # On vérifie qu'on a bien la mention d'une lecture partielle ou qu'on voit que c'est pas complet
    # Dans votre script, vous renvoyez le contenu tronqué mais pas forcément un message explicite.
    # On peut juste vérifier la longueur du bloc.
    assert "bigfile.py" in report_content, "Le fichier bigfile.py doit apparaître dans l'arborescence"

    # On check la taille du bloc. On s'attend à ce qu'il ne contienne pas 50k caractères.
    # Par exemple, disons qu'il ne dépasse pas ~12000 caractères (on laisse de la marge).
    assert len(report_content) < 15000, "La sortie devrait être tronquée pour bigfile.py"


def test_codescribe_export_txt(sample_project, tmp_path):
    """
    Vérifie l'option --export-txt : en plus du .md, on doit générer un fichier .txt.
    """
    output_md = tmp_path / "export_test.md"
    cmd = [
        "python", "codescribe.py",
        "--source", str(sample_project),
        "--export-txt",
        "--output", str(output_md)
    ]
    result = subprocess.run(cmd, capture_output=True)
    assert result.returncode == 0, f"Erreur: {result.stderr.decode()}"

    # Vérifier que le .md existe
    assert output_md.exists(), "Le fichier .md doit exister"
    # Le .txt doit exister aussi, avec le même nom de base
    output_txt = tmp_path / "export_test.txt"
    assert output_txt.exists(), "Le fichier .txt doit être créé avec --export-txt"


def test_codescribe_txt_only(sample_project, tmp_path):
    """
    Vérifie l'option --txt : on ne génère qu'un .txt (pas de .md).
    """
    output_txt = tmp_path / "export_only.txt"
    cmd = [
        "python", "codescribe.py",
        "--source", str(sample_project),
        "--txt",
        "--output", str(output_txt)
    ]
    result = subprocess.run(cmd, capture_output=True)
    assert result.returncode == 0

    # Le fichier txt doit exister
    assert output_txt.exists(), "Le fichier texte doit être créé en mode --txt"

    # Vérifier qu'aucun fichier .md n'a été généré
    possible_md = tmp_path / "export_only.md"
    assert not possible_md.exists(), "Aucun fichier .md ne doit être généré en mode --txt seulement"
