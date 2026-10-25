---
name: gw-media-content-now
description: "Produce one unpublished post piece (texts per channel plus images) in a dated folder, from a proposal id or a free topic. Use when the user picks a proposal from gw-media-content, or asks for a single post, announcement or image about something that just happened."
license: MIT
compatibility: "Needs Python 3, git, Node with Playwright and ImageMagick (convert with WebP) for the media step."
metadata:
  version: "0.4.0"
  source: "Galivelop workshop; generalised from the World-Maker-Fantasy social-media skill"
---

# gw-media-content-now

If `.claude/gw/gw-media-content-now.md` exists in the project, read it first: it holds what is specific to the project.
Then read `.claude/gw/gw-media-content.md` if it exists (folder, languages, channels, palette, screenshots, task
prefixes, dated Reddit rules; its shape is in the `gw-media-content` skill).

You make **one piece**: `<dir>/AAAA-MM-DD/NN-<tema>/`, with texts for each channel and the images that go with
them. Pieces accumulate in the day's folder. Nothing is ever published: the user posts and records where. Shared
material is in `.claude/skills/gw-media-content/`: `catalogo.md`, `reglas.json`, `plantilla/`, `scripts/`.

## Steps

1. **Input.** A proposal id (`AAAA-MM-DD/P3`: read its block in `<dir>/propuestas/AAAA-MM-DD.md`) or a free topic
   (pick the row of `catalogo.md` that fits; with no repo data behind it, say so and stop). Done when you can name
   the topic, the facts to use and the channels: the proposal's networks (or the request's) among the active ones.
2. **Folder.** `<dir>/AAAA-MM-DD/` for today; `NN` is the next free two-digit number there (01 if none); `<tema>` is a
   lowercase slug (`a-z`, `0-9`, `-`). Copy `.claude/skills/gw-media-content/plantilla/` into `NN-<tema>/`, delete the
   channel files not in use, and set `Idiomas:` and `## Canales` in `ficha.md`. Done when the piece folder holds
   `ficha.md` plus one file per channel.
3. **Facts first: `ficha.md`.** Every claim in the piece goes in the table `Hechos comprobados` with its source.
   Numbers come from `python3 .claude/skills/gw-media-content/scripts/cifras.py [--desde REF]`; the rest from a cited
   file and line or commit. Only what is merged; lore only from the project's canon. Task ids, branches and
   internal notes go in `Uso interno`. Done when each fact a channel will use has a source cell.
4. **Media.** Every image a channel carries exists in `medios/` and is listed in `## Imágenes` with alt text in
   every language.
   - From the template: copy the source for the chosen format from `medios/fuente/` to `<name>.<lang>.html`, fill
     every `{{...}}`, delete the unused sources, apply the palette from the note.
   - Screenshots: steps in the note; crop to what matters, save in `medios/fuente/` as `.png` or `.jpg`; no personal
     data, no placeholder or broken text on screen.
   - Render: `node .claude/skills/gw-media-content/scripts/render.mjs <piece-folder>` (it names what is missing and the
     command to fix it). Use the `.png` for LinkedIn, the `.webp` for X, Reddit, Discord and extra channels, the
     `.pdf` for a LinkedIn carousel. Read each render image before using it.
5. **Channels.** Write each channel file in every language, from the ficha only, in the shape of its template file and
   within `reglas.json` (`comprobar.py` enforces it). Each post names its image on an `Imagen:` line.
   - **Reddit** only when the note or the ficha holds the subreddit's pasted rules with the date read; fill the
     `## Reddit` block from them. Without them, ask the user to paste the rules (Reddit cannot be read
     automatically), then continue.
   - **Extra channels** (declared in the note): one `<canal>.md` with a section per language, limits and tone from the
     note; if the note gives none, ask.
6. **Check.** `python3 .claude/skills/gw-media-content/scripts/comprobar.py [--prefijos-tarea <prefixes>] <piece-folder>`
   prints `OK`; each line it prints is a fix to make. Then reread the English: natural, not a literal translation.
   Done when `OK` is printed and the reread found nothing to change.
7. **Close.** Mark the proposal `**Status:** done → <piece folder>`. Commit with the project's commit format; the log
   row names the folder, its channels and that it is ready to publish. Show the user the texts and image paths.
   After publishing, the user fills `## Publicado` in `ficha.md`.
