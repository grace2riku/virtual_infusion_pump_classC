"""Command-Line Entry Point (UNIT-005.4) per SDD-VIP-001 v0.3 §4.18.

Realises SRS-OPS-002(`vip-ctrl` CLI 起動)+ SRS-OPS-003(初回起動デフォルト
動作)+ SRS-OPS-010(JSON Lines ログ)+ SRS-OPS-011(`--diagnose`)。

Inc.1 範囲は **対話的 start/stop コマンド経路を提供しない**(SDD §3 設計方針 +
B17 Step 19 申し送り = 対話 UI は Inc.4 で正式実装)。本 CLI は以下の 3 経路を
公開:

* `vip-ctrl --version`             : バージョン文字列を stdout 出力 + exit 0
* `vip-ctrl --diagnose`            : `--persist-path` のレコードを atomic_writer.read +
                                      from_json + integrity validator で読込・検証し、
                                      JSON Lines snapshot を stdout 出力 + exit 0
* `vip-ctrl`(デフォルト)         : 起動メッセージを stderr に出力 + 初期 snapshot
                                      (state=IDLE / flow=0 / accumulated=0、または既存
                                      永続レコードの復元値)を JSON Lines で stdout 出力
                                      + exit 0(対話モードは Inc.4)

引数解析エラーは argparse 標準動作(stderr + exit 2)に準じる。

Related SRS: SRS-OPS-002(必須)、SRS-OPS-003(必須)、SRS-OPS-010(推奨)、
             SRS-OPS-011(推奨)。
Related SDD: §4.18(本ユニット)、§4.5(integrity validator 利用)、§4.4
             (atomic_writer.read 利用)。
Related RCM: —(運用要求のため RCM 直接対応なし、ただし SRS-OPS-003 の
             「IDLE / 流量 0 / 積算 0 デフォルト」は SRS-027 フェイルセーフ
             起動と整合)。
Related HZ:  HZ-007(永続記録破損時のフェイルセーフ起動経路を `--diagnose`
             で観測可能にする)。
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import IO

from vip_integrity.validator import (
    IntegrityFailure,
)
from vip_integrity.validator import (
    Ok as ValidatedOk,
)
from vip_integrity.validator import (
    validate as validate_integrity,
)
from vip_persist import atomic_writer
from vip_persist.serializer import from_json

__all__ = [
    "DiagnoseResult",
    "PackageNotFoundError",
    "build_parser",
    "main",
    "run_default",
    "run_diagnose",
    "run_version",
]


_PACKAGE_NAME = "vip"
_DEFAULT_PERSIST_PATH = Path.home() / ".vip-ctrl" / "persist.json"
_FALLBACK_VERSION = "unknown"


@dataclass(frozen=True, slots=True)
class DiagnoseResult:
    """`--diagnose` の結果を構造化(SDD §4.18.B Result 型整合)."""

    persist_path: Path
    record_present: bool
    integrity_ok: bool
    failures: list[IntegrityFailure]


# ---------------------------------------------------------------------------
# JSON Lines 出力ヘルパ(SRS-OPS-010 整合)
# ---------------------------------------------------------------------------


def _emit_event(
    out: IO[str],
    *,
    level: str,
    component: str,
    event: str,
    details: dict[str, object],
) -> None:
    """SRS-OPS-010 整合の JSON Lines 1 行を `out` に書く.

    最低 5 キー(timestamp / level / component / event / details)を必須含有。
    """
    record = {
        "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "level": level,
        "component": component,
        "event": event,
        "details": details,
    }
    out.write(json.dumps(record, ensure_ascii=False, sort_keys=True))
    out.write("\n")
    out.flush()


# ---------------------------------------------------------------------------
# サブコマンド本体(各 1 関数で stdin/out/err DI のため pure 化)
# ---------------------------------------------------------------------------


def _resolve_version() -> str:
    """インストール済パッケージのバージョンを取得(取得失敗時は fallback)."""
    try:
        return version(_PACKAGE_NAME)
    except PackageNotFoundError:
        return _FALLBACK_VERSION


def run_version(*, out: IO[str]) -> int:
    """`--version`: バージョン文字列を `out` に 1 行出力."""
    out.write(f"vip-ctrl {_resolve_version()}\n")
    out.flush()
    return 0


def run_diagnose(
    *,
    persist_path: Path,
    out: IO[str],
) -> int:
    """`--diagnose`: 永続レコードを読込・検証 + JSON Lines snapshot を `out` に出力.

    - レコード不存在: SRS-OPS-003 デフォルト相当の snapshot を出力(record_present=false)
    - 読込 OSError: ReadErr → record_present=false で報告
    - JSON / pydantic 例外: integrity_ok=false で報告
    - integrity validator 結果: Ok / FailsafeRecommended で構造化
    """
    result = _diagnose(persist_path)
    _emit_event(
        out,
        level="info" if result.integrity_ok else "warning",
        component="cli",
        event="diagnose",
        details={
            "persist_path": str(result.persist_path),
            "record_present": result.record_present,
            "integrity_ok": result.integrity_ok,
            "failure_count": len(result.failures),
            "failures": [type(f).__name__ for f in result.failures],
        },
    )
    return 0


def run_default(
    *,
    persist_path: Path,
    out: IO[str],
    err: IO[str],
) -> int:
    """`vip-ctrl`(デフォルト): 起動メッセージ(stderr)+ 初期 snapshot(stdout JSON Lines).

    Inc.1 範囲は対話モードを提供しないため、起動メッセージで Inc.4 への申し送りを
    明記し、初期 snapshot を 1 行出力して exit 0 する。SRS-OPS-003 整合(IDLE /
    流量 0 / 積算 0)、または既存永続レコードを復元する場合はその値を表示。
    """
    err.write(
        f"vip-ctrl {_resolve_version()} (Inc.1) — 対話モードは Inc.4 UI 層で正式実装予定。\n"
        "本起動はデフォルト snapshot 出力のみ実施します。\n",
    )
    err.flush()
    result = _diagnose(persist_path)
    _emit_event(
        out,
        level="info",
        component="cli",
        event="boot_snapshot",
        details={
            "persist_path": str(result.persist_path),
            "record_present": result.record_present,
            "integrity_ok": result.integrity_ok,
            "default_state": "IDLE",
            "default_flow_rate": "0.0",
            "default_accumulated_volume": "0.0",
        },
    )
    return 0


# ---------------------------------------------------------------------------
# 内部ヘルパ(diagnose ロジック本体)
# ---------------------------------------------------------------------------


def _diagnose(persist_path: Path) -> DiagnoseResult:
    """`persist_path` の永続レコードを読込・検証(本関数は I/O 経由のみ)."""
    if not persist_path.exists():
        return DiagnoseResult(
            persist_path=persist_path,
            record_present=False,
            integrity_ok=True,  # 不存在 = SRS-OPS-003 デフォルトで起動可能
            failures=[],
        )
    read_result = atomic_writer.read(persist_path)
    if not isinstance(read_result, atomic_writer.ReadOk):
        return DiagnoseResult(
            persist_path=persist_path,
            record_present=False,
            integrity_ok=False,
            failures=[],
        )
    try:
        raw = from_json(read_result.data)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError):
        return DiagnoseResult(
            persist_path=persist_path,
            record_present=True,
            integrity_ok=False,
            failures=[],
        )
    # SDD §4.5.A の sealed union(`ValidationResult = Ok | FailsafeRecommended`)を
    # `isinstance` で 2 分岐網羅(`match` の implicit fallthrough = branch coverage 不到達
    # を回避)。bandit B101 は `assert isinstance` を使わないことで回避。mypy は 2 分岐目
    # で `FailsafeRecommended` に narrow できるため `result.reasons` を安全にアクセス可能。
    result = validate_integrity(raw)
    if isinstance(result, ValidatedOk):
        return DiagnoseResult(
            persist_path=persist_path,
            record_present=True,
            integrity_ok=True,
            failures=[],
        )
    return DiagnoseResult(
        persist_path=persist_path,
        record_present=True,
        integrity_ok=False,
        failures=list(result.reasons),
    )


# ---------------------------------------------------------------------------
# argparse + main
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    """SDD §4.18.A で定義した CLI 引数パーサを構築."""
    parser = argparse.ArgumentParser(
        prog="vip-ctrl",
        description=(
            "Virtual Infusion Pump Control Software CLI (Inc.1)。"
            " 対話 start/stop は Inc.4 UI 層で正式実装。"
        ),
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--version",
        action="store_true",
        help="バージョン文字列を stdout 出力 + exit 0",
    )
    mode.add_argument(
        "--diagnose",
        action="store_true",
        help="永続レコード整合性検証 + JSON Lines snapshot を stdout 出力 + exit 0",
    )
    parser.add_argument(
        "--persist-path",
        type=Path,
        default=_DEFAULT_PERSIST_PATH,
        help=f"永続レコードのパス(デフォルト: {_DEFAULT_PERSIST_PATH})",
    )
    return parser


def main(
    argv: list[str] | None = None,
    *,
    stdout: IO[str] | None = None,
    stderr: IO[str] | None = None,
) -> int:
    """エントリポイント本体. 各サブモードへ振り分け + 戻り値を返す."""
    out: IO[str] = stdout if stdout is not None else sys.stdout
    err: IO[str] = stderr if stderr is not None else sys.stderr
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.version:
        return run_version(out=out)
    if args.diagnose:
        return run_diagnose(persist_path=args.persist_path, out=out)
    return run_default(persist_path=args.persist_path, out=out, err=err)


if __name__ == "__main__":  # pragma: no cover — script entry, exercised by integration
    raise SystemExit(main())
