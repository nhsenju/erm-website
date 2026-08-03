from pathlib import Path
import re
import shutil

ROOT = Path(__file__).resolve().parent
BACKUP = ROOT / "_backup_before_verify_fix"
BACKUP.mkdir(exist_ok=True)

FILES = [
    "index.html",
    "servizi.html",
    "chi-siamo.html",
    "contatti.html",
    "privacy.html",
    "successo.html",
    "404.html",
    "style.css",
]

def backup(path):
    dest = BACKUP / path.name
    if path.exists() and not dest.exists():
        shutil.copy2(path, dest)

def load(name):
    path = ROOT / name
    if not path.exists():
        print(f"[MISSING] {name}")
        return None
    return path.read_text(encoding="utf-8")

def save(name, text):
    path = ROOT / name
    backup(path)
    path.write_text(text, encoding="utf-8")
    print(f"[SAVE] {name}")

print("=" * 70)
print("VERIFICA E CORREZIONE SITO ERMETES")
print("=" * 70)

# ============================================================
# 1. CORREGGI TUTTI I LOGO IMG MALFORMATI
# ============================================================

logo_pattern = re.compile(
    r'<a href="/" class="logo">\s*'
    r'<img\s+'
    r'src="/assets/logo-ermetes\.png"\s+'
    r'alt="Ermetes Multiservizi"\s+'
    r'width="728"\s*'
    r'height="208"\s*'
    r'/?\s*>\s*'
    r'</a>',
    re.MULTILINE
)

correct_logo = '''<a href="/" class="logo">
  <img
    src="/assets/logo-ermetes.png"
    alt="Ermetes Multiservizi"
    width="728"
    height="208"
  >
</a>'''

for name in ["index.html", "servizi.html", "chi-siamo.html", "contatti.html"]:
    text = load(name)
    if text is None:
        continue

    # Cerca anche il caso specifico con </a> mancante/errato
    if 'src="/assets/logo-ermetes.png"' in text:
        new_text, count = logo_pattern.subn(correct_logo, text)

        if count:
            save(name, new_text)
            print(f"[OK] {name}: logo normalizzato")
        else:
            print(f"[CHECK] {name}: logo presente, controllo manuale necessario")
    else:
        print(f"[--] {name}: logo non trovato")

# ============================================================
# 2. FAVICON CORRETTO
# ============================================================

favicon_old = '<link rel="icon" href="/assets/favicon.ico" type="image/svg+xml">'

favicon_new = '''<link rel="icon" href="/assets/favicon.ico" sizes="any">
<link rel="icon" type="image/png" sizes="32x32" href="/assets/favicon-32x32.png">
<link rel="apple-touch-icon" href="/assets/apple-touch-icon.png">'''

for name in [
    "index.html",
    "servizi.html",
    "chi-siamo.html",
    "contatti.html",
]:
    text = load(name)
    if text is None:
        continue

    if favicon_old in text:
        save(name, text.replace(favicon_old, favicon_new))
        print(f"[OK] {name}: favicon corretto")
    elif 'favicon-32x32.png' in text:
        print(f"[--] {name}: favicon già corretto")
    else:
        print(f"[CHECK] {name}: favicon da controllare")

# ============================================================
# 3. RIMUOVI INLINE STYLE
# ============================================================

inline_replacements = {
    "contatti.html": [
        (
            '<div style="margin-top:36px;text-align:center">',
            '<div class="areas-section">'
        ),
        (
            '<ul class="areas" style="justify-content:center">',
            '<ul class="areas areas--center">'
        ),
    ],
    "chi-siamo.html": [
        (
            '<h2 style="text-align:left">',
            '<h2>'
        ),
    ],
    "successo.html": [
        (
            '<section class="pagehero" style="text-align:center">',
            '<section class="pagehero pagehero--center">'
        ),
    ],
    "404.html": [
        (
            '<section class="pagehero" style="text-align:center">',
            '<section class="pagehero pagehero--center">'
        ),
    ],
}

for name, replacements in inline_replacements.items():
    text = load(name)
    if text is None:
        continue

    new_text = text

    for old, new in replacements:
        new_text = new_text.replace(old, new)

    if new_text != text:
        save(name, new_text)
        print(f"[OK] {name}: inline style rimosso")
    else:
        print(f"[--] {name}: nessuna modifica necessaria")

# ============================================================
# 4. CORREGGI SPAZIATURE TESTO
# ============================================================

for name in FILES:
    if not name.endswith(".html"):
        continue

    text = load(name)
    if text is None:
        continue

    new_text = text

    replacements = {
        "bastano2 minuti": "bastano 2 minuti",
        "richiesta,forniti": "richiesta, forniti",
        "richiesta, fornita": "richiesta, fornita",
    }

    for old, new in replacements.items():
        new_text = new_text.replace(old, new)

    if new_text != text:
        save(name, new_text)
        print(f"[OK] {name}: spaziature corrette")

# ============================================================
# 5. CSS UTILITY
# ============================================================

css_path = ROOT / "style.css"

if css_path.exists():
    css = css_path.read_text(encoding="utf-8")
    backup(css_path)

    block = '''

/* =========================================================
   ERMETES - UTILITY LAYOUT
   ========================================================= */

.pagehero--center {
  text-align: center;
}

.areas-section {
  margin-top: 36px;
  text-align: center;
}

.areas--center {
  justify-content: center;
}
'''

    if ".pagehero--center" not in css:
        css = css.rstrip() + "\n" + block
        css_path.write_text(css, encoding="utf-8")
        print("[OK] style.css: utility aggiunte")
    else:
        print("[--] style.css: utility già presenti")

# ============================================================
# 6. CONTROLLO INLINE STYLE RESIDUI
# ============================================================

print()
print("=" * 70)
print("CONTROLLO INLINE STYLE RESIDUI")
print("=" * 70)

found_inline = False

for name in FILES:
    if not name.endswith(".html"):
        continue

    text = load(name)
    if text is None:
        continue

    matches = re.findall(r'\sstyle="[^"]*"', text)

    if matches:
        found_inline = True
        print(f"[INLINE] {name}:")
        for match in matches:
            print("   ", match)
    else:
        print(f"[OK] {name}: nessun inline style")

# ============================================================
# 7. CONTROLLO TAG IMG
# ============================================================

print()
print("=" * 70)
print("CONTROLLO IMMAGINI")
print("=" * 70)

for name in FILES:
    if not name.endswith(".html"):
        continue

    text = load(name)
    if text is None:
        continue

    imgs = re.findall(r'<img\b[^>]*>', text, flags=re.IGNORECASE)

    for img in imgs:
        if 'alt=' not in img.lower():
            print(f"[WARN] {name}: immagine senza alt:")
            print("   ", img[:150])

print()
print("=" * 70)
print("VERIFICA COMPLETATA")
print("=" * 70)
print(f"Backup: {BACKUP}")
print()

if found_inline:
    print("ATTENZIONE: rimangono alcuni inline style.")
else:
    print("OK: nessun inline style residuo nei file controllati.")

