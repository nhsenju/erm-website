from pathlib import Path
import re
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent

HTML_FILES = [
    "index.html",
    "servizi.html",
    "chi-siamo.html",
    "contatti.html",
    "privacy.html",
    "successo.html",
    "404.html",
]

REQUIRED_FILES = [
    "style.css",
    "nav.js",
    "script.js",
    "assets/logo-ermetes.png",
    "assets/favicon.ico",
]

ERROR_PATTERNS = [
    r'bastano2',
    r'richiesta,forniti',
    r'728"height',
    r'208"</a>',
    r'M36h18',
    r'autocomplete="tel"inputmode="tel"',
    r'name="preventivo"',
    r'XXXXXXXXXX',
    r'\[indirizzo\]',
    r'\[P\.IVA\]',
]

def ok(msg):
    print(f"[OK]   {msg}")

def warn(msg):
    print(f"[WARN] {msg}")

def fail(msg):
    print(f"[FAIL] {msg}")

print("=" * 70)
print("AUDIT COMPLETO ERMETES MULTISERVIZI")
print("=" * 70)

errors = 0
warnings = 0

# ------------------------------------------------------------
# 1. FILE PRINCIPALI
# ------------------------------------------------------------
print("\n=== FILE PRINCIPALI ===")

for name in HTML_FILES + REQUIRED_FILES:
    path = ROOT / name

    if path.exists():
        ok(name)
    else:
        fail(f"manca {name}")
        errors += 1

# ------------------------------------------------------------
# 2. HTML
# ------------------------------------------------------------
print("\n=== HTML ===")

for name in HTML_FILES:
    path = ROOT / name

    if not path.exists():
        continue

    text = path.read_text(encoding="utf-8", errors="replace")

    if "<!DOCTYPE html>" in text:
        ok(f"{name}: DOCTYPE")
    else:
        fail(f"{name}: DOCTYPE mancante")
        errors += 1

    if "<html" in text and 'lang="it"' in text:
        ok(f"{name}: lang=it")
    else:
        warn(f"{name}: lang=it da verificare")
        warnings += 1

    if "<title>" in text and "</title>" in text:
        ok(f"{name}: title")
    else:
        fail(f"{name}: title mancante")
        errors += 1

    if '<meta name="description"' in text:
        ok(f"{name}: meta description")
    else:
        warn(f"{name}: meta description mancante")
        warnings += 1

# ------------------------------------------------------------
# 3. ERRORI NOTI / PLACEHOLDER
# ------------------------------------------------------------
print("\n=== ERRORI NOTI / PLACEHOLDER ===")

found = False

for name in HTML_FILES:
    path = ROOT / name

    if not path.exists():
        continue

    text = path.read_text(encoding="utf-8", errors="replace")

    for pattern in ERROR_PATTERNS:
        if re.search(pattern, text):
            found = True
            warn(f"{name}: trovato {pattern}")

if not found:
    ok("nessun errore noto nei file attivi")

# ------------------------------------------------------------
# 4. INLINE STYLE
# ------------------------------------------------------------
print("\n=== INLINE STYLE ===")

inline_found = False

for name in HTML_FILES:
    path = ROOT / name

    if not path.exists():
        continue

    text = path.read_text(encoding="utf-8", errors="replace")

    if 'style="' in text:
        inline_found = True
        warn(f"{name}: contiene style inline")

if not inline_found:
    ok("nessun style inline")

# ------------------------------------------------------------
# 5. LOGO
# ------------------------------------------------------------
print("\n=== LOGO ===")

for name in ["index.html", "servizi.html", "chi-siamo.html", "contatti.html"]:
    path = ROOT / name

    if not path.exists():
        continue

    text = path.read_text(encoding="utf-8", errors="replace")

    if 'src="/assets/logo-ermetes.png"' in text:
        ok(f"{name}: logo")
    else:
        fail(f"{name}: logo non trovato")
        errors += 1

# ------------------------------------------------------------
# 6. FORM NETLIFY
# ------------------------------------------------------------
print("\n=== FORM PREVENTIVO ===")

index = ROOT / "index.html"

if index.exists():
    text = index.read_text(encoding="utf-8", errors="replace")

    checks = {
        'id="preventivo"': "sezione preventivo",
        'id="leadForm"': "form leadForm",
        'data-netlify="true"': "Netlify",
        'name="form-name" value="preventivo"': "form-name Netlify",
        'action="/successo.html"': "pagina successo",
    }

    for pattern, label in checks.items():
        if pattern in text:
            ok(label)
        else:
            fail(f"{label} mancante")
            errors += 1

# ------------------------------------------------------------
# 7. CANONICAL
# ------------------------------------------------------------
print("\n=== SEO CANONICAL ===")

for name in HTML_FILES:
    path = ROOT / name

    if not path.exists():
        continue

    text = path.read_text(encoding="utf-8", errors="replace")

    if '<link rel="canonical"' in text:
        ok(f"{name}: canonical")
    else:
        warn(f"{name}: canonical mancante")
        warnings += 1

# ------------------------------------------------------------
# 8. FAVICON
# ------------------------------------------------------------
print("\n=== FAVICON ===")

for name in ["index.html", "servizi.html", "chi-siamo.html", "contatti.html"]:
    path = ROOT / name

    if not path.exists():
        continue

    text = path.read_text(encoding="utf-8", errors="replace")

    if "favicon" in text:
        ok(f"{name}: favicon")
    else:
        warn(f"{name}: favicon non trovato")
        warnings += 1

# ------------------------------------------------------------
# 9. LINK LOCALI
# ------------------------------------------------------------
print("\n=== LINK LOCALI ===")

missing_links = set()

for name in HTML_FILES:
    path = ROOT / name

    if not path.exists():
        continue

    text = path.read_text(encoding="utf-8", errors="replace")

    for href in re.findall(r'href=["\']([^"\']+)["\']', text):

        if href.startswith(("http://", "https://", "mailto:", "tel:", "#")):
            continue

        href = href.split("#")[0]
        href = href.split("?")[0]

        if not href or href == "/":
            target = ROOT / "index.html"
        elif href.startswith("/"):
            target = ROOT / href.lstrip("/")
        else:
            target = (path.parent / href).resolve()

        if not target.exists():
            missing_links.add((name, href))

if missing_links:
    for name, href in sorted(missing_links):
        fail(f"{name}: link non trovato -> {href}")
        errors += 1
else:
    ok("nessun link locale mancante")

# ------------------------------------------------------------
# 10. ASSET SRC
# ------------------------------------------------------------
print("\n=== ASSET IMMAGINI ===")

missing_assets = set()

for name in HTML_FILES:
    path = ROOT / name

    if not path.exists():
        continue

    text = path.read_text(encoding="utf-8", errors="replace")

    for src in re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', text):

        if src.startswith(("http://", "https://")):
            continue

        src = src.split("?")[0]

        if src.startswith("/"):
            target = ROOT / src.lstrip("/")
        else:
            target = path.parent / src

        if not target.exists():
            missing_assets.add((name, src))

if missing_assets:
    for name, src in sorted(missing_assets):
        fail(f"{name}: asset mancante -> {src}")
        errors += 1
else:
    ok("nessun asset immagine mancante")

# ------------------------------------------------------------
# 11. WHATSAPP
# ------------------------------------------------------------
print("\n=== WHATSAPP ===")

if index.exists():
    text = index.read_text(encoding="utf-8", errors="replace")

    match = re.search(r'https://wa\.me/([^?"]+)', text)

    if not match:
        warn("link WhatsApp non trovato")
        warnings += 1
    elif "XXXXXXXXXX" in match.group(1):
        warn("WhatsApp contiene ancora il numero placeholder")
        warnings += 1
    else:
        ok("numero WhatsApp configurato")

# ------------------------------------------------------------
# 12. PRIVACY
# ------------------------------------------------------------
print("\n=== PRIVACY ===")

privacy = ROOT / "privacy.html"

if privacy.exists():
    text = privacy.read_text(encoding="utf-8", errors="replace")

    placeholders = [
        "[indirizzo]",
        "[P.IVA]",
        "Questa pagina è un modello",
    ]

    privacy_placeholders = [
        x for x in placeholders if x in text
    ]

    if privacy_placeholders:
        for item in privacy_placeholders:
            warn(f"privacy: ancora presente -> {item}")
            warnings += 1
    else:
        ok("privacy senza placeholder")

# ------------------------------------------------------------
# RISULTATO
# ------------------------------------------------------------
print("\n" + "=" * 70)
print("RISULTATO AUDIT")
print("=" * 70)

print(f"ERRORI : {errors}")
print(f"WARNING: {warnings}")

if errors == 0:
    print("\n[OK] Nessun errore bloccante trovato.")
else:
    print("\n[ATTENZIONE] Ci sono errori da correggere.")

print("=" * 70)
