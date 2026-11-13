"""scripts/private-check.py (E2): key formats, e-mail addresses and private names in the tree (--all) and in what a
range of commits adds (--range, --commits), plus the local file .claude/gw.local.json that config.py reads. Temporary
repos, git isolated as in test_hooks.
"""
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from test_hooks import BASE_CONFIG, FAKE_TOKEN, ROOT

SCRIPT = ROOT / "scripts" / "private-check.py"
CONFIG = ROOT / "scripts" / "config.py"
# Built by concatenation so this file itself passes the check it tests.
AT = "@"
PRIVATE_MAIL = "jane.doe" + AT + "corp.io"


class Repo(unittest.TestCase):
    config = None

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="gw-private-")).resolve()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        gitconfig = self.tmp / "gitconfig"
        gitconfig.write_text("[user]\n\tname = Test\n\temail = test@example.com\n[commit]\n\tgpgsign = false\n"
                             "[init]\n\tdefaultBranch = main\n")
        self.env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
        self.env.update(GIT_CONFIG_GLOBAL=str(gitconfig), GIT_CONFIG_NOSYSTEM="1")
        self.work = self.tmp / "work"
        self.git("init", "-q", str(self.work), cwd=self.tmp)
        self.write(".claude/gw.json", json.dumps(dict(BASE_CONFIG, **(self.config or {}))))
        (self.work / ".githooks").mkdir()
        shutil.copy2(ROOT / "templates" / "githooks" / "pre-commit", self.work / ".githooks" / "pre-commit")
        self.write("README.md", "hello\n")
        self.commit("base")
        self.base = self.sha()

    def git(self, *args, cwd=None):
        r = subprocess.run(["git", *args], cwd=cwd or self.work, env=self.env, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        return r.stdout

    def write(self, rel, text):
        path = self.work / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)

    def commit(self, message):
        self.git("add", "-A")
        self.git("commit", "-q", "--no-verify", "-m", message)

    def sha(self, rev="HEAD"):
        return self.git("rev-parse", rev).strip()

    def local(self, data):
        self.write(".claude/gw.local.json", data if isinstance(data, str) else json.dumps(data))

    def check(self, *args, stdin=None):
        if "--all" in args:  # --all reads the tracked files
            self.git("add", "-A")
        r =subprocess.run(["python3", str(SCRIPT), "--root", str(self.work), *args], cwd=self.tmp, env=self.env,
                           capture_output=True, text=True, input=stdin)
        return r.returncode, r.stdout + r.stderr


class Emails(Repo):
    def test_a_private_address_fails_with_where_and_the_fix(self):
        self.write("docs/team.md", "intro\nwrite to " + PRIVATE_MAIL + " please\n")
        code, out = self.check("--all", "--no-names")
        self.assertEqual(code, 1, out)
        self.assertIn("docs/team.md:2: e-mail " + PRIVATE_MAIL, out)
        self.assertIn("privateCheck.allowEmails", out)
        self.assertIn("git commit -a", out)

    def test_built_in_public_addresses_pass(self):
        public = ["a" + AT + "example.com", "b" + AT + "mail.example.org", "c" + AT + "example.net",
                  "d" + AT + "host.example", "123+me" + AT + "users.noreply.github.com",
                  "noreply" + AT + "anthropic.com", "No-Reply" + AT + "corp.io", "git" + AT + "github.com"]
        self.write("docs/ok.md", "\n".join(public) + "\nreact" + AT + "18.3.1 and @types/node\n")
        code, out = self.check("--all", "--no-names")
        self.assertEqual(code, 0, out)

    def test_allow_lists_public_and_local(self):
        other = "boss" + AT + "corp.io"
        self.write("docs/team.md", PRIVATE_MAIL + "\n" + other + "\n")
        self.write(".claude/gw.json", json.dumps(dict(BASE_CONFIG, privateCheck={"allowEmails": [PRIVATE_MAIL]})))
        code, out = self.check("--all", "--no-names")
        self.assertEqual(code, 1, out)
        self.assertNotIn(PRIVATE_MAIL, out)
        self.assertIn("e-mail " + other, out)
        self.local({"allowEmails": [other.upper()]})  # case-insensitive
        code, out = self.check("--all", "--no-names")
        self.assertEqual(code, 0, out)

    def test_keys_glued_to_a_letter_or_an_escape_are_found(self):
        # D37: the hook's regex also finds a key after an escaped newline or a percent-encoded character.
        self.write("docs/a.md", "x=\\n" + "sk-" + "ant-" + "A1b2C3d4" * 3 + "\n")
        self.write("docs/b.md", "a%3D" + "AKIA" + "ABCDEFGH12345678" + "\n")
        self.write("docs/c.md", "x=\\n" + "sk-" + "or-v1-" + "0123456789abcdef" * 2 + "\n")
        code, out = self.check("--all", "--no-names")
        self.assertEqual(code, 1, out)
        self.assertIn("docs/a.md:1: key sk-ant-A\u2026", out)
        self.assertIn("docs/b.md:1: key AKIAABCD\u2026", out)
        self.assertIn("docs/c.md:1: key sk-or-v1\u2026", out)

    def test_emails_false_and_private_check_false(self):
        self.write("docs/team.md", PRIVATE_MAIL + "\n")
        self.write(".claude/gw.json", json.dumps(dict(BASE_CONFIG, privateCheck={"emails": False})))
        self.assertEqual(self.check("--all")[0], 0)
        self.write("docs/key.md", FAKE_TOKEN + "\n")
        code, out = self.check("--all")
        self.assertEqual(code, 1, out)  # emails off, keys still on
        self.assertIn("docs/key.md:1: key ghp_A1b2…", out)
        self.assertNotIn(FAKE_TOKEN, out)  # never printed whole
        self.write(".claude/gw.json", json.dumps(dict(BASE_CONFIG, privateCheck=False)))
        code, out = self.check("--all")
        self.assertEqual(code, 0, out)
        self.assertIn("off (privateCheck is false", out)

    def test_markers_skip_a_checked_line(self):
        self.write("docs/a.md", PRIVATE_MAIL + "  <!-- gw-allow-private -->\n" + FAKE_TOKEN + " # gw-allow-secret\n")
        self.assertEqual(self.check("--all", "--no-names")[0], 0)
        self.write("docs/a.md", PRIVATE_MAIL + " # gw-allow-secret\n")  # only skips the key check
        self.assertEqual(self.check("--all", "--no-names")[0], 1)

    def test_at_most_ten_hits(self):
        self.write("docs/many.md", "".join(f"u{i}" + AT + "corp.io\n" for i in range(15)))
        code, out = self.check("--all", "--no-names")
        self.assertEqual(code, 1, out)
        self.assertEqual(out.count(": e-mail "), 10)
        self.assertIn("… and 5 more", out)

    def test_max_hits_key_changes_how_many_are_printed(self):
        self.write("docs/many.md", "".join(f"u{i}" + AT + "corp.io\n" for i in range(15)))
        self.write(".claude/gw.json", json.dumps(dict(BASE_CONFIG, privateCheck={"maxHits": 3})))
        code, out = self.check("--all", "--no-names")
        self.assertEqual(code, 1, out)
        self.assertEqual(out.count(": e-mail "), 3)
        self.assertIn("… and 12 more", out)
        self.write(".claude/gw.json", json.dumps(dict(BASE_CONFIG, privateCheck=True)))  # true: the defaults
        self.assertEqual(self.check("--all", "--no-names")[1].count(": e-mail "), 10)
        self.write(".claude/gw.json", json.dumps(dict(BASE_CONFIG, privateCheck={"maxHits": 0})))
        code, out = self.check("--all", "--no-names")
        self.assertEqual(code, 2, out)
        self.assertIn("$.privateCheck: matches none of the allowed forms", out)
        self.assertIn("maxHits: must be at least 1, got 0", out)


class Names(Repo):
    def test_names_match_case_and_separators_in_content_paths_and_messages(self):
        self.local({"privateNames": ["Secret-Project"]})
        self.write("docs/a.md", "see secret_project here\n")
        self.write("docs/SECRET PROJECT.md", "x\n")
        self.commit("work on secretproject and Secret Project")
        code, out = self.check("--range", f"{self.base}..HEAD")
        self.assertEqual(code, 1, out)
        short = self.sha()[:7]
        self.assertIn(f"docs/a.md:1 (commit {short}): private name secret_project", out)
        self.assertIn(f"docs/SECRET PROJECT.md (commit {short}) (path): private name SECRET PROJECT", out)
        self.assertIn(f"commit {short} (message): private name Secret Project", out)
        self.assertNotIn("secretproject", out)  # no separator is another word
        self.assertIn("git rebase -i <the remote branch>", out)
        self.assertNotIn("NOT pushed", out)
        code, out = self.check("--range", f"{self.base}..HEAD", "--no-names")
        self.assertEqual(code, 0, out)

    def test_names_of_anonymize_are_checked_and_their_aliases_pass(self):
        self.local({"anonymize": {"Secret App": "private-project-1"}})
        self.write("docs/a.md", "from secret-app\n")
        self.write("docs/b.md", "from private-project-1\n")
        code, out = self.check("--all")
        self.assertEqual(code, 1, out)
        self.assertIn("docs/a.md:1: private name secret-app", out)
        self.assertNotIn("docs/b.md", out)

    def test_no_local_file_skips_names_with_a_notice(self):
        self.write("docs/a.md", "Secret-Project\n")
        code, out = self.check("--all")
        self.assertEqual(code, 0, out)
        self.assertIn("no .claude/gw.local.json, so private names are not checked", out)

    def test_a_malformed_local_file_fails_closed(self):
        for bad, reason in (("{nope", "invalid JSON"), ('["x"]', "expected a JSON object"),
                            ('{"privateName": ["x"]}', "unknown key 'privateName'"),
                            ('{"privateNames": "x"}', "'privateNames' must be a list of non-empty strings"),
                            ('{"privateNames": [""]}', "'privateNames' must be a list of non-empty strings"),
                            ('{"anonymize": ["x"]}', "'anonymize' must map non-empty names to aliases"),
                            ('{"anonymize": {"x": "project-1"}}', "'anonymize' must map non-empty names to aliases"),
                            ('{"anonymize": {"x": "private-project-"}}', "aliases private-project-N"),
                            ('{"anonymize": {"x": 1}}', "aliases private-project-N"),
                            ('{"anonymize": {" ": "private-project-1"}}', "must map non-empty names")):
            self.local(bad)
            code, out = self.check("--all")
            self.assertEqual(code, 2, bad)
            self.assertIn(reason, out)
            self.assertIn("config.py", out)  # the command that checks the fix
            self.assertEqual(self.check("--all", "--no-names")[0], 2, bad)  # its allowEmails are read too

    def test_config_local_command(self):
        cli = ["python3", str(CONFIG), "--root", str(self.work), "local"]
        r = subprocess.run(cli, capture_output=True, text=True, env=self.env)
        self.assertEqual((r.returncode, r.stdout.strip()), (0, "null"))
        self.local({"privateNames": ["A"]})
        r = subprocess.run(cli, capture_output=True, text=True, env=self.env)
        self.assertEqual(json.loads(r.stdout), {"privateNames": ["A"], "allowEmails": [], "anonymize": {}})
        # The names of anonymize are private names too, listed once.
        self.local({"privateNames": ["A"], "anonymize": {"A": "private-project-1", "b_c": "private-project-2"}})
        r = subprocess.run(cli, capture_output=True, text=True, env=self.env)
        self.assertEqual(json.loads(r.stdout)["privateNames"], ["A", "b_c"])
        self.local("[]")
        r = subprocess.run(cli, capture_output=True, text=True, env=self.env)
        self.assertEqual(r.returncode, 2)
        self.assertIn("expected a JSON object", r.stderr)


class Advice(Repo):
    """D47: a refusal says the commits are not pushed yet and the exact command that fixes only them."""

    def bad(self, name="a"):
        self.write(f"docs/{name}.md", PRIVATE_MAIL + "\n")
        self.commit(f"add {name}")
        return self.sha()

    def good(self, name="g"):
        self.write(f"docs/{name}.md", "fine\n")
        self.commit(f"add {name}")
        return self.sha()

    def push_check(self, shas, *flags):
        if "--remote" not in flags:
            flags = flags + ("--remote", "origin")
        return self.check("--no-names", "--commits", "-", *flags, stdin="\n".join(shas) + "\n")

    def remote(self):
        remote = self.tmp / "remote.git"
        self.git("init", "-q", "--bare", str(remote), cwd=self.tmp)
        self.git("remote", "add", "origin", str(remote))
        return remote

    def test_one_new_commit_is_amended(self):
        sha = self.bad()
        code, out = self.push_check([sha], "--base", self.base)
        self.assertEqual(code, 1, out)
        self.assertIn("are NOT pushed yet", out)
        self.assertIn("it is only the last commit", out)
        self.assertIn("git commit --amend", out)
        self.assertNotIn("rebase -i", out)

    def test_several_commits_name_the_remote_base(self):
        first = self.bad("a")
        second = self.bad("b")
        code, out = self.push_check([first, second], "--base", self.base)
        self.assertEqual(code, 1, out)
        self.assertIn(f"git rebase -i {self.base[:12]}", out)
        self.assertNotIn("--rebase-merges", out)
        self.assertIn(f"{first[:7]}, {second[:7]}", out)
        self.assertIn("never rewrite what is already on the remote", out)

    def test_private_commit_that_is_not_the_last_needs_a_rebase(self):
        first = self.bad("a")
        last = self.good()
        code, out = self.push_check([first, last], "--base", self.base)
        self.assertEqual(code, 1, out)
        self.assertIn(f"git rebase -i {self.base[:12]}", out)
        self.assertNotIn("git commit --amend", out)

    def test_only_the_last_of_several_is_amended(self):
        self.good()
        sha = self.bad()
        code, out = self.push_check([self.sha("HEAD~1"), sha], "--base", self.base)
        self.assertEqual(code, 1, out)
        self.assertIn("it is only the last commit", out)
        self.assertNotIn("rebase -i", out)

    def test_new_branch_uses_the_merge_base_with_the_protected_branch(self):
        self.remote()
        self.git("push", "-q", "origin", "HEAD:refs/heads/main")
        self.git("fetch", "-q", "origin")
        first = self.bad("a")
        second = self.good()
        code, out = self.push_check([first, second], "--remote", "origin", "--ref", "feature")
        self.assertEqual(code, 1, out)
        self.assertIn(f"git rebase -i {self.base[:12]}", out)

    def test_no_remote_base_gives_the_alternative_command(self):
        first = self.bad("a")
        second = self.good()
        code, out = self.push_check([first, second], "--remote", "origin", "--ref", "feature")
        self.assertEqual(code, 1, out)
        self.assertIn("no remote base found for (feature)", out)
        self.assertIn(f"git rebase -i {self.base[:12]}", out)

    def test_base_is_the_parent_of_the_first_bad_commit_and_merges_are_kept(self):
        self.remote()
        self.git("push", "-q", "origin", "HEAD:refs/heads/main")
        self.git("checkout", "-q", "-b", "feature")
        self.write("docs/ok.md", "fine\n")
        self.commit("published work")
        published = self.sha()
        self.git("push", "-q", "origin", "feature")
        bad = self.bad("a")
        self.git("checkout", "-q", "main")
        self.write("docs/m.md", "main moved\n")
        self.commit("main moves")
        self.git("push", "-q", "origin", "main")
        self.git("checkout", "-q", "feature")
        self.git("merge", "-q", "--no-edit", "main")
        merge = self.sha()
        code, out = self.push_check([bad, merge], "--base", published, "--ref", "feature")
        self.assertEqual(code, 1, out)
        self.assertIn(f"git rebase -i --rebase-merges {published[:12]}", out)
        self.assertNotIn("git rebase -i --rebase-merges " + self.base[:12], out)

    def test_branch_cut_from_another_published_branch_does_not_rewrite_it(self):
        self.remote()
        self.git("push", "-q", "origin", "HEAD:refs/heads/main")
        self.git("checkout", "-q", "-b", "featA")
        self.write("docs/a-pub.md", "fine\n")
        self.commit("featA work")
        feat_a = self.sha()
        self.git("push", "-q", "origin", "featA")
        self.git("checkout", "-q", "-b", "featB")
        bad = self.bad("b")
        code, out = self.push_check([bad], "--ref", "featB")
        self.assertEqual(code, 1, out)
        self.assertIn("it is only the last commit", out)
        self.git("checkout", "-q", "-b", "featC", feat_a)
        first = self.bad("c")
        last = self.good("d")
        code, out = self.push_check([first, last], "--ref", "featC")
        self.assertEqual(code, 1, out)
        self.assertIn(f"git rebase -i {feat_a[:12]}", out)
        self.assertNotIn(f"git rebase -i {self.base[:12]}", out)

    def test_a_manual_range_does_not_claim_the_commits_are_unpushed(self):
        self.remote()
        sha = self.bad("a")
        code, out = self.check("--no-names", "--range", f"{self.base}..HEAD", "--remote", "origin")
        self.assertEqual(code, 1, out)
        self.assertNotIn("NOT pushed", out)
        self.assertNotIn("git commit --amend", out)
        self.assertIn("git rebase -i <the remote branch>", out)

    def test_a_pushed_branch_that_is_not_checked_out_is_named(self):
        sha = self.bad("a")
        self.git("checkout", "-q", "-b", "other", self.base)
        code, out = self.push_check([sha], "--base", self.base, "--ref", "feature")
        self.assertEqual(code, 1, out)
        self.assertIn(f"git rebase -i {self.base[:12]} feature", out)
        self.assertNotIn("git commit --amend", out)

    def test_a_tag_or_head_is_not_named_in_the_rebase(self):
        # D79: `git rebase -i <base> <tag>` detaches HEAD and leaves the tag behind; HEAD is no branch either.
        sha = self.bad("a")
        self.git("checkout", "-q", "-b", "other", self.base)
        for ref in ("refs/tags/v-pushed", "HEAD"):
            code, out = self.push_check([sha], "--base", self.base, "--ref", ref)
            self.assertEqual(code, 1, out)
            self.assertIn(f"git rebase -i {self.base[:12]}", out)
            self.assertNotIn(f"{self.base[:12]} {ref}", out)

    def test_the_amend_advice_never_stages_everything(self):
        sha = self.bad()
        code, out = self.push_check([sha], "--base", self.base)
        self.assertEqual(code, 1, out)
        self.assertNotIn("git add -A", out)
        self.assertIn("git add <the fixed files>", out)


class Commits(Repo):
    def test_a_value_removed_later_is_still_in_the_history(self):
        self.write("docs/a.md", "one\n" + PRIVATE_MAIL + "\n")
        self.commit("add")
        added = self.sha()[:7]
        self.write("docs/a.md", "one\n")
        self.commit("remove")
        code, out = self.check("--range", f"{self.base}..HEAD", "--no-names")
        self.assertEqual(code, 1, out)
        self.assertIn(f"docs/a.md:2 (commit {added}): e-mail {PRIVATE_MAIL}", out)

    def test_only_what_the_commits_add(self):
        self.write("docs/old.md", PRIVATE_MAIL + "\n")
        self.commit("old, already public")
        start = self.sha()
        self.write("docs/old.md", PRIVATE_MAIL + "\nnew line\n")
        self.commit("touch")
        self.assertEqual(self.check("--range", f"{start}..HEAD", "--no-names")[0], 0)

    def test_a_merge_reports_only_its_own_lines(self):
        self.git("checkout", "-q", "-b", "side")
        self.write("docs/side.md", PRIVATE_MAIL + "\n")
        self.commit("side")
        side = self.sha()
        self.git("checkout", "-q", "main")
        self.write("docs/main.md", "main\n")
        self.commit("main")
        self.git("merge", "-q", "--no-ff", "--no-commit", "side")
        evil = "evil" + AT + "corp.io"
        self.write("docs/main.md", "main\n" + evil + "\n")
        self.commit("merge")
        merge = self.sha()[:7]
        code, out = self.check("--range", f"{side}..HEAD", "--no-names")  # the side commit is outside the range
        self.assertEqual(code, 1, out)
        self.assertIn(f"docs/main.md:2 (commit {merge}): e-mail {evil}", out)
        self.assertNotIn(PRIVATE_MAIL, out)

    def test_commits_from_stdin(self):
        self.write("docs/a.md", PRIVATE_MAIL + "\n")
        self.commit("add")
        code, out = self.check("--commits", "-", "--no-names", stdin=self.sha() + "\n")
        self.assertEqual(code, 1, out)
        self.assertIn(PRIVATE_MAIL, out)
        code, out = self.check("--commits", "-", "--no-names", stdin="1" * 40 + "\n")
        self.assertEqual(code, 2, out)
        self.assertIn("is not in this clone", out)

    def test_bad_range_fails_closed(self):
        code, out = self.check("--range", "nope..HEAD")
        self.assertEqual(code, 2, out)
        self.assertIn("git fetch --deepen=200 origin", out)
        code, out = self.check("--range", "HEAD")
        self.assertEqual(code, 2, out)
        self.assertIn("--range needs A..B", out)

    def test_the_key_regex_comes_from_the_hook(self):
        (self.work / ".githooks" / "pre-commit").write_text("#!/bin/sh\nexit 0\n")
        code, out = self.check("--all", "--no-names")
        self.assertEqual(code, 2, out)
        self.assertIn("has no KEY_FORMATS line", out)
        shutil.rmtree(self.work / ".githooks")
        code, out = self.check("--all", "--no-names")
        self.assertEqual(code, 2, out)
        self.assertIn("reinstall the hooks", out)


class ThisRepo(unittest.TestCase):
    def test_the_tree_has_no_keys_nor_private_addresses(self):
        r = subprocess.run(["python3", str(SCRIPT), "--all", "--no-names"], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)


class Crashes(unittest.TestCase):
    def test_a_missing_config_py_exits_2_not_1(self):
        tmp = Path(tempfile.mkdtemp(prefix="gw-private-imp-")).resolve()
        self.addCleanup(shutil.rmtree, tmp, True)
        shutil.copy2(SCRIPT, tmp / "private-check.py")
        r = subprocess.run(["python3", "-B", str(tmp / "private-check.py"), "--all"], capture_output=True, text=True,
                           cwd=tmp)
        self.assertEqual(r.returncode, 2, r.stderr)
        self.assertIn("cannot load config.py", r.stderr)
        self.assertIn("ModuleNotFoundError", r.stderr)


if __name__ == "__main__":
    unittest.main()
