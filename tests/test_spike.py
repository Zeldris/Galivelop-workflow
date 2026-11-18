"""C12: exploration branches `spike/<topic>` (spikeBranch). commit-message.py asks no Refs nor task record there and
marks the commit with a `Spike:` trailer; the pre-push and merge-branch.sh refuse to bring a spike into a working
branch or the protected one, and say what to do instead. End to end in temporary projects."""
import json
import sys
import unittest

from test_commit_message import Msg
from test_hooks import ROOT
from test_utils import Base as UtilsBase

sys.path.insert(0, str(ROOT / "scripts"))
import config as gwconfig  # noqa: E402

TODO = "task.py new <id>"


class Prefix(unittest.TestCase):
    def test_prefix_with_and_without_slash(self):
        self.assertEqual(gwconfig.spike_prefix({}), "spike/")
        self.assertEqual(gwconfig.spike_prefix({"spikeBranch": "exp"}), "exp/")
        self.assertEqual(gwconfig.spike_prefix({"spikeBranch": "exp-"}), "exp-")
        self.assertEqual(gwconfig.spike_prefix({"spikeBranch": ""}), "")

    def test_branch_names(self):
        self.assertTrue(gwconfig.is_spike_branch("spike/x", "spike/"))
        self.assertTrue(gwconfig.is_spike_branch("refs/heads/spike/x", "spike/"))
        self.assertFalse(gwconfig.is_spike_branch("spike/", "spike/"))  # no topic
        self.assertFalse(gwconfig.is_spike_branch("spiked", gwconfig.spike_prefix({"spikeBranch": "spike"})))
        self.assertFalse(gwconfig.is_spike_branch("feature/spike/x", "spike/"))
        self.assertFalse(gwconfig.is_spike_branch("spike/x", ""))  # feature off
        self.assertFalse(gwconfig.is_spike_branch("", "spike/"))  # detached HEAD


class CommitMsg(Msg):
    def setUp(self):
        super().setUp()
        self.configure(commitFormat="conventional", commitRefs=True, commitNext=True)

    def code_attempt(self, message):
        self.n += 1
        self.p.write("src/app.py", f"x = {self.n}\n")
        r = self.p.commit(message, ok=False)
        return r.returncode, r.stderr

    def last_body(self):
        return self.p.git("log", "-1", "--format=%B").stdout

    def test_spike_commit_without_refs_is_accepted_and_marked(self):
        self.p.git("checkout", "-q", "-b", "spike/idea")
        self.accepted("feat(X1): probar una idea\n\nNext: decidir")
        self.assertIn("Spike: spike/idea", self.last_body())
        self.assertNotIn("Refs:", self.last_body())

    def test_same_commit_on_a_working_branch_is_refused(self):
        self.p.git("checkout", "-q", "-b", "feature")
        self.refused("feat(X1): probar una idea\n\nNext: decidir", "no Refs trailer")

    def test_spike_still_needs_format_and_next(self):
        self.p.git("checkout", "-q", "-b", "spike/idea")
        self.refused("probar una idea\n\nNext: decidir", "type(scope)")
        self.refused("feat(X1): probar una idea", "Next:")

    def test_an_existing_spike_trailer_is_not_repeated(self):
        self.p.git("checkout", "-q", "-b", "spike/idea")
        self.accepted("feat(X1): idea\n\nSpike: spike/idea\nNext: decidir")
        self.assertEqual(self.last_body().count("Spike:"), 1)

    def test_task_record_not_asked_on_a_spike(self):
        self.configure(commitRefs=False, taskRecord={"enabled": True})
        self.p.git("checkout", "-q", "-b", "feature")
        code, err = self.code_attempt("feat(X1): codigo\n\nNext: seguir")
        self.assertNotEqual(code, 0, err)
        self.assertIn("task record", err)
        self.p.git("checkout", "-q", "-b", "spike/code")
        code, err = self.code_attempt("feat(X1): codigo\n\nNext: seguir")
        self.assertEqual(code, 0, err)

    def test_feature_off_with_empty_prefix(self):
        self.configure(spikeBranch="")
        self.p.git("checkout", "-q", "-b", "spike/idea")
        self.refused("feat(X1): probar una idea\n\nNext: decidir", "no Refs trailer")

    def test_prefix_without_slash(self):
        self.configure(spikeBranch="exp")
        self.p.git("checkout", "-q", "-b", "expand")
        self.refused("feat(X1): idea\n\nNext: decidir", "no Refs trailer")
        self.p.git("checkout", "-q", "-b", "exp/a")
        self.accepted("feat(X1): idea\n\nNext: decidir")
        self.assertIn("Spike: exp/a", self.last_body())

    def test_detached_head_is_not_a_spike(self):
        self.p.git("checkout", "-q", "--detach")
        self.refused("feat(X1): idea\n\nNext: decidir", "no Refs trailer")


class Spike(UtilsBase):
    """The pre-push and merge-branch.sh (commits made with the trailer the commit-msg hook adds)."""

    def spike(self, name="spike/idea", trailer=True, n=1):
        p = self.p
        p.branch(name)
        for i in range(n):
            p.write(f"docs/{name.replace('/', '_')}{i}.md", f"{i}\n")
            p.commit(f"idea {i}" + (f"\n\nSpike: {name}" if trailer else ""))
        return p.sha()

    def set_config(self, **keys):
        p = self.p
        cfg = json.loads((p.work / ".claude" / "gw.json").read_text())
        cfg.update(keys)
        p.write(".claude/gw.json", json.dumps(cfg))
        p.commit("config")
        p.git("push", "-q", "--no-verify", "origin", "HEAD:main")
        p.base = p.sha()

    def push(self, ref):
        return self.p.push("origin", ref)

    def refused(self, code, out, why="Spike: trailer"):
        self.assertNotEqual(code, 0, out)
        self.assertIn("come from an exploration branch", out)
        self.assertIn(why, out)
        self.assertIn(TODO, out)

    def feature_with_merge(self, delete=False):
        self.spike()
        p = self.p
        p.branch("feature")
        p.git("merge", "-q", "--no-ff", "--no-edit", "spike/idea")
        if delete:
            p.git("branch", "-D", "spike/idea")

    def test_pushing_the_spike_branch_itself_is_allowed(self):
        self.spike()
        code, out = self.push("spike/idea")
        self.assertEqual(code, 0, out)
        self.assertNotIn("exploration branch", out)

    def test_merge_into_a_working_branch_refused(self):
        self.feature_with_merge()
        code, out = self.push("feature")
        self.refused(code, out)
        self.assertIn("into feature", out)

    def test_merge_into_main_refused(self):
        self.feature_with_merge()
        code, out = self.push("feature:main")
        self.refused(code, out)
        self.assertIn("into main", out)

    def test_spike_pushed_earlier_still_refused(self):
        self.spike()
        self.assertEqual(self.push("spike/idea")[0], 0)
        p = self.p
        p.branch("feature")
        p.git("merge", "-q", "--no-ff", "--no-edit", "spike/idea")
        self.refused(*self.push("feature"))

    def test_branch_deleted_after_merge_still_refused(self):
        self.feature_with_merge(delete=True)
        self.refused(*self.push("feature"))

    def test_fast_forward_refused(self):
        self.spike()
        self.p.git("checkout", "-q", "-b", "feature")
        self.refused(*self.push("feature"))

    def test_merge_of_unmarked_spike_refused_by_its_subject(self):
        self.spike(trailer=False)
        p = self.p
        p.branch("feature")
        p.git("merge", "-q", "--no-ff", "--no-edit", "spike/idea")
        self.refused(*self.push("feature"), why="merge of an exploration branch")

    def test_squash_refused(self):
        self.spike()
        p = self.p
        p.branch("feature")
        p.git("merge", "-q", "--squash", "spike/idea")
        p.git("commit", "-q", "--no-edit")
        self.refused(*self.push("feature"))

    def test_detached_head_push_refused(self):
        self.feature_with_merge()
        self.p.git("checkout", "-q", "--detach")
        self.refused(*self.push("HEAD:refs/heads/other"))

    def test_spike_into_another_spike_allowed(self):
        self.feature_with_merge()
        code, out = self.push("feature:spike/other")
        self.assertEqual(code, 0, out)

    def test_working_branch_without_spike_allowed(self):
        p = self.p
        p.branch("feature")
        p.write("docs/w.md", "w\n")
        p.commit("work")
        code, out = self.push("feature")
        self.assertEqual(code, 0, out)

    def test_feature_off_with_empty_prefix(self):
        self.set_config(spikeBranch="")
        self.feature_with_merge()
        code, out = self.push("feature")
        self.assertEqual(code, 0, out)

    def test_prefix_without_slash(self):
        self.set_config(spikeBranch="exp")
        self.spike(name="exp/a")
        self.p.git("checkout", "-q", "-b", "feature")
        self.refused(*self.push("feature"))

    # merge-branch.sh
    def test_merge_branch_refuses_a_spike_with_its_reason(self):
        self.spike()
        p = self.p
        p.branch("feature")
        before = p.sha()
        code, out = p.script("merge-branch.sh", "spike/idea", "Merge spike", "--reviewed")
        self.assertEqual(code, 2, out)
        self.assertIn("spike/idea is an exploration branch", out)
        self.assertIn("task record", out)
        self.assertIn("git branch -D spike/idea", out)
        self.assertEqual(p.sha(), before)

    def test_merge_branch_refuses_a_branch_carrying_a_spike(self):
        self.spike()
        p = self.p
        p.branch("agent/X1-a")
        p.git("merge", "-q", "--no-ff", "--no-edit", "spike/idea")
        p.branch("feature")
        before = p.sha()
        code, out = p.script("merge-branch.sh", "agent/X1-a", "Merge agent", "--reviewed")
        self.assertEqual(code, 2, out)
        self.assertIn("carries an exploration branch's commits", out)
        self.assertEqual(p.sha(), before)

    def test_merge_branch_into_a_spike_and_feature_off(self):
        self.spike()
        p = self.p
        p.branch("spike/other")
        code, out = p.script("merge-branch.sh", "spike/idea", "Merge spike", "--reviewed")
        self.assertEqual(code, 0, out)
        self.set_config(spikeBranch="")
        self.spike(name="spike/b")
        p.branch("feature")
        code, out = p.script("merge-branch.sh", "spike/b", "Merge spike", "--reviewed")
        self.assertEqual(code, 0, out)


if __name__ == "__main__":
    unittest.main()
