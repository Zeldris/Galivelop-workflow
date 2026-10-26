# Project note of gw-media-content

Shared by `gw-media-content` and `gw-media-content-now`. The note is `.claude/gw/gw-media-content.md` in the project: a
list of `key: value` lines (keys in English). The workflow neither creates nor overwrites it. Without it the defaults
apply and you say so once.

| Key | Default | Holds |
|---|---|---|
| Folder | `docs/difusion` | the `<dir>` of every path in the skills |
| Languages | `es, en` | any ISO 639-1 codes (two lowercase letters); the first is the main language; one `## <lang>` section per language in every channel file |
| Channels | `x, reddit, linkedin, discord` | the active channels; add `web` when the project's website reads the pieces (see below) |
| Extra channels | none | a channel beyond those five: see below |
| Web languages | the piece's `Idiomas:` | the website's languages (e.g. `es, gl, en`), passed as `comprobar.py --idiomas-web` |
| Palette | the template's | CSS variable overrides for `medios/fuente/*.html` |
| Screenshots | none | the steps that produce a screenshot of the running app |
| Task prefixes | none | e.g. `INS,FLU`: task-id prefixes of the project, passed to `comprobar.py --prefijos-tarea` |
| Reddit | none | per subreddit: the rules pasted by the user and the date read |

## Web

`web` is the project's own website: `web.md` holds one ```json block another system reads (copy
`plantilla/web.md`) with `estado`, `fecha`, `texto` (one text per language) and an optional `muro` (title, paragraphs
and images, each with its alt text per language). The skill always leaves `"estado": "borrador"`; only the user
writes `"listo"`, which is the go to publish. The keys of `texto` are the languages of `web.md`: every one of
`Idiomas:` plus any other the site needs; every other text in the block carries exactly those. With `Web languages`
in the note, they must be exactly those. Each image of `muro` is a `.webp` render listed in `## Imágenes` with `web`
in its Canales cell. `web` is never an extra channel.

## Extra channels

Channel names are lowercase `[a-z0-9-]+`. Declare each one under `Extra channels:` with its shape, one line per
channel, in exactly one of two ways:

```
Extra channels:
- mastodon: límite: 500; tono: cercano
- portal: formato: propio; plantilla: docs/difusion/portal.json
```

- `límite: N` is a channel with the usual shape (`<canal>.md`, a `## <lang>` section per language, `Imagen:` lines) and
  at most `N` characters per language section.
- `formato: propio` + `plantilla: <path in the project>` is a channel whose file another system consumes (a JSON
  block for a website, say): `<canal>.md` has the shape of that template, with no `## <lang>` sections and no length
  check. `gw-media-content-now` copies the template into the piece as `<canal>.md`.

Tone and image format are free text for the agent. A channel without `límite` or `formato: propio` has no length
check: ask the user which of the two it is. Every piece lists the extra channels it uses in `## Canales` of its
`ficha.md`; images of an extra channel are `.webp`, `.png` or `.jpg`.

## The check command

Build it from the note and from the piece's own `## Canales` (an option for a channel the piece does not list is a
usage error, exit 2). Each extra channel of the piece adds one option:

```
python3 .claude/skills/gw-media-content/scripts/comprobar.py \
  [--prefijos-tarea INS,FLU] \
  [--limite mastodon=500]... [--formato-propio portal]... [--idiomas-web es,gl,en] \
  <dir>/AAAA-MM-DD/NN-<tema>
```

`--prefijos-tarea` carries the `Task prefixes` value; `--limite <canal>=N` is for each `límite: N` channel and
`--formato-propio <canal>` for each `formato: propio` channel; `--idiomas-web` carries `Web languages` when the piece
lists `web`. Options go before the folder.

## Reddit

The line `Reddit:` holds, per subreddit, the rules the user pasted and the date read. The piece's `ficha.md` needs them
under `### Normas de r/<subreddit>` with `Normas leídas:` at most `reddit.normas_dias` (in `reglas.json`) days before
the piece's date folder: copy them from the note when that holds; otherwise ask the user to paste them again. Rules
are never invented or fetched: Reddit blocks automatic readers.
