"""
Dark and Darker Market Scraper
Entry point — same CLI menu as the original, now writes to PostgreSQL.
"""
import time
from dotenv import load_dotenv

load_dotenv()  # loads DATABASE_URL from scraper/.env if present

import db
from scraper import MarketplaceScraper


def run_scan(scraper, num_refreshes, delay=3):
    run_id = db.start_run()
    total_inserted = 0
    error_msg = None

    try:
        print(f"\nStarting scan ({num_refreshes} refresh(es))...")
        for i in range(num_refreshes):
            print(f"\n--- Scan {i + 1}/{num_refreshes} ---")
            items = scraper.scrape_marketplace_items()
            inserted = db.save_items(items)
            total_inserted += inserted
            print(f"  Saved {inserted} rows to database (total this run: {total_inserted})")

            if i < num_refreshes - 1:
                scraper.click_refresh_button()
                time.sleep(delay)

    except Exception as e:
        error_msg = str(e)
        print(f"Scan error: {e}")

    db.finish_run(run_id, total_inserted, error_msg)
    print(f"\nScan complete. {total_inserted} rows inserted.")


def main():
    print("Dark and Darker Market Scraper")
    print("================================")
    print("1. Calibrate table layout")
    print("2. Capture test screenshot")
    print("3. Run marketplace scan")
    choice = input("Enter choice (1-3): ").strip()

    scraper = MarketplaceScraper()

    if choice == "1":
        scraper.calibrate_table_layout(wait_for_key=True)

    elif choice == "2":
        scraper.capture_test_screenshot(wait_for_key=True)

    elif choice == "3":
        try:
            num_refreshes = int(input("Number of refreshes (1-20): "))
            num_refreshes = max(1, min(num_refreshes, 20))
        except ValueError:
            num_refreshes = 1

        print("\nSwitch to your game window.")
        scraper.wait_for_trigger_key("space")
        run_scan(scraper, num_refreshes)

    else:
        print("Invalid choice.")


if __name__ == "__main__":
    main()
