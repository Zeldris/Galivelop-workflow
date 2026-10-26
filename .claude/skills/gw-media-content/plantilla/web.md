# Web: <tema>

Lo lee la web del proyecto, no una persona: un solo bloque ```json con estas claves, sin nada que se salga de él.

- `estado`: `"borrador"` mientras se prepara; la persona lo cambia a `"listo"` cuando quiere que la web lo publique.
- `fecha`: el día de publicación (año-mes-día, como el nombre de la carpeta de fecha).
- `texto`: el texto de la novedad, uno por idioma. Sus claves son los idiomas de este archivo: los de `Idiomas:` en
  `ficha.md` y cualquier otro que pida la web (p. ej. `gl`); los demás textos llevan esos mismos idiomas.
- `muro` (opcional): la entrada del muro, con `titulo`, `cuerpo` (párrafos) e `imagenes`. Cada imagen tiene
  `archivo` (un render `medios/<nombre>.webp`, o uno por idioma: `{"es": "medios/a.webp", "en": "medios/a.en.webp"}`)
  y `alt`; su fila de `## Imágenes` en la ficha lleva `web` en Canales. Sin muro, borra la clave.

```json
{
  "estado": "borrador",
  "fecha": "AAAA-MM-DD",
  "texto": {
    "es": "{{…}}",
    "en": "{{…}}"
  },
  "muro": {
    "titulo": {"es": "{{…}}", "en": "{{…}}"},
    "cuerpo": [
      {"es": "{{…}}", "en": "{{…}}"}
    ],
    "imagenes": [
      {"archivo": "medios/tarjeta.webp", "alt": {"es": "{{…}}", "en": "{{…}}"}}
    ]
  }
}
```
