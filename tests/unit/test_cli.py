"""Unit test — UNIT-005.4 CLI Entry Point (SDD-VIP-001 v0.3 §4.18).

Step 19 H1 で UNIT-005.4 CLI 新規追加に伴う UT。MC/DC 100% 目標、
- `--version` / `--diagnose` / デフォルト 3 経路の正常動作
- argparse 引数エラー(相互排他違反など)
- `--diagnose` の各経路:レコード不存在 / 読込 OSError / JSON 解析エラー /
  pydantic ValidationError / integrity Ok / integrity FailsafeRecommended

CLI は subprocess を経由せず、`main(argv, stdout, stderr)` を直接呼出して
in-memory `io.StringIO` で出力を検査する(test 高速化 + 確実な caputure)。
"""

from __future__ import annotations

import io
import json
from decimal import Decimal
from typing import TYPE_CHECKING, Any
from unittest.mock import patch

import pytest

from vip_ctrl import cli
from vip_ctrl.state_machine import State
from vip_persist import atomic_writer
from vip_persist.records import RuntimeState, Settings
from vip_persist.serializer import build_persisted_record, to_json

if TYPE_CHECKING:
    from pathlib import Path

# ---------------------------------------------------------------------------
# Helpers — 永続レコードを atomic_writer.write で配置する
# ---------------------------------------------------------------------------


def _build_good_record_bytes() -> bytes:
    """整合性検証 Ok を取れる代表値レコードを JSON bytes で返す."""
    settings = Settings(
        flow_rate=Decimal("60.0"),
        dose_volume=Decimal("60.0"),
        duration_min=60,
    )
    runtime_state = RuntimeState(
        state=State.IDLE,
        current_flow=Decimal("0.0"),
        accumulated_volume=Decimal("0.0"),
    )
    return to_json(build_persisted_record(settings, runtime_state, "2026-05-07T00:00:00Z"))


def _write_good_record(path: Path) -> None:
    """`atomic_writer.write` 経由で整合レコードを配置."""
    res = atomic_writer.write(_build_good_record_bytes(), path)
    assert isinstance(res, atomic_writer.WriteOk)


def _write_corrupt_record(path: Path) -> None:
    """checksum 不一致になる破損レコード(末尾を 1 byte 改竄)を配置."""
    data = _build_good_record_bytes()
    # JSON の checksum 部の末尾 1 文字を別の hex 文字に反転
    text = data.decode()
    flipped = text.replace('"checksum":"', '"checksum":"X', 1) if '"checksum":"' in text else text
    res = atomic_writer.write(flipped.encode(), path)
    assert isinstance(res, atomic_writer.WriteOk)


# ---------------------------------------------------------------------------
# UT-005.4-01 — `--version` 経路
# ---------------------------------------------------------------------------
def test_ut_005_4_01_version_outputs_one_line_then_exit_zero() -> None:
    """`--version`: 1 行のバージョン文字列を stdout 出力 + return 0."""
    out = io.StringIO()
    err = io.StringIO()
    rc = cli.main(["--version"], stdout=out, stderr=err)
    assert rc == 0
    lines = out.getvalue().splitlines()
    assert len(lines) == 1
    assert lines[0].startswith("vip-ctrl ")
    assert err.getvalue() == ""


# ---------------------------------------------------------------------------
# UT-005.4-02 — `--version` の fallback(importlib.metadata で PackageNotFoundError)
# ---------------------------------------------------------------------------
def test_ut_005_4_02_version_falls_back_when_package_unknown() -> None:
    """`importlib.metadata.version` が `PackageNotFoundError` でも `unknown` を返して exit 0."""
    out = io.StringIO()
    err = io.StringIO()
    with patch("vip_ctrl.cli.version", side_effect=cli.PackageNotFoundError):
        rc = cli.main(["--version"], stdout=out, stderr=err)
    assert rc == 0
    assert "unknown" in out.getvalue()


# ---------------------------------------------------------------------------
# UT-005.4-03 — `--diagnose` レコード不存在経路(SRS-OPS-003 デフォルト相当)
# ---------------------------------------------------------------------------
def test_ut_005_4_03_diagnose_no_record(tmp_path: Path) -> None:
    """レコード不存在: integrity_ok=true(デフォルト起動可)、record_present=false."""
    persist = tmp_path / "no_record.json"
    out = io.StringIO()
    rc = cli.main(["--diagnose", "--persist-path", str(persist)], stdout=out)
    assert rc == 0
    payload = json.loads(out.getvalue().strip())
    assert payload["event"] == "diagnose"
    assert payload["level"] == "info"
    assert payload["details"]["record_present"] is False
    assert payload["details"]["integrity_ok"] is True
    assert payload["details"]["failure_count"] == 0


# ---------------------------------------------------------------------------
# UT-005.4-04 — `--diagnose` 整合レコード経路
# ---------------------------------------------------------------------------
def test_ut_005_4_04_diagnose_good_record(tmp_path: Path) -> None:
    """整合レコード存在: record_present=true、integrity_ok=true."""
    persist = tmp_path / "good.json"
    _write_good_record(persist)
    out = io.StringIO()
    rc = cli.main(["--diagnose", "--persist-path", str(persist)], stdout=out)
    assert rc == 0
    payload = json.loads(out.getvalue().strip())
    assert payload["details"]["record_present"] is True
    assert payload["details"]["integrity_ok"] is True
    assert payload["details"]["failure_count"] == 0
    # SRS-OPS-010 必須 5 キー網羅
    assert {"timestamp", "level", "component", "event", "details"} <= set(payload.keys())


# ---------------------------------------------------------------------------
# UT-005.4-05 — `--diagnose` 破損レコード(checksum 不一致)経路
# ---------------------------------------------------------------------------
def test_ut_005_4_05_diagnose_checksum_mismatch(tmp_path: Path) -> None:
    """破損レコード(checksum 不一致): integrity_ok=false、failure_count > 0."""
    persist = tmp_path / "corrupt.json"
    _write_corrupt_record(persist)
    out = io.StringIO()
    rc = cli.main(["--diagnose", "--persist-path", str(persist)], stdout=out)
    assert rc == 0
    payload = json.loads(out.getvalue().strip())
    assert payload["level"] == "warning"
    assert payload["details"]["record_present"] is True
    assert payload["details"]["integrity_ok"] is False
    assert payload["details"]["failure_count"] >= 1
    assert any("Checksum" in name for name in payload["details"]["failures"])


# ---------------------------------------------------------------------------
# UT-005.4-06 — `--diagnose` JSON 不正経路
# ---------------------------------------------------------------------------
def test_ut_005_4_06_diagnose_invalid_json(tmp_path: Path) -> None:
    """JSON 不正バイト列: from_json で JSONDecodeError → integrity_ok=false."""
    persist = tmp_path / "broken.json"
    persist.write_bytes(b"not a valid json {")
    out = io.StringIO()
    rc = cli.main(["--diagnose", "--persist-path", str(persist)], stdout=out)
    assert rc == 0
    payload = json.loads(out.getvalue().strip())
    assert payload["details"]["record_present"] is True
    assert payload["details"]["integrity_ok"] is False
    assert payload["details"]["failure_count"] == 0  # 失敗一覧は decode 段階で空


# ---------------------------------------------------------------------------
# UT-005.4-07 — `--diagnose` UTF-8 デコード失敗経路
# ---------------------------------------------------------------------------
def test_ut_005_4_07_diagnose_utf8_decode_error(tmp_path: Path) -> None:
    """UTF-8 として decode できないバイト列: UnicodeDecodeError → integrity_ok=false."""
    persist = tmp_path / "binary.json"
    persist.write_bytes(b"\xff\xfe\x00\x00invalid utf-8")
    out = io.StringIO()
    rc = cli.main(["--diagnose", "--persist-path", str(persist)], stdout=out)
    assert rc == 0
    payload = json.loads(out.getvalue().strip())
    assert payload["details"]["record_present"] is True
    assert payload["details"]["integrity_ok"] is False


# ---------------------------------------------------------------------------
# UT-005.4-08 — `--diagnose` `atomic_writer.read` ReadErr 経路
# ---------------------------------------------------------------------------
def test_ut_005_4_08_diagnose_read_error(tmp_path: Path) -> None:
    """`atomic_writer.read` が ReadErr を返す経路: record_present=false、integrity_ok=false.

    `Path.exists()` は True を返すよう mock しつつ `atomic_writer.read` で ReadErr
    を返すパッチを入れる(典型的には permission denied などの OSError)。
    """
    persist = tmp_path / "exists_but_unreadable.json"
    persist.write_bytes(b"placeholder")
    out = io.StringIO()
    err = OSError("simulated permission denied")
    with patch.object(atomic_writer, "read", return_value=atomic_writer.ReadErr(err)):
        rc = cli.main(["--diagnose", "--persist-path", str(persist)], stdout=out)
    assert rc == 0
    payload = json.loads(out.getvalue().strip())
    assert payload["details"]["record_present"] is False  # 読めない = 不在扱い
    assert payload["details"]["integrity_ok"] is False
    assert payload["level"] == "warning"


# ---------------------------------------------------------------------------
# UT-005.4-09 — デフォルト経路(レコード不存在)
# ---------------------------------------------------------------------------
def test_ut_005_4_09_default_no_record(tmp_path: Path) -> None:
    """デフォルト: 起動メッセージを stderr、boot_snapshot を stdout に JSON Lines 出力."""
    persist = tmp_path / "no_record.json"
    out = io.StringIO()
    err = io.StringIO()
    rc = cli.main(["--persist-path", str(persist)], stdout=out, stderr=err)
    assert rc == 0
    # stderr: 起動メッセージ + Inc.4 申し送り
    assert "Inc.1" in err.getvalue()
    assert "Inc.4" in err.getvalue()
    # stdout: JSON Lines 1 行
    payload = json.loads(out.getvalue().strip())
    assert payload["event"] == "boot_snapshot"
    assert payload["details"]["default_state"] == "IDLE"
    assert payload["details"]["default_flow_rate"] == "0.0"
    assert payload["details"]["default_accumulated_volume"] == "0.0"
    assert payload["details"]["record_present"] is False


# ---------------------------------------------------------------------------
# UT-005.4-10 — デフォルト経路(整合レコード存在)
# ---------------------------------------------------------------------------
def test_ut_005_4_10_default_with_good_record(tmp_path: Path) -> None:
    """デフォルト + 整合レコード: integrity_ok=true、record_present=true."""
    persist = tmp_path / "good.json"
    _write_good_record(persist)
    out = io.StringIO()
    err = io.StringIO()
    rc = cli.main(["--persist-path", str(persist)], stdout=out, stderr=err)
    assert rc == 0
    payload = json.loads(out.getvalue().strip())
    assert payload["details"]["record_present"] is True
    assert payload["details"]["integrity_ok"] is True


# ---------------------------------------------------------------------------
# UT-005.4-11 — argparse 相互排他違反(--version + --diagnose 同時指定)
# ---------------------------------------------------------------------------
def test_ut_005_4_11_mutually_exclusive_args() -> None:
    """`--version` と `--diagnose` の同時指定は argparse がエラーで SystemExit(2)."""
    with pytest.raises(SystemExit) as excinfo:
        cli.main(["--version", "--diagnose"], stdout=io.StringIO(), stderr=io.StringIO())
    assert excinfo.value.code == 2


# ---------------------------------------------------------------------------
# UT-005.4-12 — argparse 未知の引数
# ---------------------------------------------------------------------------
def test_ut_005_4_12_unknown_argument() -> None:
    """未知の引数で argparse が SystemExit(2)."""
    with pytest.raises(SystemExit) as excinfo:
        cli.main(["--unknown-flag"], stdout=io.StringIO(), stderr=io.StringIO())
    assert excinfo.value.code == 2


# ---------------------------------------------------------------------------
# UT-005.4-13 — `build_parser` 単独テスト(再利用性)
# ---------------------------------------------------------------------------
def test_ut_005_4_13_build_parser_returns_parser(tmp_path: Path) -> None:
    """`build_parser` が `argparse.ArgumentParser` を返し、CLI 引数定義を保持."""
    parser = cli.build_parser()
    args = parser.parse_args([])
    assert args.version is False
    assert args.diagnose is False
    assert args.persist_path == cli._DEFAULT_PERSIST_PATH  # noqa: SLF001
    custom_path = tmp_path / "x.json"
    args = parser.parse_args(["--persist-path", str(custom_path)])
    assert args.persist_path == custom_path


# ---------------------------------------------------------------------------
# UT-005.4-14 — JSON Lines レコード形式の SRS-OPS-010 必須 5 キー網羅
# ---------------------------------------------------------------------------
def test_ut_005_4_14_jsonlines_minimum_keys(tmp_path: Path) -> None:
    """SRS-OPS-010 必須 5 キー(timestamp / level / component / event / details)を全行に含む."""
    persist = tmp_path / "no_record.json"
    out = io.StringIO()
    cli.main(["--diagnose", "--persist-path", str(persist)], stdout=out)
    cli.main(["--persist-path", str(persist)], stdout=out, stderr=io.StringIO())
    lines = [line for line in out.getvalue().splitlines() if line.strip()]
    assert len(lines) == 2
    required = {"timestamp", "level", "component", "event", "details"}
    for line in lines:
        rec: dict[str, Any] = json.loads(line)
        assert required <= set(rec.keys()), f"missing keys in {line}"


# ---------------------------------------------------------------------------
# UT-005.4-15 — `_diagnose` 単独契約検証(integrity_ok 二択保証)
# ---------------------------------------------------------------------------
def test_ut_005_4_15_diagnose_helper_contract(tmp_path: Path) -> None:
    """`_diagnose` ヘルパは常に `DiagnoseResult` を返し、`integrity_ok` は bool 型."""
    persist = tmp_path / "x.json"
    res = cli._diagnose(persist)  # noqa: SLF001
    assert isinstance(res, cli.DiagnoseResult)
    assert isinstance(res.integrity_ok, bool)
    assert isinstance(res.record_present, bool)
    assert res.persist_path == persist
