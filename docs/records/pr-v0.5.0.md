**Título:** `Versión 0.5.0 «Base»: recogida H15, evolutivos de la 0.5 y arreglos de la 0.4`

## Summary

`ccr-d1e2d496-0vzck8` (hace de `version/0.5.0`) → `main` (`0e04504`, `v0.4.3`). Son 211 commits y `main` ya está
fusionada en la rama. La entrada completa está en el `CHANGELOG.md` (`[0.5.0] - 2026-11-04`).

```diff
 main (v0.4.3)
+  oleadas 1-3 de la 0.5        A8 (nombres en inglés), D11-D31, E6, E17, D19 ciPython, D21 agent-signatures.py
+  recogida H15                 7 proyectos, 44 propuestas, 13 aprobadas
+    arreglos                   D32-D39, E18 (no hay 0.4.4: salen aquí)
+    evolutivos                 B14, D40, B15, E19
+  /code-review vs origin/main  10 hallazgos arreglados (7caaae9..73b2a23)
+  arreglo del CI (Python 3.12) handoff.py set-row sin Path.read_text(newline=) (8ea7436)
+  arreglo del CI (macOS)       test_ci_local con el sistema de la máquina, no ubuntu fijo
+  retro aprobada               R1, R5 a la 0.5.1; R2, R3, R4, R6 a la 0.6 (roadmap)
```

Arreglos de la revisión:

- **D36:** la marca de `reviewed.sh` pasa el `commit-msg` estricto.
- **D33:** `config-guard.py` vigila:
  - `pull`, `am`, `bisect`, `checkout-index` y `read-tree -u`;
  - `stash branch`;
  - los `find` que escriben desde la raíz.
- **D34:** un `WIP:` solo pasa si `gw.json` falta o no es JSON.
- **E19:** `tests-after-main.py` solo avisa de un archivo descubierto que no se analiza, y reconoce más bases
  `*TestCase`.
- **B15:** `subagent-cap.py` no sigue a la definición de usuario si la del proyecto existe.
- **D38:** la marca del `pre-push` se llama `gw-push-in-progress`.

## Evidence

- **Antes:** con el `commit-msg` estricto instalado, `reviewed.sh` fallaba con «no Refs trailer» (test
  `MarkUnderStrictCommitMsg`). `git pull` pasaba sin preguntar en `config-guard.py`.
  **Después:** esos casos, y uno por cada hallazgo, están en verde. `bash tests/check.sh` está en verde en local
  (1394 + 317 + 27 + 11 + 23 tests). `version.py --release` da OK.
- **CI:** en `cdb37d1` dio rojo en Ubuntu (Python 3.12): 8 tests de `handoff.py set-row` fallaban porque
  `Path.read_text(newline=)` es de 3.13.
  - El arreglo está en `8ea7436`, con el test estático `test_utils.OldestPython`, que falla sin el arreglo y pasa con
    él.
  - La suite completa está en verde con Python 3.12 (1394 tests).
  - En `8ea7436`, Ubuntu en verde; macOS en rojo: 3 tests de `test_ci_local` daban por hecho que la máquina es Linux
    (jobs con `runs-on: ubuntu-latest` fijo). Ahora usan el sistema de la máquina; reproducido y arreglado simulando
    macOS.

## Merge Danger

**Door:** two-way. `main` es lo que instalan los proyectos, pero volver a `v0.4.3` es reinstalar esa etiqueta
(`/gw-update`).

**Blast Radius:** amplio. Los proyectos que actualicen reciben ganchos más estrictos:

- `config-guard.py` pregunta en más órdenes;
- `commit-msg` falla cerrado con el config roto;
- hay un `PreToolUse` nuevo, `agent-signatures.py`;
- se renombran a inglés archivos y claves (A8), con avisos de `doctor.py` y migración en `/gw-update`;
- las claves viejas de `web.md` se mantienen durante la `0.x`.
