#!/usr/bin/env node
// gw-media-content: turns the sources of a piece's media into the files that get published.
//
//   node render.mjs <piece-folder | date-folder> [source...]
//   node render.mjs --plan <piece-folder | date-folder> [source...]    (print what would be rendered, as JSON)
//
// A piece folder is <dir>/AAAA-MM-DD/NN-<topic>/; a date folder holds several pieces and every one with a
// medios/fuente/ is rendered. Sources live in <piece>/medios/fuente/:
//   *.html, *.svg   rendered with Playwright's Chromium at the size they declare, <meta name="gw-size"
//                   content="1200x675"> (an SVG declares it in a comment: <!-- gw-size: 1200x675 -->; default
//                   1200x675), to medios/<name>.webp (1600 px wide at most), medios/<name>-mini.webp (720 px) and
//                   medios/<name>.png (the same size as the .webp: LinkedIn takes JPG, PNG and GIF, not WebP)
//   carrusel*.html  a document carousel: each <section class="slide"> becomes a page of medios/<name>.pdf
//   *.png, *.jpg    screenshots: converted as they are to medios/<name>.webp, <name>-mini.webp and <name>.png
// Without [source...] every source is rendered; with them, only those (file names inside medios/fuente/).
//
// Needs, and fails closed without them:
//   Playwright, resolved from the current folder, then from the folder in the env var GW_PLAYWRIGHT_DIR
//     (install: npm i -D playwright && npx playwright install chromium)
//   ImageMagick with WebP support (`magick`, or `convert` in version 6) for the WebP and PNG files
import { execFileSync } from 'node:child_process';
import { existsSync, mkdtempSync, readdirSync, readFileSync, rmSync, statSync } from 'node:fs';
import { createRequire } from 'node:module';
import { tmpdir } from 'node:os';
import { basename, extname, join, resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

const USO = 'usage: node render.mjs [--plan] <piece-folder | date-folder> [source...]';
const PAGINAS = new Set(['.html', '.svg']);
const CAPTURAS = new Set(['.png', '.jpg', '.jpeg']);
const TAMANO_POR_DEFECTO = { width: 1200, height: 675 };
const ANCHO_MAX = 1600;
const ANCHO_MINI = 720;
const CALIDAD = { '': 82, '-mini': 78 };

class Fallo extends Error {}

export function parsearArgumentos(argv) {
  const resto = [];
  let plan = false;
  let ayuda = false;
  for (const a of argv) {
    if (a === '--plan') plan = true;
    else if (a === '--help' || a === '-h') ayuda = true;
    else if (a.startsWith('--')) throw new Fallo(`unknown option ${a}. ${USO}`);
    else resto.push(a);
  }
  if (ayuda) return { ayuda: true };
  if (!resto.length) throw new Fallo(USO);
  return { carpeta: resto[0], pedidas: resto.slice(1).map((p) => basename(p)), plan };
}

export function parsearTamano(texto) {
  const m =
    texto.match(/<meta\s+name=["']gw-size["']\s+content=["'](\d+)x(\d+)["']/i) ||
    texto.match(/<!--\s*gw-size\s*:\s*(\d+)x(\d+)\s*-->/i);
  if (!m) return { ...TAMANO_POR_DEFECTO };
  const tamano = { width: Number(m[1]), height: Number(m[2]) };
  if (tamano.width < 100 || tamano.height < 100 || tamano.width > 4000 || tamano.height > 4000) {
    throw new Fallo(`gw-size ${m[1]}x${m[2]} is out of range (100 to 4000 px on each side); fix the size in the source`);
  }
  return tamano;
}

const esFuente = (f) => PAGINAS.has(extname(f).toLowerCase()) || CAPTURAS.has(extname(f).toLowerCase());
const esCarrusel = (f) => extname(f).toLowerCase() === '.html' && /^carrusel/i.test(basename(f, extname(f)));

export function piezasDe(carpeta) {
  const base = resolve(carpeta);
  if (!existsSync(base) || !statSync(base).isDirectory()) throw new Fallo(`${base} is not a folder; pass a piece folder (<dir>/AAAA-MM-DD/NN-<topic>)`);
  if (existsSync(join(base, 'medios', 'fuente'))) return [base];
  const hijas = readdirSync(base, { withFileTypes: true })
    .filter((d) => d.isDirectory() && existsSync(join(base, d.name, 'medios', 'fuente')))
    .map((d) => join(base, d.name))
    .sort();
  if (!hijas.length) throw new Fallo(`no medios/fuente/ in ${base} or in any folder below it; the sources of the media go in <piece>/medios/fuente/`);
  return hijas;
}

export function planDe(pieza, pedidas) {
  const fuenteDir = join(pieza, 'medios', 'fuente');
  const todas = readdirSync(fuenteDir).filter(esFuente).sort();
  const porNombre = new Map();
  for (const f of todas) {
    const nombre = basename(f, extname(f));
    if (porNombre.has(nombre)) throw new Fallo(`${porNombre.get(nombre)} and ${f} would both give medios/${nombre}.*; rename one of them (${fuenteDir})`);
    porNombre.set(nombre, f);
  }
  for (const p of pedidas) if (!todas.includes(p)) throw new Fallo(`${p} is not a source (.html, .svg, .png, .jpg) in ${fuenteDir}`);
  const elegidas = pedidas.length ? todas.filter((f) => pedidas.includes(f)) : todas;
  if (!elegidas.length) throw new Fallo(`no source (.html, .svg, .png or .jpg) in ${fuenteDir}`);
  const salida = join(pieza, 'medios');
  return elegidas.map((f) => {
    const nombre = basename(f, extname(f));
    const ruta = join(fuenteDir, f);
    const captura = CAPTURAS.has(extname(f).toLowerCase());
    const pdf = esCarrusel(f);
    const tamano = captura ? null : parsearTamano(readFileSync(ruta, 'utf8'));
    return {
      fuente: f,
      ruta,
      nombre,
      tipo: captura ? 'captura' : pdf ? 'pdf' : 'pagina',
      tamano,
      salidas: pdf ? [join(salida, `${nombre}.pdf`)] : [join(salida, `${nombre}.webp`), join(salida, `${nombre}-mini.webp`), join(salida, `${nombre}.png`)],
    };
  });
}

function resolverPlaywright() {
  const bases = [process.cwd()];
  if (process.env.GW_PLAYWRIGHT_DIR) bases.push(resolve(process.env.GW_PLAYWRIGHT_DIR));
  for (const base of bases) {
    const req = createRequire(join(base, 'noop.js'));
    for (const nombre of ['playwright', join(base, 'playwright')]) {
      try {
        return req.resolve(nombre);
      } catch {}
    }
  }
  return null;
}

function imagemagick() {
  for (const orden of ['magick', 'convert']) {
    try {
      const formatos = execFileSync(orden, ['-list', 'format'], { encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] });
      if (/\bWEBP\b/.test(formatos)) return orden;
    } catch {}
  }
  return null;
}

const FALTA_PLAYWRIGHT =
  'ERROR: Playwright not found (looked from the current folder and from GW_PLAYWRIGHT_DIR). ' +
  'Install it in the project and run again from its folder: npm i -D playwright && npx playwright install chromium';
const FALTA_IMAGEMAGICK =
  'ERROR: ImageMagick with WebP support not found (tried `magick` and `convert`). ' +
  'Install it: apt install imagemagick webp (Debian/Ubuntu) or brew install imagemagick webp (macOS)';

function aImagenes(im, entrada, nombre, salidaDir) {
  for (const [sufijo, extension] of [['', 'webp'], ['-mini', 'webp'], ['', 'png']]) {
    const destino = join(salidaDir, `${nombre}${sufijo}.${extension}`);
    const ancho = sufijo ? ANCHO_MINI : ANCHO_MAX;
    const calidad = extension === 'webp' ? ['-quality', String(CALIDAD[sufijo])] : [];
    execFileSync(im, [entrada, '-auto-orient', '-resize', `${ancho}x>`, '-strip', ...calidad, destino]);
    console.log(`${destino} (${Math.round(statSync(destino).size / 1024)} KB)`);
  }
}

async function prepararPagina(navegador, entrada, mensajeTamano) {
  const pagina = await navegador.newPage({ viewport: entrada.tamano, deviceScaleFactor: 1 });
  await pagina.goto(pathToFileURL(entrada.ruta).href, { waitUntil: 'load' });
  const rotas = await pagina.evaluate(async () => {
    await document.fonts.ready;
    const fallan = [];
    for (const i of document.images) {
      try {
        await i.decode();
      } catch {
        fallan.push(i.getAttribute('src') || '(empty src)');
      }
    }
    return fallan;
  });
  if (rotas.length) throw new Fallo(`${entrada.fuente}: image(s) that do not load: ${rotas.join(', ')}; fix the path (relative to medios/fuente/)`);
  const { width, height } = entrada.tamano;
  const desborda = await pagina.evaluate(
    ([w, h]) => {
      const el = document.documentElement;
      const slides = [...document.querySelectorAll('section.slide')];
      if (slides.length) return slides.some((s) => s.scrollHeight > s.clientHeight + 1 || s.scrollWidth > s.clientWidth + 1);
      return el.scrollWidth > w + 1 || el.scrollHeight > h + 1;
    },
    [width, height],
  );
  if (desborda) throw new Fallo(`${entrada.fuente}: the content overflows ${width}x${height}; ${mensajeTamano}`);
  return pagina;
}

async function ejecutar(entradas, salidaDir) {
  const necesitaNavegador = entradas.some((e) => e.tipo !== 'captura');
  const necesitaIm = entradas.some((e) => e.tipo !== 'pdf');
  let playwrightRuta = null;
  if (necesitaNavegador) {
    playwrightRuta = resolverPlaywright();
    if (!playwrightRuta) throw new Fallo(FALTA_PLAYWRIGHT);
  }
  const im = necesitaIm ? imagemagick() : null;
  if (necesitaIm && !im) throw new Fallo(FALTA_IMAGEMAGICK);

  const tmp = mkdtempSync(join(tmpdir(), 'gw-media-'));
  let navegador;
  let fallos = 0;
  try {
    if (necesitaNavegador) {
      const { chromium } = createRequire(import.meta.url)(playwrightRuta);
      try {
        navegador = await chromium.launch();
      } catch (err) {
        throw new Fallo(`Playwright cannot start Chromium (${String(err.message).split('\n')[0]}); run: npx playwright install chromium`);
      }
    }
    for (const e of entradas) {
      try {
        if (e.tipo === 'captura') {
          aImagenes(im, e.ruta, e.nombre, salidaDir);
          continue;
        }
        if (e.tipo === 'pdf') {
          const pagina = await prepararPagina(navegador, e, 'shorten the text of the slide or split it in two');
          const n = await pagina.locator('section.slide').count();
          if (!n) throw new Fallo(`${e.fuente}: no <section class="slide"> in the carousel; each slide is one <section class="slide">`);
          const { width, height } = e.tamano;
          await pagina.pdf({
            path: e.salidas[0],
            width: `${width}px`,
            height: `${height}px`,
            printBackground: true,
            margin: { top: '0', right: '0', bottom: '0', left: '0' },
            preferCSSPageSize: true,
          });
          await pagina.close();
          console.log(`${e.salidas[0]} (${n} pages, ${Math.round(statSync(e.salidas[0]).size / 1024)} KB)`);
        } else {
          const pagina = await prepararPagina(navegador, e, 'shorten the text or lower the font size');
          const png = join(tmp, `${e.nombre}.png`);
          await pagina.screenshot({ path: png, clip: { x: 0, y: 0, ...e.tamano } });
          await pagina.close();
          aImagenes(im, png, e.nombre, salidaDir);
        }
      } catch (err) {
        console.error(err instanceof Fallo ? `ERROR: ${err.message.replace(/^ERROR: /, '')}` : `ERROR: ${e.fuente}: ${err.message}`);
        fallos++;
      }
    }
  } finally {
    await navegador?.close();
    rmSync(tmp, { recursive: true, force: true });
  }
  return fallos;
}

async function main() {
  const args = parsearArgumentos(process.argv.slice(2));
  if (args.ayuda) {
    console.log(USO);
    return 0;
  }
  const piezas = piezasDe(args.carpeta).map((p) => ({ pieza: p, entradas: planDe(p, args.pedidas) }));
  if (args.plan) {
    console.log(JSON.stringify(piezas.map((p) => ({ pieza: p.pieza, fuentes: p.entradas.map(({ ruta, nombre, ...resto }) => resto) })), null, 2));
    return 0;
  }
  let fallos = 0;
  for (const p of piezas) fallos += await ejecutar(p.entradas, join(p.pieza, 'medios'));
  return fallos ? 1 : 0;
}

if (import.meta.url === pathToFileURL(process.argv[1] ?? '').href) {
  try {
    process.exitCode = await main();
  } catch (err) {
    if (!(err instanceof Fallo)) throw err;
    console.error(err.message.startsWith('ERROR') || err.message.startsWith('usage') ? err.message : `ERROR: ${err.message}`);
    process.exitCode = err.message.includes('usage:') ? 2 : 1;
  }
}
