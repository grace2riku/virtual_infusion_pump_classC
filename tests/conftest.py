"""Shared pytest fixtures and configuration.

Expanded in Step 19 B2+ with unit-specific fixtures (mock pump, frozen clock,
hypothesis profiles, etc). Step 19 F5 で `linux_only` マーカーの auto-skip
hook を追加(F6 で予定だった機能を F5 で先取り、ITPR §8.1 規定との整合性
を確保 — IT-PERF / IT-PWR / IT-SIDE は Linux runner 限定)。
"""

from __future__ import annotations

import sys

import pytest


def pytest_collection_modifyitems(
    config: pytest.Config,  # noqa: ARG001 — required by pytest hook signature
    items: list[pytest.Item],
) -> None:
    """`linux_only` マーカー付きテストを Linux 以外で auto-skip する.

    ITPR §8.1 規定「IT-PERF / IT-PWR / IT-SIDE は Linux runner 限定 +
    nightly schedule での実行」を機械化。ローカル開発環境(macOS / Windows)
    では `linux_only` マーカー付きテストを **collection 直後に skip 化** する
    ことで、flake が発生しがちな環境依存試験を開発時に巻き込まないようにする。

    Step 19 F5 で先取り実装(本来 F6(IT-PWR で `subprocess.SIGKILL` 使用)で
    導入予定だったが、F5(IT-PERF)の macOS sleep ジッタ flake 対策として
    早期化)。F6 / F7 でもそのまま再利用可能。
    """
    if sys.platform == "linux":
        return
    skip_marker = pytest.mark.skip(
        reason=f"linux_only test (current platform: {sys.platform})",
    )
    for item in items:
        if "linux_only" in item.keywords:
            item.add_marker(skip_marker)
