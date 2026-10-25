import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("upstream", ROOT / "scripts/update-upstream.py")
upstream = importlib.util.module_from_spec(spec)
spec.loader.exec_module(upstream)


def release(tag, **kwargs):
    return dict(tag_name=tag, draft=False, prerelease=False) | kwargs


class ReleaseTests(unittest.TestCase):
    # Keep fixtures independent of the real pin: these tests also run on update PRs.
    recipe = upstream.PIN.sub(
        lambda match: match[1] + "weekly-2026-10-18",
        (ROOT / "snap/snapcraft.yaml").read_text())

    def test_newest_date_wins_not_api_order(self):
        result, outputs = upstream.update_recipe(self.recipe, [
            release("weekly-2026-10-19"), release("weekly-2026-10-25"),
            release("weekly-2026-10-18")])
        self.assertEqual(outputs["latest"], "weekly-2026-10-25")
        self.assertEqual(outputs["needs_update"], "true")
        self.assertEqual(result, self.recipe.replace("version: &upstream-version weekly-2026-10-18",
                                                    "version: &upstream-version weekly-2026-10-25"))

    def test_skips_unpublished_prerelease_and_other_tags(self):
        _, outputs = upstream.update_recipe(self.recipe, [
            release("weekly-2026-10-25"),
            release("weekly-2026-11-01", prerelease=True),
            release("weekly-2026-11-08", draft=True),
            release("v999"), release("weekly-2026-12-01\nmalicious=true")])
        self.assertEqual(outputs["latest"], "weekly-2026-10-25")

    def test_same_version_and_older_versions_are_noops(self):
        for tag in ["weekly-2026-10-18", "weekly-2026-10-11"]:
            with self.subTest(tag=tag):
                result, outputs = upstream.update_recipe(self.recipe, [release(tag)])
                self.assertEqual(result, self.recipe)
                self.assertEqual(outputs["needs_update"], "false")

    def test_rejects_empty_or_invalid_release_data(self):
        for releases in [[], [release("v1")], [release("weekly-2026-02-30")]]:
            with self.subTest(releases=releases), self.assertRaises(ValueError):
                upstream.update_recipe(self.recipe, releases)

    def test_requires_exactly_one_pin(self):
        for recipe in ["", self.recipe + "version: &upstream-version weekly-2026-10-18\n"]:
            with self.subTest(recipe=recipe), self.assertRaises(ValueError):
                upstream.update_recipe(recipe, [release("weekly-2026-10-25")])

    def test_update_is_idempotent(self):
        releases = [release("weekly-2026-10-25")]
        updated, _ = upstream.update_recipe(self.recipe, releases)
        again, outputs = upstream.update_recipe(updated, releases)
        self.assertEqual(again, updated)
        self.assertEqual(outputs["needs_update"], "false")


if __name__ == "__main__":
    unittest.main()
