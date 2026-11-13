"""scripts/backport.sh (D81), end to end in a temporary project: commits of a minor's branch brought onto a patch branch.

Same conventions as test_utils.py (the temporary project comes from test_hooks.py; git runs isolated from this
machine's configuration).
"""
import shutil
import sys
import unittest

from test_hooks import ROOT, Project, Snapshot

sys.dont_write_bytecode = True
LOG = "docs/log.md"
ROADMAP = "docs/roadmap.md"
CONFIG = {"language": "es", "proposalsDir": "docs/proposals",
          "roadmapFiles": [{"path": ROADMAP, "done": "hecho", "open": ["pendiente"]}]}
HARVEST = "docs/proposals/harvest-1.md"


class Base(Snapshot):
    prefix = "gw-backport-"
    config = CONFIG
    log = LOG
    roadmap_text = "roadmap v1\n"

    def build(self):
        p = self.p = Project(self.tmp, self.config)
        shutil.copy2(ROOT / "scripts" / "backport.sh", p.work / ".claude" / "gw" / "scripts" / "backport.sh")
        p.write(self.log, "log v1\n")
        p.write(ROADMAP, self.roadmap_text)
        p.write("code.txt", "line 1\nline 2\nline 3\n")
        p.commit("base files")
        p.git("branch", "minor")
        p.git("checkout", "-q", "-b", "patch")

    def run_bp(self, *args):
        return self.p.run("bash", str(self.p.work / ".claude" / "gw" / "scripts" / "backport.sh"), *args)

    def on_minor(self, files, message):
        """A commit on `minor` (dict path -> text); back on `patch` afterwards. Returns its sha."""
        self.p.git("checkout", "-q", "minor")
        for path, text in files.items():
            self.p.write(path, text)
        self.p.commit(message)
        sha = self.p.sha()
        self.p.git("checkout", "-q", "patch")
        return sha

    def on_patch(self, files, message):
        for path, text in files.items():
            self.p.write(path, text)
        self.p.commit(message)
        return self.p.sha()

    def subjects(self, n=10):
        return self.p.git("log", f"-{n}", "--format=%s").stdout.splitlines()

    def head_is_clean(self):
        return self.p.git("status", "--porcelain", "--untracked-files=no").stdout == ""


class Refusals(Base):
    def test_no_shas(self):
        code, out = self.run_bp()
        self.assertEqual(code, 2, out)
        self.assertIn("no commits given; pass the shas to bring", out)

    def test_unknown_sha(self):
        code, out = self.run_bp("deadbeef00000000000000000000000000000000")
        self.assertEqual(code, 2, out)
        self.assertIn("unknown commit 'deadbeef00000000000000000000000000000000'; fetch it and retry: git fetch origin", out)

    def test_unknown_from_branch(self):
        sha = self.on_minor({"a.txt": "a\n"}, "fix(A1): a")
        code, out = self.run_bp("--from", "nope", sha)
        self.assertEqual(code, 2, out)
        self.assertIn("unknown branch 'nope'", out)

    def test_dirty_tree(self):
        sha = self.on_minor({"a.txt": "a\n"}, "fix(A1): a")
        self.p.write("code.txt", "changed\n")
        code, out = self.run_bp(sha)
        self.assertEqual(code, 2, out)
        self.assertIn("the working tree has uncommitted changes; commit them", out)
        self.assertNotIn("a.txt", self.p.git("ls-files").stdout)

    def test_detached_head(self):
        sha = self.on_minor({"a.txt": "a\n"}, "fix(A1): a")
        self.p.git("checkout", "-q", "--detach")
        code, out = self.run_bp(sha)
        self.assertEqual(code, 2, out)
        self.assertIn("HEAD is detached; check out the patch branch first: git checkout <patch-branch>", out)

    def test_cherry_pick_in_progress(self):
        s1 = self.on_minor({"code.txt": "line 1\nminor\nline 3\n"}, "fix(A1): minor")
        self.on_patch({"code.txt": "line 1\npatch\nline 3\n"}, "fix(A2): patch")
        self.assertNotEqual(self.p.git("cherry-pick", s1, ok=False).returncode, 0)
        code, out = self.run_bp(s1)
        self.assertEqual(code, 2, out)
        self.assertIn("a CHERRY_PICK_HEAD operation is already in progress; finish or cancel it first: "
                      "git cherry-pick --continue (or: git cherry-pick --abort)", out)

    def test_merge_in_progress(self):
        self.on_minor({"code.txt": "line 1\nminor\nline 3\n"}, "fix(A1): minor")
        self.on_patch({"code.txt": "line 1\npatch\nline 3\n"}, "fix(A2): patch")
        self.assertNotEqual(self.p.git("merge", "--no-commit", "minor", ok=False).returncode, 0)
        code, out = self.run_bp(self.p.sha("minor"))
        self.assertEqual(code, 2, out)
        self.assertIn("a MERGE_HEAD operation is already in progress", out)

    def test_rebase_in_progress(self):
        self.on_minor({"code.txt": "line 1\nminor\nline 3\n"}, "fix(A1): minor")
        self.on_patch({"code.txt": "line 1\npatch\nline 3\n"}, "fix(A2): patch")
        self.assertNotEqual(self.p.git("rebase", "minor", ok=False).returncode, 0)
        code, out = self.run_bp(self.p.sha("minor"))
        self.assertEqual(code, 2, out)
        self.assertIn("a rebase-merge operation is already in progress", out)
        self.assertIn("git rebase --continue (or: git rebase --abort)", out)


class Picks(Base):
    def test_out_of_order_shas_are_picked_oldest_first_with_x(self):
        s1 = self.on_minor({"a.txt": "a\n"}, "fix(A1): first")
        s2 = self.on_minor({"b.txt": "b\n"}, "fix(A2): second")
        s3 = self.on_minor({"c.txt": "c\n"}, "fix(A3): third")
        code, out = self.run_bp(s3, s1, s2)
        self.assertEqual(code, 0, out)
        self.assertEqual(self.subjects(3), ["fix(A3): third", "fix(A2): second", "fix(A1): first"])
        self.assertIn(f"(cherry picked from commit {s1})", self.p.git("log", "-3", "--format=%B").stdout)
        self.assertIn("summary for patch:", out)
        self.assertEqual(out.count("\n  picked: "), 3, out)

    def test_merge_commit_uses_first_parent(self):
        self.p.git("checkout", "-q", "minor")
        self.p.git("checkout", "-q", "-b", "side")
        self.p.write("side.txt", "side\n")
        self.p.commit("feat(A1): side")
        self.p.git("checkout", "-q", "minor")
        self.p.git("merge", "-q", "--no-ff", "-m", "merge side", "side")
        merge = self.p.sha()
        self.p.git("checkout", "-q", "patch")
        code, out = self.run_bp(merge)
        self.assertEqual(code, 0, out)
        self.assertEqual(self.subjects(1), ["merge side"])
        self.assertEqual(self.p.git("show", "--format=", "--name-only", "HEAD").stdout.split(), ["side.txt"])
        self.assertIn(f"(cherry picked from commit {merge})", self.p.git("log", "-1", "--format=%B").stdout)

    def test_sha_already_in_head(self):
        sha = self.on_minor({"a.txt": "a\n"}, "fix(A1): a")
        self.p.git("merge", "-q", "--ff-only", "minor")
        before = self.p.sha()
        code, out = self.run_bp(sha)
        self.assertEqual(code, 0, out)
        self.assertEqual(self.p.sha(), before)
        self.assertIn("already in HEAD:", out)

    def test_equivalent_patch_upstream_is_skipped_empty(self):
        sha = self.on_minor({"a.txt": "a\n"}, "fix(A1): a")
        self.on_patch({"a.txt": "a\n"}, "fix(A1): same change made on the patch")
        before = self.p.sha()
        code, out = self.run_bp(sha)
        self.assertEqual(code, 0, out)
        self.assertEqual(self.p.sha(), before)
        self.assertIn("skipped", out)
        self.assertIn("(empty", out)
        self.assertIn("skipped (empty):", out)
        self.assertTrue(self.head_is_clean())
        self.assertFalse((self.p.work / ".git" / "CHERRY_PICK_HEAD").exists())

    def test_log_only_conflict_takes_the_patch_version(self):
        s1 = self.on_minor({LOG: "log minor\n", "a.txt": "a\n"}, "fix(A1): a and log")
        self.on_patch({LOG: "log patch\n"}, "fix(A2): patch log")
        code, out = self.run_bp(s1)
        self.assertEqual(code, 0, out)
        self.assertIn(f"conflict in {LOG} resolved with this branch's version", out)
        self.assertEqual((self.p.work / LOG).read_text(), "log patch\n")
        self.assertEqual((self.p.work / "a.txt").read_text(), "a\n")
        self.assertEqual(self.subjects(1), ["fix(A1): a and log"])

    def test_log_and_roadmap_conflict_both_resolved(self):
        s1 = self.on_minor({LOG: "log minor\n", ROADMAP: "roadmap minor\n", "a.txt": "a\n"}, "fix(A1): all")
        self.on_patch({LOG: "log patch\n", ROADMAP: "roadmap patch\n"}, "fix(A2): patch")
        code, out = self.run_bp(s1)
        self.assertEqual(code, 0, out)
        self.assertIn(f"conflict in {ROADMAP} resolved with this branch's version", out)
        self.assertEqual((self.p.work / ROADMAP).read_text(), "roadmap patch\n")
        self.assertEqual((self.p.work / LOG).read_text(), "log patch\n")

    def test_roadmap_only_conflict_leaving_nothing_is_skipped(self):
        s1 = self.on_minor({ROADMAP: "roadmap minor\n"}, "docs(A1): roadmap")
        self.on_patch({ROADMAP: "roadmap patch\n"}, "docs(A2): patch roadmap")
        before = self.p.sha()
        code, out = self.run_bp(s1)
        self.assertEqual(code, 0, out)
        self.assertEqual(self.p.sha(), before)
        self.assertIn("skipped (empty):", out)

    def test_code_conflict_stops_and_names_the_remaining_shas(self):
        s1 = self.on_minor({"code.txt": "line 1\nminor\nline 3\n"}, "fix(A1): minor")
        s2 = self.on_minor({"b.txt": "b\n"}, "fix(A2): b")
        self.on_patch({"code.txt": "line 1\npatch\nline 3\n"}, "fix(A3): patch")
        code, out = self.run_bp(s1, s2)
        self.assertEqual(code, 1, out)
        self.assertIn("conflict in code.txt while picking", out)
        self.assertIn("git cherry-pick --continue", out)
        self.assertIn("git cherry-pick --abort", out)
        self.assertIn(f"rerun with the remaining commits: bash {self.p.work}/.claude/gw/scripts/backport.sh {s2}", out)
        self.assertTrue((self.p.work / ".git" / "CHERRY_PICK_HEAD").exists())
        self.assertFalse((self.p.work / "b.txt").exists())

    def test_code_conflict_alongside_a_log_conflict_still_stops(self):
        s1 = self.on_minor({"code.txt": "line 1\nminor\nline 3\n", LOG: "log minor\n"}, "fix(A1): minor")
        self.on_patch({"code.txt": "line 1\npatch\nline 3\n", LOG: "log patch\n"}, "fix(A2): patch")
        code, out = self.run_bp(s1)
        self.assertEqual(code, 1, out)
        self.assertIn("conflict in code.txt while picking", out)
        self.assertNotIn(LOG + " while", out)
        self.assertIn("no commits remain after this one, so no rerun is needed", out)

    def test_rerun_after_resolving_a_conflict_completes(self):
        s1 = self.on_minor({"code.txt": "line 1\nminor\nline 3\n"}, "fix(A1): minor")
        s2 = self.on_minor({"b.txt": "b\n"}, "fix(A2): b")
        self.on_patch({"code.txt": "line 1\npatch\nline 3\n"}, "fix(A3): patch")
        self.assertEqual(self.run_bp(s1, s2)[0], 1)
        self.p.write("code.txt", "line 1\nboth\nline 3\n")
        self.p.git("add", "code.txt")
        self.p.git("-c", "core.editor=true", "cherry-pick", "--continue")
        code, out = self.run_bp(s2)
        self.assertEqual(code, 0, out)
        self.assertIn("picked:", out)
        self.assertEqual(self.subjects(2), ["fix(A2): b", "fix(A1): minor"])


class FromHarvest(Base):
    def harvest_on_minor(self, text="# Harvest repo - 2026-11-13\n\nideas\n"):
        return self.on_minor({HARVEST: text, "docs/proposals/other.md": "# Not a harvest\n"}, "docs(A9): harvest")

    def test_harvest_files_missing_in_head_come_in_their_own_commit(self):
        s1 = self.on_minor({"a.txt": "a\n"}, "fix(A1): a\n\nRefs: A1, D7\nSiguiente: x")
        self.harvest_on_minor()
        code, out = self.run_bp("--from", "minor", s1)
        self.assertEqual(code, 0, out)
        self.assertEqual((self.p.work / HARVEST).read_text(), "# Harvest repo - 2026-11-13\n\nideas\n")
        self.assertFalse((self.p.work / "docs/proposals/other.md").exists())
        self.assertEqual(self.subjects(2), ["docs(A1): trae las recogidas de minor al parche", "fix(A1): a"])
        body = self.p.git("log", "-1", "--format=%B").stdout
        self.assertIn(f"- {HARVEST}", body)
        trailers = self.p.git("interpret-trailers", "--parse", stdin=body).stdout.splitlines()
        self.assertEqual(trailers, ["Refs: A1, D7", "Siguiente: seguir con el parche"])
        self.assertEqual(self.p.git("show", "--format=", "--name-only", "HEAD").stdout.split(), [HARVEST])

    def test_no_harvest_commit_when_head_already_has_the_file(self):
        s1 = self.on_minor({"a.txt": "a\n"}, "fix(A1): a")
        self.harvest_on_minor()
        self.on_patch({HARVEST: "# Harvest repo - patch copy\n"}, "docs(A2): harvest")
        code, out = self.run_bp("--from", "minor", s1)
        self.assertEqual(code, 0, out)
        self.assertIn("no harvest files in minor that HEAD lacks", out)
        self.assertEqual(self.subjects(1), ["fix(A1): a"])

    def test_no_harvest_commit_when_the_branch_has_none(self):
        s1 = self.on_minor({"a.txt": "a\n"}, "fix(A1): a")
        code, out = self.run_bp("--from", "minor", s1)
        self.assertEqual(code, 0, out)
        self.assertIn("no harvest files in minor that HEAD lacks", out)

    def test_without_from_the_harvest_is_not_brought(self):
        s1 = self.on_minor({"a.txt": "a\n"}, "fix(A1): a")
        self.harvest_on_minor()
        code, out = self.run_bp(s1)
        self.assertEqual(code, 0, out)
        self.assertFalse((self.p.work / HARVEST).exists())


class FromEdgeCases(Base):
    def test_from_with_no_shas_brings_only_the_harvest(self):
        self.on_minor({HARVEST: "# Harvest repo\n"}, "docs(A9): harvest")
        code, out = self.run_bp("--from", "minor")
        self.assertEqual(code, 0, out)
        self.assertEqual(self.subjects(1), ["docs: trae las recogidas de minor al parche"])
        self.assertEqual((self.p.work / HARVEST).read_text(), "# Harvest repo\n")

    def test_code_conflict_on_the_last_sha_with_from_says_how_to_get_the_harvest(self):
        s1 = self.on_minor({"code.txt": "line 1\nminor\nline 3\n"}, "fix(A1): minor")
        self.on_patch({"code.txt": "line 1\npatch\nline 3\n"}, "fix(A2): patch")
        code, out = self.run_bp("--from", "minor", s1)
        self.assertEqual(code, 1, out)
        self.assertIn("then bring the harvest files (no shas left): bash ", out)
        self.assertIn("backport.sh --from minor \n", out + "\n")
        self.assertNotIn("no rerun is needed", out)

    def test_no_shas_and_no_from_still_refused(self):
        code, out = self.run_bp("--refs", "A1")
        self.assertEqual(code, 2, out)
        self.assertIn("no commits given", out)


class SpacesAndAccents(Base):
    log = "docs/my log.md"
    config = dict(CONFIG, log="docs/my log.md")

    def test_log_with_a_space_conflicting_alone_is_resolved(self):
        s1 = self.on_minor({self.log: "log minor\n", "a.txt": "a\n"}, "fix(A1): a and log")
        self.on_patch({self.log: "log patch\n"}, "fix(A2): patch log")
        code, out = self.run_bp(s1)
        self.assertEqual(code, 0, out)
        self.assertIn("conflict in docs/my log.md resolved with this branch's version", out)
        self.assertEqual((self.p.work / self.log).read_text(), "log patch\n")

    def test_harvest_file_with_a_space_and_an_accent_is_brought(self):
        name = "docs/proposals/recogida \u00e9 1.md"
        self.on_minor({name: "# Harvest repo\n"}, "docs(A9): harvest")
        code, out = self.run_bp("--from", "minor")
        self.assertEqual(code, 0, out)
        self.assertEqual((self.p.work / name).read_text(), "# Harvest repo\n")
        self.assertIn(f"- {name}", self.p.git("log", "-1", "--format=%B").stdout)


class HarvestRefs(Base):
    config = dict(CONFIG, commitRefs=True, commitFormat="conventional", commitNext=True, refsSources=[ROADMAP],
                  taskId="[A-Z]\\d+")
    roadmap_text = "| A1 | first | hecho |\n"

    def minor_with(self, refs):
        sha = self.on_minor({"a.txt": "a\n"}, f"fix(A1): a\n\nRefs: {refs}\nSiguiente: x")
        self.on_minor({HARVEST: "# Harvest repo\n"}, "docs(A1): harvest\n\nRefs: A1\nSiguiente: x")
        return sha

    def refs_of_head(self):
        body = self.p.git("log", "-1", "--format=%B").stdout
        return self.p.git("interpret-trailers", "--parse", stdin=body).stdout.splitlines()[:1]

    def test_only_accepted_ids_stay_in_refs(self):
        sha = self.minor_with("A1, D2")
        code, out = self.run_bp("--from", "minor", sha)
        self.assertEqual(code, 0, out)
        self.assertEqual(self.refs_of_head(), ["Refs: A1"])

    def test_no_accepted_id_stops_before_touching_the_index(self):
        sha = self.minor_with("D2")
        code, out = self.run_bp("--from", "minor", sha)
        self.assertEqual(code, 1, out)
        self.assertIn("no task id for the harvest commit's Refs that this branch accepts", out)
        self.assertIn("--refs <id>", out)
        self.assertEqual(self.p.git("status", "--porcelain").stdout, "")
        self.assertFalse((self.p.work / HARVEST).exists())

    def test_refs_option_overrides(self):
        sha = self.minor_with("D2")
        code, out = self.run_bp("--from", "minor", "--refs", "A1", sha)
        self.assertEqual(code, 0, out)
        self.assertEqual(self.refs_of_head(), ["Refs: A1"])

    def test_refs_option_with_an_unaccepted_id_stops_too(self):
        sha = self.minor_with("A1")
        code, out = self.run_bp("--from", "minor", "--refs", "Z9", sha)
        self.assertEqual(code, 1, out)
        self.assertIn("tried: Z9", out)
        self.assertEqual(self.p.git("status", "--porcelain").stdout, "")

    def test_a_failed_commit_unstages_so_the_rerun_is_not_refused(self):
        sha = self.minor_with("A1")
        hook = self.p.work / ".githooks" / "commit-msg"
        hook.write_text("#!/bin/sh\necho boom >&2\nexit 1\n")
        hook.chmod(0o755)
        code, out = self.run_bp("--from", "minor", sha)
        self.assertEqual(code, 1, out)
        self.assertIn("the harvest commit failed (see above); its files were unstaged and removed again", out)
        self.assertIn("boom", out)
        self.assertEqual(self.p.git("status", "--porcelain").stdout.replace("?? .githooks/commit-msg\n", ""), "")
        hook.unlink()
        code, out = self.run_bp("--from", "minor", "--refs", "A1")
        self.assertEqual(code, 0, out)
        self.assertIn("harvest files brought in one commit", out)


if __name__ == "__main__":
    unittest.main()
