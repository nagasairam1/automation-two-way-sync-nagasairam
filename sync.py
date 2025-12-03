import argparse
import time

from logic.sync_logic import sync_all_leads_to_tasks, sync_tasks_to_leads
from utils.logger import logger  # noqa: F401  # ensure logger config is loaded


def main() -> None:
    parser = argparse.ArgumentParser(description="Two-way sync between Airtable Leads and Trello Tasks")
    parser.add_argument(
        "--full",
        action="store_true",
        help="Run a one-off full sync (Airtable -> Trello, then Trello -> Airtable).",
    )
    parser.add_argument(
        "--poll",
        action="store_true",
        help="Continuously poll every 60 seconds and sync both directions.",
    )
    args = parser.parse_args()

    if args.full:
        logger.info("Running one-off full sync...")
        sync_all_leads_to_tasks()
        sync_tasks_to_leads()
        logger.info("Full sync completed.")
        return

    if args.poll:
        logger.info("Starting polling sync loop (every 60 seconds)...")
        try:
            while True:
                sync_all_leads_to_tasks()
                sync_tasks_to_leads()
                time.sleep(60)
        except KeyboardInterrupt:
            logger.info("Stopping polling loop.")
        return

    parser.print_help()


if __name__ == "__main__":
    main()
