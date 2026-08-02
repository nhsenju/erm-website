const { chromium } = require("playwright");
const fs = require("fs");
const path = require("path");

const ROOT = path.resolve(__dirname, "..");
const OUT = path.join(ROOT, "audit", "visual");

const pages = [
  "index.html",
  "servizi.html",
  "chi-siamo.html",
  "contatti.html",
  "privacy.html",
  "successo.html",
  "404.html"
];

const viewports = [
  {
    name: "desktop",
    width: 1440,
    height: 1000
  },
  {
    name: "tablet",
    width: 1024,
    height: 900
  },
  {
    name: "mobile",
    width: 390,
    height: 844
  }
];

async function main() {

  fs.mkdirSync(OUT, { recursive: true });

  const browser = await chromium.launch();

  const results = [];

  for (const pageFile of pages) {

    const pagePath = path.join(ROOT, pageFile);

    if (!fs.existsSync(pagePath)) {
      console.log(`⚠ Pagina non trovata: ${pageFile}`);
      continue;
    }

    for (const viewport of viewports) {

      console.log(
        `Analisi ${pageFile} — ${viewport.name}`
      );

      const browserPage = await browser.newPage({
        viewport: {
          width: viewport.width,
          height: viewport.height
        },
        deviceScaleFactor: 1
      });

      try {

        const url = `file://${pagePath}`;

        await browserPage.goto(url, {
          waitUntil: "networkidle"
        });

        /*
         * Piccola attesa per permettere a font e immagini
         * di completare il rendering.
         */
        await browserPage.waitForTimeout(300);

        const screenshotName =
          `${pageFile.replace(".html", "")}-${viewport.name}.png`;

        await browserPage.screenshot({
          path: path.join(OUT, screenshotName),
          fullPage: true
        });

        const data = await browserPage.evaluate(() => {

          const html = document.documentElement;
          const body = document.body;

          const all = [...document.querySelectorAll("*")];

          /*
           * --------------------------------------------------
           * ELEMENTI CHE ESCONO DAL VIEWPORT
           * --------------------------------------------------
           */

          const overflowing = all
            .map(el => {

              const rect = el.getBoundingClientRect();

              return {
                tag: el.tagName.toLowerCase(),
                id: el.id || null,
                class:
                  typeof el.className === "string"
                    ? el.className
                    : null,
                left: Math.round(rect.left),
                right: Math.round(rect.right),
                top: Math.round(rect.top),
                width: Math.round(rect.width),
                height: Math.round(rect.height)
              };

            })
            .filter(item =>
              item.left < -1 ||
              item.right > window.innerWidth + 1
            )
            .slice(0, 50);


          /*
           * --------------------------------------------------
           * IMMAGINI
           * --------------------------------------------------
           */

          const images = [...document.images].map(img => {

            const rect = img.getBoundingClientRect();

            return {
              src: img.currentSrc || img.src,

              naturalWidth: img.naturalWidth,
              naturalHeight: img.naturalHeight,

              renderedWidth: Math.round(rect.width),
              renderedHeight: Math.round(rect.height),

              loading: img.loading,

              decoding:
                img.getAttribute("decoding"),

              widthAttr:
                img.getAttribute("width"),

              heightAttr:
                img.getAttribute("height"),

              alt: img.alt,

              complete: img.complete,

              visible:
                rect.width > 0 &&
                rect.height > 0
            };
          });


          /*
           * --------------------------------------------------
           * HEADING
           * --------------------------------------------------
           */

          const headings = [
            ...document.querySelectorAll(
              "h1,h2,h3,h4,h5,h6"
            )
          ].map(el => ({
            tag: el.tagName.toLowerCase(),
            text: el.innerText
              .trim()
              .replace(/\s+/g, " ")
              .slice(0, 160)
          }));


          /*
           * --------------------------------------------------
           * FONT
           * --------------------------------------------------
           */

          const fonts = [
            ...document.fonts
          ].map(font => ({
            family: font.family,
            weight: font.weight,
            style: font.style,
            status: font.status
          }));


          /*
           * --------------------------------------------------
           * FONT USATI REALMENTE
           * --------------------------------------------------
           */

          const computedFonts = {};

          for (const el of all) {

            const style = getComputedStyle(el);

            const family = style.fontFamily;
            const weight = style.fontWeight;
            const size = style.fontSize;
            const lineHeight = style.lineHeight;

            const key =
              `${family} | ${weight} | ${size} | ${lineHeight}`;

            computedFonts[key] =
              (computedFonts[key] || 0) + 1;
          }


          /*
           * --------------------------------------------------
           * COLORI REALMENTE UTILIZZATI
           * --------------------------------------------------
           */

          const computedColors = {};

          for (const el of all) {

            const style = getComputedStyle(el);

            const values = [
              style.color,
              style.backgroundColor,
              style.borderTopColor,
              style.borderRightColor,
              style.borderBottomColor,
              style.borderLeftColor
            ];

            for (const value of values) {

              if (
                value &&
                value !== "rgba(0, 0, 0, 0)" &&
                value !== "transparent"
              ) {
                computedColors[value] =
                  (computedColors[value] || 0) + 1;
              }
            }
          }


          /*
           * --------------------------------------------------
           * DIMENSIONI PRINCIPALI
           * --------------------------------------------------
           */

          const main =
            document.querySelector("main");

          const header =
            document.querySelector("header");

          const footer =
            document.querySelector("footer");

          const mainRect = main
            ? main.getBoundingClientRect()
            : null;

          const headerRect = header
            ? header.getBoundingClientRect()
            : null;

          const footerRect = footer
            ? footer.getBoundingClientRect()
            : null;


          /*
           * --------------------------------------------------
           * ELEMENTI CON INLINE STYLE
           * --------------------------------------------------
           */

          const inlineStyles = [
            ...document.querySelectorAll("[style]")
          ].map(el => ({
            tag: el.tagName.toLowerCase(),
            id: el.id || null,
            class:
              typeof el.className === "string"
                ? el.className
                : null,
            style: el.getAttribute("style")
          }));


          /*
           * --------------------------------------------------
           * BOTTONI / LINK
           * --------------------------------------------------
           */

          const buttons = [
            ...document.querySelectorAll(
              "button, a"
            )
          ].map(el => {

            const rect =
              el.getBoundingClientRect();

            return {
              tag: el.tagName.toLowerCase(),

              text: el.innerText
                .trim()
                .replace(/\s+/g, " ")
                .slice(0, 120),

              href:
                el.getAttribute("href"),

              ariaLabel:
                el.getAttribute("aria-label"),

              width:
                Math.round(rect.width),

              height:
                Math.round(rect.height)
            };

          });


          /*
           * --------------------------------------------------
           * RETURN
           * --------------------------------------------------
           */

          return {

            viewport: {
              width: window.innerWidth,
              height: window.innerHeight
            },

            document: {
              scrollWidth: html.scrollWidth,
              clientWidth: html.clientWidth,
              scrollHeight: html.scrollHeight,
              bodyWidth: body.scrollWidth
            },

            horizontalOverflow:
              html.scrollWidth >
              window.innerWidth + 1,

            main: mainRect
              ? {
                  left: Math.round(mainRect.left),
                  width: Math.round(mainRect.width),
                  right: Math.round(mainRect.right),
                  top: Math.round(mainRect.top)
                }
              : null,

            header: headerRect
              ? {
                  width: Math.round(headerRect.width),
                  height: Math.round(headerRect.height)
                }
              : null,

            footer: footerRect
              ? {
                  width: Math.round(footerRect.width),
                  height: Math.round(footerRect.height)
                }
              : null,

            overflowing,

            images,

            headings,

            fonts,

            computedFonts,

            computedColors,

            inlineStyles,

            buttons
          };

        });

        results.push({
          page: pageFile,

          viewportName: viewport.name,

          viewportSize: {
            width: viewport.width,
            height: viewport.height
          },

          screenshot: screenshotName,

          ...data
        });

      } catch (error) {

        console.error(
          `✗ Errore ${pageFile} — ${viewport.name}`
        );

        results.push({
          page: pageFile,
          viewportName: viewport.name,
          viewportSize: viewport,
          error: error.message
        });

      } finally {

        await browserPage.close();
      }
    }
  }

  await browser.close();


  /*
   * ------------------------------------------------------
   * REPORT JSON
   * ------------------------------------------------------
   */

  const reportPath =
    path.join(OUT, "visual-report.json");

  fs.writeFileSync(
    reportPath,
    JSON.stringify(
      results,
      null,
      2
    ),
    "utf-8"
  );


  /*
   * ------------------------------------------------------
   * SUMMARY
   * ------------------------------------------------------
   */

  const total =
    results.length;

  const overflow =
    results.filter(
      result => result.horizontalOverflow
    );

  const errors =
    results.filter(
      result => result.error
    );

  const totalImages =
    results.reduce(
      (sum, result) =>
        sum +
        (result.images
          ? result.images.length
          : 0),
      0
    );

  const imagesWithoutDimensions =
    results.reduce(
      (sum, result) =>
        sum +
        (result.images || []).filter(
          img =>
            !img.widthAttr ||
            !img.heightAttr
        ).length,
      0
    );

  const inlineStyles =
    results.reduce(
      (sum, result) =>
        sum +
        (result.inlineStyles || []).length,
      0
    );


  /*
   * ------------------------------------------------------
   * TERMINAL REPORT
   * ------------------------------------------------------
   */

  console.log("");

  console.log(
    "============================================================"
  );

  console.log(
    "ERMETES — VISUAL AUDIT COMPLETATO"
  );

  console.log(
    "============================================================"
  );

  console.log("");

  console.log(
    `Pagine analizzate:       ${pages.length}`
  );

  console.log(
    `Viewport analizzati:    ${total}`
  );

  console.log(
    `Overflow rilevati:      ${overflow.length}`
  );

  console.log(
    `Errori Playwright:      ${errors.length}`
  );

  console.log(
    `Immagini analizzate:    ${totalImages}`
  );

  console.log(
    `Immagini senza size:    ${imagesWithoutDimensions}`
  );

  console.log(
    `Inline style rilevati:  ${inlineStyles}`
  );

  console.log("");

  console.log(
    "RISULTATO PER PAGINA"
  );

  console.log(
    "------------------------------------------------------------"
  );


  for (const result of results) {

    if (result.error) {

      console.log(
        `✗ ${result.page.padEnd(18)} ` +
        `${result.viewportName.padEnd(8)} ` +
        "ERRORE"
      );

      continue;
    }

    const status =
      result.horizontalOverflow
        ? "⚠ OVERFLOW"
        : "✓ OK";

    console.log(
      `${status.padEnd(12)} ` +
      `${result.page.padEnd(18)} ` +
      `${result.viewportName}`
    );
  }


  console.log("");

  console.log(
    "FILE GENERATI"
  );

  console.log(
    "------------------------------------------------------------"
  );

  console.log(
    `Screenshot: ${OUT}`
  );

  console.log(
    `Report:     ${reportPath}`
  );

  console.log("");

  if (overflow.length === 0) {

    console.log(
      "✓ Nessun overflow orizzontale rilevato."
    );

  } else {

    console.log(
      `⚠ ${overflow.length} viewport presentano overflow.`
    );
  }

  console.log("");

  console.log(
    "============================================================"
  );
}


main().catch(error => {

  console.error("");
  console.error(
    "✗ AUDIT FALLITO"
  );
  console.error("");
  console.error(error);

  process.exit(1);
});