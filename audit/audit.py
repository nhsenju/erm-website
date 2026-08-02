#!/usr/bin/env python3

from pathlib import Path
from collections import Counter
import re
import json
import html
import sys

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
REPORT_DIR = ROOT / "audit"
REPORT_FILE = REPORT_DIR / "audit-report.json"

HTML_FILES = sorted(ROOT.glob("*.html"))
CSS_FILES = sorted(ROOT.glob("*.css"))
JS_FILES = sorted(ROOT.glob("*.js"))

IMAGE_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".webp", ".avif", ".gif", ".svg"
}

report = {
    "project": str(ROOT),
    "pages": [],
    "css": [],
    "javascript": [],
    "images": [],
    "global": {
        "font_families": [],
        "font_weights": [],
        "font_sizes": [],
        "spacing_values": [],
        "colors": [],
        "container_widths": [],
        "border_radii": [],
    },
    "issues": []
}


# ---------------------------------------------------------
# Utilities
# ---------------------------------------------------------

def read_file(path):
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="latin-1")


def add_issue(severity, category, file, message):
    report["issues"].append({
        "severity": severity,
        "category": category,
        "file": str(file.relative_to(ROOT)),
        "message": message
    })


def unique_sorted(values):
    return sorted(set(values))


def extract_regex(pattern, text, flags=re.I):
    return re.findall(pattern, text, flags)


# ---------------------------------------------------------
# CSS audit
# ---------------------------------------------------------

def audit_css():

    fonts = []
    weights = []
    sizes = []
    spacing = []
    colors = []
    containers = []
    radii = []

    for css_file in CSS_FILES:

        text = read_file(css_file)

        fonts += extract_regex(
            r'font-family\s*:\s*([^;{}]+)',
            text
        )

        weights += extract_regex(
            r'font-weight\s*:\s*([^;{}]+)',
            text
        )

        sizes += extract_regex(
            r'font-size\s*:\s*([^;{}]+)',
            text
        )

        colors += extract_regex(
            r'#[0-9a-fA-F]{3,8}',
            text
        )

        spacing += extract_regex(
            r'(?:margin|padding|gap|top|right|bottom|left)\s*:\s*(-?\d+(?:\.\d+)?(?:px|rem|em|%))',
            text
        )

        containers += extract_regex(
            r'(?:max-width|width)\s*:\s*(\d+(?:\.\d+)?(?:px|rem))',
            text
        )

        radii += extract_regex(
            r'border-radius\s*:\s*([^;{}]+)',
            text
        )

        report["css"].append({
            "file": str(css_file.relative_to(ROOT)),
            "bytes": css_file.stat().st_size
        })

    report["global"]["font_families"] = unique_sorted(
        [x.strip() for x in fonts]
    )

    report["global"]["font_weights"] = unique_sorted(
        [x.strip() for x in weights]
    )

    report["global"]["font_sizes"] = unique_sorted(
        [x.strip() for x in sizes]
    )

    report["global"]["spacing_values"] = unique_sorted(
        [x.strip() for x in spacing]
    )

    report["global"]["colors"] = unique_sorted(
        [x.lower() for x in colors]
    )

    report["global"]["container_widths"] = unique_sorted(
        [x.strip() for x in containers]
    )

    report["global"]["border_radii"] = unique_sorted(
        [x.strip() for x in radii]
    )

    # Font consistency
    if len(report["global"]["font_families"]) > 3:
        add_issue(
            "warning",
            "typography",
            CSS_FILES[0] if CSS_FILES else ROOT,
            f"Trovate {len(report['global']['font_families'])} famiglie font."
        )

    # Weight consistency
    unexpected_weights = [
        x for x in report["global"]["font_weights"]
        if not re.match(r"^(400|500|600|700|normal|bold)$", x, re.I)
    ]

    if unexpected_weights:
        add_issue(
            "warning",
            "typography",
            CSS_FILES[0] if CSS_FILES else ROOT,
            "Pesi font non standard: " +
            ", ".join(unexpected_weights)
        )

    # Hardcoded colors
    if len(report["global"]["colors"]) > 8:
        add_issue(
            "warning",
            "colors",
            CSS_FILES[0] if CSS_FILES else ROOT,
            f"Trovati {len(report['global']['colors'])} colori HEX."
        )

    # Non-8px spacing
    bad_spacing = []

    for value in report["global"]["spacing_values"]:
        match = re.match(r"(-?\d+(?:\.\d+)?)px$", value)

        if match:
            number = float(match.group(1))

            if number != 0 and number % 4 != 0:
                bad_spacing.append(value)

    if bad_spacing:
        add_issue(
            "warning",
            "spacing",
            CSS_FILES[0] if CSS_FILES else ROOT,
            "Valori spacing non multipli di 4px: " +
            ", ".join(bad_spacing[:30])
        )


# ---------------------------------------------------------
# HTML / SEO / accessibility
# ---------------------------------------------------------

def audit_html():

    titles = Counter()

    for page in HTML_FILES:

        text = read_file(page)

        lower = text.lower()

        title_match = re.search(
            r"<title[^>]*>(.*?)</title>",
            text,
            re.I | re.S
        )

        description_match = re.search(
            r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']*)',
            text,
            re.I
        )

        canonical_match = re.search(
            r'<link[^>]+rel=["\']canonical["\'][^>]+href=["\']([^"\']*)',
            text,
            re.I
        )

        h1s = re.findall(
            r"<h1\b[^>]*>(.*?)</h1>",
            text,
            re.I | re.S
        )

        h2s = re.findall(
            r"<h2\b[^>]*>(.*?)</h2>",
            text,
            re.I | re.S
        )

        images = re.findall(
            r"<img\b([^>]*)>",
            text,
            re.I
        )

        links = re.findall(
            r'<a\b[^>]+href=["\']([^"\']+)["\']',
            text,
            re.I
        )

        page_data = {
            "file": str(page.relative_to(ROOT)),
            "title": html.unescape(
                re.sub(r"<[^>]+>", "", title_match.group(1)).strip()
            ) if title_match else None,
            "description": description_match.group(1).strip()
            if description_match else None,
            "canonical": canonical_match.group(1).strip()
            if canonical_match else None,
            "h1_count": len(h1s),
            "h2_count": len(h2s),
            "images": len(images),
            "links": len(links),
        }

        report["pages"].append(page_data)

        # TITLE
        if not title_match:
            add_issue(
                "error",
                "seo",
                page,
                "Manca il <title>."
            )
        else:
            titles[page_data["title"]] += 1

            title_length = len(page_data["title"])

            if title_length < 20:
                add_issue(
                    "warning",
                    "seo",
                    page,
                    f"Title molto corto ({title_length} caratteri)."
                )

            if title_length > 65:
                add_issue(
                    "warning",
                    "seo",
                    page,
                    f"Title molto lungo ({title_length} caratteri)."
                )

        # DESCRIPTION
        if not description_match:
            add_issue(
                "error",
                "seo",
                page,
                "Manca la meta description."
            )
        else:

            desc_length = len(page_data["description"])

            if desc_length < 70:
                add_issue(
                    "warning",
                    "seo",
                    page,
                    f"Meta description corta ({desc_length} caratteri)."
                )

            if desc_length > 170:
                add_issue(
                    "warning",
                    "seo",
                    page,
                    f"Meta description lunga ({desc_length} caratteri)."
                )

        # CANONICAL
        if not canonical_match:
            add_issue(
                "warning",
                "seo",
                page,
                "Manca il canonical."
            )

        # H1
        if len(h1s) == 0:
            add_issue(
                "error",
                "seo",
                page,
                "Manca H1."
            )

        elif len(h1s) > 1:
            add_issue(
                "warning",
                "seo",
                page,
                f"Trovati {len(h1s)} H1."
            )

        # OG
        og_required = [
            "og:title",
            "og:description",
            "og:image",
            "og:url"
        ]

        for og in og_required:

            if not re.search(
                rf'property=["\']{re.escape(og)}["\']',
                text,
                re.I
            ):
                add_issue(
                    "warning",
                    "social",
                    page,
                    f"Manca {og}."
                )

        # LANG
        if not re.search(
            r"<html[^>]+lang=",
            text,
            re.I
        ):
            add_issue(
                "warning",
                "accessibility",
                page,
                "Manca lang sull'elemento html."
            )

        # IMG
        for index, attrs in enumerate(images, 1):

            if not re.search(r'\balt\s*=', attrs, re.I):

                add_issue(
                    "error",
                    "accessibility",
                    page,
                    f"Immagine #{index} senza alt."
                )

            if not re.search(r'\bwidth\s*=', attrs, re.I):
                add_issue(
                    "warning",
                    "performance",
                    page,
                    f"Immagine #{index} senza width."
                )

            if not re.search(r'\bheight\s*=', attrs, re.I):
                add_issue(
                    "warning",
                    "performance",
                    page,
                    f"Immagine #{index} senza height."
                )

        # INLINE STYLE
        inline_styles = re.findall(
            r'\bstyle=["\'][^"\']+["\']',
            text,
            re.I
        )

        if inline_styles:

            add_issue(
                "warning",
                "maintainability",
                page,
                f"Trovati {len(inline_styles)} inline style."
            )

        # EMPTY LINKS
        if re.search(
            r'href=["\'](?:#|javascript:void\(0\))["\']',
            text,
            re.I
        ):

            add_issue(
                "warning",
                "links",
                page,
                "Trovati link potenzialmente vuoti."
            )

    # Duplicate titles
    for title, count in titles.items():

        if count > 1:

            for page in HTML_FILES:

                text = read_file(page)

                if title in text:

                    add_issue(
                        "error",
                        "seo",
                        page,
                        f"Title duplicato: {title}"
                    )


# ---------------------------------------------------------
# Images
# ---------------------------------------------------------

def audit_images():

    if not ASSETS.exists():
        return

    for image in sorted(ASSETS.rglob("*")):

        if image.suffix.lower() not in IMAGE_EXTENSIONS:
            continue

        size = image.stat().st_size

        data = {
            "file": str(image.relative_to(ROOT)),
            "bytes": size,
            "kb": round(size / 1024, 1),
            "mb": round(size / 1024 / 1024, 2),
        }

        report["images"].append(data)

        if size > 500 * 1024:

            add_issue(
                "warning",
                "images",
                image,
                f"Immagine pesante: {round(size / 1024)} KB."
            )

        if image.suffix.lower() in {".jpg", ".jpeg", ".png"} and size > 200 * 1024:

            add_issue(
                "warning",
                "images",
                image,
                "Valutare conversione WebP/AVIF."
            )


# ---------------------------------------------------------
# JavaScript
# ---------------------------------------------------------

def audit_js():

    for js_file in JS_FILES:

        text = read_file(js_file)

        report["javascript"].append({
            "file": str(js_file.relative_to(ROOT)),
            "bytes": js_file.stat().st_size
        })

        if "document.write(" in text:

            add_issue(
                "warning",
                "javascript",
                js_file,
                "Utilizzato document.write()."
            )


# ---------------------------------------------------------
# Report
# ---------------------------------------------------------

def print_report():

    issues = report["issues"]

    errors = sum(
        1 for x in issues if x["severity"] == "error"
    )

    warnings = sum(
        1 for x in issues if x["severity"] == "warning"
    )

    print()
    print("=" * 70)
    print("ERMETES WEBSITE — AUDIT")
    print("=" * 70)

    print()
    print(f"Pagine HTML:       {len(HTML_FILES)}")
    print(f"CSS:               {len(CSS_FILES)}")
    print(f"JavaScript:        {len(JS_FILES)}")
    print(f"Immagini:          {len(report['images'])}")

    print()
    print("DESIGN SYSTEM")
    print("-" * 70)

    print(
        "Font:",
        len(report["global"]["font_families"]),
        report["global"]["font_families"]
    )

    print(
        "Pesi:",
        len(report["global"]["font_weights"]),
        report["global"]["font_weights"]
    )

    print(
        "Font sizes:",
        len(report["global"]["font_sizes"])
    )

    print(
        "Spacing:",
        len(report["global"]["spacing_values"])
    )

    print(
        "Colori HEX:",
        len(report["global"]["colors"])
    )

    print(
        "Container widths:",
        len(report["global"]["container_widths"])
    )

    print()
    print("IMMAGINI")
    print("-" * 70)

    heavy = [
        x for x in report["images"]
        if x["bytes"] > 500 * 1024
    ]

    print(
        f"Immagini >500 KB: {len(heavy)}"
    )

    for image in heavy:
        print(
            f"  ⚠ {image['file']} — {image['kb']} KB"
        )

    print()
    print("ISSUES")
    print("-" * 70)

    if not issues:
        print("✓ Nessun problema statico rilevato.")

    else:

        for issue in issues:

            icon = "✗" if issue["severity"] == "error" else "⚠"

            print(
                f"{icon} [{issue['category']}] "
                f"{issue['file']}: "
                f"{issue['message']}"
            )

    print()
    print("=" * 70)
    print(
        f"ERRORI: {errors} | WARNING: {warnings}"
    )
    print("=" * 70)

    REPORT_DIR.mkdir(exist_ok=True)

    REPORT_FILE.write_text(
        json.dumps(
            report,
            indent=2,
            ensure_ascii=False
        ),
        encoding="utf-8"
    )

    print()
    print(f"Report JSON: {REPORT_FILE}")


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------

def main():

    print("Scansione progetto Ermetes...")

    audit_css()
    audit_html()
    audit_images()
    audit_js()

    print_report()


if __name__ == "__main__":
    main()