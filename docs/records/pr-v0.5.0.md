**Título:** `Versión 0.5.0 «Base»: recogida H15, evolutivos de la 0.5 y arreglos de la 0.4`

## Summary

`ccr-d1e2d496-0vzck8` (hace de `version/0.5.0`) → `main` (`0e04504`, `v0.4.3`). Son 206 commits; `main` ya está
fusionada en la rama. La entrada completa está en el `CHANGELOG.md` (`[0.5.0] - 2026-11-04`).

```diff
 main (v0.4.3)
+  oleadas 1-3 de la 0.5        A8 (nombres en inglés), D11-D31, E6, E17, D19 ciPython, D21 agent-signatures.py
+  recogida H15                 7 proyectos, 44 propuestas, 13 aprobadas
+    arreglos                   D32-D39, E18 (no hay 0.4.4: salen aquí)
+    evolutivos                 B14, D40, B15, E19
+  /code-review vs origin/main  10 hallazgos arreglados (7caaae9..73b2a23)
```

Los arreglos de la revisión:

- **D36:** la marca de `reviewed.sh` pasa el `commit-msg` estricto.
- **D33:** `config-guard.py` vigila `pull`, `am`, `bisect`, `checkout-index`, `read-tree -u`, `stash branch` y los
  `find` que escriben desde la raíz.
- **D34:** un `WIP:` solo pasa si `gw.json` falta o no es JSON.
- **E19:** `tests-after-main.py` solo avisa de un archivo descubierto que no se analiza, y reconoce más bases
  `*TestCase`.
- **B15:** `subagent-cap.py` no sigue a la definición de usuario si la del proyecto existe.
- **D38:** la marca del `pre-push` se llama `gw-push-in-progress`.

## Evidence

- **Antes:** con el `commit-msg` estricto instalado, `reviewed.sh` fallaba con «no Refs trailer» (test
  `MarkUnderStrictCommitMsg`). `git pull` y `find . -name 'settings*' -delete` pasaban sin preguntar en
  `config-guard.py`.
  **Después:** esos casos, y uno por cada hallazgo, están en verde. `bash tests/check.sh` en verde sobre `cdb37d1` (y sobre la fusión con `main`, que ya está dentro)
  (1393 + 317 + 27 + 11 + 23 tests). `version.py --release` OK.
- **CI:** `<pendiente: python3 scripts/ci-status.py tras la subida>`.

## Merge Danger

**Door:** two-way. `main` es lo que instalan los proyectos, pero volver a `v0.4.3` es reinstalar esa etiqueta
(`/gw-update`).

**Blast Radius:** amplio. Los proyectos que actualicen reciben ganchos más estrictos:

- `config-guard.py` pregunta en más órdenes;
- `commit-msg` falla cerrado con el config roto;
- hay un `PreToolUse` nuevo, `agent-signatures.py`;
- se renombran a inglés archivos y claves (A8), con avisos de `doctor.py` y migración en `/gw-update`;
- las claves viejas de `web.md` se mantienen durante la `0.x`.
