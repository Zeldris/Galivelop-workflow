# Web: <topic>

The project's website reads this file, not a person: one ```json block with these keys and nothing outside it.

- `status`: `"draft"` while it is being prepared; the person changes it to `"ready"` when the website may publish it.
- `date`: the publication day (year-month-day, like the date folder name).
- `text`: the text of the news item, one per language. Its keys are the languages of this file: those of `Languages:`
  in `sheet.md` and any other the website asks for (e.g. `gl`); every other text carries those same languages.
- `wall` (optional): the wall entry, with `title`, `body` (paragraphs) and `images`. Each image has `file` (a render
  `media/<name>.webp`, or one per language: `{"es": "media/a.webp", "en": "media/a.en.webp"}`) and `alt`; its row in
  `## Images` of the sheet lists `web` in Channels. Without a wall, delete the key.

```json
{
  "status": "draft",
  "date": "YYYY-MM-DD",
  "text": {
    "es": "{{…}}",
    "en": "{{…}}"
  },
  "wall": {
    "title": {"es": "{{…}}", "en": "{{…}}"},
    "body": [
      {"es": "{{…}}", "en": "{{…}}"}
    ],
    "images": [
      {"file": "media/card.webp", "alt": {"es": "{{…}}", "en": "{{…}}"}}
    ]
  }
}
```
