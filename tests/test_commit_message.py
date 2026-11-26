"""templates/githooks/commit-msg with scripts/commit-message.py: commitFormat, commitRefs, refsSources and the Agent
trailer (D11, D12, D15), end to end through `git commit` in a temporary project."""
import json
import unittest

from test_hooks import Base, ROOT

ROADMAP = "# Roadmap\n\n| id | task |\n|---|---|\n| D11 | format |\n| D12 | refs |\n\n- [ ] **D15** agent\n- ~~D16~~ done\n"


class Msg(Base):
    hooks = ("pre-push", "pre-commit", "commit-msg")
    config = {}

    def setUp(self):
        super().setUp()
        self.n = 0

    def configure(self, **keys):
        p = self.p
        cfg = json.loads((p.work / ".claude" / "gw.json").read_text())
        cfg.update(keys)
        p.write(".claude/gw.json", json.dumps(cfg))
        p.git("add", ".claude/gw.json")
        p.git("commit", "-q", "--no-verify", "-m", "config")

    def configure_docs(self, primary):
        """A12: a schema-2 config (the `languages` block; the old `language` key is gone)."""
        p = self.p
        cfg = json.loads((p.work / ".claude" / "gw.json").read_text())
        cfg.pop("language", None)
        cfg.update(schemaVersion=2, languages={"docs": {"primary": primary}})
        p.write(".claude/gw.json", json.dumps(cfg))
        p.git("add", ".claude/gw.json")
        p.git("commit", "-q", "--no-verify", "-m", "config")

    def roadmap(self, text=ROADMAP, stage=True):
        self.p.write("docs/roadmap.md", text)
        if stage:
            self.p.git("add", "docs/roadmap.md")

    def attempt(self, message):
        """Commit a small change with `message`; (returncode, stderr)."""
        self.n += 1
        self.p.write("docs/notes.md", f"n{self.n}\n")
        r = self.p.commit(message, ok=False)
        return r.returncode, r.stderr

    def accepted(self, message):
        code, err = self.attempt(message)
        self.assertEqual(code, 0, err)

    def refused(self, message, *reasons):
        before = self.p.sha()
        code, err = self.attempt(message)
        self.assertNotEqual(code, 0, err)
        self.assertEqual(self.p.sha(), before, "the refused commit was created")
        self.assertIn("commit-msg:", err)
        for reason in reasons:
            self.assertIn(reason, err)
        self.assertIn("git commit -e -F", err)


class Defaults(Msg):
    def test_free_and_no_refs_change_nothing(self):
        self.accepted("anything goes")
        self.accepted("Fase 1: old style\n\nbody\n\nRefs: NOPE-1\nAgent: claude-opus")  # signatures are allowed by default


class Conventional(Msg):
    def setUp(self):
        super().setUp()
        self.configure(commitFormat="conventional")

    def test_accepted_forms(self):
        for subject in ("feat: add x", "fix(D11): y", "feat(D11)!: breaking", "refactor(a-b c): z", "WIP: feat(D11): x",
                        "WIP: fix: x", "hotfix(D69): urgent", "fixup! feat: x", "squash! whatever", "amend! whatever", 'Revert "feat: x"',
                        "Merge branch 'x'", 'Reapply "feat: x"'):
            with self.subTest(subject=subject):
                self.accepted(subject + "\n\nbody")

    def test_the_review_mark_subject_is_exempt_only_when_exact(self):
        sha = "0123456789abcdef0123456789abcdef01234567"
        self.accepted(f"Reviewed: {sha}")
        self.accepted(f"Revisado: {sha}")
        self.accepted(f"Reviewed: {sha}{'89abcdef' * 3}")  # SHA-256 repository
        for subject in ("Reviewed: abc123", f"Reviewed: {sha} and more", f"reviewed: {sha}", f"WIP: Reviewed: {sha}"):
            with self.subTest(subject=subject):
                self.refused(subject, "not in the conventional form")

    def test_refused_forms(self):
        for subject in ("added x", "feature: x", "feat x", "feat:x", "feat(): x", "feat(a)(b): x", "Feat: x",
                        "WIP:feat: x", "wip: feat: x"):
            with self.subTest(subject=subject):
                self.refused(subject, "not in the conventional form", repr(subject))

    def test_only_the_first_line_counts_and_comments_are_ignored(self):
        self.accepted("feat: ok\n\nfree text: not checked")
        self.n += 1
        self.p.write("docs/notes.md", "c\n")
        self.p.git("add", "-A")
        r = self.p.git("commit", "-q", "-e", ok=False, env={"GIT_EDITOR": "sh -c 'printf \"# c\\nfix: after comment\\n\" > \"$1\"' _"})
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_a_merge_with_a_free_message_is_accepted(self):
        p = self.p
        p.git("checkout", "-q", "-b", "side")
        p.write("docs/side.md", "s\n")
        p.git("add", "-A")
        p.git("commit", "-q", "-m", "feat: side")
        p.git("checkout", "-q", "main")
        p.write("docs/main.md", "m\n")
        p.git("add", "-A")
        p.git("commit", "-q", "-m", "feat: main")
        r = p.git("merge", "--no-ff", "-m", "Merge side", "side", ok=False)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        r = p.git("merge", "--no-ff", "-m", "joined", "side", ok=False)  # already up to date: nothing is created

    def test_a_merge_with_a_conflict_concluded_by_hand_skips_the_format(self):
        p = self.p
        p.write("docs/c.md", "base\n")
        p.git("add", "-A")
        p.git("commit", "-q", "-m", "feat: base")
        p.git("checkout", "-q", "-b", "side")
        p.write("docs/c.md", "side\n")
        p.git("commit", "-q", "-a", "-m", "feat: side")
        p.git("checkout", "-q", "main")
        p.write("docs/c.md", "main\n")
        p.git("commit", "-q", "-a", "-m", "feat: main")
        self.assertNotEqual(p.git("merge", "side", ok=False).returncode, 0)
        p.write("docs/c.md", "both\n")
        p.git("add", "-A")
        r = p.git("commit", "-q", "-m", "resolved without a type", ok=False)
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_a_merge_with_a_message_in_progress_skips_the_format_even_if_not_merge_like(self):
        p = self.p
        p.git("checkout", "-q", "-b", "side")
        p.write("docs/side.md", "s\n")
        p.git("add", "-A")
        p.git("commit", "-q", "-m", "feat: side")
        p.git("checkout", "-q", "main")
        p.write("docs/main.md", "m\n")
        p.git("add", "-A")
        p.git("commit", "-q", "-m", "feat: main")
        r = p.git("merge", "--no-ff", "-m", "joined the two", "side", ok=False)  # whether or not MERGE_HEAD is there
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_revert_and_cherry_pick_in_progress_skip_the_format(self):
        p = self.p
        p.write("docs/r.md", "r\n")
        p.git("add", "-A")
        p.git("commit", "-q", "-m", "feat: r")
        target = p.sha()
        p.write("docs/r.md", "r2\n")
        p.git("commit", "-q", "-a", "-m", "feat: r2")
        r = p.git("revert", "--no-edit", target, ok=False)  # conflict: stays in progress
        self.assertNotEqual(r.returncode, 0)
        p.write("docs/r.md", "fixed\n")
        p.git("add", "-A")
        r = p.git("commit", "-q", "-m", "resolved the revert", ok=False)
        self.assertEqual(r.returncode, 0, r.stderr)
        p.git("checkout", "-q", "-b", "other", p.base)
        p.write("docs/r.md", "other\n")
        p.git("add", "-A")
        p.git("commit", "-q", "--no-verify", "-m", "feat: other")
        p.git("checkout", "-q", "main")
        p.write("docs/r.md", "main\n")
        p.git("commit", "-q", "-a", "-m", "feat: main r")
        r = p.git("cherry-pick", "other", ok=False)
        self.assertNotEqual(r.returncode, 0)
        p.write("docs/r.md", "picked\n")
        p.git("add", "-A")
        r = p.git("commit", "-q", "-m", "resolved the pick", ok=False)
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_a_rebase_skips_the_format(self):
        p = self.p
        p.git("checkout", "-q", "-b", "topic")
        p.write("docs/t.md", "t\n")
        p.git("add", "-A")
        p.git("commit", "-q", "--no-verify", "-m", "no type here")
        p.git("checkout", "-q", "main")
        p.write("docs/m.md", "m\n")
        p.git("add", "-A")
        p.git("commit", "-q", "-m", "feat: m")
        p.git("checkout", "-q", "topic")
        r = p.git("rebase", "main", "-x", "true", ok=False)  # reword-like replays go through commit-msg only for edits
        self.assertEqual(r.returncode, 0, r.stderr)
        r = p.git("rebase", "-i", "--root", "--exec", "true", ok=False, env={"GIT_SEQUENCE_EDITOR": "sed -i.bak s/^pick/reword/",
                                                                         "GIT_EDITOR": "true"})
        self.assertEqual(r.returncode, 0, r.stderr)


class Refs(Msg):
    def setUp(self):
        super().setUp()
        self.configure(commitRefs=True, plan=["docs/roadmap.md"], taskId="[A-Z]\\d+")
        self.roadmap()
        self.p.git("commit", "-q", "--no-verify", "-m", "roadmap")

    def test_missing_refs(self):
        self.refused("work", "no Refs trailer", "commitRefs: true")

    def test_the_review_mark_needs_no_refs(self):
        self.accepted("Revisado: 0123456789abcdef0123456789abcdef01234567")

    def test_valid_refs_in_every_entry_shape(self):
        for ids in ("D11", "D12", "D15", "D16", "D11, D12", "D11,D12 D15"):
            with self.subTest(ids=ids):
                self.accepted(f"work\n\nbody\n\nRefs: {ids}")

    def test_unknown_id(self):
        self.refused("work\n\nRefs: D99", "no entry opens: D99", "docs/roadmap.md")

    def test_an_id_in_a_later_cell_is_not_valid(self):  # D179: Refs reads only the first cell
        self.roadmap(ROADMAP + "| Siguiente paso | B99 crear ficha |\n| 2 | see D18-D31 |\n")
        self.p.git("commit", "-q", "--no-verify", "-m", "roadmap")
        self.refused("work\n\nRefs: B99", "no entry opens: B99")
        self.refused("work\n\nRefs: D31", "no entry opens: D31")

    def test_one_unknown_among_several(self):
        self.refused("work\n\nRefs: D11, D99, D98", "D99, D98")

    def test_id_with_the_wrong_shape(self):
        self.refused("work\n\nRefs: d11", "no entry opens: d11")
        self.refused("work\n\nRefs: D11x", "no entry opens: D11x")

    def test_two_refs_lines(self):
        self.accepted("work\n\nRefs: D11\nRefs: D12")
        self.refused("work\n\nRefs: D11\nRefs: D98", "D98")

    def test_refs_outside_the_last_paragraph_is_not_a_trailer(self):
        self.refused("work\n\nRefs: D11\n\nSiguiente: next", "no Refs trailer")

    def test_refs_in_the_middle_of_the_body_is_missing(self):
        self.refused("work\n\nthe body mentions\nRefs: D11 in a line\nof text", "no Refs trailer")

    def test_trailers_after_refs_are_fine(self):
        self.accepted("work\n\nbody\n\nRefs: D11\nSiguiente: next step")

    def test_findings_in_the_body_is_refused(self):
        self.refused("work\n\nFindings: 3\n\nmore body\n\nRefs: D11\nSiguiente: x", "`Findings:` line is outside",
                     "next to `Refs:`")

    def test_retries_in_the_body_is_refused(self):
        self.refused("work\n\nRetries: 1\n\nRefs: D11\nSiguiente: x", "`Retries:` line is outside")

    def test_both_in_the_last_paragraph_pass(self):
        self.accepted("work\n\nbody\n\nRefs: D11\nFindings: 3\nRetries: 1\nSiguiente: x")

    def test_a_mention_inside_a_sentence_passes(self):
        self.accepted("work\n\nthe Findings: 3 trailer and a Retries: 1 one are read\n\nRefs: D11\nSiguiente: x")

    def test_a_prose_line_that_starts_like_the_trailer_passes(self):
        # metrics.py sums only integer values: a line without one is not a lost trailer
        self.accepted("work\n\nFindings: the reviewer flagged two edge cases\nRetries: none needed\n\nRefs: D11\nSiguiente: x")

    def test_a_space_before_the_colon_is_still_that_trailer(self):
        self.refused("work\n\nFindings : 3\n\nRefs: D11\nSiguiente: x", "`Findings:` line is outside the trailer block")

    def test_the_configured_trailer_names_are_followed(self):
        self.configure(metrics={"quality": {"findingsTrailer": "Hallazgos"}})
        self.refused("work\n\nHallazgos: 3\n\nRefs: D11\nSiguiente: x", "`Hallazgos:` line is outside")
        self.accepted("work\n\nFindings: 3\n\nRefs: D11\nHallazgos: 3\nSiguiente: x")

    def warned(self, message):
        code, err = self.attempt(message)
        self.assertEqual(code, 0, err)
        return err

    def test_review_fixes_without_findings_warn_but_pass(self):  # E60
        err = self.warned("fix(D11): arreglos de la revisión\n\ndos casos\n\nRefs: D11\nSiguiente: x")
        self.assertIn("WARNING: the message speaks of review fixes (\"arreglos de la revisión\")", err)
        self.assertIn("add `Findings: <accepted findings>` next to `Refs:`", err)
        err = self.warned("fix(D11): the three REVIEW FIXES of the block\n\nRefs: D11\nSiguiente: x")
        self.assertIn("(\"review fixes\")", err)

    def test_review_fixes_with_findings_or_unrelated_words_do_not_warn(self):  # E60
        self.assertNotIn("review fixes", self.warned("fix(D11): review fixes\n\nRefs: D11\nFindings: 2\nSiguiente: x"))
        self.assertNotIn("review fixes", self.warned("feat(D11): findingsWords key\n\nRefs: D11\nSiguiente: x"))
        self.assertNotIn("review fixes", self.warned("feat(D11): plain work\n\nRefs: D11\nSiguiente: x"))

    def test_the_trailers_and_a_negation_do_not_warn(self):  # E60: only the subject and body speak of the fixes
        msg = "feat(D11): plain work\n\nbody\n\nRefs: D11\nSiguiente: /code-review del bloque y arreglar sus hallazgos"
        self.assertNotIn("review fixes", self.warned(msg))
        self.assertNotIn("WARNING", self.warned("feat(D11): x\n\nsin arreglos de la revisión\n\nRefs: D11\nSiguiente: x"))
        self.assertNotIn("WARNING", self.warned("feat(D11): x\n\nno review fixes this time\n\nRefs: D11\nSiguiente: x"))
        err = self.warned("fix(D11): x\n\nsin review fixes graves; hechos los review fixes leves\n\nRefs: D11\nSiguiente: x")
        self.assertIn("(\"review fixes\")", err)

    def test_the_loose_words_finding_and_hallazgo_do_not_warn_by_default(self):  # D155
        for word in ("hallazgo", "hallazgos", "finding", "findings"):
            msg = f"feat(D11): x\n\nEl análisis dio un {word} sobre el parser\n\nRefs: D11\nSiguiente: x"
            self.assertNotIn("WARNING", self.warned(msg), word)
        self.assertIn("WARNING", self.warned("fix(D11): review fixes\n\nsolo un hallazgo\n\nRefs: D11\nSiguiente: x"))
        self.assertNotIn("WARNING", self.warned("fix(D11): review fixes\n\nRefs: D11\nFindings: 1\nSiguiente: x"))

    FIXES = "fix(D11): arreglos de la revisión\n\ncierre\n\nRefs: D11\nSiguiente: x"

    def test_no_review_closed_yet_warns(self):  # B62: no commit of the branch carries Findings:
        self.accepted("feat(D11): plain\n\nRefs: D11\nSiguiente: x")
        self.assertIn("WARNING", self.warned(self.FIXES))

    def test_a_closed_review_right_before_does_not_warn_again(self):  # B62: it would count twice in metrics.py
        self.accepted("fix(D11): a\n\nRefs: D11\nFindings: 3\nSiguiente: x")
        self.accepted("fix(D11): b\n\nRefs: D11\nFindings: 2\nSiguiente: x")
        self.assertNotIn("WARNING", self.warned(self.FIXES))

    def test_a_commit_after_the_close_opens_the_block_and_warns(self):  # B62: the risk, a later real close
        self.accepted("fix(D11): a\n\nRefs: D11\nFindings: 3\nSiguiente: x")
        self.accepted("feat(D11): more work\n\nRefs: D11\nSiguiente: x")
        self.assertIn("WARNING", self.warned(self.FIXES))

    def test_merges_are_read_like_change_size(self):  # B62 with D141: a merge carries it or is skipped
        p = self.p
        for n, (side, merge) in enumerate((("", "Findings: 4\n"), ("Findings: 1\n", ""))):
            p.git("checkout", "-q", "-b", f"fix{n}")
            p.write("docs/side.md", f"{n}\n")
            p.git("add", "-A")
            p.git("commit", "-q", "--no-verify", "-m", f"fix(D11): side\n\nRefs: D11\n{side}Siguiente: x")
            p.git("checkout", "-q", "main")
            p.git("merge", "-q", "--no-ff", "--no-verify", "-m", f"Merge\n\nRefs: D11\n{merge}Siguiente: x", f"fix{n}")
            self.assertNotIn("WARNING", self.warned(self.FIXES), (side, merge))

    def test_a_close_already_on_the_protected_branch_does_not_count(self):  # B62: only the branch's commits
        self.accepted("fix(D11): a\n\nRefs: D11\nFindings: 3\nSiguiente: x")
        self.p.git("push", "-q", "--no-verify", "origin", "main")
        self.p.git("fetch", "-q", "origin")
        self.assertIn("WARNING", self.warned(self.FIXES))

    def test_without_the_protected_branch_the_warning_stays(self):  # B62: no block, as in change-size.py
        p = self.p
        p.git("checkout", "-q", "-b", "work")
        p.git("branch", "-q", "-D", "main")
        p.git("update-ref", "-d", "refs/remotes/origin/main")
        self.accepted("fix(D11): a\n\nRefs: D11\nFindings: 3\nSiguiente: x")
        self.assertIn("WARNING", self.warned(self.FIXES))

    def test_a_git_error_keeps_the_warning(self):  # B62: git log fails after printing a close, the warning stays
        import importlib.util
        import subprocess
        spec = importlib.util.spec_from_file_location("commit_message_b62", ROOT / "scripts" / "commit-message.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        def fake(root, *args):
            if args[0] == "log":
                return subprocess.CompletedProcess(args, 128, "\x02Findings: 3\n\0", "fatal: bad object")
            return subprocess.CompletedProcess(args, 0, "", "")
        mod.git = fake
        self.assertFalse(mod.review_just_closed(self.p.work, {}, "Findings"))
        cfg = mod.gwconfig.load(self.p.work)
        self.assertIn("WARNING", mod.findings_warning(cfg, "fix(D11): review fixes\n\nRefs: D11", [("Refs", "D11")],
                                                      self.p.work))

    def test_a_shallow_clone_reads_what_it_has(self):  # B62: the boundary ends the walk without an error
        p = self.p
        self.accepted("fix(D11): a\n\nRefs: D11\nFindings: 3\nSiguiente: x")
        closed = p.sha()
        self.accepted("feat(D11): more\n\nRefs: D11\nSiguiente: x")
        shallow = p.work / ".git" / "shallow"
        shallow.write_text(p.sha() + "\n")  # the close is beyond the boundary: the block looks open
        self.assertIn("WARNING", self.warned(self.FIXES))
        p.git("reset", "-q", "--hard", closed)
        shallow.write_text(closed + "\n")  # the boundary is the close itself
        self.assertNotIn("WARNING", self.warned(self.FIXES))

    def test_findings_words_follow_the_config_and_empty_turns_it_off(self):  # E60
        self.configure(metrics={"quality": {"findingsTrailer": "Hallazgos", "findingsWords": ["code review"]}})
        err = self.warned("fix(D11): the code\n  review pass\n\nRefs: D11\nSiguiente: x")
        self.assertIn("(\"code review\") and has no `Hallazgos:` trailer", err)
        self.assertNotIn("WARNING", self.warned("fix(D11): code review\n\nRefs: D11\nHallazgos: 1\nSiguiente: x"))
        self.configure(metrics={"quality": {"findingsWords": []}})
        self.assertNotIn("WARNING", self.warned("fix(D11): findings\n\nRefs: D11\nSiguiente: x"))

    def test_a_message_without_trailers_keeps_its_own_refusal(self):
        self.refused("work", "no Refs trailer")

    def test_an_id_added_in_the_same_commit_is_valid(self):
        self.refused("work\n\nRefs: D20", "D20")
        self.roadmap(ROADMAP + "- [ ] D20 new\n")
        self.accepted("work\n\nRefs: D20")

    def test_an_id_only_in_the_working_tree_is_invalid(self):
        self.roadmap(ROADMAP + "- [ ] D21 unstaged\n", stage=False)
        self.n += 1
        self.p.write("docs/notes.md", "x\n")
        self.p.git("add", "docs/notes.md")  # stage only the note
        r = self.p.git("commit", "-q", "-m", "work\n\nRefs: D21", ok=False)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("D21", r.stderr)

    def test_an_id_mentioned_but_not_opening_an_entry_is_invalid(self):
        self.roadmap(ROADMAP + "\nSee D30 for later.\n")
        self.refused("work\n\nRefs: D30", "D30")

    def test_empty_refs_sources_means_plan_plus_log(self):
        self.p.write("docs/log.md", "# Log\n\n- [ ] D40 from the log\n")
        self.p.git("add", "-A")
        self.p.git("commit", "-q", "--no-verify", "-m", "log")
        self.accepted("work\n\nRefs: D40")

    def test_refs_sources_replaces_plan_and_log(self):
        self.p.write("docs/other/a.md", "- D50 in a folder\n")
        self.p.write("docs/other/b.txt", "- D51 not markdown\n")
        self.p.git("add", "-A")
        self.p.git("commit", "-q", "--no-verify", "-m", "other")
        self.configure(refsSources=["docs/other"])
        self.accepted("work\n\nRefs: D50")
        self.refused("work\n\nRefs: D11", "D11")  # the plan is no longer a source
        self.refused("work\n\nRefs: D51", "D51")  # only .md files of a folder

    def test_a_file_in_refs_sources(self):
        self.configure(refsSources=["docs/roadmap.md"])
        self.accepted("work\n\nRefs: D12")

    def test_no_source_tracked_says_so(self):
        self.configure(refsSources=["docs/nowhere"])
        self.refused("work\n\nRefs: D11", "nothing tracked in docs/nowhere")

    def test_default_task_id_shape(self):
        self.configure(taskId=None)
        cfg = json.loads((self.p.work / ".claude" / "gw.json").read_text())
        cfg.pop("taskId")
        self.p.write(".claude/gw.json", json.dumps(cfg))
        self.roadmap(ROADMAP + "- [ ] AB-7 default shape\n")
        self.accepted("work\n\nRefs: AB-7")

    def test_gw_task_id_overrides_the_config_like_handoff(self):
        self.roadmap(ROADMAP + "- [ ] ZZ.1 other shape\n")
        self.p.write("docs/notes.md", "e\n")
        r = self.p.commit("work\n\nRefs: ZZ.1", ok=False, env={"GW_TASK_ID": "ZZ\\.\\d"})
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_a_divider_line_in_the_body_keeps_the_refs_trailer(self):
        self.accepted("work\n\nbody\n---\nmore\n\nRefs: D11")

    def test_a_merge_skips_refs(self):
        p = self.p
        p.git("checkout", "-q", "-b", "side")
        p.write("docs/side.md", "s\n")
        p.git("add", "-A")
        p.git("commit", "-q", "-m", "side\n\nRefs: D11")
        p.git("checkout", "-q", "main")
        p.write("docs/main.md", "m\n")
        p.git("add", "-A")
        p.git("commit", "-q", "-m", "main\n\nRefs: D12")
        r = p.git("merge", "--no-ff", "-m", "Merge side", "side", ok=False)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_a_rebase_skips_refs(self):
        p = self.p
        p.git("checkout", "-q", "-b", "topic")
        p.write("docs/t.md", "t\n")
        p.git("add", "-A")
        p.git("commit", "-q", "--no-verify", "-m", "no refs")
        r = p.git("rebase", "-i", "--root", env={"GIT_SEQUENCE_EDITOR": "sed -i.bak s/^pick/reword/", "GIT_EDITOR": "true"},
                  ok=False)
        self.assertEqual(r.returncode, 0, r.stderr)


class AgentTrailer(Msg):
    def test_a_skill_name_is_accepted_whatever_the_setting(self):
        for signatures in (True, False):
            self.configure(agentSignatures=signatures)
            self.accepted("work\n\nAgent: gw-orchestrate-dealer")

    def test_a_model_name_is_refused_only_with_signatures_false(self):
        values = ("claude-opus", "GPT-5", "o3", "Gemini 2", "anthropic", "gpt4o", "o3-mini", "sonnet", "ChatGPT", "4o",
                  "haiku-writer", "chatgpt-helper")
        self.configure(agentSignatures=True)
        for value in values:
            with self.subTest(value=value, signatures=True):
                self.accepted(f"work\n\nAgent: {value}")
        self.configure(agentSignatures=False)
        for value in values:
            with self.subTest(value=value, signatures=False):
                self.refused(f"work\n\nAgent: {value}", "Agent trailer names a model", f"Agent: {value}",
                             "agentSignatures: false")

    def test_names_that_only_look_like_models_pass(self):
        self.configure(agentSignatures=False)
        for value in ("gw-orchestrate-dealer", "orchestrate-dealer", "ops", "reviewer", "o-ring", "optimizer", "Claudette",
                      "gptools", "fabled", "opusx"):
            with self.subTest(value=value):
                self.accepted(f"work\n\nAgent: {value}")

    def test_an_agent_line_outside_the_trailer_block_is_not_checked(self):
        self.configure(agentSignatures=False)
        self.accepted("work\n\nAgent: claude-opus in a sentence, then\nmore text of the body")

    def test_a_divider_line_in_the_body_is_not_a_patch_start(self):
        self.configure(agentSignatures=False, commitRefs=True, plan=["docs/roadmap.md"], taskId="[A-Z]\\d+")
        self.roadmap()
        self.accepted("work\n\nbody\n---\nmore\n\nRefs: D11\nAgent: gw-orchestrate-dealer")
        self.refused("work\n\nbody\n---\nmore\n\nRefs: D11\nAgent: claude", "Agent trailer names a model")

    def test_a_merge_checks_the_agent_trailer(self):
        self.configure(agentSignatures=False)
        p = self.p
        p.git("checkout", "-q", "-b", "side")
        p.write("docs/side.md", "s\n")
        p.git("add", "-A")
        p.git("commit", "-q", "-m", "side")
        p.git("checkout", "-q", "main")
        p.write("docs/main.md", "m\n")
        p.git("add", "-A")
        p.git("commit", "-q", "-m", "main")
        r = p.git("merge", "--no-ff", "-m", "Merge side\n\nAgent: GPT-5", "side", ok=False)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("Agent trailer names a model", r.stderr)

    def test_a_rebase_skips_the_agent_trailer(self):
        self.configure(agentSignatures=False)
        p = self.p
        p.git("checkout", "-q", "-b", "topic")
        p.write("docs/t.md", "t\n")
        p.git("add", "-A")
        p.git("commit", "-q", "--no-verify", "-m", "old\n\nAgent: claude-opus")
        r = p.git("rebase", "-i", "--root", env={"GIT_SEQUENCE_EDITOR": "sed -i.bak s/^pick/reword/", "GIT_EDITOR": "true"},
                  ok=False)
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_comment_lines_and_scissors_are_ignored(self):
        self.configure(agentSignatures=False)
        p = self.p
        p.write("docs/notes.md", "c\n")
        p.write("docs/d.md", "Agent: claude-opus\n")
        p.git("add", "-A")
        script = self.tmp / "ed.sh"
        script.write_text("#!/bin/sh\nprintf '%s\\n' 'work' '' 'Agent: gw-orchestrate-dealer' '# Agent: claude-opus' | cat - \"$1\" > \"$1.n\" && mv \"$1.n\" \"$1\"\n")
        script.chmod(0o755)
        r = p.git("commit", "-q", "-v", ok=False, env={"GIT_EDITOR": str(script)})
        self.assertEqual(r.returncode, 0, r.stderr)


class NextTrailer(Msg):
    """commitNext (D31): the Siguiente:/Next: trailer, by language, with GW_NO_NEXT=1 as the escape."""

    def setUp(self):
        super().setUp()
        self.configure(commitNext=True)

    def test_off_by_default_and_without_the_key(self):
        self.configure(commitNext=False)
        self.accepted("no trailer at all")

    def test_present_in_english_is_next(self):
        self.accepted("work\n\nbody\n\nNext: do the rest")

    def test_missing_is_refused_with_the_escape_in_the_message(self):
        self.refused("work\n\nbody", "no `Next:` trailer", "GW_NO_NEXT=1")

    def test_the_word_follows_the_language(self):
        self.refused("work\n\nSiguiente: lo que sea", "no `Next:` trailer")
        self.configure(language="es")
        self.refused("work\n\nNext: do it", "no `Siguiente:` trailer")
        self.accepted("work\n\nSiguiente: lo que sea")

    def test_the_word_follows_languages_docs_primary_of_a_schema_2_config(self):
        self.configure_docs("es")
        self.refused("work\n\nNext: do it", "no `Siguiente:` trailer")
        self.accepted("work\n\nSiguiente: lo que sea")
        self.configure_docs("gl")  # no word of its own: English
        self.refused("work\n\nSiguiente: lo que sea", "no `Next:` trailer")
        self.accepted("work\n\nNext: do it")

    def test_an_empty_value_or_a_line_in_the_body_is_missing(self):
        self.refused("work\n\nNext:", "no `Next:` trailer")
        self.refused("work\nNext: in the body\nmore body\n\nRefs: D11", "no `Next:` trailer")

    def test_it_may_precede_other_trailers_such_as_attribution_lines(self):
        self.accepted("work\n\nNext: step\nCo-Authored-By: A Human <h@example.com>")

    def test_the_escape_skips_it_for_one_commit(self):
        self.p.write("docs/notes.md", "escape\n")
        r = self.p.commit("work without it", env={"GW_NO_NEXT": "1"}, ok=False)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.refused("work without it")  # the next commit is checked again

    def test_other_values_of_the_escape_do_not_skip_it(self):
        self.p.write("docs/notes.md", "escape\n")
        r = self.p.commit("work", env={"GW_NO_NEXT": "0"}, ok=False)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("no `Next:` trailer", r.stderr)

    def test_wip_still_needs_it(self):
        self.refused("WIP: work", "no `Next:` trailer")
        self.accepted("WIP: work\n\nNext: fix the red test")

    def test_git_written_lines_are_exempt(self):
        for subject in ("fixup! work", "squash! work", "amend! work", 'Revert "work"', 'Reapply "work"'):
            self.accepted(subject)

    def test_a_plain_commit_titled_merge_is_not_exempt(self):
        self.refused("Merge things by hand", "no `Next:` trailer")

    def test_the_error_does_not_demand_the_trailer_to_be_the_last_line(self):
        code, err = self.attempt("work")
        self.assertNotEqual(code, 0)
        self.assertNotIn("last line", err)
        self.assertIn("with a `Next: <next step>` line", err)

    def test_a_merge_in_progress_is_exempt(self):
        p = self.p
        p.git("checkout", "-q", "-b", "side")
        p.write("side.txt", "s\n")
        p.git("add", "-A")
        p.git("commit", "-q", "--no-verify", "-m", "side")
        p.git("checkout", "-q", "-")
        p.write("main.txt", "m\n")
        p.git("add", "-A")
        p.git("commit", "-q", "--no-verify", "-m", "main")
        r = p.git("merge", "--no-ff", "side", "-m", "merged without trailer", ok=False)
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_core_comment_char_auto_does_not_hide_or_invent_the_trailer(self):
        self.p.git("config", "core.commentChar", "auto")
        self.accepted("work\n\nNext: step\n\n# Please enter the commit message")
        self.refused("work\n\n# Next: only in a comment", "no `Next:` trailer")

    def test_it_works_with_the_other_checks(self):
        self.configure(commitFormat="conventional", commitRefs=True, plan=["docs/roadmap.md"], taskId="[A-Z]\\d+")
        self.roadmap()
        self.accepted("feat(D11): x\n\nRefs: D11\nNext: y")
        self.refused("feat(D11): x\n\nRefs: D11", "no `Next:` trailer")


class FailClosed(Msg):
    def test_an_unreadable_config_stops_the_commit(self):
        self.p.write(".claude/gw.json", "{ not json")
        before = self.p.sha()
        self.p.write("docs/notes.md", "z\n")
        self.p.git("add", "docs/notes.md")
        r = self.p.git("commit", "-q", "-m", "work", ok=False)
        self.assertNotEqual(r.returncode, 0)
        # D34: the pre-commit only warns with an unreadable config; the commit-msg is what stops a non-WIP commit.
        self.assertIn("commit-msg: cannot read or validate .claude/gw.json", r.stderr)
        self.assertEqual(self.p.sha(), before)

    def test_the_script_alone_fails_closed_on_a_bad_config(self):
        self.p.write(".claude/gw.json", json.dumps({"commitFormat": "loose"}))
        msg = self.p.work / "msg.txt"
        msg.write_text("work\n")
        code, out = self.p.run("python3", str(ROOT / "scripts" / "commit-message.py"), "--root", str(self.p.work), str(msg))
        self.assertEqual(code, 1, out)
        self.assertIn("commitFormat", out)
        self.assertIn("python3", out)

    def test_a_missing_script_stops_the_commit(self):
        (self.p.work / ".claude" / "gw" / "scripts" / "commit-message.py").unlink()
        self.p.write("docs/notes.md", "z\n")
        self.p.git("add", "docs/notes.md")
        r = self.p.git("commit", "-q", "-m", "work", ok=False)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("commit-message.py is missing", r.stderr)
        self.assertIn("/gw-update", r.stderr)


class A13Keys(Msg):
    """A13: commitTypes, commitWipPrefix, agentModelNames/Shapes and agentSignaturePatterns."""

    def invalid_config(self, message, *reasons):
        """The config breaks the schema: the hook refuses every commit, naming the key, and creates nothing."""
        before = self.p.sha()
        code, err = self.attempt(message)
        self.assertNotEqual(code, 0, err)
        self.assertEqual(self.p.sha(), before, "the refused commit was created")
        self.assertIn("commit-msg: cannot read or validate .claude/gw.json", err)
        for reason in reasons:
            self.assertIn(reason, err)

    def test_commit_types_default_set_and_bad(self):
        self.configure(commitFormat="conventional")
        self.accepted("hotfix: x\n\nbody")
        self.configure(commitTypes=["feat", "chore"])
        self.accepted("chore: x\n\nbody")
        self.refused("fix: x\n\nbody", "not in the conventional form", "one of feat, chore")
        self.configure(commitTypes=[])
        self.invalid_config("feat: x\n\nbody", "$.commitTypes: needs at least 1 item")

    def test_wip_prefix_default_set_empty_and_bad(self):
        self.configure(commitFormat="conventional")
        self.accepted("WIP: feat: x\n\nbody")
        self.configure(commitWipPrefix="RED: ")
        self.accepted("RED: feat: x\n\nbody")
        self.refused("WIP: feat: x\n\nbody", "not in the conventional form")
        self.configure(commitWipPrefix="")
        self.accepted("feat: x")
        self.refused("WIP: feat: x\n\nbody", "not in the conventional form")
        self.configure(commitWipPrefix=5)
        self.invalid_config("feat: x", "$.commitWipPrefix: expected string, got int")

    def test_agent_model_names_and_shapes_only_add(self):
        self.configure(agentSignatures=False)
        self.accepted("work\n\nAgent: grok-4")
        self.accepted("work\n\nAgent: my-model")
        self.configure(agentModelNames=["Grok", "my-model"], agentModelShapes=["ZED\\d+"])
        self.refused("work\n\nAgent: my-model", "Agent trailer names a model")
        self.refused("work\n\nAgent: the My_Model", "Agent trailer names a model")
        self.accepted("work\n\nAgent: my-models")
        self.refused("work\n\nAgent: grok-4", "Agent trailer names a model", "Agent: grok-4")
        self.refused("work\n\nAgent: zed9", "Agent trailer names a model")
        self.refused("work\n\nAgent: claude-opus", "Agent trailer names a model")  # a built-in stays
        self.accepted("work\n\nAgent: gw-orchestrate-dealer")
        self.configure(agentModelNames=["grok"])  # a list without a built-in name does not remove it
        self.refused("work\n\nAgent: sonnet", "Agent trailer names a model")
        self.refused("work\n\nAgent: gpt5", "Agent trailer names a model")
        self.configure(agentSignatures=True)  # without agentSignatures: false they do nothing
        self.accepted("work\n\nAgent: grok-4")

    def test_bad_agent_model_values_fail_closed_with_the_reason(self):
        self.configure(agentSignatures=False, agentModelShapes=["("])
        self.invalid_config("work\n\nAgent: skill", "$.agentModelShapes[0]: '(' is not a valid regex")
        self.configure(agentModelShapes=[], agentModelNames=[""])
        self.invalid_config("work\n\nAgent: skill", "$.agentModelNames[0]")

    def test_signature_patterns_only_add_and_fail_closed(self):
        self.configure(agentSignatures=False)
        self.accepted("work\n\nSent from my agent")
        self.configure(agentSignaturePatterns=["^sent from my agent"])
        self.refused("work\n\nSent from my agent", "agent signature", "Sent from my agent")
        self.refused("work\n\nClaude-Session: https://x", "agent signature")  # a built-in stays
        self.accepted("work\n\nNothing to see")
        self.configure(agentSignaturePatterns=["["])  # not a regex for Python: the schema check refuses
        self.invalid_config("work\n\nNothing", "$.agentSignaturePatterns[0]")
        for rx in (r"\d+", "(?i)x", "(?:x)sig", "[[:space:]]*made-by:", r"(a)\1", r"a\bb"):
            with self.subTest(rx=rx):  # Python re and grep -E read these differently: only the common subset is accepted
                self.configure(agentSignaturePatterns=[rx])
                self.invalid_config("work\n\nNothing", "$.agentSignaturePatterns[0]", "read differently")
        self.configure(agentSignatures=True, agentSignaturePatterns=["xsig"])  # with agentSignatures true they do nothing
        self.accepted("work\n\nxsig")


class ClearWarning(Msg):
    """D108: a commit that closes a phase or version, with the session's compaction budget passed, asks for /clear;
    only a warning."""
    WORDS = "/clear"

    def setUp(self):
        super().setUp()
        import os
        import shutil
        import sys
        sys.path.insert(0, str(ROOT / "scripts"))
        import session_log
        p = self.p
        for name in ("recover.py", "session_log.py", "roadmap.py", "context_guard.py"):
            shutil.copy2(ROOT / "scripts" / name, p.work / ".claude" / "gw" / "scripts" / name)
        home = p.tmp / "home"
        p.env["HOME"] = str(home)
        self.folder = home / ".claude" / "projects" / session_log.folder_of(os.path.realpath(str(p.work)))
        self.folder.mkdir(parents=True)
        self.configure(commitFormat="conventional", taskId="[A-Z]\\d+",
                       roadmapFiles=[{"path": "docs/roadmap.md", "done": "done", "open": ["pending"]}])
        self.log(1, "1")
        self.table("pending", "pending")
        self.p.git("add", "-A"); self.p.git("commit", "-q", "--no-verify", "-m", "roadmap")
        self.transcript(2)

    def log(self, budget, phase):
        line = f"Compaction budget: {budget}\n" if budget is not None else ""
        self.p.write("docs/log.md", f"# Log\n\n## Current state\n\n| Field | Value |\n|---|---|\n"
                                    f"| Phase in progress | **{phase}** |\n\n{line}")

    def table(self, d11, d12, d13="pending"):
        self.roadmap(f"# Roadmap\n\n## `0.6` «Measure»\n\n| id | task | status |\n|---|---|---|\n| D11 | a | {d11} |\n"
                     f"\n### More\n\n| D12 | b | {d12} |\n\n## `0.7`\n\n| D13 | c | {d13} |\n")

    def transcript(self, compactions):
        lines = ['{"type": "user", "message": {"content": "x"}}'] + ['{"type": "system", "subtype": "compact_boundary"}'] * compactions
        (self.folder / "s.jsonl").write_text("\n".join(lines) + "\n")

    def warned(self, message, expected):
        code, err = self.attempt(message)
        self.assertEqual(code, 0, err)
        (self.assertIn if expected else self.assertNotIn)(self.WORDS, err)
        return err

    def test_closing_a_version_with_the_budget_passed_warns_and_commits(self):
        self.table("done (2026-11-14)", "done")
        before = self.p.sha()
        err = self.warned("feat(D12): x", True)
        self.assertIn("closes the roadmap section `0.6`", err)
        self.assertIn("(2 > 1)", err)
        self.assertNotEqual(self.p.sha(), before)

    def test_changing_the_phase_warns(self):
        self.log(1, "2")
        self.assertIn("a phase", self.warned("docs(D11): x", True))

    def test_budget_not_passed_gives_no_warning(self):
        self.transcript(1)
        self.table("done", "done")
        self.warned("feat(D11): x", False)

    def test_closing_a_single_row_warns_with_the_budget_passed(self):  # D176
        self.table("done", "pending")  # D12 still open in `0.6`: no section closes
        err = self.warned("feat(D11): x", True)
        self.assertIn("closes the roadmap task D11", err)
        self.log(1, "1")  # the row is done at HEAD now; same phase, the log otherwise rewritten, no row changed
        self.p.write("docs/log.md", self.p.work.joinpath("docs/log.md").read_text() + "more\n")
        self.warned("feat(D11): x", False)

    def test_filler_rows_are_not_task_rows(self):  # D178: rows keyed by "—" overwrote each other
        head = "| id | task | status |\n|---|---|---|\n"
        self.roadmap(head + "| — | x | done |\n| — | y | pending |\n")
        self.p.git("add", "-A"); self.p.git("commit", "-q", "--no-verify", "-m", "filler")
        self.roadmap(head + "| — | y | pending |\n| — | x | done |\n")  # the last «—» row moves
        self.assertNotIn("closes the roadmap task", self.warned("feat(D11): x", False))

    def test_closing_a_single_row_gives_no_warning_when_clear_on_task_close_is_off(self):  # D176
        self.configure(clearOnTaskClose=False)
        self.table("done", "pending")
        self.warned("feat(D11): x", False)

    def test_closing_a_single_row_without_the_budget_passed_gives_no_warning(self):  # D176
        self.transcript(1)
        self.table("done", "pending")
        self.warned("feat(D11): x", False)

    def test_no_transcript_or_no_budget_line_gives_no_warning(self):
        (self.folder / "s.jsonl").unlink()
        self.table("done", "done")
        self.warned("feat(D11): x", False)
        self.transcript(5)
        self.log(None, "3")
        self.warned("feat(D11): x", False)

    def test_missing_pieces_give_no_warning(self):
        (self.p.work / ".claude" / "gw" / "scripts" / "recover.py").unlink()
        self.table("done", "done")
        self.warned("feat(D11): x", False)
        self.configure(roadmapFiles=[])
        self.p.write(".claude/gw/scripts/recover.py", (ROOT / "scripts" / "recover.py").read_text())
        self.table("pending", "pending", "done")
        self.warned("feat(D13): x", False)

    def test_a_wip_commit_gives_no_warning(self):
        self.table("done", "done")
        self.log(1, "2")
        self.warned("WIP: feat(D11): x", False)


if __name__ == "__main__":
    unittest.main()
