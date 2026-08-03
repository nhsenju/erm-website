from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parent
BACKUP = ROOT / "_backup_before_index_fix"
BACKUP.mkdir(exist_ok=True)

path = ROOT / "index.html"
backup = BACKUP / "index.html"

if not backup.exists():
    shutil.copy2(path, backup)
    print(f"[BACKUP] {backup}")

text = path.read_text(encoding="utf-8")
original = text

# ------------------------------------------------------------
# 1. FORM: elimina il name="preventivo"
#    Il form ha già id="leadForm" e la section ha id="preventivo".
#    Il nome Netlify è già definito correttamente dal campo
#    hidden: name="form-name" value="preventivo".
# ------------------------------------------------------------

old = '<form id="leadForm" name="preventivo" method="POST"'
new = '<form id="leadForm" method="POST"'

if old in text:
    text = text.replace(old, new)
    print("[FIX] rimosso name=\"preventivo\" dal form")
else:
    print("[OK] name=\"preventivo\" sul form non trovato")

# ------------------------------------------------------------
# 2. SVG hamburger: corregge M36h18 -> M3 6h18
# ------------------------------------------------------------

old = '<path d="M36h18M3 12h18M3 18h18"/>'
new = '<path d="M3 6h18M3 12h18M3 18h18"/>'

if old in text:
    text = text.replace(old, new)
    print("[FIX] corretto SVG hamburger")
else:
    print("[OK] SVG hamburger già corretto")

# ------------------------------------------------------------
# 3. Spazio mancante tra attributi telefono
# ------------------------------------------------------------

old = 'autocomplete="tel"inputmode="tel"'
new = 'autocomplete="tel" inputmode="tel"'

if old in text:
    text = text.replace(old, new)
    print("[FIX] aggiunto spazio tra attributi telefono")
else:
    print("[OK] attributi telefono già separati")

# ------------------------------------------------------------
# SALVATAGGIO
# ------------------------------------------------------------

if text != original:
    path.write_text(text, encoding="utf-8")
    print("[SAVE] index.html aggiornato")
else:
    print("[NO CHANGE] nessuna modifica necessaria")

print()
print("=" * 60)
print("FIX INDEX COMPLETATO")
print("=" * 60)
print(f"Backup: {backup}")
