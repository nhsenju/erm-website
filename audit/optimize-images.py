from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
OUTPUT = ASSETS / "optimized"

OUTPUT.mkdir(parents=True, exist_ok=True)

# Dimensione massima del lato lungo.
# Valori volutamente conservativi per mantenere qualità.
TARGETS = {
    "before.webp": 1000,
    "after.webp": 1000,
    "team-2.webp": 1200,
}

# Qualità WebP alta.
QUALITY = 88


def format_kb(size):
    return f"{size / 1024:.1f} KB"


print()
print("=" * 72)
print("ERMETES — OTTIMIZZAZIONE IMMAGINI")
print("=" * 72)
print()

for filename, max_dimension in TARGETS.items():

    source = ASSETS / filename
    destination = OUTPUT / filename

    if not source.exists():
        print(f"⚠ File non trovato: {source}")
        continue

    with Image.open(source) as image:

        original_width, original_height = image.size
        original_size = source.stat().st_size

        # Mantiene proporzioni.
        scale = min(
            1,
            max_dimension / max(
                original_width,
                original_height
            )
        )

        new_width = round(original_width * scale)
        new_height = round(original_height * scale)

        if scale < 1:
            resized = image.resize(
                (new_width, new_height),
                Image.Resampling.LANCZOS
            )
        else:
            resized = image.copy()

        # Conversione RGB/RGBA corretta.
        if resized.mode not in ("RGB", "RGBA"):
            if "A" in resized.getbands():
                resized = resized.convert("RGBA")
            else:
                resized = resized.convert("RGB")

        resized.save(
            destination,
            "WEBP",
            quality=QUALITY,
            method=6
        )

        new_size = destination.stat().st_size

        reduction = (
            100 -
            (new_size / original_size * 100)
        )

        print(f"✓ {filename}")
        print(
            f"  prima:  "
            f"{original_width}x{original_height} "
            f"({format_kb(original_size)})"
        )
        print(
            f"  dopo:   "
            f"{new_width}x{new_height} "
            f"({format_kb(new_size)})"
        )
        print(
            f"  riduzione: {reduction:.1f}%"
        )
        print()

print("=" * 72)
print(f"Output: {OUTPUT}")
print("=" * 72)
print()
