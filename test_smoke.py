#!/usr/bin/env python
# sentinel:skip-file -- negative-test fixture: deliberately references placeholder
# token strings (REPLACE_ME, __PLACEHOLDER__, {{...}}) to assert they are ABSENT
# from the shipped HTML. These are assertions, not unfilled placeholders.
"""Minimal smoke test for the Orforglipron_LivingMeta shipped HTML dashboard.

This repo is a single-file offline HTML living-review dashboard (no build step,
no node package). The deliverable is the HTML artifact itself, so the smoke test
validates the structural and offline-safety invariants that matter for shipping:

  * file is UTF-8 with no BOM (BOM breaks some browsers / our pipeline)
  * <script> tags are balanced (no truncated script blocks)
  * no unfilled template placeholders ({{...}}, REPLACE_ME, __PLACEHOLDER__)
  * no hardcoded local filesystem paths leaked into the shipped asset
  * every external CSS/JS asset load carries a Subresource Integrity hash
  * the core meta-analysis engine functions are present (pooling + SMD + tau2)

Run:  python -m pytest -q   (or)   python test_smoke.py
"""
import os
import re

ROOT = os.path.dirname(os.path.abspath(__file__))
HTML = os.path.join(ROOT, "ORFORGLIPRON_REVIEW.html")
INDEX = os.path.join(ROOT, "index.html")


def _read(path):
    with open(path, "rb") as fh:
        raw = fh.read()
    return raw


def test_no_bom():
    for path in (HTML, INDEX):
        raw = _read(path)
        assert not raw.startswith(b"\xef\xbb\xbf"), f"{os.path.basename(path)} has a UTF-8 BOM"


def test_decodes_as_utf8():
    for path in (HTML, INDEX):
        _read(path).decode("utf-8")  # raises if not valid utf-8


def test_script_tags_balanced():
    s = _read(HTML).decode("utf-8")
    opens = len(re.findall(r"<script[\s>]", s))
    closes = len(re.findall(r"</script>", s))
    assert opens == closes, f"script tag imbalance: {opens} open vs {closes} close"


def test_no_unfilled_placeholders():
    s = _read(HTML).decode("utf-8")
    assert "REPLACE_ME" not in s
    assert "__PLACEHOLDER__" not in s
    assert not re.search(r"\{\{[A-Za-z_][A-Za-z0-9_]*\}\}", s), "unfilled {{token}} placeholder"


def test_no_hardcoded_local_paths():
    # shipped assets must not leak a developer's local filesystem path
    for path in (HTML, INDEX):
        s = _read(path).decode("utf-8")
        assert not re.search(r"[A-Za-z]:\\Users\\", s), f"{os.path.basename(path)} leaks a C:\\Users path"
        assert not re.search(r"/home/[a-z]+/", s), f"{os.path.basename(path)} leaks a /home path"


def test_external_assets_have_sri():
    # every <link>/<script> that loads from cdnjs must carry an integrity hash
    s = _read(HTML).decode("utf-8")
    for tag in re.findall(r"<(?:link|script)[^>]*cdnjs\.cloudflare\.com[^>]*>", s):
        assert "integrity=" in tag, f"external asset without SRI integrity: {tag[:120]}"


def test_engine_functions_present():
    s = _read(HTML).decode("utf-8")
    for fn in ("function computeSMD(", "function pauleMandelTau2(", "function poolWith("):
        assert fn in s, f"missing engine function: {fn}"


if __name__ == "__main__":
    passed = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"PASS {name}")
            passed += 1
    print(f"\n{passed} passed")
