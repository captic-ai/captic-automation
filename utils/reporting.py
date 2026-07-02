from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from xml.etree import ElementTree


@dataclass(frozen=True)
class RegressionSummary:
    total: int
    passed: int
    failed: int
    skipped: int
    errors: int
    duration_seconds: float
    failed_tests: list[str]

    @property
    def executed(self) -> int:
        """Tests that actually ran (excludes skipped)."""
        return max(self.total - self.skipped, 0)

    @property
    def pass_rate(self) -> float:
        """Pass rate over executed tests, as a 0-100 percentage."""
        if self.executed == 0:
            return 100.0
        return round(self.passed / self.executed * 100, 1)

    @property
    def is_green(self) -> bool:
        return self.failed == 0 and self.errors == 0


def collect_summary(junit_xml_path: str | Path) -> RegressionSummary:
    xml_path = Path(junit_xml_path)
    if not xml_path.exists():
        raise FileNotFoundError(f"JUnit XML not found: {xml_path}")

    root = ElementTree.parse(xml_path).getroot()
    suites = [root] if root.tag == "testsuite" else root.findall("testsuite")
    if not suites:
        raise ValueError(f"No <testsuite> nodes found in {xml_path}")

    total = passed = failed = skipped = errors = 0
    duration_seconds = 0.0
    failed_tests: list[str] = []

    for suite in suites:
        total += int(suite.attrib.get("tests", 0))
        failed += int(suite.attrib.get("failures", 0))
        skipped += int(suite.attrib.get("skipped", 0))
        errors += int(suite.attrib.get("errors", 0))
        duration_seconds += float(suite.attrib.get("time", 0.0))

        for case in suite.findall("testcase"):
            failure = case.find("failure")
            error = case.find("error")
            if failure is None and error is None:
                continue
            classname = case.attrib.get("classname", "unknown")
            name = case.attrib.get("name", "unknown")
            failed_tests.append(f"{classname}::{name}")

    passed = max(total - failed - skipped - errors, 0)

    return RegressionSummary(
        total=total,
        passed=passed,
        failed=failed,
        skipped=skipped,
        errors=errors,
        duration_seconds=duration_seconds,
        failed_tests=failed_tests[:10],
    )
