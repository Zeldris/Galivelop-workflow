### ES

- **Seguridad (E28):** `protectedBranch` tiene que ser un nombre de rama de git (`git check-ref-format --branch`) y
  `merge-main.py`, `reviewed.sh` y `review-before-main.sh` hacen el fetch con `--` y refspec explícito, para que git
  no lo lea como una opción (`--upload-pack=…`). `metrics.ledger` tiene que ser una ruta dentro del repo y el gancho
  `Stop` no escribe en un registro enlazado ni fuera del repo. **Al actualizar:** un `metrics.ledger` absoluto o con
  `..` ya no pasa `config.py validate` y los ganchos se paran con ese mensaje; mueve el archivo dentro del repo y pon
  su ruta en `.claude/gw.json`.

### EN

- **Security (E28):** `protectedBranch` must be a git branch name (`git check-ref-format --branch`), and
  `merge-main.py`, `reviewed.sh` and `review-before-main.sh` fetch with `--` and an explicit refspec, so git never
  reads it as an option (`--upload-pack=…`). `metrics.ledger` must be a path inside the repo, and the `Stop` hook does
  not write to a linked ledger or one outside the repo. **When updating:** an absolute `metrics.ledger` or one with
  `..` no longer passes `config.py validate` and the hooks stop with that message; move the file into the repo and
  set its path in `.claude/gw.json`.
