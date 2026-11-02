# Roadmap

> Version map of Galivelop-workflow ([español](roadmap.md)). It comes from the design closed on 2026-11-01
> ([`diseno/H-roadmap.md`](diseno/H-roadmap.md), "new map"), which holds the detail and the user's answers.
> The versioning rule is in plan §7: only the latest published minor receives patches and new features go to the
> next minor; **everything that breaks goes in `0.5`**.

## Identifiers

Each task carries the letter of its design block and a number (`B3`, `D12`): that of its numbered question in
`docs/diseno/` (`B3` = `B-3`, question 3 of block B), never that of a section (`## A2.`, `B1` in parentheses).
A new task takes the next free number in its block (in A, from `A7`) and **a number is never reused**. This file, in
Spanish, is the single source of ids (D13): `trace.py` and the `commit-msg` hook read them from here. The new features
that harvests bring wait in [`registros/pendiente.md`](registros/pendiente.md) with their version and get an id when
they enter the version. The English file (`roadmap.en.md`) only translates; it is not a source of ids.

| Block | Topic | Design |
|---|---|---|
| A | Framework: audience, names, versioning | [`A-marco.md`](diseno/A-marco.md) |
| B | Spend and model measurement | [`B-medicion.md`](diseno/B-medicion.md) |
| C | Questions and restrictive mode | [`C-preguntas.md`](diseno/C-preguntas.md) |
| D | Git: environments, releases, traceability, roles | [`D-git.md`](diseno/D-git.md) |
| E | Deterministic rules, front-end tests, documentation | [`E-calidad.md`](diseno/E-calidad.md) |
| G | Management Center (MMC) | [`G-mmc.md`](diseno/G-mmc.md) |
| H | Roadmap and version map | [`H-roadmap.md`](diseno/H-roadmap.md) |

## Map

| Version | Name | Branch | Status |
|---|---|---|---|
| `0.4.4` | Patch | `ccr-6dfbc880-ddr41g` | pending (another day, A6 cadence) |
| `0.5` | Base | `version/0.5.0` | **in progress** |
| `0.6` | Measure | — | — |
| `0.7` | Ask | — | — |
| `0.8` | Front end and other agents | — | — |
| `0.9` | Stable | — | — |
| `1.0` | MMC 1 (read-only) | — | — |
| `1.1` | MMC 2 (config) | — | — |
| `1.2` | MMC 3 (profiles, environments, roles) | — | — |

Checkboxes: `[ ]` pending, `[x]` done (with the date; `git log -S` gives the commit).

### `0.4.4` — patch

- [ ] **D6:** `worktree.baseRef: "head"` in the `settings.json` the workflow installs.
- [ ] **Retro 0.4.2 P5:** the `pre-commit` QUOTED rule, with no false positives in `.md` (a real secret stays
  blocked).

### `0.5` "Base" — everything that breaks

In this order, because each step uses the previous one:

1. **Plan and roadmap**
   - [x] **H14** (2026-11-02): new versioning rule in `AGENTS.md` and plan §7.
   - [x] **D13** (2026-11-02): this roadmap, with its English pair.
   - [x] **H12** (2026-11-02): `pendiente-1.0.0.md` becomes `pendiente.md`, with the version on each line.
   - [ ] **A7:** the plan rewritten according to the table in section A1 (§1, §2, §7, §9, §10).
2. **Names**
   - [ ] **A8:** `gw-` on our own skills (third-party ones keep their name, A3) and scripts in English (section A2).
   - [ ] **A4:** project paths in English (`docs/handoff.md`, `docs/records/`…), configurable in `gw.json`, also in
     Spanish-language projects. `gw-update` renames them and the hooks accept both names during `0.x`.
3. **Versioned config**
   - [ ] **A9:** `schemaVersion` in `gw.json` and its migration in `gw-update` (section A3, point 2).
4. **Traceability**
   - [ ] **D11:** Conventional Commits type on the first line (`fix(B1): …`) and `version.py` suggests the bump.
   - [ ] **D12:** mandatory `Refs: <id>` trailer in the `commit-msg` hook (except merges), validated against this
     file.
   - [ ] **D15:** optional `Agent: <skill>` trailer, no model.
   - [ ] **D16:** subagent branches `agent/<id>-<topic>` and `fusionar.sh` copies `Refs:` to the merge commit.
5. **Public repo**
   - [ ] **E2:** private-data check in the `pre-push` (emails, keys, private repos; list in
     `.claude/gw.local.json`).
   - [ ] **E3 / D3:** anonymised harvests (`private-project-1`) and a review of those already published.
6. **Deterministic rules**
   - [ ] **E1:** audit of `AGENTS.md` and `CLAUDE.md`, with a line-limit check.
   - [ ] **E6:** each `REVIEW.md` rule names its check or says "judgement".
7. **What was already waiting:** the items of [`registros/pendiente.md`](registros/pendiente.md) marked `0.5`.

### `0.6` "Measure"

- [ ] **B1, B2, B3:** `Stop` hook that reads the session logs and writes `docs/metrics/ledger.jsonl` (tokens by model
  and type, date, branch, `Refs`, subagent); prices in a dated table.
- [ ] **B4, B5, B6:** `metrics.py report --period …`, `compare` and the 1.5× alert in `SessionStart`; skill
  `gw-metrics`.
- [ ] **B7, B8, B10, B11:** `models.disabled` with its hook, quality signals, the `selector` recommends model and
  effort for the main session, model and effort per agent.

### `0.7` "Ask"

- [ ] **C1-C8, C10:** `docs/questions.md`, restrictive mode with its hook, `gw-mode`, `modes.careful` on by
  default; subagents return their questions.
- [ ] **D14:** `trace.py <id>`.

### `0.8` "Front end and other agents"

- [ ] **E4:** installation profiles (minimal/core/full, `core` by default).
- [ ] **E5, E7, E9-E16:** front-end tests: guide in `patrones.md`, config template and the checks that E9-E16
  decide.
- [ ] **D7, B9:** `AGENTS.md` readable without `@include`, skills also in `.agents/skills`; non-Anthropic models via
  opencode.

### `0.9` "Stable"

- [ ] **E8:** full documentation review, by subagents.
- [ ] **G2:** what the MMC needs from the scripts: JSON outputs with a minimum version.

### `1.0` "MMC 1"

- [ ] **G1, G3, G6, G7:** read-only: `mmc.py` on 127.0.0.1, `--static` for the cloud, data and git views.

### `1.1` "MMC 2"

- [ ] **G4:** config from the MMC through `config.py`, with the diff and no commit.

### `1.2` "MMC 3"

- [ ] **G5, G8, D9, D10, D17:** layered profiles, configurable and new environments with `rc` tags for `uat`,
  roles with a per-environment git-user check.

## Afterwards, no number

It comes out when what it needs exists, and then it gets a version:

- **B13:** deterministic model table and publication of the trend with an A/B test, over the B8 signals; needs
  four weeks of ledger.
- **G10:** multi-project MMC. **C9:** `modes.freeze`. **B12:** explorer pattern in `orchestrate-dealer`.
  **B1** (option): OpenTelemetry.
- **R3:** harvest of the private repos (`galivelop-image-generator`, `galivelop-voice-generator`), once there is read
  access.
