# Redes sociales para proyectos indie de software: qué pesa, qué temas, qué formatos

Consulta: 2026-10-25. Para rediseñar la skill que **prepara** (no publica) contenido para World-Maker-Fantasy (app/juego) y Galivelop-workflow (flujo con agentes de IA).

## Resumen

1. **Límite de esta investigación:** varias fuentes primarias dieron 403 o no se pudieron abrir (blog de ingeniería de X, reddiquette, reglas de r/gamedev, página de TikTok). Esos puntos van marcados «no verificado» o «secundaria»; la skill debe tratarlos como hipótesis y no como reglas duras.
2. **X:** el único dato primario sólido son los pesos del *heavy ranker* (repo `twitter/the-algorithm-ml`, abril de 2023): respuesta que el autor contesta = 75, respuesta = 13,5, retuit = 1, favorito = 0,5, bloqueo/silenciar = -74, reporte = -369. Conversación > likes. Los pesos cambian.
3. **Enlaces en X:** la «penalización de enlaces» se desmintió en 2026 (Bier, abril; Musk, julio: «hace más de un año que no»). Son declaraciones, no documentación. Regla segura: enlace en el cuerpo con contexto suficiente; no depender de ello.
4. **Instagram:** Mosseri (enero de 2025) dice que las tres señales principales son tiempo de visionado, likes y envíos (*sends*); métricas por alcance (*per reach*). Los envíos pesan más con desconocidos.
5. **TikTok:** señales = interacciones, información del vídeo y ajustes del dispositivo (estos con peso menor); ver el vídeo entero pesa más que señales débiles.
6. **LinkedIn:** el feed se reconstruyó con LLM y transformers (2025-2026). Los documentos (PDF/carrusel) admiten hasta 300 páginas y 100 MB (ayuda oficial). Sin datos primarios sobre enlaces o hashtags.
7. **Reddit/Discord/Mastodon/Bluesky:** las comunidades mandan más que el algoritmo. Reddit castiga la autopromoción pura; los devlogs y postmortems con sustancia funcionan; cada subreddit tiene sus reglas y hay que leerlas antes.
8. **Temas que más rinden en indie dev:** devlog técnico con un GIF/clip, antes/después, fallos y lecciones, hitos con números y #screenshotsaturday; para el flujo de IA, métricas reales (tokens, tests, coste) y errores propios.
9. **Visuales generables desde el repo:** HTML→PNG con Playwright (tarjetas de métricas, citas, código, OG), PDF→carrusel LinkedIn, ffmpeg (clips, subtítulos, timelapse), GIF de grabación de Playwright, gráficos desde JSON/CSV.
10. **Formatos oficiales fiables:** Shorts hasta 3 min y vertical o cuadrado (ayuda de YouTube); LinkedIn documentos 300 págs/100 MB; Bluesky 300 caracteres, 4 imágenes, vídeo 3 min (fuentes secundarias coincidentes).
11. **Horarios y frecuencia:** solo hay estudios secundarios (Sprout, Buffer) y se contradicen; la skill no debe prometer «mejor hora», solo sugerir y medir.
12. **Diseño de la skill:** catálogo `tema × formato × red` en §4, con la fuente de datos del repo para cada tipo; todo queda en borrador para revisión humana, con texto alternativo siempre.

---

## 1. Qué pesa en cada red

Leyenda de fuente: **P** = primaria; **S** = secundaria (con fecha); **NV** = no verificado en esta sesión (conocimiento general, comprobar antes de fijarlo en la skill).

### 1.1 X

| Aspecto | Hallazgo | Fuente |
|---|---|---|
| Señales | Puntuación = suma ponderada de probabilidades de acción. Pesos (abril 2023): favorito 0,5; retuit 1; respuesta 13,5; clic de perfil bueno 12; clic bueno (entra y responde/da like) 11; clic bueno v2 (2+ min en la conversación) 10; respuesta con réplica del autor **75**; vídeo visto ≥50 % 0,005; feedback negativo -74; reporte -369. Los pesos se ajustan con el tiempo. | P: github.com/twitter/the-algorithm-ml (`projects/home/recap/README.md`) |
| Implicación | Las conversaciones (y que el autor responda) pesan mucho más que likes. Preguntas y respuestas rápidas del autor. | derivado de P |
| Enlaces externos | Bier (jefe de producto) calificó de «fake news» el deboost de enlaces (abril 2026) y recomienda el enlace en el cuerpo con contexto; en julio de 2026 Musk dijo que no se penaliza «desde hace más de un año». Antes (2023-2025) circulaba que sí. No hay documento oficial. | S: Social Media Today, ppc.land, roboin.io, siecledigital.fr (abril y julio 2026) |
| Formato, longitud, hashtags, horarios | Estudio de Sprout 2025: X rinde martes-jueves 9-14 h; Buffer: lunes y viernes 11 h (más de 1 M de posts). Contradicen en parte. | S: Sprout 2025 (vía Social Media Today), Buffer (fecha 2025-2026 sin confirmar) |
| Límites técnicos de imagen/vídeo | No verificado esta sesión. | NV |
| Blog de ingeniería de X (2023-03-31) | No pudo abrirse (403). | — |

### 1.2 LinkedIn

| Aspecto | Hallazgo | Fuente |
|---|---|---|
| Algoritmo | LinkedIn reconstruyó el feed con LLM (LLaMA 3 afinado como dual encoder para recuperación, 2000 candidatos) y modelos transformer; prioriza relevancia temática y patrones de interacción. | P parcial: arXiv 2510.14223 («Large Scale Retrieval for the LinkedIn Feed using Causal Language Models»); resúmenes S: ppc.land (marzo 2026), Search Engine Land |
| Documentos/carruseles | PDF/PPT/DOC hasta **100 MB y 300 páginas**; vídeos/animaciones dentro del documento se muestran estáticos. | P: linkedin.com/help/linkedin/answer/97459 |
| Vídeo | Máx. 10 min (personal) / 30 min (página): solo API de terceros. | S: docs.zernio.com (2026) |
| Horarios | Sprout 2025: martes-jueves, 10-13 h. Buffer 2026: tramo 17-20 h; contradice. | S |
| Enlaces, hashtags, longitud, frecuencia | Sin fuente primaria hallada. Práctica común (NV): enlace en comentario o en el cuerpo, 3-5 hashtags. | NV |

### 1.3 Reddit

| Aspecto | Hallazgo | Fuente |
|---|---|---|
| Autopromoción | La reddiquette y las reglas de r/gamedev no pudieron abrirse (403 / bloqueado). Guía de marketing: «mira mi juego, wishlist» no funciona; devlogs y postmortems sí; r/gamedev tiene un hilo recurrente Screenshot Saturday. | S: presskit.gg/field-guides/reddit-marketing-indie-games (fecha no indicada) |
| Norma comunitaria | Cada sub tiene normas propias y algunos suspenden sus días de promoción (ejemplo r/iosgaming). | S: redlib/r/iosgaming |
| «Regla 9:1» / 10 % de la reddiquette | No confirmada. | NV |
| r/IndieDev, r/indiegaming, r/programming, r/ClaudeAI | No se verificó cada regla. La skill debe pedir al usuario que lea la barra lateral/wiki antes de publicar y registrar la fecha de lectura. | NV |

### 1.4 Discord

| Aspecto | Hallazgo | Fuente |
|---|---|---|
| Canales de anuncios | Canal de tipo Announcement con botón Follow; lo publicado aparece en los servidores que lo siguen; `@everyone/@here` no se propagan. | P: support.discord.com/hc/en-us/articles/360028384531 |
| Foros | Sin documentación oficial hallada; seguimiento de foros solo con bots de terceros. | NV |
| Uso en la skill | Discord es canal de comunidad, no de alcance: posts de changelog, hilos de feedback, vista previa a testers. | juicio |

### 1.5 Instagram y Threads

| Aspecto | Hallazgo | Fuente |
|---|---|---|
| Señales | «Las tres señales principales: tiempo de visionado, likes y envíos». Mira tiempo medio de visionado, likes por alcance y envíos por alcance. Likes algo más importantes para contenido conectado; envíos para no conectado. En 2024: tasa > recuento; envíos por alcance correlaciona más con el alcance. | P citada vía S: Social Media Today («Instagram shares algorithm insights 2025», enero 2025) y Social Samosa |
| Reels | 9:16, 1080×1920, ≥720 px, 30 fps; recorte a 4:5 en el feed principal y 3:4 en la cuadrícula; los de más de 3 min no se recomiendan a audiencias nuevas. | S: guías (argil.ai, Hootsuite) 2025-2026; no se abrió la ayuda oficial |
| Carrusel | 4:5 (1080×1350); 2-10 tarjetas. | S/NV |
| Threads | No verificado. | NV |

### 1.6 TikTok

| Aspecto | Hallazgo | Fuente |
|---|---|---|
| Señales | Interacciones (likes, compartir, seguir, comentarios), información del vídeo (leyendas, sonidos, hashtags) y ajustes de dispositivo/cuenta (peso menor). Terminar un vídeo largo pesa más que una señal débil. | P (extractos y reimpresiones): newsroom.tiktok.com/en-us/how-tiktok-recommends-videos-for-you/ (2020, actualizada 2023); la página no pudo abrirse directamente |
| Formato | 9:16, 1080×1920; subida hasta 60 min, grabación en la app hasta 10 min; MP4 H.264/AAC. | S: guías (stackinfluence, Shopify) 2025 |
| Horarios | Sprout: miércoles 14-17 h; Buffer: sábado el mejor. Contradicen. | S |

### 1.7 YouTube Shorts

| Aspecto | Hallazgo | Fuente |
|---|---|---|
| Definición | Subidos desde el **15-10-2024**, cuadrados o verticales y de hasta **3 min** se clasifican como Shorts. | P: support.google.com/youtube/answer/15424877 |
| Recomendación/Creator Insider | No se consultó. | NV |

### 1.8 Bluesky

| Aspecto | Hallazgo | Fuente |
|---|---|---|
| Feeds | Los feeds personalizados son servicios (*feed generators*) identificados por un AT-URI; el servicio devuelve URIs de posts (`getFeedSkeleton`). Los usuarios eligen su algoritmo. | P: docs.bsky.app/docs/starter-templates/custom-feeds; atproto.com/guides/feeds |
| Límites | 300 caracteres (grafemas); 4 imágenes ≤2 MB (JPEG/PNG/WebP); 1 vídeo MP4 ≤100 MB y ≤3 min (no mezclable con imágenes); alt text hasta 2000 caracteres (imagen) / 1000 (vídeo). Algunas guías discrepan. | S: recurpost.com, Ayrshare (2025-2026) |
| Hashtags | Sin fuente oficial hallada. | NV |
| Implicación | Una publicación en Bluesky puede entrar en feeds temáticos (p. ej. de dev/gamedev); usar palabras clave claras. Las imágenes necesitan alt text. | juicio |

### 1.9 Mastodon

| Aspecto | Hallazgo | Fuente |
|---|---|---|
| Hashtags CamelCase | Mayúscula al inicio de cada palabra para lectores de pantalla; los hashtags no distinguen mayúsculas. | S: fedi.tips, wisechecker.com (fecha no indicada). Docs oficiales no abiertas |
| Sin algoritmo, alt text | Línea de tiempo cronológica y texto alternativo: práctica conocida, sin fuente abierta esta sesión. | NV |
| Implicación | Los hashtags son el único mecanismo de descubrimiento: 3-5, en CamelCase; alt text siempre. | juicio |

### 1.10 Web / blog propio

| Aspecto | Hallazgo | Fuente |
|---|---|---|
| Open Graph | `og:image` 1200×630 (≈1,91:1) como estándar práctico; mínimo ≈600×315; tags en HTML renderizado en servidor; X necesita `twitter:card=summary_large_image`. Peso recomendado <1 MB. | S: guías (dev.to/grabbit, frontendchecklist.io, 2026); ogp.me no se abrió |
| RSS, SEO | No se consultó. El blog propio es el único sitio donde el enlace no depende de otra red; sirve como destino canónico (permalink) de los posts largos. | NV/juicio |

### 1.11 Frecuencia y horarios (resumen)

| Red | Mejor franja (secundaria) | Cuidado |
|---|---|---|
| Todas | Lun-jue, 10-13 h; miércoles el mejor (Sprout, ≈2,5 mil millones de interacciones, 600 000 perfiles, 2025) | La zona horaria y el público de un indie pueden diferir. |
| X | Mar-jue 9-14 h (Sprout 2025); lun/vie 11 h (Buffer) | Contradictorio. |
| LinkedIn | Mar-jue 10-13 h (Sprout); 17-20 h (Buffer 2026) | Contradictorio. |
| TikTok | Mié 14-17 h (Sprout); sábado (Buffer, 7,1 M de posts) | Contradictorio. |
| Frecuencia | Sin estudio hallado | La skill no fija cadencia; la propone según lo que haya en el repo. |

---

## 2. Temáticas que funcionan

Fuentes para este apartado: guía de marketing de Reddit (S, presskit.gg), resúmenes de Chris Zukowski (S: Game World Observer 2025-03-11, WN Hub, Unity), documentación de Steamworks (P: «Steam Next Fest – Tips»). No se consultaron postmortems de GDC ni el blog de Steamworks completos; los ejemplos de la columna «evidencia» son los hallados. El resto es juicio y debe validarse con la propia recogida (`gw-harvest`).

| Tema | Mejor red | Por qué | Evidencia |
|---|---|---|---|
| Cómo funciona la app (demo corta) | TikTok/Shorts/Reels, Bluesky, X | Un clip de 15-30 s muestra la propuesta; los mejores resultados vienen de enseñar el juego (jugabilidad) | Zukowski: el Steam page debe mostrar varias situaciones distintas (S) |
| Devlog técnico | Reddit (r/gamedev, r/IndieDev), LinkedIn, blog | Sustancia que no es promoción pura | presskit.gg (S): devlogs y postmortems sí funcionan |
| #screenshotsaturday | X, Bluesky, Mastodon, Reddit (hilo de r/gamedev) | Hilo semanal recurrente que da audiencia | presskit.gg (S) |
| Fallos y lecciones | LinkedIn, Reddit, X | Alta conversación (respuestas), dato fiable en X: las respuestas pesan 13,5-75 | pesos de X (P) |
| Datos/métricas del flujo con IA | LinkedIn, X, r/ClaudeAI, blog | Cifras propias y verificables; público de devs | juicio |
| Antes/después | Instagram, TikTok, X | Visual, rápido, compartible (envíos) | Mosseri: envíos (S/P) |
| Entre bastidores / build in public | X, Bluesky, Mastodon | Conversación continua con seguidores | juicio |
| Hitos | LinkedIn, X | Cifras redondas, noticia concreta | juicio |
| Preguntas a la comunidad | X, Bluesky, Discord, Reddit | Respuestas pesan mucho en X; en Discord es el canal natural | pesos de X (P) |
| Lore y mundo del juego | Instagram, TikTok, Mastodon, Discord | Imagen + texto breve; afinidad con fantasía y arte | juicio |
| Changelog / roadmap | Discord, blog, Steam (anuncios), LinkedIn (resumen) | Destino de enlace estable; en Steam, eventos y anuncios | Steamworks: feedback desde el propio demo (P) |
| Tutorial corto | YouTube Shorts, TikTok, blog | Búsqueda y vigencia | juicio |
| Next Fest / demos | Steam, X, Discord | Demo lista ≈10 días antes para prensa; enlace de feedback en el menú | P: Steamworks Next Fest Tips |

**Advertencia para la skill:** el proyecto de World-Maker-Fantasy y el flujo de IA tienen públicos distintos; no mezclar en un mismo post.

---

## 3. Visuales y multimedia

Tamaños: P = oficial; S = secundaria; NV = no verificado.

| Formato | Redes | Especificación | Autogenerable desde el repo |
|---|---|---|---|
| Carrusel / PDF | LinkedIn (PDF ≤300 págs, ≤100 MB — P); Instagram carrusel 4:5 1080×1350 (S) | Una idea por tarjeta | Sí: HTML → PDF con Playwright (`page.pdf`) o PNG por tarjeta |
| GIF | X, Bluesky (vía vídeo), Mastodon, Reddit | NV: tamaños | Sí: grabación de Playwright (vídeo) → ffmpeg `palettegen/paletteuse` |
| Vídeo corto vertical | TikTok, Reels, Shorts (Shorts: vertical/cuadrado ≤3 min — P) | 9:16, 1080×1920, H.264/AAC (S) | Sí: ffmpeg + grabación de Playwright; subtítulos quemados con `subtitles` |
| Clip con subtítulos | todas | La mayoría ve sin sonido (NV) | Sí: ffmpeg + `.srt` |
| Encuestas | X, LinkedIn, Instagram stories, Discord, Mastodon, Bluesky (NV) | Texto corto | Solo el texto |
| Antes/después | Instagram, X, TikTok | Mismo encuadre | Sí: dos capturas lado a lado (HTML→PNG) o `git stash`/dos commits |
| Tarjeta de cita | LinkedIn, X, Instagram | 1:1 o 1,91:1 | Sí: HTML→PNG |
| Infografía | LinkedIn, blog | Vertical largo | Sí: HTML/SVG→PNG |
| Fragmento de código bonito (estilo carbon.sh) | X, LinkedIn, Bluesky, Mastodon | Imagen con alt text con el código | Sí: HTML+resaltador (Shiki/Prism)→PNG |
| Tarjeta de métricas / gráfico | todas | Alt text con las cifras | Sí: datos→SVG/PNG (matplotlib, Vega, HTML) |
| Mapa, concept art | Instagram, Mastodon, Discord, Reddit | Imagen original | Mapa: posiblemente del propio juego; arte: lo aporta el usuario |
| Memes | X, Reddit | Riesgo de marca | No automatizar |
| Hilo | X, Bluesky (300 car.), Mastodon | Primer post autosuficiente | Sí, texto |
| Timelapse | TikTok, Shorts, X | NV | Sí: commits como fotogramas (`git log` + capturas) + ffmpeg |
| Live / audio / podcast | Twitch, YouTube, Discord | NV | No |
| Open Graph | web, enlaces en todas | 1200×630, <1 MB (S) | Sí: HTML→PNG |
| Mockup de dispositivo | Instagram, LinkedIn, web | Marco + captura | Sí: HTML/CSS → PNG |
| Comparativa / tabla | LinkedIn, blog, Reddit | Tabla en imagen con alt text | Sí: HTML→PNG o Markdown |

**Ruta técnica propuesta (comprobable por script):** una plantilla HTML por tipo → Playwright `screenshot` a tamaño de la red → ffmpeg para vídeo/GIF. El script valida dimensiones, peso y alt text; la skill solo decide el contenido.

---

## 4. Recomendaciones para la skill

### 4.1 Catálogo (tema × formato × red × datos del repo)

| Tipo de post | Formato | Redes | Datos del repo |
|---|---|---|---|
| Resumen de versión | Hilo o carrusel de 5-7 tarjetas | X, Bluesky, Mastodon, LinkedIn (PDF) | `CHANGELOG.md`, `plugin.json` (versión), `git log` desde la última etiqueta |
| Entrada de devlog | Texto largo + 1 imagen/GIF | Reddit, blog, LinkedIn | Bitácora (`docs/traspaso.md`), `git log`, ADR |
| Decisión de diseño | Texto + diagrama | LinkedIn, blog, X | ADR, `docs/plan.md` |
| Métricas del flujo con IA | Tarjeta de métricas/gráfico | LinkedIn, X, r/ClaudeAI | Informes de `/opt-tokens`, `/retro`, tokens por sesión |
| Fallos y lecciones | Texto personal + cita | LinkedIn, Reddit, X | `/retro`, propuestas de `docs/propuestas/`, commits `WIP:` |
| Estado de tests/calidad | Tarjeta (verde/rojo) | X, Mastodon | `tests/comprobar.sh`, CI |
| Hito | Tarjeta + texto breve | LinkedIn, X | Número de versión, cuenta de commits, fases cerradas |
| Antes/después | Dos imágenes | Instagram, X, TikTok | Capturas de dos commits |
| Roadmap | Tabla/infografía | Discord, blog, LinkedIn | `docs/plan.md`, issues |
| Pregunta a la comunidad | Texto + encuesta | X, Bluesky, Discord | Decisiones abiertas de la bitácora |
| Screenshot Saturday | 1 GIF/captura + hashtag | X, Bluesky, Mastodon, Reddit | Capturas nuevas de la semana |
| Clip de funcionamiento | Vídeo vertical con subtítulos | TikTok, Reels, Shorts | Grabación de Playwright |
| Lore / mundo | Imagen + texto | Instagram, Mastodon, Discord | Datos del juego (WMF) |
| Código bonito | Imagen + alt text | X, LinkedIn | Diff o fragmento de un commit |
| Tutorial corto | Vídeo o hilo | Shorts, blog | Documentación `docs/es/` |

### 4.2 Reglas de la skill

1. **Solo prepara**: entrega borradores por red, nunca publica; el usuario confirma.
2. **Una pieza canónica y adaptaciones** por red (longitud, hashtags, formato), con la fuente y fecha del dato de red en un archivo de reglas versionado, para poder actualizarlo.
3. **Alt text obligatorio** en toda imagen; hashtags en CamelCase.
4. **Enlace en el cuerpo con contexto** (X, 2026) salvo que el usuario prefiera comentario; en Reddit, valor primero y regla del subreddit leída.
5. **Los datos salen del repo**; las cifras se calculan con script, no las inventa el agente («lo comprobable lo hace un script»).
6. **No prometer horarios**: ofrecer una franja y registrar resultados.
7. **Verificar de nuevo** los puntos NV antes de fijarlos (reglas de Reddit, TikTok oficial, X en GitHub, Instagram oficial, límites de LinkedIn vídeo).
8. **Seguridad:** no incluir secretos, rutas privadas ni datos de otros repos; de otros proyectos solo se lee.

### 4.3 Pendiente de investigar

- Reglas actuales de r/gamedev, r/IndieDev, r/indiegaming, r/programming y r/ClaudeAI (leer a mano; Reddit bloquea la lectura automática).
- Documentación oficial de Mastodon y Threads; ayuda oficial de Instagram (carrusel, Reels); límites de X.
- Blog de Steamworks sobre marketing y postmortems del GDC con cifras.
- Estudios completos de Sprout y Buffer (fechas exactas).

---

## Fuentes (consultadas el 2026-10-25)

Primarias:
- https://github.com/twitter/the-algorithm-ml/blob/main/projects/home/recap/README.md (pesos del heavy ranker, abril 2023)
- https://www.linkedin.com/help/linkedin/answer/97459 (documentos en LinkedIn)
- https://support.google.com/youtube/answer/15424877 (Shorts de tres minutos)
- https://support.discord.com/hc/en-us/articles/360028384531 (canales de anuncios)
- https://docs.bsky.app/docs/starter-templates/custom-feeds y https://atproto.com/guides/feeds
- https://newsroom.tiktok.com/en-us/how-tiktok-recommends-videos-for-you/ (leído por extractos)
- https://arxiv.org/html/2510.14223v1 (LinkedIn, recuperación del feed)
- https://partner.steamgames.com/doc/marketing/upcoming_events/nextfest/tips

Secundarias:
- https://www.socialmediatoday.com/news/instagram-shares-algorithm-insights-2025/738034/ (Mosseri, enero 2025)
- https://www.socialsamosa.com/news-2/instagram-reveals-key-factors-for-boosting-reach-8646916
- https://ppc.land/x-drops-year-old-link-penalty-musk-tells-zuckerberg-on-platform/ (julio 2026)
- https://roboin.io/article/en/2026/04/13/x-denies-link-deboost-recommends-in-post-links/ (abril 2026)
- https://www.socialmediatoday.com/news/best-times-to-post-2025-sprout-social/744014/ y https://sproutsocial.com/insights/best-times-to-post-on-social-media/ (Sprout, 2025)
- https://ppc.land/linkedin-rebuilds-its-feed-from-scratch-with-llms-and-gpu-powered-ranking/ (marzo 2026)
- https://presskit.gg/field-guides/reddit-marketing-indie-games
- https://gameworldobserver.com/2025/03/11/steam-page-launch-guide-wishlists-zukowski y https://wnhub.io/news/stores-and-publishing/item-47311
- https://recurpost.com/bluesky-scheduler/bluesky-post-size/ y https://www.ayrshare.com/docs/apis/post/social-networks/bluesky.md
- https://stackinfluence.com/blog/tiktok-video-sizes-the-ultimate-guide
- https://blog.hootsuite.com/instagram-reel-size-length/ y https://argil.ai/blog/instagram-reel-size-e350f
- https://fedi.tips/what-are-hashtags-how-do-i-use-them-on-mastodon-and-the-fediverse/
- https://dev.to/grabbit/open-graph-image-sizes-and-dimensions-the-complete-2026-guide-1k16
- https://docs.zernio.com/platforms/linkedin

No abiertas (403 o bloqueo): support.reddithelp.com (reddiquette), reddit.com/r/gamedev/wiki/rules, blog.x.com (ingeniería, algoritmo 2023), tiktok.com (página directa).
