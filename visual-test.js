const { chromium } = require("playwright");
const fs = require("fs");
const path = require("path");

const BASE_URL = process.env.SITE_URL || "http://127.0.0.1:8080";

const viewports = [
  {
    name: "mobile-375",
    width: 375,
    height: 812
  },
  {
    name: "mobile-390",
    width: 390,
    height: 844
  },
  {
    name: "tablet-768",
    width: 768,
    height: 1024
  },
  {
    name: "desktop-1440",
    width: 1440,
    height: 900
  }
];

const pages = [
  "/",
  "/servizi.html",
  "/chi-siamo.html",
  "/contatti.html"
];

const outputDir = path.join(__dirname, "visual-test");

if (!fs.existsSync(outputDir)) {
  fs.mkdirSync(outputDir);
}

(async () => {
  console.log("==========================================");
  console.log(" ERMETES - VISUAL TEST");
  console.log("==========================================");
  console.log("");

  console.log(`Sito testato: ${BASE_URL}`);
  console.log("");

  let browser;

  try {
    browser = await chromium.launch({
      headless: true
    });
  } catch (error) {
    console.error("❌ Impossibile avviare Chromium.");
    console.error("");
    console.error("Esegui:");
    console.error("  npx playwright install chromium");
    console.error("");
    process.exit(1);
  }

  let totalErrors = 0;
  let totalWarnings = 0;

  for (const viewport of viewports) {
    console.log("");
    console.log("------------------------------------------");
    console.log(
      `${viewport.name} → ${viewport.width}x${viewport.height}`
    );
    console.log("------------------------------------------");

    const browserContext = await browser.newContext({
      viewport: {
        width: viewport.width,
        height: viewport.height
      },
      deviceScaleFactor: 1
    });

    const page = await browserContext.newPage();

    page.on("pageerror", error => {
      console.log(`❌ JavaScript error: ${error.message}`);
      totalErrors++;
    });

    page.on("console", message => {
      if (message.type() === "error") {
        console.log(`❌ Console error: ${message.text()}`);
        totalErrors++;
      }
    });

    for (const route of pages) {
      const url = `${BASE_URL}${route}`;

      try {
        const response = await page.goto(url, {
          waitUntil: "networkidle",
          timeout: 30000
        });

        if (!response) {
          console.log(`❌ ${route} → nessuna risposta`);
          totalErrors++;
          continue;
        }

        if (response.status() >= 400) {
          console.log(
            `❌ ${route} → HTTP ${response.status()}`
          );
          totalErrors++;
          continue;
        }

        console.log(`✅ ${route} → HTTP ${response.status()}`);

        // Controllo overflow orizzontale
        const overflow = await page.evaluate(() => {
          return {
            scrollWidth: document.documentElement.scrollWidth,
            clientWidth: document.documentElement.clientWidth
          };
        });

        if (overflow.scrollWidth > overflow.clientWidth + 2) {
          console.log(
            `⚠️  ${route} → OVERFLOW ORIZZONTALE: ` +
            `${overflow.scrollWidth}px > ${overflow.clientWidth}px`
          );

          totalWarnings++;
        } else {
          console.log(`   ✓ Nessun overflow orizzontale`);
        }

        // Controllo elementi fuori viewport
        const overflowingElements = await page.evaluate(() => {
          const elements = [];

          document.querySelectorAll("*").forEach(el => {
            const rect = el.getBoundingClientRect();

            if (
              rect.right > window.innerWidth + 2 ||
              rect.left < -2
            ) {
              elements.push({
                tag: el.tagName,
                class: el.className,
                left: Math.round(rect.left),
                right: Math.round(rect.right)
              });
            }
          });

          return elements.slice(0, 10);
        });

        if (overflowingElements.length > 0) {
          console.log(
            `⚠️  ${route} → elementi fuori viewport:`
          );

          overflowingElements.forEach(el => {
            console.log(
              `     ${el.tag} .${el.class} ` +
              `left=${el.left}px right=${el.right}px`
            );
          });

          totalWarnings++;
        } else {
          console.log(`   ✓ Elementi contenuti nella viewport`);
        }

        // Immagini senza alt
        const imagesWithoutAlt = await page.evaluate(() => {
          return [...document.images]
            .filter(img => !img.hasAttribute("alt"))
            .map(img => img.src);
        });

        if (imagesWithoutAlt.length > 0) {
          console.log(
            `⚠️  ${route} → immagini senza alt: ` +
            `${imagesWithoutAlt.length}`
          );

          totalWarnings++;
        } else {
          console.log(`   ✓ ALT immagini OK`);
        }

        // Immagini non caricate
        const brokenImages = await page.evaluate(() => {
          return [...document.images]
            .filter(img => !img.complete || img.naturalWidth === 0)
            .map(img => img.src);
        });

        if (brokenImages.length > 0) {
          console.log(`❌ ${route} → immagini non caricate:`);

          brokenImages.forEach(src => {
            console.log(`     ${src}`);
          });

          totalErrors++;
        } else {
          console.log(`   ✓ Immagini caricate`);
        }

        // Titolo
        const title = await page.title();

        if (!title || title.trim().length === 0) {
          console.log(`⚠️  ${route} → title mancante`);
          totalWarnings++;
        } else {
          console.log(`   ✓ Title: ${title}`);
        }

        // Screenshot
        const safeRoute = route
          .replace(/\//g, "_")
          .replace(/\.html/g, "");

        const screenshotName =
          `${viewport.name}${safeRoute || "_home"}.png`;

        await page.screenshot({
          path: path.join(outputDir, screenshotName),
          fullPage: true
        });

        console.log(
          `   📸 Screenshot: visual-test/${screenshotName}`
        );

      } catch (error) {
        console.log(
          `❌ ${route} → ${error.message}`
        );

        totalErrors++;
      }
    }

    await browserContext.close();
  }

  await browser.close();

  console.log("");
  console.log("==========================================");
  console.log(" RISULTATO TEST VISUALE");
  console.log("==========================================");
  console.log("");
  console.log(`Errori:  ${totalErrors}`);
  console.log(`Avvisi:  ${totalWarnings}`);
  console.log("");
  console.log(
    `Screenshot salvati nella cartella: ${outputDir}`
  );
  console.log("");

  if (totalErrors === 0 && totalWarnings === 0) {
    console.log("🎉 TEST PERFETTO");
  } else if (totalErrors === 0) {
    console.log("✅ Nessun errore grave. Controlla gli avvisi.");
  } else {
    console.log("⚠️  Ci sono problemi da correggere.");
  }

  console.log("");

  process.exit(totalErrors > 0 ? 1 : 0);
})();
