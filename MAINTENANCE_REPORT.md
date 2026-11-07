Last Edit: Claude Opus 5.5 - 2026-11-07 - Motive: Release this fork as a wheel on Thalovant's skill index instead of a Git install.

# Maintenance report (Thalovant fork)

## 2026-11-07 - Thalovant builds carry a local version label

**Why.** Thalovant's Story Time runtime installed this fork from Git
(`git+https://github.com/thalovant/ovos-common-reading-pipeline-plugin.git@8a447eb`), and that install is
the reason its pod mounted a GitHub credential. The runtime can install a pinned
wheel from Thalovant's private skill index instead, but this fork's version
(`0.1.13`) is also on PyPI as upstream's release, with different code. uv
reads the index beside PyPI, so a wheel with the same number could lose to
upstream's.

**Change.**

- `version.py` gains `VERSION_LOCAL = "thalovant.1"`, and `setup.py`'s
  `get_version()` appends it: the build is `0.1.13+thalovant.1`. PyPI never
  accepts a local version, so `==0.1.13+thalovant.1` can only match Thalovant's
  wheel.
- `publish.yml` (upstream's PyPI release) ignores `v*+thalovant.*` tags.
- `tests/test_version.py` checks the built version: upstream's public number
  from `version.py`, then `thalovant.N`, in canonical PEP 440 form.

**Releasing.** Tag the commit `v0.1.13+thalovant.1`, build the wheel from the tag
(`python -m build --wheel`), and have a Thalovant admin upload it to the
fork's catalog row with `POST /v1/marketplace/skills/{id}/versions`
(multipart). This public fork cannot call the private reusable release
workflow in `thalovant/skill-index`, so there is no release workflow here.
Any later Thalovant release of new code bumps `N`; the index refuses a second
wheel under the same version.

**Which code.** The tag for `0.1.13+thalovant.1` sits on this pull request's
first commit, which is the live commit `8a447eb` plus the version scheme. The
`thalovant` branch also holds #2 and #3 (read-ahead), merged on 2026-10-01 but
never deployed: #2 changes what a client must do (it must drop held sentences
on stop; thalovant-android and thalovant-voice branches
`fix/drop-read-ahead-on-stop`). The second commit sets the branch to
`thalovant.2`, so a release of that work gets its own version.

**Verification.** At the first commit (live code `8a447eb` plus this scheme): `pytest tests` on Python 3.12, 437 passed, 1 skipped (`requirements.txt` and `requirements-test.txt`). `python setup.py --version` prints `0.1.13+thalovant.1`. The wheel built there holds the same 190 files as a wheel built from `8a447eb`, except `version.py`, and passes the Thalovant API's `validate_wheel`.

**Transparency Report.** AI Model: Claude Opus 5.5 (`claude-opus-5-5`) in
Claude Code. Actions Taken: wrote the version label, the tag filter, the test
and this report; ran the test suite. Oversight: prepared for the owner's
review as a pull request; not merged or released by the AI.
