"""Generate InsightFlow's deterministic, fully synthetic fintech review dataset."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from time import perf_counter
from typing import Iterable

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT = PROJECT_ROOT / "data" / "sample_reviews.csv"
START_DATE = date(2025, 7, 1)
END_DATE = date(2026, 6, 30)

REQUIRED_COLUMNS = (
    "review_id", "date", "rating", "review_text", "platform", "app_version",
    "country", "city", "device", "user_segment", "subscription_tier",
    "customer_tenure_months", "acquisition_channel", "language",
    "support_ticket_created", "verified_user",
)

RELEASES: tuple[tuple[date, str], ...] = (
    (date(2025, 7, 1), "3.0.0"),
    (date(2025, 8, 1), "3.0.1"),
    (date(2025, 9, 1), "3.1.0"),
    (date(2025, 10, 1), "3.1.1"),
    (date(2025, 11, 1), "3.2.0"),
    (date(2025, 12, 1), "3.2.1"),
    (date(2026, 1, 15), "3.2.2"),
    (date(2026, 3, 1), "3.3.0"),
    (date(2026, 4, 1), "3.3.1"),
    (date(2026, 5, 1), "3.4.0"),
)

PLATFORM_DEVICES = {
    "Android": (
        "Samsung Galaxy S23", "Samsung Galaxy A54", "OnePlus 12", "OnePlus Nord",
        "Google Pixel 8", "Xiaomi Redmi Note 13", "Nothing Phone 2", "Motorola Edge",
    ),
    "iOS": ("iPhone 13", "iPhone 14", "iPhone 15", "iPhone 15 Pro", "iPhone SE"),
    "Web": (
        "Chrome on macOS", "Chrome on Windows", "Safari on macOS",
        "Edge on Windows", "Firefox on Linux",
    ),
}

COUNTRY_CITIES = {
    "India": ("Delhi", "Mumbai", "Bengaluru", "Hyderabad", "Pune", "Chennai", "Kolkata", "Ahmedabad", "Jaipur", "Bhopal"),
    "United States": ("New York", "San Francisco"),
    "United Kingdom": ("London", "Manchester"),
    "Singapore": ("Singapore",),
    "Australia": ("Sydney", "Melbourne"),
    "United Arab Emirates": ("Dubai", "Abu Dhabi"),
}

ISSUES: dict[str, tuple[str, ...]] = {
    "app": (
        "the app crashes on startup", "the app freeze happens after login",
        "the app is slow when the dashboard loads", "there is lag during payment",
        "the screen goes blank after the latest update", "the app crash opens transaction history",
        "the update installation keeps failing", "battery drain is much worse now",
    ),
    "payment": (
        "payment failed but money deducted", "the transfer is still payment pending",
        "I was charged twice for one payment", "the recipient was not credited",
        "the QR payment failed at checkout", "card declined even though funds are available",
        "merchant payment took hours to confirm", "checkout failed during bill payment",
    ),
    "login": (
        "OTP not received so I cannot log in", "Face ID fails every time",
        "the session expiry happens too quickly", "password reset is stuck in a loop",
        "device verification keeps repeating", "my account blocked without an explanation",
        "login failed after the update", "profile details cannot be edited",
    ),
    "refund": (
        "refund not received after ten days", "the refund is still pending",
        "the refund delayed again", "I cannot cancel the transfer",
        "a cancellation fee appeared without warning",
    ),
    "fees": (
        "the hidden charge was not shown earlier", "the transfer fee is too high",
        "there is an unexpected charge on my statement", "subscription pricing is unclear",
        "international conversion fee is excessive", "small order fee makes no sense",
    ),
    "support": (
        "support did not reply for three days", "support was unhelpful and sent a generic reply",
        "I cannot contact support", "the ticket was closed before resolution",
        "support fixed the issue but the slow response was frustrating",
    ),
    "notifications": (
        "transaction status not updating", "the payment notification arrived late",
        "transaction alerts are missing", "I receive duplicate notification messages",
        "there are too many promotional alerts",
    ),
    "kyc": (
        "document upload has a UI bug", "selfie verification is not working",
        "approval is delayed and I cannot log in", "the app asks for device verification again",
        "KYC status not updating",
    ),
    "cards": (
        "card issue controls are not working", "card declined at a regular merchant",
        "the replacement card delivery arrived late", "my card freeze button not working",
    ),
    "subscription": (
        "membership benefit is missing", "loyalty points are not showing",
        "subscription pricing changed unexpectedly", "points missing after a bill payment",
    ),
    "search": (
        "search results are irrelevant", "filters and sorting reset every time",
        "transaction search is slow", "no relevant results appear in transaction history",
    ),
    "tracking": (
        "tracking is inaccurate for the card delivery", "delivery status not updating",
        "I cannot track the replacement card",
    ),
    "security": (
        "this duplicate charge looks like fraud", "an unrecognized transaction appeared",
        "security alerts arrived too late", "I need help because this looks like a scam",
    ),
    "positive": (
        "great app and the interface is clean", "payments are fast and reliable now",
        "support fixed my issue quickly", "the latest version feels smooth and easy to use",
        "the refund arrived much faster than expected", "onboarding was simple",
        "transaction alerts are useful", "excellent service and reliable transfers",
    ),
}

FEATURES: tuple[tuple[str, str], ...] = (
    ("Dark mode", "dark mode"),
    ("Scheduled payments", "scheduled delivery for recurring payments"),
    ("Reorder", "a one-tap reorder option for bill payments"),
    ("Advanced filters", "better filters and sorting for transaction history"),
    ("Personalization", "personalized recommendations for spending"),
    ("CSV export", "CSV export for transactions"),
    ("PDF statements", "PDF statements"),
    ("Budgeting insights", "a budgeting dashboard with spending categories"),
    ("Recurring transfers", "recurring transfers"),
    ("Card controls", "card freeze controls"),
    ("Multi-currency", "multi-currency wallet support"),
    ("Widgets", "home-screen widgets"),
    ("Family accounts", "family account access"),
    ("Team access", "team access and permissions"),
    ("API integrations", "API access and bank integrations"),
)

OPENINGS = (
    "", "Honestly, ", "Since yesterday, ", "After the latest update, ",
    "For the last few days, ", "On my account, ", "I noticed that ",
)
CONTEXTS = (
    "", " This happened while paying a bill.", " It worked fine last week.",
    " I tried twice on Wi-Fi and mobile data.", " The rest of the app is useful.",
    " This is especially frustrating on a paid plan.",
)
CLOSINGS = (
    "", " Please fix this.", " Need a reliable solution.", " Kindly check asap.",
    " This should be clearer.", " Hope the next update resolves it.",
)
REQUEST_OPENINGS = (
    "Please add", "Would be useful if you added", "Wish there was",
    "Can you add", "Need an option to add", "It would be better if you added",
    "Add support for", "Feature request: please add",
)
HINGLISH_LINES = (
    "payment pending hai aur money deducted",
    "OTP nahi aa raha, cannot log in",
    "app baar baar crash ho rahi hai after update",
    "charges bahut high hain for this transfer",
    "support ka reply late mila",
)


@dataclass(frozen=True, slots=True)
class GeneratorConfig:
    """Configuration for one reproducible dataset generation run."""

    rows: int = 10_000
    seed: int = 42
    output: Path = DEFAULT_OUTPUT
    duplicate_rows: int | None = None
    invalid_dates: int | None = None
    invalid_ratings: int | None = None
    blank_texts: int | None = None
    missing_optional_values: int | None = None


@dataclass(frozen=True, slots=True)
class GenerationReport:
    """Auditable counts for generated and intentionally corrupted records."""

    base_rows: int
    duplicate_rows: int
    invalid_dates: int
    invalid_ratings: int
    missing_optional_values: int
    blank_texts: int
    hinglish_rows: int
    noisy_text_rows: int
    feature_request_rows: int
    final_rows: int
    runtime_seconds: float


def set_seed(seed: int) -> np.random.Generator:
    """Return an isolated NumPy random generator."""
    return np.random.default_rng(seed)


def select_version_for_date(review_date: date) -> str:
    """Return the newest app version released on a review date."""
    return next(version for released, version in reversed(RELEASES) if review_date >= released)


def generate_dates(rows: int, rng: np.random.Generator) -> list[date]:
    """Sample uneven dates with weekday, seasonal, launch, and incident effects."""
    dates = [START_DATE + timedelta(days=offset) for offset in range((END_DATE - START_DATE).days + 1)]
    weights = np.array([1.12 if value.weekday() < 5 else 0.82 for value in dates], dtype=float)
    weights *= 1 + 0.14 * np.sin(np.linspace(0, 4 * np.pi, len(dates)))
    for center, width, lift in (
        (date(2025, 12, 8), 18, 1.1),
        (date(2026, 3, 8), 10, 1.35),
        (date(2026, 5, 5), 12, 0.7),
    ):
        distance = np.array([abs((value - center).days) for value in dates])
        weights *= 1 + lift * np.exp(-((distance / width) ** 2))
    selected = rng.choice(len(dates), size=rows, p=weights / weights.sum())
    return [dates[index] for index in selected]


def select_user_profile(rng: np.random.Generator) -> tuple[str, str, int, str]:
    """Generate a correlated segment, tier, tenure, and acquisition channel."""
    segment = str(rng.choice(
        ["Returning User", "New User", "Power User", "Student", "Small Business"],
        p=[0.38, 0.25, 0.15, 0.14, 0.08],
    ))
    tier_probabilities = {
        "Returning User": [0.70, 0.27, 0.03],
        "New User": [0.84, 0.15, 0.01],
        "Power User": [0.48, 0.45, 0.07],
        "Student": [0.89, 0.105, 0.005],
        "Small Business": [0.30, 0.18, 0.52],
    }
    tier = str(rng.choice(["Free", "Premium", "Business"], p=tier_probabilities[segment]))
    tenure_ranges = {
        "New User": (0, 4), "Returning User": (4, 25), "Power User": (12, 49),
        "Small Business": (6, 49), "Student": (0, 19),
    }
    low, high = tenure_ranges[segment]
    tenure = int(rng.integers(low, high))
    channel_options = {
        "New User": (["Paid Search", "Social", "Referral", "Organic"], [0.32, 0.28, 0.25, 0.15]),
        "Student": (["Campus Campaign", "Referral", "Social", "Organic"], [0.36, 0.29, 0.25, 0.10]),
        "Small Business": (["Business Sales", "Partnership", "Organic"], [0.55, 0.30, 0.15]),
        "Power User": (["Organic", "Referral", "Partnership"], [0.55, 0.35, 0.10]),
        "Returning User": (["Organic", "Referral", "Paid Search", "Social"], [0.45, 0.25, 0.18, 0.12]),
    }
    channels, probabilities = channel_options[segment]
    return segment, tier, tenure, str(rng.choice(channels, p=probabilities))


def select_theme(
    review_date: date,
    version: str,
    platform: str,
    segment: str,
    rng: np.random.Generator,
) -> str:
    """Select an intent with product-release and segment-specific probabilities."""
    themes = list(ISSUES) + ["feature"]
    weights = {
        "app": 0.095, "payment": 0.115, "login": 0.065, "refund": 0.05,
        "fees": 0.065, "support": 0.055, "notifications": 0.05, "kyc": 0.04,
        "cards": 0.045, "subscription": 0.035, "search": 0.025, "tracking": 0.015,
        "security": 0.02, "positive": 0.17, "feature": 0.16,
    }
    if version == "3.2.1" and platform == "Android":
        weights["app"] *= 4.8
        weights["login"] *= 2.1
    elif version == "3.2.2":
        weights["app"] *= 0.48
    if version == "3.3.0":
        weights["payment"] *= 4.0
        weights["support"] *= 1.5
    elif version == "3.3.1":
        weights["payment"] *= 0.52
    if version == "3.4.0":
        weights["positive"] *= 2.2
        weights["app"] *= 0.38
        weights["feature"] *= 1.35
    if review_date >= date(2026, 4, 1):
        weights["fees"] *= 1 + 1.8 * ((review_date - date(2026, 4, 1)).days / 90)
    if segment == "New User":
        weights["kyc"] *= 3.8
        weights["login"] *= 1.6
    if segment in {"Power User", "Small Business"}:
        weights["feature"] *= 1.7
    probabilities = np.array([weights[theme] for theme in themes])
    return str(rng.choice(themes, p=probabilities / probabilities.sum()))


def select_feature(review_date: date, segment: str, rng: np.random.Generator) -> tuple[str, str]:
    """Select a requested capability with late-period and segment correlations."""
    weights = np.ones(len(FEATURES), dtype=float)
    if review_date >= date(2026, 4, 1):
        for index, (group, _) in enumerate(FEATURES):
            if group in {"CSV export", "PDF statements", "Budgeting insights"}:
                weights[index] *= 4.2
    if segment in {"Power User", "Small Business"}:
        for index, (group, _) in enumerate(FEATURES):
            if group in {"CSV export", "PDF statements", "API integrations", "Team access"}:
                weights[index] *= 4.0
    if segment == "Student":
        for index, (group, _) in enumerate(FEATURES):
            if group in {"Budgeting insights", "Dark mode", "Widgets"}:
                weights[index] *= 2.4
    index = int(rng.choice(len(FEATURES), p=weights / weights.sum()))
    return FEATURES[index]


def derive_rating(intent: str, version: str, rng: np.random.Generator) -> int:
    """Generate correlated but non-deterministic ratings."""
    if intent == "positive":
        probabilities = [0.005, 0.015, 0.06, 0.34, 0.58]
    elif intent == "feature":
        probabilities = [0.03, 0.07, 0.20, 0.38, 0.32]
    else:
        probabilities = [0.34, 0.25, 0.19, 0.12, 0.10]
    if version == "3.4.0" and intent != "feature":
        probabilities = np.asarray(probabilities, dtype=float)
        moved_from_one = probabilities[0] * 0.32
        moved_from_two = probabilities[1] * 0.22
        probabilities[0] -= moved_from_one
        probabilities[1] -= moved_from_two
        probabilities[3] += moved_from_two
        probabilities[4] += moved_from_one
    return int(rng.choice([1, 2, 3, 4, 5], p=np.asarray(probabilities) / np.sum(probabilities)))


def generate_review_text(
    intent: str,
    review_date: date,
    segment: str,
    language: str,
    rng: np.random.Generator,
) -> str:
    """Compose varied short, medium, and long synthetic customer feedback."""
    if language == "Hinglish" and intent != "feature":
        core = str(rng.choice(HINGLISH_LINES))
    elif intent == "feature":
        _, capability = select_feature(review_date, segment, rng)
        core = f"{rng.choice(REQUEST_OPENINGS)} {capability}"
    else:
        core = str(rng.choice(ISSUES[intent]))
    length = str(rng.choice(["short", "medium", "long"], p=[0.22, 0.59, 0.19]))
    if length == "short":
        text = core
    elif length == "medium":
        text = f"{rng.choice(OPENINGS)}{core}.{rng.choice(CLOSINGS)}"
    else:
        secondary = str(rng.choice(ISSUES["positive"] if intent != "positive" else ISSUES["notifications"]))
        text = f"{rng.choice(OPENINGS)}{core}.{rng.choice(CONTEXTS)} Also, {secondary}.{rng.choice(CLOSINGS)}"
    return " ".join(text.split())


def inject_text_noise(text: str, rng: np.random.Generator) -> str:
    """Add controlled public-safe typographical noise."""
    method = str(rng.choice(["lower", "upper", "spaces", "typo", "emoji", "punctuation"]))
    if method == "lower":
        return text.lower()
    if method == "upper":
        return text.upper()
    if method == "spaces":
        return f"  {text.replace(' ', '  ', 2)}  "
    if method == "typo":
        replacements = {"notification": "notifcation", "received": "recieved", "crash": "crsh", "Please": "pls"}
        for source, replacement in replacements.items():
            if source in text:
                return text.replace(source, replacement, 1)
        return text + " veryyy slow"
    if method == "emoji":
        return text + str(rng.choice([" 👍", " 😕", " 🙏", " ✅"]))
    return text.rstrip(".") + str(rng.choice(["!", "!!", "..."]))


def generate_primary_rows(config: GeneratorConfig) -> pd.DataFrame:
    """Generate the requested number of unique primary review rows."""
    if config.rows < 1:
        raise ValueError("rows must be at least 1")
    rng = set_seed(config.seed)
    dates = generate_dates(config.rows, rng)
    records: list[dict[str, object]] = []
    for index, review_date in enumerate(dates, start=1):
        platform = str(rng.choice(["Android", "iOS", "Web"], p=[0.55, 0.35, 0.10]))
        segment, tier, tenure, channel = select_user_profile(rng)
        country = str(rng.choice(list(COUNTRY_CITIES), p=[0.65, 0.10, 0.08, 0.05, 0.06, 0.06]))
        city = str(rng.choice(COUNTRY_CITIES[country]))
        version = select_version_for_date(review_date)
        intent = select_theme(review_date, version, platform, segment, rng)
        language = str(rng.choice(["English", "Hinglish", "Informal English"], p=[0.85, 0.10, 0.05]))
        text = generate_review_text(intent, review_date, segment, language, rng)
        noisy = language == "Informal English" or rng.random() < 0.055
        if noisy:
            text = inject_text_noise(text, rng)
        rating = derive_rating(intent, version, rng)
        sensitive_issue = intent in {"payment", "refund", "security", "login"}
        ticket_probability = 0.10 + (0.28 if rating <= 2 else 0) + (0.18 if sensitive_issue else 0) + (0.12 if tier in {"Premium", "Business"} else 0)
        records.append({
            "review_id": f"REV-{index:06d}",
            "date": review_date.isoformat(),
            "rating": rating,
            "review_text": text,
            "platform": platform,
            "app_version": version,
            "country": country,
            "city": city,
            "device": str(rng.choice(PLATFORM_DEVICES[platform])),
            "user_segment": segment,
            "subscription_tier": tier,
            "customer_tenure_months": tenure,
            "acquisition_channel": channel,
            "language": language,
            "support_ticket_created": bool(rng.random() < min(ticket_probability, 0.85)),
            "verified_user": rng.choice([True, False, pd.NA], p=[0.94, 0.045, 0.015]),
            "_noisy": noisy,
            "_intent": intent,
        })
    return pd.DataFrame.from_records(records)


def _scaled_count(configured: int | None, rows: int, default: int, rate: float) -> int:
    if configured is not None:
        return min(configured, rows)
    return min(default, max(1, round(rows * rate)))


def inject_data_quality_issues(
    primary: pd.DataFrame,
    config: GeneratorConfig,
) -> tuple[pd.DataFrame, GenerationReport]:
    """Inject bounded validation examples without changing shared constants."""
    started = perf_counter()
    rng = set_seed(config.seed + 10_007)
    output = primary.copy(deep=True)
    duplicate_count = _scaled_count(config.duplicate_rows, len(output), 150, 0.015)
    invalid_dates = _scaled_count(config.invalid_dates, len(output), 15, 0.0015)
    invalid_ratings = _scaled_count(config.invalid_ratings, len(output), 15, 0.0015)
    blank_texts = _scaled_count(config.blank_texts, len(output), 15, 0.0015)
    missing_values = _scaled_count(config.missing_optional_values, len(output), 45, 0.0045)

    available = np.arange(len(output))
    rng.shuffle(available)
    cursor = 0
    date_rows = available[cursor:cursor + invalid_dates]; cursor += invalid_dates
    rating_rows = available[cursor:cursor + invalid_ratings]; cursor += invalid_ratings
    blank_rows = available[cursor:cursor + blank_texts]; cursor += blank_texts
    missing_rows = available[cursor:cursor + missing_values]; cursor += missing_values
    casing_rows = available[cursor:cursor + min(12, max(1, len(output) // 1000))]; cursor += len(casing_rows)
    whitespace_rows = available[cursor:cursor + min(20, max(1, len(output) // 500))]; cursor += len(whitespace_rows)

    output.loc[date_rows, "date"] = rng.choice(["not-a-date", "2026-99-40", "31/31/2026"], size=len(date_rows))
    output["rating"] = output["rating"].astype("object")
    output.loc[rating_rows, "rating"] = rng.choice(
        ["unknown", "six", "bad-rating"], size=len(rating_rows)
    )
    output.loc[blank_rows, "review_text"] = rng.choice(["", "   ", "\t"], size=len(blank_rows))
    optional_fields = ["city", "customer_tenure_months", "acquisition_channel", "verified_user", "subscription_tier"]
    for row in missing_rows:
        output.loc[row, str(rng.choice(optional_fields))] = pd.NA
    output.loc[casing_rows, "platform"] = output.loc[casing_rows, "platform"].map(
        {"Android": "android", "iOS": "IOS", "Web": " web "}
    )
    output.loc[whitespace_rows, "review_text"] = "  " + output.loc[whitespace_rows, "review_text"].astype(str) + "  "

    duplicate_pool = np.setdiff1d(available, np.concatenate([date_rows, rating_rows, blank_rows, missing_rows, casing_rows, whitespace_rows]))
    duplicate_indices = rng.choice(duplicate_pool, size=duplicate_count, replace=False)
    duplicates = output.iloc[duplicate_indices].copy(deep=True)
    output = pd.concat([output, duplicates], ignore_index=True)

    report = GenerationReport(
        base_rows=len(primary),
        duplicate_rows=duplicate_count,
        invalid_dates=invalid_dates,
        invalid_ratings=invalid_ratings,
        missing_optional_values=missing_values,
        blank_texts=blank_texts,
        hinglish_rows=int(primary["language"].eq("Hinglish").sum()),
        noisy_text_rows=int(primary["_noisy"].sum()),
        feature_request_rows=int(primary["_intent"].eq("feature").sum()),
        final_rows=len(output),
        runtime_seconds=perf_counter() - started,
    )
    return output.drop(columns=["_noisy", "_intent"]), report


def validate_generated_distribution(dataframe: pd.DataFrame, report: GenerationReport) -> None:
    """Raise a clear error when a critical generation contract is violated."""
    missing = set(REQUIRED_COLUMNS) - set(dataframe.columns)
    if missing:
        raise ValueError(f"Generated data is missing required columns: {sorted(missing)}")
    primary = dataframe.iloc[:report.base_rows]
    if primary["review_id"].duplicated().any():
        raise ValueError("Primary review IDs are not unique.")
    normalized_platforms = primary["platform"].astype(str).str.strip().str.lower()
    if set(normalized_platforms) != {"android", "ios", "web"}:
        raise ValueError("All supported platforms must be represented.")
    parsed_dates = pd.to_datetime(primary["date"], errors="coerce")
    valid = parsed_dates.notna()
    expected_versions = parsed_dates.loc[valid].dt.date.map(select_version_for_date)
    if not primary.loc[valid, "app_version"].reset_index(drop=True).equals(expected_versions.reset_index(drop=True)):
        raise ValueError("App versions are inconsistent with release dates.")
    for platform, devices in PLATFORM_DEVICES.items():
        platform_rows = primary[normalized_platforms.eq(platform.lower())]
        if not platform_rows["device"].isin(devices).all():
            raise ValueError(f"{platform} rows contain incompatible devices.")
    text = dataframe["review_text"].fillna("").astype(str)
    if text.str.contains(r"https?://|www\.|[\w.+-]+@[\w.-]+\.\w+|\+?\d[\d -]{8,}\d", regex=True).any():
        raise ValueError("Generated reviews contain prohibited contact data or URLs.")
    if report.feature_request_rows < max(1, round(report.base_rows * 0.15)):
        raise ValueError("Feature-request coverage is below 15%.")
    if dataframe.duplicated().sum() != report.duplicate_rows:
        raise ValueError("Exact duplicate count does not match the generation report.")


def generate_dataset(config: GeneratorConfig) -> tuple[pd.DataFrame, GenerationReport]:
    """Generate, corrupt, and validate one deterministic synthetic dataset."""
    started = perf_counter()
    primary = generate_primary_rows(config)
    dataframe, interim = inject_data_quality_issues(primary, config)
    report = GenerationReport(
        interim.base_rows, interim.duplicate_rows, interim.invalid_dates,
        interim.invalid_ratings, interim.missing_optional_values, interim.blank_texts,
        interim.hinglish_rows, interim.noisy_text_rows, interim.feature_request_rows,
        interim.final_rows, perf_counter() - started,
    )
    validate_generated_distribution(dataframe, report)
    return dataframe.loc[:, REQUIRED_COLUMNS], report


def write_dataset(dataframe: pd.DataFrame, output: Path) -> None:
    """Write a stable UTF-8 CSV, creating its parent directory."""
    output.parent.mkdir(parents=True, exist_ok=True)
    dataframe.to_csv(output, index=False, encoding="utf-8")


def print_generation_report(dataframe: pd.DataFrame, report: GenerationReport) -> None:
    """Print an inspectable generation and distribution summary."""
    print("InsightFlow synthetic dataset generated")
    print(f"Base rows: {report.base_rows:,}")
    print(f"Duplicate rows injected: {report.duplicate_rows:,}")
    print(f"Invalid dates: {report.invalid_dates:,}")
    print(f"Invalid ratings: {report.invalid_ratings:,}")
    print(f"Missing optional values: {report.missing_optional_values:,}")
    print(f"Blank review texts: {report.blank_texts:,}")
    print(f"Feature-request rows: {report.feature_request_rows:,}")
    print(f"Hinglish rows: {report.hinglish_rows:,}")
    print(f"Noisy-text rows: {report.noisy_text_rows:,}")
    print(f"Final CSV rows: {report.final_rows:,}")
    print(f"Runtime: {report.runtime_seconds:.3f}s")
    for column in ("platform", "app_version", "country", "user_segment", "subscription_tier", "rating"):
        print(f"\n{column} distribution")
        print(dataframe[column].value_counts(dropna=False).to_string())


def parse_args(arguments: Iterable[str] | None = None) -> argparse.Namespace:
    """Parse command-line generation options."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rows", type=int, default=10_000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args(arguments)


def main(arguments: Iterable[str] | None = None) -> None:
    """Generate and write the configured sample dataset."""
    args = parse_args(arguments)
    dataframe, report = generate_dataset(GeneratorConfig(args.rows, args.seed, args.output))
    write_dataset(dataframe, args.output)
    print_generation_report(dataframe, report)


if __name__ == "__main__":
    main()
