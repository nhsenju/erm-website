from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parent
BACKUP = ROOT / "_backup_before_fix"

FILES = [
    "servizi.html",
    "chi-siamo.html",
    "contatti.html",
    "privacy.html",
    "successo.html",
    "404.html",
    "style.css",
]

BACKUP.mkdir(exist_ok=True)

def backup(path):
    dest = BACKUP / path.name
    if not dest.exists():
        shutil.copy2(path, dest)

def replace(filename, replacements):
    path = ROOT / filename

    if not path.exists():
        print(f"[SKIP] {filename} non trovato")
        return

    backup(path)

    text = path.read_text(encoding="utf-8")
    original = text

    for old, new in replacements:
        if old in text:
            text = text.replace(old, new)
            print(f"[OK] {filename}: {old[:60]!r}")
        else:
            print(f"[--] {filename}: pattern non trovato")

    if text != original:
        path.write_text(text, encoding="utf-8")
        print(f"[SAVE] {filename}")


# ------------------------------------------------------------
# LOGO ROTTO
# ------------------------------------------------------------

old_logo = '<img src="/assets/logo-ermetes.png" alt="Ermetes Multiservizi" width="728"height="208"</a>'

new_logo = '''<a href="/" class="logo">
  <img
    src="/assets/logo-ermetes.png"
    alt="Ermetes Multiservizi"
    width="728"
    height="208"
  >
</a>'''

replace("servizi.html", [(old_logo, new_logo)])
replace("contatti.html", [(old_logo, new_logo)])


# ------------------------------------------------------------
# FAVICON
# ------------------------------------------------------------

old_favicon = '<link rel="icon" href="/assets/favicon.ico" type="image/svg+xml">'

new_favicon = '''<link rel="icon" href="/assets/favicon.ico" sizes="any">
<link rel="icon" type="image/png" sizes="32x32" href="/assets/favicon-32x32.png">
<link rel="apple-touch-icon" href="/assets/apple-touch-icon.png">'''

for filename in [
    "servizi.html",
    "chi-siamo.html",
    "contatti.html",
]:
    replace(filename, [(old_favicon, new_favicon)])


# ------------------------------------------------------------
# CONTATTI
# ------------------------------------------------------------

replace("contatti.html", [
    (
        '<div style="margin-top:36px;text-align:center">',
        '<div class="areas-section">'
    ),
    (
        '<ul class="areas" style="justify-content:center">',
        '<ul class="areas areas--center">'
    ),
    (
        'bastano2 minuti',
        'bastano 2 minuti'
    ),
])


# ------------------------------------------------------------
# CHI SIAMO
# ------------------------------------------------------------

replace("chi-siamo.html", [
    (
        '<h2 style="text-align:left">',
        '<h2>'
    ),
])


# ------------------------------------------------------------
# SUCCESSO / 404
# ------------------------------------------------------------

for filename in ["successo.html", "404.html"]:
    replace(filename, [
        (
            '<section class="pagehero" style="text-align:center">',
            '<section class="pagehero pagehero--center">'
        ),
    ])


# ------------------------------------------------------------
# PRIVACY
# ------------------------------------------------------------

replace("privacy.html", [
    (
        'descrizione della richiesta,forniti tramite il modulo preventivo.',
        'descrizione della richiesta, forniti tramite il modulo preventivo.'
    ),
])


# ------------------------------------------------------------
# CSS
# ------------------------------------------------------------

css = ROOT / "style.css"

if css.exists():
    backup(css)

    text = css.read_text(encoding="utf-8")

    css_block = '''

/* =========================================================
   LAYOUT UTILITY
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

    if ".pagehero--center" not in text:
        css.write_text(text.rstrip() + "\n" + css_block, encoding="utf-8")
        print("[OK] style.css: aggiunte classi utility")
    else:
        print("[--] style.css: classi utility già presenti")


print()
print("=" * 60)
print("CORREZIONE COMPLETATA")
print("=" * 60)
print(f"Backup creato in: {BACKUP}")
print()
