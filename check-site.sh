#!/usr/bin/env bash

set -u

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

echo ""
echo "=========================================="
echo " ERMETES MULTISERVIZI - SITE CHECK"
echo "=========================================="
echo ""

ERRORS=0
WARNINGS=0

ok() {
  echo "  ✅ $1"
}

warn() {
  echo "  ⚠️  $1"
  WARNINGS=$((WARNINGS + 1))
}

error() {
  echo "  ❌ $1"
  ERRORS=$((ERRORS + 1))
}

echo "1. STRUTTURA FILE"
echo "------------------------------------------"

[ -f "index.html" ] && ok "index.html presente" || error "index.html mancante"
[ -f "style.css" ] && ok "style.css presente" || error "style.css mancante"
[ -f "script.js" ] && ok "script.js presente" || warn "script.js mancante"
[ -f "nav.js" ] && ok "nav.js presente" || warn "nav.js mancante"
[ -d "assets" ] && ok "cartella assets presente" || error "cartella assets mancante"

echo ""
echo "2. PLACEHOLDER / DATI DA SOSTITUIRE"
echo "------------------------------------------"

PLACEHOLDERS=$(grep -RniE \
  "tuodominio\.it|NOME AZIENDA|0000 000000" \
  --include="*.html" \
  --include="*.js" \
  --include="*.css" \
  . 2>/dev/null || true)

if [ -n "$PLACEHOLDERS" ]; then
  warn "Sono presenti ancora placeholder:"
  echo "$PLACEHOLDERS"
else
  ok "Nessun placeholder evidente"
fi

echo ""
echo "3. HTML / SEO"
echo "------------------------------------------"

for file in *.html; do
  [ -f "$file" ] || continue

  TITLE=$(grep -oi "<title>" "$file" | wc -l)
  DESCRIPTION=$(grep -oi 'name="description"' "$file" | wc -l)
  H1=$(grep -oi "<h1" "$file" | wc -l)
  CANONICAL=$(grep -oi 'rel="canonical"' "$file" | wc -l)

  [ "$TITLE" -ge 1 ] \
    && ok "$file → title presente" \
    || warn "$file → title mancante"

  [ "$DESCRIPTION" -ge 1 ] \
    && ok "$file → meta description presente" \
    || warn "$file → meta description mancante"

  [ "$H1" -eq 1 ] \
    && ok "$file → un solo H1" \
    || warn "$file → H1 trovati: $H1"

  [ "$CANONICAL" -ge 1 ] \
    && ok "$file → canonical presente" \
    || warn "$file → canonical mancante"
done

echo ""
echo "4. IMMAGINI"
echo "------------------------------------------"

IMAGE_COUNT=0

while IFS= read -r file; do
  IMAGE_COUNT=$((IMAGE_COUNT + 1))

  SIZE=$(du -h "$file" | cut -f1)

  case "$file" in
    *.jpg|*.jpeg|*.png)
      BYTES=$(stat -c%s "$file")

      if [ "$BYTES" -gt 1048576 ]; then
        warn "$file → $SIZE (oltre 1 MB)"
      else
        ok "$file → $SIZE"
      fi
      ;;
    *)
      ok "$file → $SIZE"
      ;;
  esac

done < <(find assets -type f \( \
  -iname "*.jpg" -o \
  -iname "*.jpeg" -o \
  -iname "*.png" -o \
  -iname "*.webp" -o \
  -iname "*.avif" \
  \) 2>/dev/null)

if [ "$IMAGE_COUNT" -eq 0 ]; then
  warn "Nessuna immagine trovata"
fi

echo ""
echo "5. ALT TEXT IMMAGINI"
echo "------------------------------------------"

for file in *.html; do
  [ -f "$file" ] || continue

  BAD_ALT=$(grep -inE '<img[^>]+(alt="")|<img[^>]+alt=""' "$file" 2>/dev/null || true)

  if [ -n "$BAD_ALT" ]; then
    warn "$file → immagini con alt vuoto"
    echo "$BAD_ALT"
  else
    ok "$file → alt immagini OK"
  fi
done

echo ""
echo "6. LINK / RIFERIMENTI AD ASSET"
echo "------------------------------------------"

while IFS= read -r ref; do

  FILE=$(echo "$ref" | sed \
    -E 's/.*(src|href)="\/?([^"]+)".*/\2/')

  case "$FILE" in
    http*|"#"|"mailto:"*|"tel:"*|"javascript:"*)
      continue
      ;;
  esac

  CLEAN=$(echo "$FILE" | cut -d'#' -f1 | cut -d'?' -f1)

  [ -z "$CLEAN" ] && continue

  if [ -e "$CLEAN" ]; then
    ok "$CLEAN"
  elif [ -e "./$CLEAN" ]; then
    ok "$CLEAN"
  else
    warn "Riferimento possibile mancante: $CLEAN"
  fi

done < <(
  grep -RhoE '(src|href)="[^"]+"' \
    --include="*.html" \
    . 2>/dev/null || true
)

echo ""
echo "7. PAROLE CHIAVE / SEO LOCALE"
echo "------------------------------------------"

KEYWORDS=(
  "pulizie"
  "manutenzioni"
  "Trentino-Alto Adige"
  "Trentino"
  "Alto Adige"
  "preventivo"
)

for keyword in "${KEYWORDS[@]}"; do
  COUNT=$(grep -Roi "$keyword" \
    --include="*.html" \
    . 2>/dev/null | wc -l)

  if [ "$COUNT" -gt 0 ]; then
    ok "\"$keyword\" → $COUNT occorrenze"
  else
    warn "\"$keyword\" → non trovata"
  fi
done

echo ""
echo "8. FILE PESANTI"
echo "------------------------------------------"

find . \
  -type f \
  -not -path "./.git/*" \
  -not -path "./node_modules/*" \
  -size +1M \
  -printf "%s %p\n" 2>/dev/null |
sort -nr |
while read -r SIZE FILE; do
  MB=$(awk "BEGIN {printf \"%.2f\", $SIZE/1048576}")
  warn "$FILE → ${MB} MB"
done

echo ""
echo "9. GIT"
echo "------------------------------------------"

if [ -d ".git" ]; then
  ok "Repository Git presente"

  if git diff --quiet && git diff --cached --quiet; then
    ok "Nessuna modifica non committata"
  else
    warn "Ci sono modifiche non ancora committate"
    git status --short
  fi
else
  error "Repository Git non trovata"
fi

echo ""
echo "=========================================="
echo " RISULTATO CHECK STATICO"
echo "=========================================="
echo ""

echo "Errori:    $ERRORS"
echo "Avvisi:    $WARNINGS"

echo ""

echo "Ora parte il TEST VISUALE..."
echo ""

if command -v node >/dev/null 2>&1; then
  node visual-test.js
else
  error "Node.js non installato"
fi

exit 0
