"""Package structure smoke tests (Step 19 B1).

Verifies that the six subsystem packages declared in SDD-VIP-001 §3 are
importable and expose the expected module name. These tests guard against:
(a) missing `__init__.py`, (b) package rename drift, and (c) accidental
introduction of C -> B upward dependencies at import time (SEP-001, a weaker
pre-check than the mypy import-graph analysis planned for later steps).

Full SEP-001 separation enforcement (UNIT-005.3 `vip_api_b` must not be
imported by class-C packages) is deferred to Step 19 B2+ when concrete modules
are added; here we only check that `vip_api_b` loads independently of
`vip_api`, without asserting the inverse direction.
"""

from __future__ import annotations

import importlib
import sys

import pytest

SUBSYSTEM_PACKAGES = (
    "vip_ctrl",
    "vip_sim",
    "vip_persist",
    "vip_integrity",
    "vip_api",
    "vip_api_b",
)


@pytest.mark.parametrize("package", SUBSYSTEM_PACKAGES)
def test_subsystem_package_importable(package: str) -> None:
    """Each declared subsystem package must import cleanly with matching name."""
    module = importlib.import_module(package)
    assert module.__name__ == package


def test_api_b_importable_without_class_c_api() -> None:
    """UNIT-005.3 (vip_api_b, class B) must be usable in isolation.

    Weak SEP-001 pre-check: importing `vip_api_b` in a fresh namespace must
    not transitively pull in `vip_api` (class C). Stronger mypy-based
    import-graph verification follows in Step 19 B2+.
    """
    # Drop any pre-cached class-C API module so this test is order-independent.
    for cached in [name for name in sys.modules if name.startswith("vip_api.")]:
        sys.modules.pop(cached, None)
    sys.modules.pop("vip_api", None)

    importlib.import_module("vip_api_b")

    assert "vip_api" not in sys.modules, (
        "vip_api_b must not transitively import the class-C vip_api package "
        "(SEP-001 logical separation per SAD-VIP-001 §9)."
    )
