"""Generate the deterministic fictional Phase 1 review dataset."""

from __future__ import annotations

import csv
from datetime import date, timedelta
from pathlib import Path


OUTPUT = Path(__file__).resolve().parent.parent / "data" / "sample_reviews.csv"

TEMPLATES = (
    ("My delivery arrived {delay} minutes late and the food was cold.", 1),
    ("The order reached me on time and everything was packed well.", 5),
    ("I received the wrong order and support has not resolved it.", 1),
    ("Payment failed twice on UPI even though my bank account was charged.", 1),
    ("The refund is still pending after {days} days.", 2),
    ("The coupon appeared valid but disappeared during checkout.", 2),
    ("The app crashes whenever I open the cart after the latest update.", 1),
    ("OTP never arrives, so I cannot log in to my account.", 1),
    ("The delivery estimate said 20 minutes but the order took over an hour.", 2),
    ("Restaurant search is fast and helped me find a good nearby place.", 5),
    ("Order tracking stopped updating while the rider was on the way.", 2),
    ("Customer support was polite and fixed my issue quickly.", 5),
    ("The food tasted fresh and the portions were generous.", 5),
    ("Two items were missing, and I was charged for both.", 1),
    ("Delivery fees are too high for restaurants less than a kilometre away.", 2),
    ("The subscription free-delivery benefit makes regular orders worthwhile.", 4),
    ("Please add dark mode because I usually order late at night.", 4),
    ("I need an option to schedule delivery for tomorrow's lunch.", 4),
    ("Please add a one-tap reorder option for my regular meals.", 4),
    ("More filters for cuisine, price, and delivery time would be useful.", 3),
    ("Recommendations have improved and now match what I usually order.", 5),
    ("The app is slow, tracking is inaccurate, and support did not reply.", 1),
    ("Good", 4),
    ("Not working", 1),
)

CITIES = ("Bengaluru", "Mumbai", "Delhi NCR", "Hyderabad", "Chennai", "Pune", "Kolkata", "Ahmedabad")
ANDROID_DEVICES = ("Samsung Galaxy", "OnePlus", "Pixel", "Xiaomi", "Nothing Phone")
IOS_DEVICES = ("iPhone 13", "iPhone 14", "iPhone 15", "iPhone SE")
SEGMENTS = ("New customer", "Regular", "Subscriber", "Lapsed", "High frequency")
ANDROID_VERSIONS = ("5.8.0", "5.8.1", "5.9.0", "5.9.1")
IOS_VERSIONS = ("5.7.2", "5.8.0", "5.8.2", "5.9.0")


def build_rows() -> list[dict[str, object]]:
    """Create 320 deterministic rows spanning more than 90 days."""
    rows: list[dict[str, object]] = []
    start = date(2025, 1, 1)
    for index in range(312):
        template, base_rating = TEMPLATES[index % len(TEMPLATES)]
        platform = "Android" if index % 2 == 0 else "iOS"
        review_text = template.format(delay=35 + index % 50, days=4 + index % 12)
        rows.append(
            {
                "review_id": f"REV-{index + 1:04d}",
                "date": (start + timedelta(days=index % 120)).isoformat(),
                "rating": min(5, max(1, base_rating + (1 if index % 19 == 0 else 0))),
                "review_text": review_text,
                "platform": platform,
                "app_version": (
                    ANDROID_VERSIONS[index % len(ANDROID_VERSIONS)]
                    if platform == "Android"
                    else IOS_VERSIONS[index % len(IOS_VERSIONS)]
                ),
                "country": CITIES[index % len(CITIES)],
                "device": (
                    ANDROID_DEVICES[index % len(ANDROID_DEVICES)]
                    if platform == "Android"
                    else IOS_DEVICES[index % len(IOS_DEVICES)]
                ),
                "user_segment": SEGMENTS[index % len(SEGMENTS)],
            }
        )

    # Deliberate missing optional values for future validation demonstrations.
    for index, field in ((7, "app_version"), (31, "country"), (58, "device"), (87, "rating"), (129, "user_segment")):
        rows[index][field] = ""

    # Eight exact duplicates retain the original review IDs intentionally.
    rows.extend(dict(rows[index]) for index in (3, 24, 48, 72, 96, 144, 192, 240))
    return rows


def main() -> None:
    """Write the sample CSV using a stable column order."""
    rows = build_rows()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
