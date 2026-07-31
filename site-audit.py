from pathlib import Path
from urllib.parse import urlparse
import re
import subprocess

ROOT = Path(".")
EXCLUDED = {".git", "node_modules", "visual-test", "__pycache__"}

errors = []
warnings = []
info = []

def add_error(msg):
    errors.append(msg)

def add_warning(msg):
    warnings.append(msg)

def add_info(msg):
    info.append(msg)

def files():
    return [
        p for p in ROOT.rglob("*")
        if p.is_file()
        and not any(part in EXCLUDED for part in p.parts)
    ]

all_files = files()
file_set = {p.as_posix() for p in all_files}

html_files = sorted(
    p for p in all_files
    if p.suffix.lower() == ".html"
)

print("=" * 72)
print(" ERMETES — SITE MASTER AUDIT")
print("=" * 72)

print(f"\nHTML trovati: {len(html_files)}")
for p in html_files:
    print(f"  • {p}")

# ------------------------------------------------------------
# HTML
# ------------------------------------------------------------

for p in html_files:
    s = p.read_text(errors="ignore")
    name = p.as_posix()

    # title
    if not re.search(r"<title>\s*.+?\s*</title>", s, re.I | re.S):
        add_error(f"{name}: <title> mancante")

    # description
    if name not in {"404.html", "successo.html"}:
        if not re.search(
            r'<meta\s+name=["\']description["\'][^>]*content=["\'][^"\']+',
            s,
            re.I
        ):
            add_warning(f"{name}: meta description mancante")

    # viewport
    if not re.search(
        r'<meta\s+name=["\']viewport["\']',
        s,
        re.I
    ):
        add_error(f"{name}: viewport mancante")

    # images
    for m in re.finditer(r'<img\b[^>]*>', s, re.I | re.S):
        tag = m.group(0)

        if not re.search(r'\balt\s*=', tag, re.I):
            add_warning(f"{name}: immagine senza alt")

        src = re.search(r'\bsrc=["\']([^"\']+)["\']', tag, re.I)
        if src:
            target = src.group(1).split("?")[0].split("#")[0]

            if target and not target.startswith(("http://", "https://", "data:", "/")):
                target_path = (p.parent / target).resolve()
                if not target_path.exists():
                    add_error(
                        f"{name}: immagine mancante → {target}"
                    )

    # old email
    if "info@ermetes.it" in s:
        add_error(f"{name}: contiene ancora la vecchia email")

    # old domain
    if "tuodominio.it" in s:
        add_error(f"{name}: contiene ancora tuodominio.it")

    # obvious broken spaces
    if "Richiediil" in s or "Richiediora" in s:
        add_warning(f"{name}: possibile testo CTA senza spazio")

    # CTA
    if name not in {
        "privacy.html",
        "successo.html",
        "404.html"
    }:
        if "Chiedi il tuo preventivo oggi" not in s:
            add_warning(
                f"{name}: CTA standard 'Chiedi il tuo preventivo oggi' assente"
            )

    # internal links
    for m in re.finditer(
        r'\b(?:href|src)=["\']([^"\']+)["\']',
        s,
        re.I
    ):
        target = m.group(1).strip()

        if not target:
            continue

        if target.startswith((
            "#",
            "mailto:",
            "tel:",
            "https://",
            "http://",
            "javascript:",
            "data:"
        )):
            continue

        clean = target.split("?")[0].split("#")[0]

        if not clean:
            continue

        if clean.startswith("/"):
            candidate = ROOT / clean.lstrip("/")
        else:
            candidate = p.parent / clean

        if not candidate.exists():
            add_error(
                f"{name}: riferimento locale mancante → {target}"
            )

# ------------------------------------------------------------
# ANCHOR
# ------------------------------------------------------------

anchors = {}

for p in html_files:
    s = p.read_text(errors="ignore")
    ids = set(re.findall(r'\bid=["\']([^"\']+)["\']', s, re.I))
    anchors[p.as_posix()] = ids

for p in html_files:
    s = p.read_text(errors="ignore")
    name = p.as_posix()

    for m in re.finditer(r'href=["\']([^"\']*#[^"\']+)["\']', s, re.I):
        href = m.group(1)

        if href.startswith("#"):
            target_file = p.resolve()
            fragment = href[1:]
        else:
            path, fragment = href.split("#", 1)

            # /#preventivo = ancora nella homepage
            if path.startswith("/"):
                if path == "/":
                    target_file = (ROOT / "index.html").resolve()
                else:
                    target_file = (ROOT / path.lstrip("/")).resolve()
            else:
                target_file = (p.parent / path).resolve()

        if not fragment:
            continue

        if target_file.exists():
            try:
                rel = Path(target_file).resolve().relative_to(
                    ROOT.resolve()
                ).as_posix()

                # index.html rappresenta /
                if rel == "index.html":
                    rel = "index.html"

            except ValueError:
                rel = Path(target_file).as_posix()

            if fragment not in anchors.get(rel, set()):
                add_error(
                    f"{name}: ancora #{fragment} non trovata in {rel}"
                )

# ------------------------------------------------------------
# SEO / ROBOTS / SITEMAP
# ------------------------------------------------------------

robots = ROOT / "robots.txt"
sitemap = ROOT / "sitemap.xml"

if not robots.exists():
    add_warning("robots.txt mancante")
else:
    rs = robots.read_text(errors="ignore")
    if "Sitemap:" not in rs:
        add_warning("robots.txt: Sitemap non dichiarata")

if not sitemap.exists():
    add_warning("sitemap.xml mancante")
else:
    ss = sitemap.read_text(errors="ignore")

    for p in html_files:
        if p.name in {"privacy.html", "404.html", "successo.html"}:
            continue

        if p.name == "index.html":
            expected = "https://ermetes-multiservizi.netlify.app/"
        else:
            expected = (
                "https://ermetes-multiservizi.netlify.app/"
                + p.name
            )

        if expected not in ss:
            add_warning(
                f"sitemap.xml: pagina non presente → {p.name}"
            )

# ------------------------------------------------------------
# CANONICAL
# ------------------------------------------------------------

for p in html_files:
    s = p.read_text(errors="ignore")
    name = p.as_posix()

    if name in {"404.html", "successo.html"}:
        continue

    canonical = re.findall(
        r'<link\s+rel=["\']canonical["\'][^>]*href=["\']([^"\']+)',
        s,
        re.I
    )

    if not canonical:
        add_warning(f"{name}: canonical mancante")
    elif len(canonical) > 1:
        add_error(f"{name}: canonical duplicata")

# ------------------------------------------------------------
# CSS
# ------------------------------------------------------------

css_files = [p for p in all_files if p.suffix.lower() == ".css"]

for p in css_files:
    s = p.read_text(errors="ignore")
    name = p.as_posix()

    if s.count("{") != s.count("}"):
        add_error(
            f"{name}: parentesi CSS non bilanciate "
            f"({s.count('{')} aperture / {s.count('}')} chiusure)"
        )

    if "MOBILE CTA REFINEMENT" in s:
        add_warning(f"{name}: vecchio blocco MOBILE CTA presente")

    if "Spazio verticale tra CTA su mobile" in s:
        add_warning(
            f"{name}: vecchio workaround spacing CTA presente"
        )

    if s.count("CTA SYSTEM") > 1:
        add_warning(f"{name}: più blocchi CTA SYSTEM")

# ------------------------------------------------------------
# JAVASCRIPT
# ------------------------------------------------------------

js_files = [
    p for p in all_files
    if p.suffix.lower() in {".js", ".mjs"}
]

for p in html_files:
    s = p.read_text(errors="ignore")

    for m in re.finditer(
        r'<script[^>]+src=["\']([^"\']+)["\']',
        s,
        re.I
    ):
        src = m.group(1)

        if src.startswith(("http://", "https://", "//")):
            continue

        candidate = ROOT / src.lstrip("/")

        if not candidate.exists():
            add_error(
                f"{p.as_posix()}: JS mancante → {src}"
            )

# ------------------------------------------------------------
# ASSET POTENZIALMENTE NON USATI
# ------------------------------------------------------------

asset_ext = {
    ".png", ".jpg", ".jpeg", ".webp",
    ".svg", ".gif", ".avif", ".ico"
}

assets = [
    p for p in all_files
    if p.suffix.lower() in asset_ext
]

source_text = "\n".join(
    p.read_text(errors="ignore")
    for p in html_files + css_files + js_files
)

# Considera anche i riferimenti HTML assoluti /assets/...
source_text += "\n" + "\n".join(
    p.read_text(errors="ignore")
    for p in html_files
)

for asset in assets:
    rel = asset.as_posix()
    filename = asset.name

    if rel not in source_text and filename not in source_text:
        add_warning(
            f"asset apparentemente non referenziato → {rel}"
        )

# ------------------------------------------------------------
# FILE TEMPORANEI / SOSPETTI
# ------------------------------------------------------------

suspicious_names = {
    ".DS_Store",
    "Thumbs.db",
}

suspicious_patterns = (
    ".tmp",
    ".bak",
    ".old",
    ".orig",
)

for p in all_files:
    if p.name in suspicious_names or p.name.endswith(suspicious_patterns):
        add_warning(
            f"file potenzialmente temporaneo → {p.as_posix()}"
        )

# ------------------------------------------------------------
# GIT
# ------------------------------------------------------------

try:
    git = subprocess.run(
        ["git", "status", "--short"],
        capture_output=True,
        text=True,
        check=True
    )

    git_lines = [
        x for x in git.stdout.splitlines()
        if x.strip()
    ]

    if git_lines:
        add_info("Git: ci sono modifiche locali")
        for line in git_lines:
            print("  ", line)
    else:
        add_info("Git: working tree pulito")

except Exception:
    add_warning("Impossibile leggere git status")

# ------------------------------------------------------------
# SUMMARY
# ------------------------------------------------------------

print("\n" + "=" * 72)
print(" ERRORI")
print("=" * 72)

if errors:
    for x in errors:
        print("❌", x)
else:
    print("✓ Nessun errore strutturale rilevato")

print("\n" + "=" * 72)
print(" AVVISI")
print("=" * 72)

if warnings:
    for x in warnings:
        print("⚠️ ", x)
else:
    print("✓ Nessun avviso")

print("\n" + "=" * 72)
print(" INFO")
print("=" * 72)

for x in info:
    print("ℹ", x)

print("\n" + "=" * 72)
print(
    f"RISULTATO FINALE — Errori: {len(errors)} | "
    f"Avvisi: {len(warnings)}"
)
print("=" * 72)

if errors:
    raise SystemExit(1)
