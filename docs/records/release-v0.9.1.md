# Release de GitHub `v0.9.1` (textos)

- **Etiqueta:** `v0.9.1`, sobre `664c0dd`, el commit de `main` de la subida del 2026-11-26.
- **Título:** el bloque de abajo.
- **Cuerpo:** el segundo bloque. La entrada completa está en el CHANGELOG.
- **Publicada:** 2026-11-26 desde una sesión local, con estos textos y la etiqueta sobre `664c0dd`.

```text
Galivelop-workflow v0.9.1
```

````markdown
## Galivelop-workflow v0.9.1 — 2026-11-26

**ES** · [English below](#en)

Parche de la recogida H28.

### Cambios

- Clon del flujo (B48): `workflowClone` se busca también en la disposición de la nube (`../<owner>/<repo>`,
  `/home/user/<owner>/<repo>`, sin distinguir mayúsculas), con un ayudante común en `config.py`; acepta URL SSH y
  salta carpetas de otro dueño, y `doctor.py` dice qué carpetas probó.
- Lecturas de otro repo (B49): `other-repo-read.py` no avisa al correr `apply.py` del clon del flujo.
- CI (B50): `check.yml` y su plantilla ponen en `PATH` solo el binario de actionlint, no su venv.
- `gw-update` (B51): se para si la rama va por detrás de la protegida, avisa del choque con el ledger y comprueba
  que una clave existe antes de recomendarla.
- Ids (B52): `handoff.py next-id` lee ids en cualquier celda de una fila (`| 1 | **B3** |`), nunca tras un guion
  del texto; `doctor.py` avisa (`plan ids`) si ninguna entrada casa con `taskId` o `$GW_TASK_ID`.
- Rojo sin arreglo (B53): `red-without-fix.sh` decide por ruta (clave `redWithoutFix.testPathRegex`, relativa al
  repo) y con marcas ancladas al inicio de línea (también con tabulador), no por el contenido del archivo.
- Revisión (B54): `review-scope.py` avisa de un árbol sin confirmar (también archivos sin seguimiento) y admite
  `--worktree`.
- Ganchos (B55, B57): el `pre-push` dice la ruta del registro y que hay un bloqueo al empezar su check; el gancho
  `Stop` avisa, una vez por commit, cuando el último commit subido tiene el CI sin resolver.
- Reglas (B56): `REVIEW.md` sin guardas temporales en tests y con tiempo límite que mata el grupo de procesos; el
  reparto contrasta el valor esperado con el código.
- Arreglos de la revisión (D179): 17 hallazgos de la fase 1 sobre lo anterior, cada uno con su test.
- De la retro (B58-B61): la caché del check ignora las rutas de `checkCacheIgnore` (por defecto, el ledger de
  métricas), así que un ledger escrito durante el check no obliga a repetirlo en el `pre-push`; `tests/check.sh` se
  para en segundos en un clon superficial y nombra `git fetch --unshallow`; el encargo de `gw-orchestrate-dealer` dice
  cómo crear la entrada del registro de decisiones (`task.py log`); `review-scope.py --worktree` en los `config.md`.

---

<a id="en"></a>

**EN**

Patch from the H28 harvest.

### Changes

- Workflow clone (B48): `workflowClone` is also looked up in the cloud layout (`../<owner>/<repo>`,
  `/home/user/<owner>/<repo>`, case-insensitive), through a shared helper in `config.py`; it takes SSH URLs and
  skips folders owned by someone else, and `doctor.py` says which folders it tried.
- Reading another repo (B49): `other-repo-read.py` does not warn when running the workflow clone's `apply.py`.
- CI (B50): `check.yml` and its template put only the actionlint binary on `PATH`, not its venv.
- `gw-update` (B51): stops if the branch is behind the protected one, warns about the clash with the ledger and
  checks that a key exists before recommending it.
- Ids (B52): `handoff.py next-id` reads ids in any cell of a row (`| 1 | **B3** |`), never after a hyphen in the
  text; `doctor.py` warns (`plan ids`) if no entry matches `taskId` or `$GW_TASK_ID`.
- Red without the fix (B53): `red-without-fix.sh` decides by path (key `redWithoutFix.testPathRegex`, relative to the
  repo) and by markers anchored at the start of a line (tabs too), not by the file's content.
- Review (B54): `review-scope.py` warns about an uncommitted tree (untracked files too) and accepts `--worktree`.
- Hooks (B55, B57): `pre-push` says the log path and that its check holds a lock when it starts; the `Stop` hook
  warns, once per commit, when the last pushed commit has an unresolved CI.
- Rules (B56): `REVIEW.md` has no temporary guards in tests and a timeout kills the process group; dealing checks
  the expected value against the code.
- Review fixes (D179): 17 phase 1 findings on the above, each with its test.
- From the retro (B58-B61): the check cache ignores the paths in `checkCacheIgnore` (by default, the metrics ledger),
  so a ledger written during the check no longer forces `pre-push` to run it again; `tests/check.sh` stops in seconds
  in a shallow clone and names `git fetch --unshallow`; the `gw-orchestrate-dealer` brief says how to create the
  decision log entry (`task.py log`); `review-scope.py --worktree` in the `config.md` files.
````
