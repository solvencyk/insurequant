# -*- coding: utf-8 -*-
"""audit_io: load the audited artifacts from a PINNED git revision, not from the (shared, possibly dirty) working tree.

Reason: other stages (publishing) edit data/bonds/capital_tier_registry.json, kics_tier{1,2}_utilization.json and the apply script in the
working tree while this audit runs.  An audit that reads a half-edited file audits nothing.  Default revision = environment
variable AUDIT_REV, else HEAD.  AUDIT_REV=WORKTREE reads the working tree (only for diagnosing).

The master kics_disclosure.json and the per-bond ledger are read from the working tree after checking they equal HEAD (unmodified).
"""
import hashlib
import json
import os
import subprocess

ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
REV = os.environ.get("AUDIT_REV", "HEAD")


def _git(args):
    return subprocess.run(["git", "-C", ROOT] + args, capture_output=True, check=True).stdout


def resolved_rev(rev=None):
    rev = rev or REV
    if rev == "WORKTREE":
        return "WORKTREE"
    return _git(["rev-parse", "--short", rev]).decode().strip()


def blob_bytes(relpath, rev=None):
    rev = rev or REV
    if rev == "WORKTREE":
        return open(ROOT + "/" + relpath, "rb").read()
    return _git(["show", "%s:%s" % (rev, relpath)])


def load_json(relpath, rev=None):
    return json.loads(blob_bytes(relpath, rev).decode("utf-8"))


def sha12(relpath, rev=None):
    return hashlib.sha256(blob_bytes(relpath, rev)).hexdigest()[:12]


def worktree_equals_head(relpath):
    """True if the working-tree file is byte-identical to HEAD's blob (ignoring CRLF/LF)."""
    a = open(ROOT + "/" + relpath, "rb").read().replace(b"\r\n", b"\n")
    b = _git(["show", "HEAD:" + relpath]).replace(b"\r\n", b"\n")
    return a == b
