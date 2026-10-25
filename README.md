# Spectrum Analyser snap

Strictly confined, amd64 packaging for
[8BitAnalysers](https://github.com/TheGoodDoktor/8BitAnalysers).

## Release updates

`sync-version-with-upstream.yml` checks upstream daily at 10:23 UTC and can
also be run manually from Actions. It selects the newest published
`weekly-YYYY-MM-DD` release, excluding drafts and prereleases, and never
downgrades. `version` in `snap/snapcraft.yaml` is the single version pin;
`source-tag` shares its value through a YAML anchor. This keeps the package
version and source tag identical even when multiple weekly tags point at
the same upstream commit.

The updater maintains one `auto-update-spectrum-analyser` PR. It then calls
the build/smoke workflow with that PR's exact commit, using the ordinary
`GITHUB_TOKEN`. Validation runs directly in the update workflow rather than
depending on an automated PR event starting CI. An existing open update PR
is tested again on subsequent runs. Failed validation leaves the PR open
for investigation; nothing merges or publishes automatically.

In repository **Settings → Actions → General → Workflow permissions**, enable
**Allow GitHub Actions to create and approve pull requests**. No personal
access token or Snap Store credentials are required. Scheduled workflows
take effect once these files are on the default branch.

## Validation and evidence

`snap.yml` also runs on main pushes, PRs, manual dispatch, and Monday mornings.
It builds with LXD, reviews the snap, then installs it in a fresh desktop VM
using ghvmctl's default Ubuntu release. The guest release follows ghvmctl's
tooling requirements independently of the snap's `core24` base and the
GitHub runner OS. The smoke test waits for the application's visible
X11 window, activates it, and checks that it remains open before capturing
the full desktop and active window. The app is built with Wayland disabled,
so xdotool can inspect its X11/XWayland window.

Each validation run provides a `snap` artifact and, when the VM reaches the
test, `smoke-test-screenshots` and `smoke-test-logs` artifacts. Failure
screenshots are diagnostic evidence, not a passing result. Check the job
status and inspect the window screenshot before merging. This verifies
startup, not all emulator/debugger functionality.

## Local checks

```sh
python3 -m unittest discover -s tests -v
# Uses gh authentication; reports changes without modifying the recipe:
python3 scripts/update-upstream.py
# Apply an available update:
python3 scripts/update-upstream.py --write
snapcraft --use-lxd
```
