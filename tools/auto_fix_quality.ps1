param([string]$Src="src")

$ErrorActionPreference='Stop'
[Console]::OutputEncoding=[System.Text.UTF8Encoding]::new()
$env:PYTHONIOENCODING="utf-8"

function Run($cmd){ Write-Host ">> $cmd"; iex $cmd; if($LASTEXITCODE -ne 0){ throw "FAILED: $cmd" }}

# Dépendances
Run "pip install pyment autoflake ruff black isort"

# 0) Docstring de MODULE (injection simple en tête si absent)
$py = @'
import os, io, tokenize, sys, re, pathlib
SRC = sys.argv[1]
for root, _, files in os.walk(SRC):
    for f in files:
        if not f.endswith(".py"): continue
        p = os.path.join(root, f)
        with open(p, "r", encoding="utf-8") as fh:
            s = fh.read()
        # ignore fichiers vides
        if not s.strip():
            continue
        # a-t-il déjà une docstring de module ?
        try:
            g = tokenize.generate_tokens(io.StringIO(s).readline)
            first_tok = next((t for t in g if t.type not in (tokenize.NL, tokenize.NEWLINE, tokenize.ENCODING, tokenize.COMMENT)), None)
        except Exception:
            first_tok = None
        has_doc = bool(first_tok and first_tok.type == tokenize.STRING)
        if has_doc:
            continue
        # trouve l'index d'insertion après shebang/encoding
        lines = s.splitlines(True)
        i = 0
        if lines and lines[0].startswith('#!'):
            i += 1
        # skip encodage
        while i < len(lines) and re.match(r'#\s*-\*-\s*coding:\s*[^*]+-\*-|#\s*coding[:=]\s*\S+', lines[i]):
            i += 1
        # insère docstring
        mod = pathlib.Path(p).as_posix()
        doc = f'"""Module {mod}."""\n\n'
        s2 = "".join(lines[:i]) + doc + "".join(lines[i:])
        if s2 != s:
            with open(p, "w", encoding="utf-8", newline="") as fh:
                fh.write(s2)
'@
$tf = Join-Path $env:TEMP "add_module_docs.py"
[IO.File]::WriteAllText($tf, $py, [Text.UTF8Encoding]::new($false))
Run "python `"$tf`" $Src"

# 1) Docstrings classes/fonctions (squelettes)
Run "pyment -w -o google $Src"

# 2) Nettoyage imports/variables inutilisés
Run "autoflake -r --in-place --remove-all-unused-imports --remove-unused-variables $Src"

# 3) Lint auto-fix (imports, petites règles)
Run "python -m ruff check $Src --fix"

# 4) Tri imports + format
Run "python -m isort $Src"
Run "python -m black $Src"

Write-Host "OK: docstrings ajoutés, imports/variables nettoyés, format aligné."
