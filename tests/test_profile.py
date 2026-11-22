"""scripts/profile.py (E4, Q-30): list, new, assign, role and show over the `profiles` block of .claude/gw.json and the
profile files. Every failing case checks the message, not only the exit code.
"""
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from test_hooks import BASE_CONFIG, ROOT

MAIL = "Ana.Lopez@Example.com"
HASH = hashlib.sha256(MAIL.strip().lower().encode()).hexdigest()


class Cli(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="gw-profile-")).resolve()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        subprocess.run(["git", "init", "-q", str(self.tmp)], check=True)
        (self.tmp / ".claude").mkdir()
        self.config = self.tmp / ".claude" / "gw.json"
        self.write(dict(BASE_CONFIG))
        self.dir = self.tmp / ".claude" / "gw" / "profiles"

    def write(self, data):
        self.config.write_text(json.dumps(data, indent=2) + "\n")

    def profile(self, name, data="{}\n"):
        self.dir.mkdir(parents=True, exist_ok=True)
        (self.dir / f"{name}.json").write_text(data)

    def run_cli(self, *args, ci=False):
        env = {k: v for k, v in os.environ.items() if k != "CI"}
        env["GIT_CONFIG_GLOBAL"] = os.devnull
        if ci:
            env["CI"] = "true"
        r = subprocess.run([sys.executable, "-B", str(ROOT / "scripts" / "profile.py"), "--root", str(self.tmp), *args],
                           capture_output=True, text=True, env=env)
        return r.returncode, r.stdout, r.stderr

    def block(self):
        return json.loads(self.config.read_text()).get("profiles")

    def fails(self, *args, reason, **kw):
        code, out, err = self.run_cli(*args, **kw)
        self.assertEqual(code, 2, (out, err))
        self.assertIn(reason, err)
        return err


class New(Cli):
    def test_creates_an_empty_profile_and_the_folder(self):
        code, out, err = self.run_cli("new", "admin")
        self.assertEqual(code, 0, err)
        self.assertEqual(json.loads((self.dir / "admin.json").read_text()), {})
        self.assertFalse(list(self.dir.glob("*.tmp")))

    def test_from_copies_the_other_byte_for_byte(self):
        self.profile("base", '{ "logSize":\t5000 }\r\n')
        self.assertEqual(self.run_cli("new", "copy", "--from", "base")[0], 0)
        self.assertEqual((self.dir / "copy.json").read_bytes(), (self.dir / "base.json").read_bytes())

    def test_existing_profile_is_refused_and_kept(self):
        self.profile("admin", '{"a": 1}')
        err = self.fails("new", "admin", reason="profile `admin` already exists")
        self.assertIn("new <name>", err)
        self.assertEqual((self.dir / "admin.json").read_text(), '{"a": 1}')

    def test_invalid_names(self):
        for bad in ("../x", "_a", "a b", ".hidden", "a/b"):
            with self.subTest(bad):
                self.fails("new", bad, reason="invalid profile name")
        self.assertFalse(self.dir.exists())

    def test_unknown_source(self):
        self.fails("new", "x", "--from", "nope", reason="unknown profile `nope`")
        self.assertFalse((self.dir / "x.json").exists())

    def test_custom_dir(self):
        self.write(dict(BASE_CONFIG, profiles={"dir": "p/x"}))
        self.assertEqual(self.run_cli("new", "a")[0], 0)
        self.assertTrue((self.tmp / "p" / "x" / "a.json").is_file())


class Role(Cli):
    def test_maps_a_role_creating_the_block(self):
        self.profile("admin")
        code, out, err = self.run_cli("role", "boss", "admin")
        self.assertEqual(code, 0, err)
        self.assertEqual(self.block()["roles"], {"boss": "admin"})

    def test_changes_an_existing_mapping(self):
        self.profile("a")
        self.profile("b")
        self.run_cli("role", "boss", "a")
        self.run_cli("role", "boss", "b")
        self.assertEqual(self.block()["roles"], {"boss": "b"})

    def test_unknown_profile(self):
        err = self.fails("role", "boss", "ghost", reason="unknown profile `ghost`")
        self.assertIn("profile.py new ghost", err)
        self.assertNotIn("profiles", json.loads(self.config.read_text()))

    def test_invalid_role_name(self):
        self.profile("a")
        self.fails("role", "bo ss", "a", reason="invalid role name")


class Assign(Cli):
    def setUp(self):
        super().setUp()
        self.profile("admin")
        self.profile("mine")
        self.run_cli("role", "boss", "admin")

    def test_writes_the_hash_never_the_address(self):
        code, out, err = self.run_cli("assign", MAIL, "--role", "boss")
        self.assertEqual(code, 0, err)
        self.assertEqual(self.block()["people"], {HASH: {"role": "boss"}})
        for text in (self.config.read_text(), out, err):
            self.assertNotIn("example.com", text.lower())
            self.assertNotIn("ana", text.lower().replace("assign", ""))
        self.assertNotIn(HASH, out)  # only a shortened hash is shown

    def test_spaces_and_case_give_the_same_hash(self):
        self.run_cli("assign", "  ana.lopez@example.COM \n", "--role", "boss")
        self.assertEqual(list(self.block()["people"]), [HASH])

    def test_profile_and_role_combined_and_merged_on_reassign(self):
        self.run_cli("assign", MAIL, "--role", "boss")
        self.assertEqual(self.run_cli("assign", MAIL, "--profile", "mine")[0], 0)
        self.assertEqual(self.block()["people"][HASH], {"role": "boss", "profile": "mine"})

    def test_neither_role_nor_profile(self):
        err = self.fails("assign", MAIL, reason="assign needs --role or --profile")
        self.assertIn("assign <email> --role <role>", err)

    def test_unknown_profile(self):
        self.fails("assign", MAIL, "--profile", "ghost", reason="unknown profile `ghost`")
        self.assertNotIn("people", self.block())

    def test_role_without_a_profile(self):
        err = self.fails("assign", MAIL, "--role", "intern", reason="role `intern` has no profile in profiles.roles")
        self.assertIn("profile.py role intern <profile>", err)

    def test_not_an_email(self):
        self.fails("assign", "ana", "--role", "boss", reason="is not an e-mail address")
        self.fails("assign", "   ", "--role", "boss", reason="is not an e-mail address")


class Show(Cli):
    def setUp(self):
        super().setUp()
        self.profile("admin")
        self.profile("mine")
        self.run_cli("role", "boss", "admin")
        self.run_cli("assign", MAIL, "--role", "boss")
        self.run_cli("assign", "own@example.org", "--profile", "mine")
        self.run_cli("assign", "both@example.org", "--role", "boss", "--profile", "mine")

    def test_role_layer(self):
        code, out, err = self.run_cli("show", MAIL)
        self.assertEqual(code, 0, err)
        self.assertIn("profile admin, layer role (role boss)", out)

    def test_person_layer(self):
        self.assertIn("profile mine, layer person", self.run_cli("show", "own@example.org")[1])
        self.assertIn("layer person, over role boss -> admin", self.run_cli("show", "both@example.org")[1])

    def test_default_layer(self):
        self.assertIn("layer default (no assignment)", self.run_cli("show", "nobody@example.org")[1])

    def test_default_email_is_git_user_email(self):
        subprocess.run(["git", "-C", str(self.tmp), "config", "user.email", MAIL], check=True)
        self.assertIn("layer role", self.run_cli("show")[1])

    def test_no_email_at_all(self):
        code, out, err = self.run_cli("show")
        self.assertEqual(code, 0, err)
        self.assertIn("layer default", out)

    def test_ci_forces_default(self):
        code, out, err = self.run_cli("show", MAIL, ci=True)
        self.assertEqual(code, 0, err)
        self.assertIn("CI always runs with the default", out)
        self.assertNotIn("layer role", out)

    def test_does_not_print_the_address(self):
        self.assertNotIn("example.com", self.run_cli("show", MAIL)[1].lower())


class List(Cli):
    def test_empty_config_without_a_profiles_block(self):
        code, out, err = self.run_cli("list")
        self.assertEqual(code, 0, err)
        self.assertIn("profiles: none", out)
        self.assertIn("roles: none", out)

    def test_counts_per_role_and_profile_with_short_hashes(self):
        self.profile("admin")
        self.profile("mine")
        self.run_cli("role", "boss", "admin")
        self.run_cli("role", "ghost", "admin")
        self.run_cli("assign", MAIL, "--role", "boss")
        self.run_cli("assign", "own@example.org", "--profile", "mine")
        code, out, err = self.run_cli("list")
        self.assertEqual(code, 0, err)
        self.assertIn("profiles: admin, mine", out)
        self.assertIn(f"boss -> admin: 1 people ({HASH[:8]})", out)
        self.assertIn("ghost -> admin: 0 people", out)
        self.assertIn("mine: 1 people (", out)
        self.assertNotIn(HASH, out)
        self.assertNotIn("example.com", out.lower())

    def test_role_pointing_to_a_missing_file_is_flagged(self):
        self.write(dict(BASE_CONFIG, profiles={"roles": {"boss": "gone"}}))
        self.assertIn("boss -> gone (missing on disk)", self.run_cli("list")[1])


class Review(Cli):
    """The findings of the review of chunk 2a, one test each."""

    def test_new_fixes_the_executors_own_missing_profile(self):  # 1
        self.profile("admin")
        self.run_cli("role", "boss", "admin")
        subprocess.run(["git", "-C", str(self.tmp), "config", "user.email", MAIL], check=True)
        self.run_cli("assign", MAIL, "--profile", "admin")
        (self.dir / "admin.json").unlink()
        code, out, err = self.run_cli("new", "admin")
        self.assertEqual(code, 0, err)
        self.assertTrue((self.dir / "admin.json").is_file())

    def test_role_fixes_the_executors_missing_role_profile(self):  # 1
        self.profile("admin")
        self.run_cli("role", "boss", "admin")
        subprocess.run(["git", "-C", str(self.tmp), "config", "user.email", MAIL], check=True)
        self.run_cli("assign", MAIL, "--role", "boss")
        raw = json.loads(self.config.read_text())
        del raw["profiles"]["roles"]["boss"]
        self.write(raw)
        self.profile("other")
        self.assertEqual(self.run_cli("list")[0], 0)
        self.assertEqual(self.run_cli("role", "boss", "other")[0], 0)

    def test_role_with_an_invalid_profile_is_refused_even_in_ci(self):  # 2
        self.profile("bad", '{"version": "9"}')
        for ci in (False, True):
            with self.subTest(ci=ci):
                err = self.fails("role", "dev", "bad", reason="a profile cannot change what is installed", ci=ci)
                self.assertIn("config.py profile", err)
        self.assertNotIn("profiles", json.loads(self.config.read_text()))

    def test_assign_with_an_invalid_profile_is_refused(self):  # 2
        self.profile("bad", '{"nope": 1}')
        self.fails("assign", MAIL, "--profile", "bad", reason="unknown key 'nope'")
        self.assertNotIn("profiles", json.loads(self.config.read_text()))

    def test_assign_does_not_keep_a_retired_role(self):  # 3
        self.profile("admin")
        self.profile("mine")
        self.run_cli("role", "qa", "admin")
        self.run_cli("assign", MAIL, "--role", "qa")
        raw = json.loads(self.config.read_text())
        del raw["profiles"]["roles"]["qa"]
        self.write(raw)
        err = self.fails("assign", MAIL, "--profile", "mine", reason="role `qa` this person already has")
        self.assertIn("profile.py role qa <profile>", err)

    def test_docstring_says_the_guard_asks(self):  # 4 (E4 chunk 2b-guard: the guard is done)
        text = (ROOT / "scripts" / "profile.py").read_text()
        self.assertIn("config-guard.py asks the user before an agent runs `new`, `assign` or `role`", text)
        self.assertNotIn("is pending, E4 chunk 2b", text)

    def test_show_with_a_missing_profile_fails_with_its_own_message(self):  # 5
        self.profile("mine")
        self.run_cli("assign", MAIL, "--profile", "mine")
        (self.dir / "mine.json").unlink()
        err = self.fails("show", MAIL, reason="unknown profile `mine`")
        self.assertNotIn("nothing was changed", err)
        self.assertIn("gw profile show:", err)

    def test_show_with_a_role_without_profile_fails_with_its_own_message(self):  # 5
        self.profile("a")
        self.run_cli("role", "qa", "a")
        self.run_cli("assign", MAIL, "--role", "qa")
        raw = json.loads(self.config.read_text())
        del raw["profiles"]["roles"]["qa"]
        self.write(raw)
        err = self.fails("show", MAIL, reason="has no profile in profiles.roles")
        self.assertNotIn("nothing was changed", err)

    def test_email_needs_a_local_part_and_a_domain(self):  # 6
        self.profile("a")
        for bad in ("@", "a@", "@b.c", "a@b@c", "a b@c.d"):
            with self.subTest(bad):
                self.fails("assign", bad, "--profile", "a", reason="is not an e-mail address")
        self.assertEqual(self.run_cli("assign", "a@b", "--profile", "a")[0], 0)

    def test_profile_dir_default_comes_from_the_schema(self):  # 7
        self.assertNotIn(".claude/gw/profiles", (ROOT / "scripts" / "profile.py").read_text())
        self.assertEqual(self.run_cli("new", "z")[0], 0)
        self.assertTrue((self.dir / "z.json").is_file())


class NoConfig(Cli):
    def test_no_config(self):
        self.config.unlink()
        for args in (("list",), ("new", "a"), ("show",), ("role", "r", "a"), ("assign", MAIL, "--role", "r")):
            with self.subTest(args):
                self.fails(*args, reason="not found")

    def test_invalid_config(self):
        self.config.write_text("{not json")
        err = self.fails("list", reason="gw profile:")
        self.assertIn("fix .claude/gw.json, then: python3 profile.py list", err)


class Format(Cli):
    def load(self):
        spec = importlib.util.spec_from_file_location("gw_profile_fmt", ROOT / "scripts" / "profile.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    def test_only_the_edit_changes_in_crlf_tab_compact_files(self):
        mod = self.load()
        text = '{\r\n\t"a": 1,\r\n\t"profiles": {"roles": {"x": "p"}}\r\n}\r\n'
        new = mod.edit_text(text, ["profiles", "people", "h"], {"role": "x"})
        self.assertEqual(json.loads(new)["profiles"], {"roles": {"x": "p"}, "people": {"h": {"role": "x"}}})
        self.assertTrue(new.startswith('{\r\n\t"a": 1,\r\n\t"profiles": {"roles": {"x": "p"}'))
        self.assertTrue(new.endswith("}\r\n"))

    def test_replacing_a_value_touches_only_that_value(self):
        mod = self.load()
        text = '{\n  "profiles": {"roles":   {"x":  "p" ,"y":"q"}},\n  "z": [1,\t2]\n}\n'
        new = mod.edit_text(text, ["profiles", "roles", "x"], "r")
        self.assertEqual(new, text.replace('"p"', '"r"'))

    def test_missing_block_added_after_the_last_key(self):
        mod = self.load()
        self.assertEqual(json.loads(mod.edit_text('{"a": 1}', ["profiles", "roles", "x"], "p")),
                         {"a": 1, "profiles": {"roles": {"x": "p"}}})
        self.assertEqual(json.loads(mod.edit_text("{}", ["profiles", "roles", "x"], "p")),
                         {"profiles": {"roles": {"x": "p"}}})
        self.assertEqual(json.loads(mod.edit_text('{"profiles": {}}', ["profiles", "roles", "x"], "p")),
                         {"profiles": {"roles": {"x": "p"}}})

    def test_cli_keeps_the_file_byte_for_byte_but_the_edit(self):
        self.profile("a")
        text = json.dumps(BASE_CONFIG, indent="\t").replace("\n", "\r\n") + "\r\n"
        self.config.write_bytes(text.encode())
        self.assertEqual(self.run_cli("role", "boss", "a")[0], 0)
        new = self.config.read_bytes().decode()
        self.assertTrue(new.startswith(text[:-5]), new)
        self.assertEqual(json.loads(new)["profiles"], {"roles": {"boss": "a"}})
        self.assertIn(',\r\n\t"profiles": {"roles": {"boss": "a"}}', new)
        self.assertTrue(new.endswith("}\r\n}\r\n") or new.endswith("}\r\n"), new)

    def test_invalid_result_is_rolled_back(self):
        mod = self.load()
        self.profile("a")
        before = self.config.read_bytes()
        real = mod.config.load
        calls = []

        def load(root=None, *a, **k):
            calls.append(1)
            raise mod.config.ConfigError("forced invalid")

        mod.config.load = load
        try:
            with self.assertRaises(mod.config.ConfigError):
                mod.write(self.tmp, ["profiles", "roles", "boss"], "a")
        finally:
            mod.config.load = real
        self.assertEqual(self.config.read_bytes(), before)
        self.assertFalse(list(self.config.parent.glob("*.tmp")))

    def test_edit_that_makes_the_config_invalid_is_refused_by_the_cli(self):
        self.write(dict(BASE_CONFIG, profiles={"roles": "oops"}))
        before = self.config.read_bytes()
        self.fails("list", reason="gw profile:")
        self.assertEqual(self.config.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
