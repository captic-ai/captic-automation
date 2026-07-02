from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from utils.notifications import build_google_chat_payload, send_google_chat_message
from utils.reporting import collect_summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Send a JUnit summary to Google Chat.")
    parser.add_argument("--junit-xml", required=True, help="Path to the JUnit XML report.")
    parser.add_argument("--suite-name", default="nightly-regression")
    parser.add_argument("--environment", default=os.getenv("TEST_ENVIRONMENT", "staging"))
    parser.add_argument("--run-url", default=None)
    parser.add_argument(
        "--execution-profile",
        default=os.getenv("EXECUTION_PROFILE"),
        help="prod_safe or staging_full; shown in the stakeholder summary.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    webhook_url = os.getenv("GOOGLE_CHAT_WEBHOOK_URL")
    if not webhook_url:
        print("GOOGLE_CHAT_WEBHOOK_URL is not set. Skipping Google Chat notification.")
        return 0

    execution_profile = args.execution_profile
    if not execution_profile:
        try:
            from config.settings import get_settings

            execution_profile = get_settings().execution_profile
        except Exception:  # noqa: BLE001 - reporting must never crash the CI step
            execution_profile = None

    summary = collect_summary(args.junit_xml)
    payload = build_google_chat_payload(
        summary=summary,
        environment=args.environment,
        suite_name=args.suite_name,
        run_url=args.run_url,
        execution_profile=execution_profile,
    )
    send_google_chat_message(webhook_url, payload)
    print("Google Chat notification sent.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
