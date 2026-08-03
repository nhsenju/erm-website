from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parent
BACKUP = ROOT / "_backup_before_hero_fix"
BACKUP.mkdir(exist_ok=True)

path = ROOT / "index.html"
backup = BACKUP / "index.html"

if not backup.exists():
    shutil.copy2(path, backup)
    print(f"[BACKUP] {backup}")

text = path.read_text(encoding="utf-8")
original = text

start_marker = "<!-- HERO -->"
end_marker = "<!-- BENEFICI -->"

start = text.find(start_marker)
end = text.find(end_marker, start + len(start_marker))

if start == -1:
    raise SystemExit("[ERRORE] Commento HERO non trovato.")

if end == -1:
    raise SystemExit("[ERRORE] Commento BENEFICI non trovato.")

# Manteniamo l'indentazione del commento HERO.
hero_start = text.rfind("\n", 0, start) + 1
hero_start_text = text[hero_start:start]

hero = '''<!-- HERO -->
<section class="hero">
  <div class="wrap hero__grid">

    <div class="hero__copy">

      <h1>
        Servizi di pulizia per case, uffici e auto a Trento e dintorni.
        <span>Senza pensieri.</span>
      </h1>

      <p class="hero__sub">
        Pulizie professionali e manutenzioni.
      </p>

      <a
        href="#preventivo"
        class="btn btn--cta btn--lg"
        data-track="cta_hero"
      >
        Chiedi il tuo preventivo oggi
      </a>

      <a
        href="https://wa.me/39XXXXXXXXXX?text=Ciao%20ERMETES%2C%20vorrei%20avere%20informazioni%20e%20un%20preventivo."
        class="btn btn--whatsapp btn--lg"
        data-track="cta_whatsapp"
        target="_blank"
        rel="noopener"
        aria-label="Contatta ERMETES su WhatsApp"
      >
        Scrivici su WhatsApp
      </a>

      <ul class="trustlist">
        <li>✔ Preventivo in giornata</li>
        <li>✔ Sopralluogo gratuito</li>
      </ul>

    </div>

    <div class="hero__signature">

      <div class="signature__bar">

        <div class="signature__item">
          <img
            src="/assets/optimized/before.webp"
            alt="Ambiente prima della pulizia"
            width="1000"
            height="667"
          >
          <span class="signature__label signature__label--before">
            CASA
          </span>
        </div>

        <div class="signature__item">
          <img
            src="/assets/optimized/after.webp"
            alt="Ambiente dopo la pulizia"
            width="1000"
            height="667"
          >
          <span class="signature__label signature__label--after">
            UFFICIO
          </span>
        </div>

      </div>

      <div class="signature__item">
        <img
          src="/assets/autolavaggio.webp"
          alt="Autolavaggio professionale ERMETES MULTISERVIZI"
          loading="lazy"
          width="1440"
          height="810"
        >
        <span class="signature__label signature__label--auto">
          AUTO
        </span>
      </div>

    </div>

  </div>
</section>

'''

# Inserisce il blocco usando l'indentazione originale del commento.
hero = hero_start_text + hero

text = text[:hero_start] + hero + text[end:]

if text != original:
    path.write_text(text, encoding="utf-8")
    print("[FIX] Struttura HERO riscritta correttamente")
    print("[SAVE] index.html aggiornato")
else:
    print("[NO CHANGE] Nessuna modifica necessaria")

print()
print("=" * 60)
print("FIX HERO COMPLETATO")
print("=" * 60)
print(f"Backup: {backup}")
