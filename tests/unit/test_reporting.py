import pytest
from pathlib import Path

from utils.reporting import collect_summary


@pytest.mark.unit
def test_collect_summary_reads_junit_xml(tmp_path: Path) -> None:
    xml_path = tmp_path / "junit.xml"
    xml_path.write_text(
        """
        <testsuite tests="4" failures="1" errors="0" skipped="1" time="12.5">
          <testcase classname="suite" name="test_pass" time="1.0" />
          <testcase classname="suite" name="test_fail" time="2.0">
            <failure message="boom">boom</failure>
          </testcase>
          <testcase classname="suite" name="test_skip" time="0.0">
            <skipped message="later" />
          </testcase>
          <testcase classname="suite" name="test_pass_2" time="1.0" />
        </testsuite>
        """.strip(),
        encoding="utf-8",
    )

    summary = collect_summary(xml_path)

    assert summary.total == 4
    assert summary.failed == 1
    assert summary.skipped == 1
    assert summary.passed == 2
    assert summary.failed_tests == ["suite::test_fail"]
