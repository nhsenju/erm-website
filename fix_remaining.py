from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parent
BACKUP = ROOT / "_backup_before_final_fix"
BACKUP.mkdir(exist_ok=True)

def fix_logo(filename):
    path = ROOT / filename

    if not path.exists():
        print(f"[SKIP] {filename} non trovato")
        return

    backup = BACKUP / filename
    if not backup.exists():
        shutil.copy2(path, backup)

    text = path.read_text(encoding="utf-8")

    broken = '<a href="/" class="logo"><img src="/assets/logo-ermetes.png" alt="Ermetes Multiservizi" width="728" height="208"</a>'

    fixed = '''<a href="/" class="logo">
  <img
    src="/assets/logo-ermetes.png"
    alt="Ermetes Multiservizi"
    width="728"
    height="208"
  >
</a>'''

    if broken in text:
        text = text.replace(broken, fixed)
        path.write_text(text, encoding="utf-8")
        print(f"[FIX] {filename}: logo corretto")
    else:
        print(f"[OK] {filename}: logo già corretto o pattern diverso")

for filename in ["servizi.html", "contatti.html"]:
    fix_logo(filename)

print()
print("Correzione completata.")
print(f"Backup: {BACKUP}")
