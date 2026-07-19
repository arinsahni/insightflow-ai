"""Explainable local feature-request intent and taxonomy classification."""

from __future__ import annotations

from dataclasses import dataclass
import re
import unicodedata

import pandas as pd


@dataclass(frozen=True, slots=True)
class FeatureTaxonomyRule:
    """Immutable vocabulary and tie-break priority for one request group."""

    phrases: tuple[str, ...]
    keywords: tuple[str, ...] = ()
    keyword_combinations: tuple[tuple[str, ...], ...] = ()
    exclusions: tuple[str, ...] = ()
    priority: int = 100


FEATURE_REQUEST_GROUPS: tuple[str, ...] = (
    "Data Export and Reports",
    "Budgeting and Spending Insights",
    "Scheduled and Recurring Payments",
    "Dark Mode and Appearance",
    "Multi-Currency and International Support",
    "Card Controls",
    "Search, Filters, and Sorting",
    "Widgets and Quick Access",
    "Family and Shared Accounts",
    "Team and Business Access",
    "API and Integrations",
    "Notifications and Custom Alerts",
    "Security and Biometric Controls",
    "Bank and Account Management",
    "Personalization",
    "Statements and Transaction History",
    "Rewards and Loyalty",
    "Customer Support Improvements",
    "Payment Methods and Wallets",
    "Other feature request",
)

FEATURE_REQUEST_TAXONOMY: dict[str, FeatureTaxonomyRule] = {
    "Data Export and Reports": FeatureTaxonomyRule((
        "csv export", "export csv", "export to csv", "download csv", "excel export",
        "export to excel", "xlsx export", "spreadsheet export", "export data",
        "data export", "transaction export", "export transactions",
        "download transactions", "download transaction data",
        "export transaction history", "export history", "download report",
        "export report", "custom report", "monthly report", "downloadable report",
        "reconciliation report", "gst report", "tax report", "save as pdf",
        "download as pdf", "pdf report", "pdf statements", "emailed report",
        "report download", "csv option", "excel option", "export option",
        "download option", "csv chahiye", "csv export chahiye",
        "statement download ka option do", "report download ka option do",
    ), keyword_combinations=(("export", "reconciliation"), ("download", "statement")), priority=1),
    "Budgeting and Spending Insights": FeatureTaxonomyRule((
        "budgeting", "budget planner", "budget tracker", "monthly budget",
        "weekly budget", "spending insights", "expense tracking", "expense tracker",
        "spending tracker", "spending categories", "expense categories",
        "custom spending categories", "category breakdown", "spending breakdown",
        "expense breakdown", "savings goal", "financial goal", "spending limit",
        "budget limit", "expense analytics", "spend analytics", "spending analytics",
        "money management", "cash flow insights", "cash flow dashboard",
        "monthly insights", "financial dashboard", "spending graph", "expense graph",
        "where my money goes", "spending by category", "kharcha tracking", "kharcha tracker",
        "spending ka breakdown", "budget tracker hona chahiye",
        "budgeting dashboard with spending categories",
    ), priority=2),
    "Scheduled and Recurring Payments": FeatureTaxonomyRule((
        "scheduled payment", "schedule payment", "schedule payments",
        "scheduled transfer", "recurring payment", "recurring payments",
        "recurring transfer", "recurring transfers", "recurring bank transfers",
        "automatic payment",
        "automatic transfer", "auto pay", "standing instruction",
        "future dated payment", "future payment", "repeat payment", "repeat transfer",
        "monthly transfer", "weekly transfer", "recurring bill", "scheduled bill",
        "payment schedule", "payment reminder", "scheduled bank transfer",
        "scheduled ordering", "one tap reorder option", "reorder option",
        "scheduled delivery for recurring payments", "recurring payment ka option do",
        "autopay ka option chahiye",
    ), exclusions=("payment pending", "pending payment", "delayed payment", "payment still processing", "payment not completed"), priority=3),
    "Dark Mode and Appearance": FeatureTaxonomyRule((
        "dark mode", "night mode", "dark theme", "black theme", "light theme",
        "theme selection", "choose theme", "custom theme", "font size",
        "larger font", "text size", "accessibility theme", "compact view",
        "appearance settings", "interface customization", "color theme",
        "colour theme", "high contrast", "dark mode add karo", "dark theme chahiye",
    ), priority=4),
    "Multi-Currency and International Support": FeatureTaxonomyRule((
        "multi currency", "multiple currencies", "foreign currency", "currency wallet",
        "currency conversion", "live exchange rate", "exchange rates",
        "international transfer support", "international payments", "overseas payment",
        "cross border transfer", "forex", "travel wallet", "usd wallet", "eur wallet",
        "gbp wallet", "usd account", "eur account", "gbp account", "remittance",
        "swift transfer", "global account", "international account", "foreign account",
        "currency support", "multi currency support karo",
    ), exclusions=("international transfer failed",), priority=5),
    "Card Controls": FeatureTaxonomyRule((
        "freeze card", "unfreeze card", "lock card", "unlock card", "card control",
        "card controls", "card limit", "set card limit", "spending limit for card",
        "atm limit", "atm withdrawal toggle", "online transaction toggle",
        "international transaction toggle", "contactless toggle",
        "disable contactless", "virtual card", "disposable virtual card",
        "replace card", "card pin control", "change card pin", "merchant control",
        "temporary card block", "block card temporarily", "card freeze controls",
        "card freeze ka option", "card limit set karne ka option",
    ), priority=6),
    "Search, Filters, and Sorting": FeatureTaxonomyRule((
        "advanced search", "better search", "transaction search", "search transactions",
        "search by merchant", "search by amount", "search by date",
        "search by category", "advanced filter", "advanced filters",
        "advanced transaction filters",
        "filter transactions", "filter by category", "filter by date",
        "filter by amount", "sort transactions", "sort by amount",
        "sorting by amount", "sort by date",
        "date range filter", "custom filter", "saved filter", "search history",
        "transaction tags", "better filters", "better filters and sorting",
        "filter option chahiye",
    ), keywords=("sorting",), priority=7),
    "Widgets and Quick Access": FeatureTaxonomyRule((
        "home screen widget", "lock screen widget", "ios widget", "android widget",
        "balance widget", "spending widget", "payment widget", "quick action",
        "shortcut", "quick transfer", "payment shortcut", "app shortcut",
        "glance view", "watch app", "smartwatch support", "apple watch", "wear os",
        "home screen widgets", "widget add karo", "quick access chahiye",
    ), keywords=("widgets",), priority=8),
    "Family and Shared Accounts": FeatureTaxonomyRule((
        "family account", "shared account", "joint account", "spouse access",
        "parent account", "child account", "teen account", "junior account",
        "family wallet", "shared wallet", "shared budget", "household account",
        "shared savings goal", "dependent account", "family card", "family profile",
        "family account access", "parent and child accounts",
        "family account ka feature", "joint account option",
    ), priority=9),
    "Team and Business Access": FeatureTaxonomyRule((
        "team access", "multiple users", "multi user access", "employee access",
        "staff accounts", "role based access", "user roles", "approval workflow",
        "approval permissions", "maker checker", "business dashboard",
        "company account", "invoice generation", "invoicing", "generate invoices",
        "bulk payments", "payroll", "vendor payments", "business reconciliation",
        "expense management", "team cards", "admin controls", "team members",
        "business users", "employee cards", "finance team access",
        "team access and permissions",
    ), priority=10),
    "API and Integrations": FeatureTaxonomyRule((
        "api access", "developer api", "public api", "rest api", "webhook",
        "webhooks", "sdk", "developer tools", "integration", "integrations",
        "integrate with", "zapier", "quickbooks", "xero", "tally",
        "erp integration", "crm integration", "accounting integration",
        "accounting software", "bank integration", "bank integrations", "bank sync",
        "open banking", "google sheets integration", "slack integration",
        "automation integration", "external integration",
        "api integration hona chahiye",
    ), priority=11),
    "Notifications and Custom Alerts": FeatureTaxonomyRule((
        "custom alert", "custom alerts", "spending alert", "low balance alert",
        "payment reminder", "bill reminder", "transaction alert settings",
        "notification settings", "choose notifications",
        "choose transaction notifications", "notification preferences",
        "disable promotional notifications", "turn off promotions", "alert threshold",
        "instant notification", "email notification", "sms alert", "push alert",
        "suspicious activity alert", "configurable alerts",
        "custom transaction alerts", "custom alert ka option chahiye",
    ), exclusions=("notification arrived late", "delayed notification", "missing notification"), priority=12),
    "Security and Biometric Controls": FeatureTaxonomyRule((
        "biometric lock", "app lock", "fingerprint lock", "face id", "face id lock",
        "biometric authentication", "face id authentication",
        "fingerprint authentication", "two factor authentication", "2fa",
        "passkey", "passkeys", "security key", "login approval",
        "device management", "trusted devices", "session management",
        "privacy controls", "hide balance", "transaction pin",
        "additional authentication", "biometric option chahiye", "app lock add karo",
    ), exclusions=("otp is not coming", "otp not received", "login failed"), priority=13),
    "Bank and Account Management": FeatureTaxonomyRule((
        "multiple bank accounts", "add another bank account", "link another bank account",
        "remove bank account", "unlink bank account", "change primary account",
        "change my primary account",
        "primary bank account", "account switching", "switch accounts",
        "account aggregation", "linked account management", "beneficiary management",
        "saved recipients", "manage beneficiaries",
        "close account option", "multiple account support", "bank linking",
        "multiple account support karo",
    ), priority=14),
    "Personalization": FeatureTaxonomyRule((
        "customize dashboard", "custom dashboard", "personalized dashboard",
        "rearrange cards", "rearrange dashboard", "custom labels",
        "nickname accounts", "account nicknames", "profile customization",
        "personalized recommendations",
        "custom home screen", "hide sections", "choose default account",
        "custom shortcuts", "personalized layout", "customize layout",
        "dashboard customization",
    ), keywords=("personalization",), priority=15),
    "Statements and Transaction History": FeatureTaxonomyRule((
        "monthly statement", "account statement", "bank statement",
        "transaction statement", "statement history", "statement archive",
        "older statements", "old statements", "full transaction history",
        "longer transaction history", "historical transactions",
        "transaction timeline", "transaction details", "merchant details",
        "statement email", "passbook", "digital passbook",
        "transaction receipt history", "transaction history", "view statements",
        "show older statements",
    ), exclusions=("download", "export", "pdf", "csv", "excel", "report"), priority=16),
    "Rewards and Loyalty": FeatureTaxonomyRule((
        "more rewards", "reward points", "cashback", "loyalty program",
        "referral rewards", "redeem points", "reward categories", "student rewards",
        "partner offers", "coupon support", "milestone rewards", "premium rewards",
        "reward redemption", "reward point redemption", "points history",
        "loyalty points", "cashback offers",
        "rewards chahiye",
    ), priority=17),
    "Customer Support Improvements": FeatureTaxonomyRule((
        "live chat", "chatbot", "call support", "callback option",
        "ticket tracking", "track support ticket", "escalation button",
        "escalate ticket", "support status", "in app help centre", "help center",
        "support history", "priority support", "human agent", "talk to a human",
        "screen sharing with support", "support chat", "callback request",
        "live agent",
    ), exclusions=("support is slow", "support did not respond", "support did not reply", "bad support", "agent was unhelpful", "ticket was closed"), priority=18),
    "Payment Methods and Wallets": FeatureTaxonomyRule((
        "apple pay", "google pay", "samsung pay", "wallet integration",
        "digital wallet", "upi lite", "payment method", "another payment method",
        "add payment method", "paypal", "tap to pay", "contactless payment",
        "qr payment support", "more qr options", "card network support",
        "rupay support", "bank card support", "wallet support",
        "wallet integration chahiye",
    ), priority=19),
}

_NORMALIZATION_REPLACEMENTS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\bmulticurrency\b"), "multi currency"),
    (re.compile(r"\bauto[\s-]?pay\b"), "auto pay"),
    (re.compile(r"\bdarkmode\b"), "dark mode"),
    (re.compile(r"\bfaceid\b"), "face id"),
    (re.compile(r"\bpls\b"), "please"),
)
_PUNCTUATION_RE = re.compile(r"[^\w\s]")
_WHITESPACE_RE = re.compile(r"\s+")
_INTENT_RE = re.compile(
    r"\b(?:please add|add an option|add support for|need an option|need a feature|"
    r"would like|would love|would be useful|it would help|it would be better if|"
    r"i wish|wish there was|"
    r"can you add|can you support|could you add|should have|should support|should allow|"
    r"why is there no|there should be|missing feature|feature request|option to|"
    r"ability to|allow users to|allow me to|allow us to|hope you add|please provide|"
    r"please introduce|introduce a feature|integrate with|support for|give us an option|"
    r"it needs a feature for|hona chahiye|option chahiye|add karo|support karo|"
    r"option do|let me|i want a|please show|please support)\b"
)
_IMPERATIVE_RE = re.compile(r"^(?:add|allow|support|show|download|provide|enable)\b")
_FALLBACK_INTENT_RE = re.compile(
    r"\b(?:please add|need an option|should have|would be useful|allow us to|"
    r"wish there was|feature request|add support for|can you add|"
    r"it would be better if|introduce a feature|please introduce)\b"
)
_COMPLAINT_ONLY_RE = re.compile(
    r"\b(?:i need my refund|i want my money back|i want my transfer completed|"
    r"payment should not fail|support should respond faster|"
    r"app needs to stop crashing|i need access to my account|"
    r"transfer should have arrived)\b"
)


@dataclass(frozen=True, slots=True)
class FeatureRequestResult:
    """Deterministic request-intent and canonical-group output."""

    is_feature_request: bool
    feature_request_text: str | None
    feature_request_confidence: float
    feature_request_group: str | None
    feature_request_method: str = "no_request_intent"
    feature_request_matched_terms: tuple[str, ...] = ()
    feature_request_score: float = 0.0

    @property
    def feature_request_detected(self) -> bool:
        """Compatibility alias for callers using the longer field name."""
        return self.is_feature_request


def normalize_feature_request_text(text: object) -> str:
    """Normalize classification text without changing its stored source value."""
    if text is None or pd.isna(text):
        return ""
    normalized = unicodedata.normalize("NFKC", str(text)).lower()
    normalized = normalized.replace("’", "'").replace("–", "-").replace("—", "-")
    for pattern, replacement in _NORMALIZATION_REPLACEMENTS:
        normalized = pattern.sub(replacement, normalized)
    normalized = _PUNCTUATION_RE.sub(" ", normalized.replace("-", " "))
    return _WHITESPACE_RE.sub(" ", normalized).strip()


def _score_rule(text: str, rule: FeatureTaxonomyRule) -> tuple[int, tuple[str, ...]]:
    if any(exclusion in text for exclusion in rule.exclusions):
        return 0, ()
    matched: list[str] = []
    score = 0
    for phrase in rule.phrases:
        if phrase in text:
            matched.append(phrase)
            score += 6 if " " in phrase else 2
    tokens = set(text.split())
    for keyword in rule.keywords:
        if keyword in tokens:
            matched.append(keyword)
            score += 2
    for combination in rule.keyword_combinations:
        if all(term in text for term in combination):
            matched.append(" + ".join(combination))
            score += 3
    return score, tuple(dict.fromkeys(matched))


def detect_feature_request(text: object) -> FeatureRequestResult:
    """Detect capability intent, score canonical groups, and apply fixed ties."""
    normalized = normalize_feature_request_text(text)
    if not normalized or _COMPLAINT_ONLY_RE.search(normalized):
        return FeatureRequestResult(False, None, 0.0, None)

    scored: list[tuple[int, int, str, tuple[str, ...]]] = []
    for group, rule in FEATURE_REQUEST_TAXONOMY.items():
        score, terms = _score_rule(normalized, rule)
        if score:
            scored.append((score, -rule.priority, group, terms))
    has_intent = bool(
        (
            scored
            and (
                _INTENT_RE.search(normalized)
                or _IMPERATIVE_RE.search(normalized)
                or re.match(r"^(?:i )?need\b", normalized)
            )
        )
        or (not scored and _FALLBACK_INTENT_RE.search(normalized))
    )
    if not has_intent:
        return FeatureRequestResult(False, None, 0.0, None)
    if not scored:
        return FeatureRequestResult(
            True, "Other requested capability", 0.58, "Other feature request",
            "intent_fallback", (), 0.0,
        )

    export_match = next(
        (item for item in scored if item[2] == "Data Export and Reports" and item[0] >= 6),
        None,
    )
    score, _, group, terms = export_match or max(
        scored, key=lambda item: (item[0], item[1])
    )
    confidence = 0.96 if score >= 12 else 0.90 if score >= 6 else 0.78 if score >= 3 else 0.68
    return FeatureRequestResult(
        True, group, confidence, group, "taxonomy_phrase", terms, float(score)
    )


def add_feature_request_columns(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Return a copy with backward-compatible request classification fields."""
    output = dataframe.copy()
    results = [detect_feature_request(text) for text in output["clean_text"]]
    output["is_feature_request"] = [result.is_feature_request for result in results]
    output["feature_request_detected"] = [result.is_feature_request for result in results]
    output["feature_request_text"] = [result.feature_request_text for result in results]
    output["feature_request_confidence"] = [result.feature_request_confidence for result in results]
    output["feature_request_group"] = [result.feature_request_group for result in results]
    output["feature_request_method"] = [result.feature_request_method for result in results]
    output["feature_request_matched_terms"] = [
        ", ".join(result.feature_request_matched_terms) if result.feature_request_matched_terms else None
        for result in results
    ]
    output["feature_request_score"] = [result.feature_request_score for result in results]
    return output
