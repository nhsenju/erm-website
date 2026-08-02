from pathlib import Path
import shutil
import re

ROOT = Path(__file__).resolve().parent.parent
BACKUP = ROOT / "audit" / "backups" / "image-fixes"
BACKUP.mkdir(parents=True, exist_ok=True)

FILES = [
    "index.html",
    "servizi.html",
    "chi-siamo.html",
    "contatti.html",
    "privacy.html",
    "successo.html",
    "404.html",
]

# Dimensioni reali delle immagini.
IMAGE_SIZES = {
    "/assets/logo-ermetes.png": (728, 208),
    "/assets/before.webp": (1000, 667),
    "/assets/after.webp": (1000, 667),
    "/assets/autolavaggio.webp": (1440, 810),
    "/assets/team.webp": (1521, 809),
    "/assets/ermetes.webp": (952, 751),
    "/assets/team-2.webp": (750, 1000),
}

# Immagini ottimizzate disponibili.
OPTIMIZED = {
    "/assets/before.webp":
        "/assets/optimized/before.webp",

    "/assets/after.webp":
        "/assets/optimized/after.webp",

    "/assets/team-2.webp":
        "/assets/optimized/team-2.webp",
}


def add_dimensions(match):
    tag = match.group(0)

    src_match = re.search(
        r'src=["\']([^"\']+)["\']',
        tag,
        re.I
    )

    if not src_match:
        return tag

    src = src_match.group(1)

    if src not in IMAGE_SIZES:
        return tag

    width, height = IMAGE_SIZES[src]

    # Non duplicare attributi esistenti.
    if not re.search(r'\bwidth\s*=', tag, re.I):
        tag = tag[:-1] + f' width="{width}"'

    if not re.search(r'\bheight\s*=', tag, re.I):
        tag = tag[:-1] + f' height="{height}"'

    return tag


def add_async_decoding(match):
    tag = match.group(0)

    src_match = re.search(
        r'src=["\']([^"\']+)["\']',
        tag,
        re.I
    )

    if not src_match:
        return tag

    src = src_match.group(1)

    # Il logo non ha bisogno di decoding async.
    if src == "/assets/logo-ermetes.png":
        return tag

    if not re.search(r'\bdecoding\s*=', tag, re.I):
        tag = tag[:-1] + ' decoding="async"'

    return tag


def add_loading(match):
    tag = match.group(0)

    src_match = re.search(
        r'src=["\']([^"\']+)["\']',
        tag,
        re.I
    )

    if not src_match:
        return tag

    src = src_match.group(1)

    # Immagini sotto la piega.
    lazy_images = {
        "/assets/before.webp",
        "/assets/after.webp",
        "/assets/autolavaggio.webp",
        "/assets/ermetes.webp",
        "/assets/team-2.webp",
    }

    if src in lazy_images:

        if not re.search(r'\bloading\s*=', tag, re.I):
            tag = tag[:-1] + ' loading="lazy"'

    return tag


def replace_optimized(match):
    tag = match.group(0)

    for old, new in OPTIMIZED.items():

        pattern = (
            r'(["\'])'
            + re.escape(old)
            + r'\1'
        )

        tag = re.sub(
            pattern,
            lambda m:
                m.group(1) + new + m.group(1),
            tag
        )

    return tag


def process_file(filename):

    source = ROOT / filename

    if not source.exists():
        print(f"⚠ File non trovato: {filename}")
        return

    # Backup individuale.
    backup = BACKUP / filename
    shutil.copy2(source, backup)

    text = source.read_text(
        encoding="utf-8"
    )

    original = text

    # Trova tutti gli <img>.
    text = re.sub(
        r'<img\b[^>]*>',
        replace_optimized,
        text,
        flags=re.I
    )

    text = re.sub(
        r'<img\b[^>]*>',
        add_dimensions,
        text,
        flags=re.I
    )

    text = re.sub(
        r'<img\b[^>]*>',
        add_async_decoding,
        text,
        flags=re.I
    )

    text = re.sub(
        r'<img\b[^>]*>',
        add_loading,
        text,
        flags=re.I
    )

    if text != original:

        source.write_text(
            text,
            encoding="utf-8"
        )

        print(f"✓ Modificato: {filename}")

    else:

        print(f"— Nessuna modifica: {filename}")


print()
print("=" * 70)
print("ERMETES — IMAGE FIX")
print("=" * 70)
print()

for filename in FILES:
    process_file(filename)

print()
print("=" * 70)
print("COMPLETATO")
print("=" * 70)
print()
print(f"Backup: {BACKUP}")
print()
