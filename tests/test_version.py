"""scripts/version.py: markers in sync with plugin.json, and a bump that moves them all."""
import importlib.util
import json
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VERSION = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))["version"]


def run(root, *args):
    return subprocess.run(["python3", str(root / "scripts" / "version.py"), *args], capture_output=True, text=True)


class Version(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        for rel in ("scripts", "skills", "templates", "schema", ".claude-plugin"):
            shutil.copytree(ROOT / rel, self.tmp / rel, ignore=shutil.ignore_patterns("__pycache__", "node_modules"))
        (self.tmp / ".claude").mkdir()
        shutil.copy(ROOT / ".claude" / "gw.json", self.tmp / ".claude" / "gw.json")
        self.set_gw(releaseDocs=None)  # this repo's own releaseDocs would need its READMEs in every temp repo
        shutil.copy(ROOT / "CHANGELOG.md", self.tmp / "CHANGELOG.md")
        self.git("init", "-q")  # the config (changelogFragments, D68) is read inside a git repository

    def set_gw(self, **keys):
        """Set (or, with None, drop) top-level keys of the temp repo's .claude/gw.json."""
        gw = self.tmp / ".claude" / "gw.json"
        data = json.loads(gw.read_text())
        for key, value in keys.items():
            if value is None:
                data.pop(key, None)
            else:
                data[key] = value
        gw.write_text(json.dumps(data))

    def test_this_repo_markers_match_plugin_json(self):
        r = run(ROOT)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_installed_node_modules_and_ignored_files_need_no_marker(self):
        """E5: an installed templates/front/node_modules or a git-ignored local file must not turn the check red."""
        lib = self.tmp / "templates" / "front" / "node_modules" / "pkg"
        lib.mkdir(parents=True, exist_ok=True)
        (lib / "index.js").write_text("module.exports = 1\n")
        (self.tmp / "templates" / "front" / "local-cache.txt").write_text("no marker\n")
        (self.tmp / ".gitignore").write_text("local-cache.txt\n")
        r = run(self.tmp)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        (self.tmp / "templates" / "front" / "tracked.ts").write_text("export {}\n")
        r = run(self.tmp)
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("missing marker: templates/front/tracked.ts", r.stdout + r.stderr)

    def git(self, *args):
        subprocess.run(["git", "-C", str(self.tmp), "-c", "user.name=t", "-c", "user.email=t@t",
                        "-c", "commit.gpgsign=false", "-c", "tag.gpgsign=false", *args], check=True, capture_output=True)

    def commit_all(self, message):
        self.git("add", "-A")
        self.git("commit", "-qm", message)

    def test_release_needs_a_new_version_when_copyable_files_changed_since_the_tag(self):
        tmp = self.tmp
        self.git("init", "-q")
        self.commit_all("released")
        self.git("tag", f"v{VERSION}")
        (tmp / "README.md").write_text("not copyable\n"); self.commit_all("docs only")
        r = run(tmp, "--release")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        script = tmp / "scripts" / "doctor.py"
        script.write_text(script.read_text() + "# changed\n"); self.commit_all("copyable change")
        r = run(tmp, "--release")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn(f"changed since v{VERSION} (scripts/doctor.py)", r.stdout)
        self.assertIn("python3 scripts/version.py X.Y.Z", r.stdout)
        self.assertEqual(run(tmp).returncode, 0, "without --release only the markers are checked")
        self.assertEqual(run(tmp, "9.8.7").returncode, 0)
        self.harvest()
        self.fill_entry("9.8.7")
        self.commit_all("bump")
        r = run(tmp, "--release")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def fill_entry(self, version, date="2026-10-25"):
        log = self.tmp / "CHANGELOG.md"
        log.write_text(log.read_text().replace(f"## [{version}] - Unreleased", f"## [{version}] - {date}", 1)
                       .replace("- (por completar)", "- Hecho.", 1).replace("- (to be filled in)", "- Done.", 1))

    def test_a_new_version_needs_a_dated_and_filled_in_changelog_entry(self):
        tmp = self.tmp
        self.git("init", "-q")
        self.commit_all("released")
        self.git("tag", f"v{VERSION}")
        self.assertEqual(run(tmp, "9.8.7").returncode, 0)
        self.harvest()
        self.commit_all("bump, entry left as the bump wrote it")
        r = run(tmp, "--release")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("undated release: the CHANGELOG heading of 9.8.7 is '## [9.8.7] - Unreleased'", r.stdout)
        self.assertIn("unfinished CHANGELOG entry for 9.8.7", r.stdout)
        self.assertNotIn("no harvest", r.stdout)
        log = tmp / "CHANGELOG.md"
        log.write_text(log.read_text().replace("## [9.8.7] - Unreleased", "## [9.8.7] - 2026-10-25", 1))
        self.commit_all("dated, placeholder still there")
        r = run(tmp, "--release")
        self.assertNotIn("undated release", r.stdout)
        self.assertIn("unfinished CHANGELOG entry for 9.8.7", r.stdout, "the placeholder alone also blocks")
        self.fill_entry("9.8.7")
        self.commit_all("filled in")
        r = run(tmp, "--release")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        log.write_text(log.read_text().replace("## [9.8.7] - 2026-10-25", "## [9.8.7] - 2026-10-25 (beta)", 1))
        self.commit_all("anything after the date")
        self.assertIn("undated release", run(tmp, "--release").stdout)
        log.write_text(log.read_text().replace("## [9.8.7] - 2026-10-25 (beta)\n", "", 1))
        self.commit_all("entry heading removed")
        self.assertIn("no CHANGELOG entry for 9.8.7", run(tmp, "--release").stdout)

    def test_the_new_changelog_entry_must_quote_only_paths_that_exist(self):
        tmp = self.tmp
        self.git("init", "-q")
        (tmp / "docs").mkdir()
        (tmp / "docs" / "real.md").write_text("x\n")
        self.commit_all("released")
        self.git("tag", f"v{VERSION}")
        self.assertEqual(run(tmp, "9.8.7").returncode, 0)
        self.harvest()
        self.fill_entry("9.8.7")
        log = tmp / "CHANGELOG.md"
        quoted = ("- Cita `docs/real.md`, `scripts/version.py`, `skills/`, `docs/records/release-vX.Y.Z.md`, "
                  "`docs/<tema>.md`, `scripts/*.sh`, `no/such`, `a/b` y `a/b c` sin ruta.")
        log.write_text(log.read_text().replace("- Hecho.", quoted, 1))
        self.commit_all("entry with only existing paths or placeholders")
        r = run(tmp, "--release")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        log.write_text(log.read_text().replace(quoted, quoted + " `docs/gone.md` y `scripts/gone.py/`.", 1))
        self.commit_all("entry quoting missing paths")
        r = run(tmp, "--release")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("CHANGELOG entry for 9.8.7 quotes `docs/gone.md`, which does not exist in the tree being released",
                      r.stdout)
        self.assertIn("scripts/gone.py/", r.stdout)
        self.assertIn("fix the path in CHANGELOG.md", r.stdout)
        self.assertNotIn("`docs/real.md`, which", r.stdout)
        self.assertNotIn("release-vX.Y.Z", r.stdout)
        self.assertNotIn("`docs/<tema>.md`, which", r.stdout)
        self.assertNotIn("no/such", r.stdout, "a first segment that is no top-level directory is not a repo path")
        self.assertNotIn("`a/b`", r.stdout)

    def test_a_path_only_in_the_working_tree_does_not_count(self):
        tmp = self.tmp
        self.git("init", "-q")
        self.commit_all("released")
        self.git("tag", f"v{VERSION}")
        self.assertEqual(run(tmp, "9.8.7").returncode, 0)
        self.harvest()
        self.fill_entry("9.8.7")
        log = tmp / "CHANGELOG.md"
        log.write_text(log.read_text().replace("- Hecho.", "- Cita `scripts/untracked.py`.", 1))
        self.commit_all("entry quotes a file")
        (tmp / "scripts" / "untracked.py").write_text("x\n")
        r = run(tmp, "--release")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("quotes `scripts/untracked.py`", r.stdout)

    def test_changelog_paths_accept_history_ignored_files_and_flag_typos_and_root_files(self):
        tmp = self.tmp
        self.git("init", "-q")
        (tmp / "docs").mkdir()
        (tmp / "docs" / "old-name.md").write_text("x\n")
        (tmp / "old-top").mkdir()
        (tmp / "old-top" / "f.md").write_text("x\n")
        self.commit_all("old names")
        self.git("rm", "-rq", "docs/old-name.md", "old-top")
        (tmp / ".gitignore").write_text(".claude/gw.local.json\n.claude/worktrees/\n")
        self.commit_all("old names gone")
        self.git("tag", f"v{VERSION}")
        self.assertEqual(run(tmp, "9.8.7").returncode, 0)
        self.harvest()
        self.fill_entry("9.8.7")
        log = tmp / "CHANGELOG.md"
        ok = ("- Antes `docs/old-name.md` y `old-top/f.md`, local `.claude/gw.local.json` y `.claude/worktrees/`, "
              "raiz `CHANGELOG.md`, `docs/records/retro-YYYY-MM-DD.md`, `docs/NNN.md`, `docs/…`, prosa ES/EN y "
              "`feat/fix`, `SKILL.md` suelto.")
        log.write_text(log.read_text().replace("- Hecho.", ok, 1))
        self.commit_all("entry with history, ignored and placeholder paths")
        r = run(tmp, "--release")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        bad = " `script/x.py`, `skill/gw-harvest/`, `GONE.md`, `docs/never.md`."
        log.write_text(log.read_text().replace(ok, ok + bad, 1))
        self.commit_all("entry with typos")
        r = run(tmp, "--release")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        for path in ("script/x.py", "skill/gw-harvest/", "GONE.md", "docs/never.md"):
            self.assertIn(f"quotes `{path}`, which does not exist in the tree being released, nor ever did", r.stdout)
        self.assertEqual(r.stdout.count("quotes `"), 4, r.stdout)

    def test_the_changelog_is_read_from_head_not_from_the_working_tree(self):
        tmp = self.tmp
        self.git("init", "-q")
        self.commit_all("released")
        self.git("tag", f"v{VERSION}")
        self.assertEqual(run(tmp, "9.8.7").returncode, 0)
        self.harvest()
        self.fill_entry("9.8.7")
        self.commit_all("entry filled in")
        log = tmp / "CHANGELOG.md"
        log.write_text(log.read_text().replace("- Hecho.", "- Cita `docs/gone.md`.", 1))
        r = run(tmp, "--release")
        self.assertEqual(r.returncode, 0, "an uncommitted edit is not what is published: " + r.stdout + r.stderr)

    def test_the_unreleased_entry_of_this_repo_quotes_only_valid_paths(self):
        spec = importlib.util.spec_from_file_location("version_under_test", ROOT / "scripts" / "version.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        head = re.search(r"^## \[[^\]]+\] - Unreleased[^\n]*", text, re.M)
        if not head:
            self.skipTest("no unreleased entry in CHANGELOG.md")
        nxt = re.search(r"^## \[", text[head.end():], re.M)
        entry = text[head.end():head.end() + nxt.start()] if nxt else text[head.end():]
        self.assertEqual(mod.changelog_paths("unreleased", entry), [])

    def harvest(self, first_line="# Harvest portal — 2026-10-23"):
        (self.tmp / "docs" / "propuestas").mkdir(parents=True, exist_ok=True)
        (self.tmp / "docs" / "propuestas" / "2026-10-23-portal.md").write_text(first_line + "\n\nNada nuevo.\n")

    def test_a_new_version_needs_a_harvest_added_since_the_last_tag(self):
        tmp = self.tmp
        self.git("init", "-q")
        self.harvest()
        self.commit_all("released, with the harvest of that version")
        self.git("tag", f"v{VERSION}")
        self.assertEqual(run(tmp, "9.8.7").returncode, 0)
        self.commit_all("bump")
        r = run(tmp, "--release")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("no harvest for 9.8.7", r.stdout)
        self.assertIn(f"since v{VERSION}", r.stdout)
        self.assertIn("gw-harvest", r.stdout)
        self.assertIn("\n  git checkout <sha> -- docs/propuestas/<file>.md", r.stdout)  # one file, not the folder
        self.assertIn("\n  git log --all --diff-filter=A --oneline --name-only -- docs/propuestas\n", r.stdout)
        self.assertIn("\n  python3 scripts/version.py --release\n", r.stdout)  # each command on its own line
        (tmp / "docs" / "propuestas" / "2026-10-24-reparto.md").write_text("# Reparto — 2026-10-24\n")
        self.commit_all("a proposals file that is not a harvest")
        r = run(tmp, "--release")
        self.assertIn("no harvest for 9.8.7", r.stdout, "only a '# Harvest' file counts")
        (tmp / "docs" / "propuestas" / "2026-10-23-portal.md").write_text("# Harvest portal — editada\n")
        self.commit_all("an edit of the old harvest")
        r = run(tmp, "--release")
        self.assertIn("no harvest for 9.8.7", r.stdout, "editing an earlier harvest is not a new one")
        (tmp / "docs" / "propuestas" / "2026-10-25-wmf.md").write_text("# Harvest wmf — 2026-10-25\n")
        self.fill_entry("9.8.7")
        self.commit_all("harvest")
        r = run(tmp, "--release")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_the_seal_warns_at_once_when_the_new_version_has_no_harvest(self):
        """D124: `version.py X.Y.Z` prints the --release harvest warning on stderr; the seal still exits 0."""
        tmp = self.tmp
        self.git("init", "-q")
        self.harvest()
        self.commit_all("released")
        self.git("tag", f"v{VERSION}")
        r = run(tmp, "9.8.7")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("warning: no harvest for 9.8.7", r.stderr)
        self.assertIn("\n  git checkout <sha> -- docs/propuestas/<file>.md", r.stderr)
        self.assertNotIn("no harvest", r.stdout)

    def test_the_seal_does_not_warn_when_the_harvest_is_there(self):
        tmp = self.tmp
        self.git("init", "-q")
        self.commit_all("released")
        self.git("tag", f"v{VERSION}")
        (tmp / "docs" / "propuestas").mkdir(parents=True)
        (tmp / "docs" / "propuestas" / "2026-10-25-wmf.md").write_text("# Harvest wmf — 2026-10-25\n")
        self.commit_all("harvest")
        r = run(tmp, "9.8.7")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertNotIn("no harvest", r.stderr)

    def test_a_harvest_a_patch_brought_from_the_minor_branch_still_counts(self):
        """B40: the 0.6.2 patch brought the 0.7 closing harvest with `git checkout <sha> -- <file>`, so the file was
        already in the tag; the commit that added it on the minor's branch is still new since the tag."""
        tmp = self.tmp
        self.git("init", "-q")
        self.commit_all("released")
        self.git("branch", "-M", "main")
        self.git("checkout", "-q", "-b", "minor")
        self.harvest("# Harvest wmf — 2026-10-25")
        self.commit_all("harvest on the minor's branch")
        self.git("checkout", "-q", "main")
        self.git("checkout", "minor", "--", "docs/propuestas/2026-10-23-portal.md")
        self.commit_all("patch with the closing harvest")
        self.git("tag", f"v{VERSION}")
        self.git("checkout", "-q", "minor")
        self.git("merge", "-q", "--no-edit", "main")
        self.assertEqual(run(tmp, "9.8.7").returncode, 0)
        self.fill_entry("9.8.7")
        self.commit_all("bump")
        r = run(tmp, "--release")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_a_harvest_added_only_by_the_patch_does_not_count(self):
        tmp = self.tmp
        self.git("init", "-q")
        self.commit_all("released")
        self.harvest("# Harvest wmf — 2026-10-25")
        self.commit_all("patch with its own harvest")
        self.git("tag", f"v{VERSION}")
        self.assertEqual(run(tmp, "9.8.7").returncode, 0)
        self.fill_entry("9.8.7")
        self.commit_all("bump")
        r = run(tmp, "--release")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("no harvest for 9.8.7", r.stdout)

    def release_with_docs(self, docs, readmes, key=True):
        """A bumped, filled-in, harvested release (9.8.7) whose releaseDocs are `docs` (the key is left out with
        key=False) and whose files are `readmes` ({path: text}), all committed in HEAD."""
        tmp = self.tmp
        self.git("init", "-q")
        self.commit_all("released")
        self.git("tag", f"v{VERSION}")
        self.assertEqual(run(tmp, "9.8.7").returncode, 0)
        self.fill_entry("9.8.7")
        self.harvest()
        if key:
            self.set_gw(releaseDocs=docs)
        for path, text in readmes.items():
            (tmp / path).write_text(text)
        self.commit_all("release")
        return run(tmp, "--release")

    def test_release_docs_must_name_the_version_being_released(self):
        r = self.release_with_docs(["README.md", "README.es.md"],
                                   {"README.md": "Status: `9.8.7`\n", "README.es.md": "Estado: `9.8.7`\n"})
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_a_release_doc_naming_an_old_version_fails_with_the_fix(self):
        r = self.release_with_docs(["README.md", "README.es.md"],
                                   {"README.md": "Status: `9.8.7`\n", "README.es.md": f"Estado: `{VERSION}`\n"})
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("stale release doc: README.es.md does not name `9.8.7`", r.stdout)
        self.assertNotIn("README.md does not", r.stdout)
        self.assertIn("retry: python3 scripts/version.py --release", r.stdout)

    def test_a_version_without_backticks_does_not_count_as_named(self):
        r = self.release_with_docs(["README.md"], {"README.md": "Status: 9.8.7 and `19.8.7`\n"})
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("stale release doc: README.md does not name `9.8.7`", r.stdout)

    def test_a_release_doc_missing_in_head_fails(self):
        r = self.release_with_docs(["README.md", "NOPE.md"], {"README.md": "`9.8.7`\n"})
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("missing release doc: NOPE.md (releaseDocs) is not in HEAD", r.stdout)
        self.set_gw(releaseDocs=["LATE.md"])
        self.commit_all("config only")
        (self.tmp / "LATE.md").write_text("`9.8.7`\n")  # only in the working tree
        self.assertIn("missing release doc: LATE.md", run(self.tmp, "--release").stdout)

    def test_no_release_docs_means_no_check(self):
        r = self.release_with_docs([], {"README.md": f"`{VERSION}`\n"})
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_an_absent_release_docs_key_means_no_check(self):
        r = self.release_with_docs(None, {"README.md": f"`{VERSION}`\n"}, key=False)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def release_harvesting_into(self, folder, gw_keys, uncommitted=None):
        """A release after a tag, with a harvest file added in `folder` and the project's gw.json keys `gw_keys`
        (the path keys are dropped first). `uncommitted`: gw.json keys left only in the working tree."""
        tmp = self.tmp
        gw = tmp / ".claude" / "gw.json"
        base = json.loads(gw.read_text())
        for key in ("proposalsDir", "recordsDir"):
            base.pop(key, None)
        gw.write_text(json.dumps(base))
        self.git("init", "-q")
        self.commit_all("released")
        self.git("tag", f"v{VERSION}")
        self.assertEqual(run(tmp, "9.8.7").returncode, 0)
        self.fill_entry("9.8.7")
        gw.write_text(json.dumps({**base, **gw_keys}))
        (tmp / folder).mkdir(parents=True, exist_ok=True)
        (tmp / folder / "2026-11-02-portal.md").write_text("# Harvest portal \u2014 2026-11-02\n")
        self.commit_all("harvest")
        if uncommitted:
            gw.write_text(json.dumps({**base, **gw_keys, **uncommitted}))
        return run(tmp, "--release")

    def test_harvest_goes_to_the_english_default_folder(self):
        r = self.release_harvesting_into("docs/proposals", {})
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_harvest_in_the_old_folder_is_found_while_the_key_is_absent(self):
        r = self.release_harvesting_into("docs/propuestas", {})
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_harvest_in_the_default_folder_is_not_found_when_the_key_names_another(self):
        r = self.release_harvesting_into("docs/proposals", {"proposalsDir": "docs/ideas"})
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("no docs/ideas/*.md starting with '# Harvest'", r.stdout)

    def test_harvest_folder_is_decided_by_the_released_commit_not_the_working_tree(self):
        r = self.release_harvesting_into("docs/ideas", {"proposalsDir": "docs/ideas"},
                                         uncommitted={"proposalsDir": "docs/other"})
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_release_without_a_valid_config_names_proposals_dir(self):
        r = self.release_harvesting_into("docs/proposals", {"proposalsDir": "/abs"})
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("cannot read proposalsDir", r.stdout)

    def suggest_after(self, tag, *messages, plugin=None):
        """--suggest in a repo tagged `tag` followed by one empty commit per message; plugin.json set to `plugin`."""
        if plugin is None:
            plugin = VERSION
        path = self.tmp / ".claude-plugin" / "plugin.json"
        path.write_text(re.sub(r'("version": ")[^"]*', lambda m: m.group(1) + plugin, path.read_text(), count=1))
        self.git("init", "-q")
        self.commit_all("released")
        self.git("tag", tag)
        for message in messages:
            self.git("commit", "-q", "--allow-empty", "-m", message)
        return run(self.tmp, "--suggest")

    def test_suggest_without_a_tag_says_so_and_suggests_nothing(self):
        self.git("init", "-q")
        self.commit_all("feat: one")
        r = run(self.tmp, "--suggest")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("no vX.Y.Z tag reachable from HEAD", r.stdout)
        self.assertIn("git fetch --tags origin && python3 scripts/version.py --suggest", r.stdout)
        self.assertNotIn("bump,", r.stdout)

    def test_suggest_with_no_commits_since_the_tag(self):
        r = self.suggest_after("v0.4.3")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("0 commit(s) since v0.4.3: no bump suggested", r.stdout)

    def test_suggest_counts_commits_out_of_format_and_suggests_nothing_for_them(self):
        r = self.suggest_after("v0.4.3", "Fix the thing", "docs: words", "chore(x): tidy")
        self.assertIn("3 commit(s) since v0.4.3, 1 not in the type(scope): text format", r.stdout)
        self.assertIn("no bump suggested", r.stdout)

    def test_suggest_fix_is_a_patch_and_feat_a_minor(self):
        r = self.suggest_after("v1.2.3", "fix(a): b", "perf: c", plugin="1.2.3")
        self.assertIn("patch bump, 1.2.3 -> 1.2.4", r.stdout)
        self.assertIn("warning: plugin.json 1.2.3 is behind the suggested 1.2.4; bump it: python3 scripts/version.py 1.2.4",
                      r.stdout)
        self.git("commit", "-q", "--allow-empty", "-m", "feat: d")
        self.assertIn("minor bump, 1.2.3 -> 1.3.0", run(self.tmp, "--suggest").stdout)

    def test_suggest_hotfix_is_a_patch(self):
        r = self.suggest_after("v0.5.1", "hotfix(D69): urgent fix", "docs: words", plugin="0.5.1")
        self.assertIn("2 commit(s) since v0.5.1: patch bump, 0.5.1 -> 0.5.2", r.stdout)
        self.assertNotIn("not in the type(scope): text format", r.stdout)

    def test_suggest_patch_types_come_from_the_config_and_default_to_fix_hotfix_perf(self):
        self.set_gw(patchCommitTypes=["fix"])
        r = self.suggest_after("v0.4.3", "perf: c", plugin="0.4.3")
        self.assertIn("no bump suggested", r.stdout, "perf is not a patch type here")
        shutil.rmtree(self.tmp / ".git", True)
        self.set_gw(patchCommitTypes=None)
        r = self.suggest_after("v0.4.3", "perf: c", plugin="0.4.3")
        self.assertIn("patch bump, 0.4.3 -> 0.4.4", r.stdout, "the default keeps perf as a patch")

    def test_suggest_reads_the_commit_types_and_the_wip_prefix_of_the_config(self):
        self.set_gw(commitTypes=["feat", "fix"], commitWipPrefix="RED: ")
        r = self.suggest_after("v0.4.3", "perf: c", "RED: fix: d", "WIP: fix: e", plugin="0.4.3")
        self.assertIn("3 commit(s) since v0.4.3, 2 not in", r.stdout)
        self.assertIn("patch bump, 0.4.3 -> 0.4.4", r.stdout)
        self.assertIn("2 not in the type(scope): text format", r.stdout, "perf is no type here; WIP: is no prefix here")

    def test_suggest_with_an_empty_wip_prefix_accepts_none(self):
        self.set_gw(commitWipPrefix="")
        r = self.suggest_after("v0.4.3", "WIP: fix: a", plugin="0.4.3")
        self.assertIn("1 not in the type(scope): text format", r.stdout)

    def test_suggest_with_an_unreadable_config_says_which_keys_it_could_not_read(self):
        (self.tmp / ".claude" / "gw.json").write_text("{not json")
        r = self.suggest_after("v0.4.3", "fix: a", plugin="0.4.3")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("cannot read commitTypes and patchCommitTypes", r.stderr)

    def test_suggest_breaking_is_a_minor_in_0x_and_a_major_from_1_0(self):
        for tag, expected in (("v0.4.3", "minor bump, 0.4.3 -> 0.5.0"), ("v1.2.3", "major bump, 1.2.3 -> 2.0.0")):
            for message in ("feat!: x", "fix(core)!: x", "fix: x\n\nBREAKING CHANGE: the format changes"):
                with self.subTest(tag=tag, message=message):
                    shutil.rmtree(self.tmp / ".git", True)
                    r = self.suggest_after(tag, message)
                    self.assertIn(expected, r.stdout)

    def test_suggest_ignores_merge_commits_and_reads_wip_prefixed_ones(self):
        self.git("init", "-q")
        self.commit_all("released")
        self.git("tag", "v0.4.3")
        self.git("checkout", "-q", "-b", "side")
        self.git("commit", "-q", "--allow-empty", "-m", "WIP: fix: on the side")
        self.git("checkout", "-q", "-")
        self.git("merge", "-q", "--no-ff", "side", "-m", "feat!: merge text that must be ignored")
        r = run(self.tmp, "--suggest")
        self.assertIn("1 commit(s) since v0.4.3: patch bump, 0.4.3 -> 0.4.4", r.stdout)

    def test_suggest_compares_with_plugin_json(self):
        cases = (("0.4.4", "is already at the suggested 0.4.4"), ("0.9.0", "is ahead of the suggested 0.4.4"),
                 ("0.4.3", "is behind the suggested 0.4.4"))
        for plugin, text in cases:
            with self.subTest(plugin=plugin):
                shutil.rmtree(self.tmp / ".git", True)
                r = self.suggest_after("v0.4.3", "fix: a", plugin=plugin)
                self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
                self.assertIn(f"warning: plugin.json", r.stdout)
                self.assertIn(text, r.stdout)

    def test_release_prints_the_suggestion_as_a_warning_without_changing_its_exit_code(self):
        self.git("init", "-q")
        self.commit_all("released")
        self.git("tag", f"v{VERSION}")
        self.git("commit", "-q", "--allow-empty", "-m", "feat: x")
        r = run(self.tmp, "--release")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("warning: suggest: 1 commit(s) since", r.stdout)
        self.assertIn("minor bump", r.stdout)

    def test_suggest_with_a_prerelease_tag_or_plugin_version_does_not_pretend(self):
        r = self.suggest_after("v1.2.3-rc1", "fix: a")
        self.assertIn("no vX.Y.Z tag reachable", r.stdout)
        shutil.rmtree(self.tmp / ".git", True)
        r = self.suggest_after("v0.4.3", "fix: a", plugin="0.4.3-rc1")
        self.assertIn("is not X.Y.Z", r.stdout)
        self.assertNotIn("is behind", r.stdout)
        self.assertIn("python3 scripts/version.py 0.4.4", r.stdout)

    def test_release_keeps_the_missing_tag_line_of_the_suggestion_when_an_odd_tag_exists(self):
        self.git("init", "-q")
        self.commit_all("one")
        self.git("tag", "v1")
        r = run(self.tmp, "--release")
        self.assertIn("warning: suggest: no vX.Y.Z tag reachable", r.stdout)

    def test_release_on_the_tagged_commit_itself_passes(self):
        self.git("init", "-q")
        self.commit_all("first release")
        self.git("tag", f"v{VERSION}")  # the only tag, on HEAD: nothing changed since it
        r = run(self.tmp, "--release")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_release_without_an_earlier_tag_fails_closed(self):
        self.git("init", "-q")
        self.commit_all("one")
        (self.tmp / "README.md").write_text("x\n"); self.commit_all("two")
        r = run(self.tmp, "--release")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("git fetch --tags origin", r.stdout)

    def test_bump_moves_every_marker_and_adds_a_changelog_entry(self):
        tmp = self.tmp
        r = run(tmp, "9.8.7")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(run(tmp).returncode, 0, run(tmp).stdout)
        self.assertIn('"version": "9.8.7"', (tmp / ".claude-plugin" / "plugin.json").read_text())
        self.assertIn('"version": "9.8.7"', (tmp / "templates" / "gw.json").read_text())
        self.assertIn("## [9.8.7] - Unreleased", (tmp / "CHANGELOG.md").read_text())
        self.assertIn('version: "9.8.7"', (tmp / "skills" / "gw-selector" / "SKILL.md").read_text())
        self.assertIn("galivelop-workflow v9.8.7", (tmp / "scripts" / "config.py").read_text())

    def test_bump_leaves_the_installed_config_alone(self):
        installed = (self.tmp / ".claude" / "gw.json").read_bytes()
        self.assertEqual(run(self.tmp, "9.8.7").returncode, 0)
        self.assertEqual((self.tmp / ".claude" / "gw.json").read_bytes(), installed)

    def test_resync_fixes_every_stale_marker_and_templates_gw_json_in_one_go(self):
        tmp = self.tmp
        gw = tmp / "templates" / "gw.json"
        gw.write_text(gw.read_text().replace(f'"version": "{VERSION}"', '"version": "0.0.9"', 1))
        for rel, old in (("scripts/config.py", "0.0.1"), ("scripts/doctor.py", "0.0.2"), ("schema/gw.schema.json", "0.0.3")):
            path = tmp / rel
            path.write_text(path.read_text().replace(f"galivelop-workflow v{VERSION}", f"galivelop-workflow v{old}", 1))
        skill = tmp / "skills" / "gw-selector" / "SKILL.md"
        skill.write_text(skill.read_text().replace(f'version: "{VERSION}"', 'version: "0.0.4"', 1))
        r = run(tmp)
        self.assertEqual(r.returncode, 1)
        for name in ("templates/gw.json", "config.py", "doctor.py", "gw.schema.json", "SKILL.md"):
            self.assertIn(name, r.stdout)
        r = run(tmp, VERSION)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        r = run(tmp)
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_only_real_markers_count_and_bytes_are_kept(self):
        tmp = self.tmp
        prose = tmp / "scripts" / "prose.py"
        prose.write_bytes(f"# galivelop-workflow v{VERSION}\r\n\r\n\r\n\r\n\r\n"
                          "# an example: galivelop-workflow v0.0.1\r\n".encode())
        body = tmp / "skills" / "extra" / "SKILL.md"
        body.parent.mkdir()
        body.write_text(f'---\nname: extra\nmetadata:\n  version: "{VERSION}"\n---\n\nExample:\n\n'
                        'metadata:\n  version: "0.0.2"\n')
        latin = tmp / "templates" / "latin.txt"
        latin.write_bytes(b"# galivelop-workflow v0.0.3\n# caf\xe9\n")
        latin_bytes = latin.read_bytes()
        r = run(tmp)
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertNotIn("prose.py", r.stdout)
        self.assertNotIn("extra", r.stdout)
        self.assertIn("latin.txt: not UTF-8", r.stdout)
        r = run(tmp, "9.8.7")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("skipped templates/latin.txt", r.stderr)
        self.assertEqual(latin.read_bytes(), latin_bytes)
        self.assertEqual(prose.read_bytes(), b"# galivelop-workflow v9.8.7\r\n\r\n\r\n\r\n\r\n"
                                             b"# an example: galivelop-workflow v0.0.1\r\n")
        text = body.read_text()
        self.assertIn('metadata:\n  version: "9.8.7"\n---', text)
        self.assertTrue(text.endswith('version: "0.0.2"\n'))

    def test_skill_version_is_read_the_same_by_apply_and_version_py(self):
        tmp = self.tmp
        crlf = tmp / "skills" / "crlf" / "SKILL.md"
        crlf.parent.mkdir()
        crlf.write_bytes(f"---\r\nname: crlf\r\nmetadata:\r\n  version: \"{VERSION}\"\r\n---\r\n\r\nBody\r\n".encode())
        note = tmp / "skills" / "note" / "SKILL.md"
        note.parent.mkdir()
        note.write_text(f"---\nname: note\nmetadata:\n  version: {VERSION}  # note\n---\n\nBody\n")
        spec = importlib.util.spec_from_file_location("apply_under_test", ROOT / "scripts" / "apply.py")
        apply_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(apply_module)
        self.assertEqual(apply_module.skill_version(crlf), VERSION)
        self.assertEqual(apply_module.skill_version(note), VERSION)
        r = run(tmp)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(run(tmp, "9.8.7").returncode, 0)
        self.assertIn(b'  version: "9.8.7"\r\n---\r\n', crlf.read_bytes())
        self.assertIn("  version: 9.8.7  # note\n", note.read_text())

    def test_a_workflow_file_without_a_marker_is_flagged(self):
        tmp = self.tmp
        (tmp / "scripts" / "nuevo.sh").write_text("#!/usr/bin/env bash\necho hi\n")
        (tmp / "templates" / "es" / "NUEVO.md").write_text("# Nuevo\n")
        skill = tmp / "skills" / "bare" / "SKILL.md"
        skill.parent.mkdir()
        skill.write_text("---\nname: bare\n---\n\nBody\n")
        (tmp / "skills" / "bare" / "notes.md").write_text("owned through its SKILL.md: no header needed\n")
        r = run(tmp)
        self.assertEqual(r.returncode, 1, r.stdout)
        for rel in ("scripts/nuevo.sh", "templates/es/NUEVO.md", "skills/bare/SKILL.md"):
            self.assertIn(f"missing marker: {rel}", r.stdout)
        self.assertNotIn("notes.md", r.stdout)
        self.assertNotIn("templates/claude/settings.json", r.stdout)

    def test_bump_touches_only_the_top_level_json_version(self):
        tmp = self.tmp
        for rel in ("templates/gw.json", ".claude-plugin/plugin.json"):
            path = tmp / rel
            data = json.loads(path.read_text())
            data = dict({"$schema": "x", "nested": {"version": "keep-me"}}, **data)
            path.write_text(json.dumps(data, indent=2) + "\n")
        self.assertEqual(run(tmp, "9.8.7").returncode, 0)
        for rel in ("templates/gw.json", ".claude-plugin/plugin.json"):
            data = json.loads((tmp / rel).read_text())
            self.assertEqual(data["version"], "9.8.7", rel)
            self.assertEqual(data["nested"], {"version": "keep-me"}, rel)

    def test_bump_fails_loudly_without_a_top_level_version_or_a_changelog_heading(self):
        tmp = self.tmp
        gw = tmp / "templates" / "gw.json"
        original = gw.read_text()
        data = json.loads(original)
        del data["version"]
        gw.write_text(json.dumps(data, indent=2) + "\n")
        plugin_before = (tmp / ".claude-plugin" / "plugin.json").read_bytes()
        r = run(tmp, "9.8.7")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn('templates/gw.json has no top-level "version"', r.stderr)
        self.assertIn("python3 scripts/version.py 9.8.7", r.stderr)
        self.assertEqual((tmp / ".claude-plugin" / "plugin.json").read_bytes(), plugin_before, "nothing written")
        gw.write_text(original)
        (tmp / "CHANGELOG.md").write_text("# Changelog\n\nNo entries yet.\n")
        r = run(tmp, "9.8.7")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("CHANGELOG.md has no `## [x.y.z]` heading", r.stderr)
        self.assertEqual((tmp / ".claude-plugin" / "plugin.json").read_bytes(), plugin_before, "nothing written")

    def test_not_semver_is_refused(self):
        self.assertEqual(run(ROOT, "1.2").returncode, 2)


class Fragments(unittest.TestCase):
    """D68: CHANGELOG fragments per branch, folded into the version's entry and deleted."""
    setUp, set_gw, git, commit_all = Version.setUp, Version.set_gw, Version.git, Version.commit_all
    ES_EN = "### ES\n\n- {0} es.\n\n### EN\n\n- {0} en.\n"

    def frag(self, name, text=None, directory="changelog.d"):
        path = self.tmp / directory / name
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(text, bytes):
            path.write_bytes(text)
        else:
            path.write_text(self.ES_EN.format(name) if text is None else text)
        return path

    def entry(self, version):
        text = (self.tmp / "CHANGELOG.md").read_text()
        start = text.index(f"## [{version}]")
        nxt = text.find("\n## [", start + 1)
        return text[start:nxt if nxt != -1 else None]

    def tag_old(self):
        """A reachable vX.Y.Z tag of an older release, so the fold can tell the version is not released."""
        self.git("add", "-A")
        self.git("commit", "-q", "--allow-empty", "-m", "base")
        self.git("tag", "v0.0.1")

    def bump(self):
        if subprocess.run(["git", "-C", str(self.tmp), "tag", "--list", "v*"], capture_output=True,
                          text=True).stdout == "":
            self.tag_old()
        r = run(self.tmp, "9.8.7")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        return r

    def test_bump_folds_two_fragments_sorted_into_the_new_entry_and_deletes_them(self):
        b = self.frag("agent-D2-b.md"); a = self.frag("agent-D1-a.md"); readme = self.frag("README.md", "# about\n")
        before = (self.tmp / "CHANGELOG.md").read_text()
        r = self.bump()
        self.assertIn("folded changelog.d/agent-D1-a.md into the CHANGELOG entry of 9.8.7", r.stdout)
        self.assertEqual(self.entry("9.8.7"), "## [9.8.7] - Unreleased\n\n### ES\n\n- agent-D1-a.md es.\n"
                         "- agent-D2-b.md es.\n\n### EN\n\n- agent-D1-a.md en.\n- agent-D2-b.md en.\n")
        self.assertFalse(a.exists() or b.exists())
        self.assertTrue(readme.exists(), "README.md is not a fragment")
        self.assertTrue((self.tmp / "CHANGELOG.md").read_text().endswith(before[before.index("## ["):]),
                        "older entries untouched")

    def test_fold_appends_to_the_current_entry_after_its_notes(self):
        self.bump()
        log = self.tmp / "CHANGELOG.md"
        log.write_text(log.read_text().replace("- (por completar)", "- Ya.", 1).replace("- (to be filled in)", "- Was.", 1))
        self.frag("x.md")
        r = run(self.tmp, "--fold")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(self.entry("9.8.7"), "## [9.8.7] - Unreleased\n\n### ES\n\n- Ya.\n- x.md es.\n\n### EN\n\n"
                         "- Was.\n- x.md en.\n")

    def test_no_fragments_is_a_no_op(self):
        before = (self.tmp / "CHANGELOG.md").read_text()
        r = run(self.tmp, "--fold")
        self.assertEqual((r.returncode, r.stdout.strip()), (0, "no CHANGELOG fragments to fold"), r.stderr)
        (self.tmp / "changelog.d").mkdir(); (self.tmp / "changelog.d" / ".gitkeep").write_text("")
        r = run(self.tmp, "--fold")
        self.assertEqual((r.returncode, r.stdout.strip()), (0, "no CHANGELOG fragments to fold"), r.stderr)
        self.assertEqual((self.tmp / "CHANGELOG.md").read_text(), before)

    def test_a_malformed_fragment_fails_with_its_reason_and_nothing_changes(self):
        cases = (("### ES\n\n- a\n", "needs exactly the headings '### ES' then '### EN' (found: '### ES')"),
                 ("### EN\n\n- a\n\n### ES\n\n- b\n", "(found: '### EN', '### ES')"),
                 ("### ES\n\n### EN\n\n- a\n", "its ### ES section is empty"),
                 ("### ES\n\n- a\n\n### EN\n\n\n", "its ### EN section is empty"),
                 ("intro\n### ES\n- a\n### EN\n- b\n", "text before '### ES'"),
                 ("### ES\n- a\n## [1.0.0]\n### EN\n- b\n", "'## [1.0.0]'"),
                 (b"### ES\n- \xe9\n### EN\n- b\n", "not UTF-8"))
        for text, reason in cases:
            with self.subTest(reason=reason):
                good = self.frag("a-good.md"); bad = self.frag("b-bad.md", text)
                before = (self.tmp / "CHANGELOG.md").read_text()
                for args in (["--fold"], ["9.8.7"]):
                    r = run(self.tmp, *args)
                    self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
                    self.assertIn("changelog.d/b-bad.md", r.stderr)
                    self.assertIn(reason, r.stderr)
                    self.assertIn("retry", r.stderr)
                    self.assertEqual((self.tmp / "CHANGELOG.md").read_text(), before)
                    self.assertTrue(good.exists() and bad.exists(), "all or nothing")
                self.assertIn(f'"version": "{VERSION}"', (self.tmp / ".claude-plugin" / "plugin.json").read_text(),
                              "the bump wrote nothing")
                bad.unlink()

    def test_a_file_that_is_not_a_md_fragment_fails(self):
        self.frag("notes.txt", "x\n")
        r = run(self.tmp, "--fold")
        self.assertEqual(r.returncode, 1)
        self.assertIn("changelog.d/notes.txt is not a CHANGELOG fragment", r.stderr)

    def test_an_entry_without_its_en_section_fails(self):
        self.bump()
        log = self.tmp / "CHANGELOG.md"
        log.write_text(log.read_text().replace("### EN\n\n- (to be filled in)\n", "", 1))
        self.frag("x.md")
        r = run(self.tmp, "--fold")
        self.assertEqual(r.returncode, 1)
        self.assertIn("the CHANGELOG entry of 9.8.7 has no ### EN section", r.stderr)
        self.assertTrue((self.tmp / "changelog.d" / "x.md").exists())

    def test_fold_refuses_a_released_version(self):
        self.commit_all("released")
        self.git("tag", f"v{VERSION}")
        self.frag("x.md")
        r = run(self.tmp, "--fold")
        self.assertEqual(r.returncode, 1)
        self.assertIn(f"{VERSION} is already released (tag v{VERSION})", r.stderr)
        self.assertIn("python3 scripts/version.py X.Y.Z", r.stderr)

    def test_release_fails_while_head_has_fragments(self):
        self.frag("README.md", "# about\n")
        self.commit_all("released")
        self.git("tag", f"v{VERSION}")
        self.assertEqual(run(self.tmp, "--release").returncode, 0, "README.md is not a fragment")
        self.frag("agent-D1-a.md"); self.commit_all("notes")
        r = run(self.tmp, "--release")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("unfolded CHANGELOG fragments in HEAD: changelog.d/agent-D1-a.md", r.stdout)
        self.assertIn("python3 scripts/version.py --fold", r.stdout)

    def test_off_switch_and_custom_directory(self):
        self.set_gw(changelogFragments=False)
        self.frag("x.md")
        before = (self.tmp / "CHANGELOG.md").read_text()
        self.assertEqual(run(self.tmp, "--fold").stdout.strip(), "no CHANGELOG fragments to fold")
        self.assertEqual((self.tmp / "CHANGELOG.md").read_text(), before)
        self.commit_all("x"); self.git("tag", f"v{VERSION}")
        self.assertNotIn("unfolded", run(self.tmp, "--release").stdout)
        self.set_gw(changelogFragments=None, changelogFragmentsDir="notes/next")
        self.git("tag", "-d", f"v{VERSION}")
        self.git("tag", "v0.0.1")
        moved = self.frag("y.md", directory="notes/next")
        self.assertEqual(run(self.tmp, "--fold").returncode, 0)
        self.assertFalse(moved.exists())
        self.assertTrue((self.tmp / "changelog.d" / "x.md").exists(), "the old directory is no longer read")
        self.assertIn("- y.md es.", self.entry(VERSION))

    def test_fragments_of_two_branches_merge_without_conflicts_and_fold(self):
        self.commit_all("base")
        self.git("checkout", "-qb", "agent/D1-a"); self.frag("agent-D1-a.md"); self.commit_all("a")
        self.git("checkout", "-q", "-"); self.git("checkout", "-qb", "agent/D2-b")
        self.frag("agent-D2-b.md"); self.commit_all("b")
        self.git("merge", "-q", "--no-ff", "-m", "m", "agent/D1-a")  # check=True: a conflict fails here
        self.bump()
        self.assertIn("- agent-D1-a.md es.\n- agent-D2-b.md es.", self.entry("9.8.7"))

    def test_a_crlf_changelog_keeps_its_line_endings(self):
        log = self.tmp / "CHANGELOG.md"
        log.write_bytes(log.read_bytes().replace(b"\n", b"\r\n"))
        self.frag("x.md")
        self.bump()
        data = log.read_bytes()
        self.assertNotIn(b"\n", data.replace(b"\r\n", b""))
        self.assertIn(b"- x.md en.\r\n", data)

    def test_fold_and_bump_fail_closed_in_a_clone_without_tags(self):  # Findings 1
        self.commit_all("released, tags not fetched")
        self.frag("x.md")
        before = (self.tmp / "CHANGELOG.md").read_text()
        for args, retry in ((["--fold"], "python3 scripts/version.py --fold"),
                            (["9.8.7"], "python3 scripts/version.py 9.8.7")):
            r = run(self.tmp, *args)
            self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
            self.assertIn("no vX.Y.Z tag reachable from HEAD", r.stderr)
            self.assertIn(f"git fetch --tags origin && {retry}", r.stderr)
            self.assertEqual((self.tmp / "CHANGELOG.md").read_text(), before)
            self.assertTrue((self.tmp / "changelog.d" / "x.md").exists())

    def test_bump_to_a_released_version_is_refused(self):  # Findings 2
        self.commit_all("old"); self.git("tag", "v0.4.0")
        before = (self.tmp / "CHANGELOG.md").read_text()
        for with_fragment in (False, True):
            if with_fragment:
                self.frag("x.md")
            r = run(self.tmp, "0.4.0")
            self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
            self.assertIn("0.4.0 is already released (tag v0.4.0)", r.stderr)
            self.assertEqual((self.tmp / "CHANGELOG.md").read_text(), before)
            self.assertIn(f'"version": "{VERSION}"', (self.tmp / ".claude-plugin" / "plugin.json").read_text())

    def test_hidden_files_are_not_fragments(self):  # Findings 3
        self.frag(".DS_Store", b"\x00\x01")
        self.assertEqual(run(self.tmp, "--fold").stdout.strip(), "no CHANGELOG fragments to fold")
        self.frag("x.md")
        self.bump()
        self.assertTrue((self.tmp / "changelog.d" / ".DS_Store").exists())
        self.commit_all("with .DS_Store"); self.git("tag", "v9.8.7")
        self.assertNotIn("unfolded", run(self.tmp, "--release").stdout)


if __name__ == "__main__":
    unittest.main()
