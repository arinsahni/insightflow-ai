"""Maintainable food-delivery product feedback taxonomy."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TaxonomyRule:
    """One deterministic theme/subtheme rule and its risk context."""

    theme: str
    subtheme: str
    phrases: tuple[str, ...]
    keywords: tuple[str, ...] = ()
    business_risks: tuple[str, ...] = ("Customer satisfaction risk",)
    critical_keywords: tuple[str, ...] = ()


THEMES: tuple[str, ...] = (
    "Delivery Experience", "Payment and Checkout", "Refunds and Cancellations",
    "Coupons and Pricing", "App Performance", "Login and Account",
    "Search and Discovery", "Order Tracking", "Restaurant Experience",
    "Customer Support", "Food Quality", "Missing or Incorrect Items",
    "Fees and Charges", "Subscription or Loyalty", "Feature Request",
    "Positive Feedback", "Other",
)

TAXONOMY: tuple[TaxonomyRule, ...] = (
    TaxonomyRule("Delivery Experience", "Late delivery", ("late delivery", "delivery arrived late", "order took over an hour", "late order"), ("late", "delayed"), ("Customer satisfaction risk", "Retention risk")),
    TaxonomyRule("Delivery Experience", "Delivery partner behavior", ("delivery partner was rude", "rider was rude"), ("rider", "driver"), ("Customer satisfaction risk", "Operational risk")),
    TaxonomyRule("Delivery Experience", "Incorrect ETA", ("incorrect eta", "inaccurate delivery estimate", "estimate said"), ("eta",), ("Customer satisfaction risk", "Retention risk")),
    TaxonomyRule("Delivery Experience", "Unable to contact delivery partner", ("cannot contact the rider", "unable to contact delivery partner"), ("contact rider",), ("Operational risk",)),
    TaxonomyRule("Payment and Checkout", "Payment failed", ("payment failed", "unable to pay", "money deducted"), ("payment", "checkout"), ("Conversion risk", "Revenue risk"), ("money deducted", "unable to order")),
    TaxonomyRule("Payment and Checkout", "UPI issue", ("upi failed", "upi issue"), ("upi",), ("Conversion risk", "Revenue risk")),
    TaxonomyRule("Payment and Checkout", "Card issue", ("card declined", "card issue"), ("card",), ("Conversion risk", "Revenue risk")),
    TaxonomyRule("Payment and Checkout", "Duplicate charge", ("charged twice", "duplicate charge"), ("double charged",), ("Trust risk", "Revenue risk"), ("charged twice",)),
    TaxonomyRule("Payment and Checkout", "Checkout friction", ("checkout failed", "checkout problem"), ("checkout",), ("Conversion risk",)),
    TaxonomyRule("Refunds and Cancellations", "Refund delayed", ("refund is still pending", "refund delayed"), ("refund pending",), ("Trust risk", "Retention risk")),
    TaxonomyRule("Refunds and Cancellations", "Refund not received", ("refund not received", "no refund"), ("refund",), ("Trust risk", "Retention risk"), ("refund not received",)),
    TaxonomyRule("Refunds and Cancellations", "Cancellation issue", ("cannot cancel", "cancellation issue"), ("cancel",), ("Retention risk",)),
    TaxonomyRule("Refunds and Cancellations", "Cancellation fee", ("cancellation fee",), ("cancel fee",), ("Trust risk",)),
    TaxonomyRule("Coupons and Pricing", "Coupon invalid", ("coupon invalid", "coupon expired"), ("coupon",), ("Conversion risk",)),
    TaxonomyRule("Coupons and Pricing", "Coupon not applied", ("coupon not applied", "coupon disappeared"), ("discount",), ("Conversion risk",)),
    TaxonomyRule("Coupons and Pricing", "Discount issue", ("discount issue", "discount missing"), ("discount",), ("Conversion risk",)),
    TaxonomyRule("Coupons and Pricing", "Price mismatch", ("price mismatch", "price changed"), ("pricing",), ("Trust risk",)),
    TaxonomyRule("App Performance", "Crash", ("app crashes", "app crash", "keeps crashing"), ("crash",), ("Conversion risk", "Retention risk"), ("crash",)),
    TaxonomyRule("App Performance", "Slow loading", ("app is slow", "slow loading"), ("slow", "lag"), ("Conversion risk",)),
    TaxonomyRule("App Performance", "UI bug", ("ui bug", "button not working"), ("bug",), ("Conversion risk",)),
    TaxonomyRule("App Performance", "Update issue", ("latest update", "after update"), ("update",), ("Retention risk",)),
    TaxonomyRule("App Performance", "App freeze", ("app freeze", "app frozen"), ("freeze", "frozen"), ("Conversion risk",)),
    TaxonomyRule("Login and Account", "OTP issue", ("otp never arrives", "otp not received", "otp issue"), ("otp",), ("Conversion risk", "Retention risk")),
    TaxonomyRule("Login and Account", "Login failure", ("cannot log in", "login failed", "login impossible"), ("login",), ("Conversion risk", "Retention risk"), ("login impossible",)),
    TaxonomyRule("Login and Account", "Account blocked", ("account blocked", "account locked"), ("blocked",), ("Trust risk", "Retention risk"), ("account blocked",)),
    TaxonomyRule("Login and Account", "Profile issue", ("profile issue", "cannot edit profile"), ("profile",), ("Customer satisfaction risk",)),
    TaxonomyRule("Search and Discovery", "Restaurant search", ("restaurant search", "find a restaurant"), ("search",), ("Conversion risk",)),
    TaxonomyRule("Search and Discovery", "Filters and sorting", ("filters and sorting", "sort restaurants"), ("filter", "sorting"), ("Conversion risk",)),
    TaxonomyRule("Search and Discovery", "No relevant results", ("no relevant results", "search results are irrelevant"), ("results",), ("Conversion risk",)),
    TaxonomyRule("Search and Discovery", "Personalization", ("recommendations match", "better recommendations"), ("recommendations", "personalization"), ("Low direct business risk",)),
    TaxonomyRule("Order Tracking", "Tracking inaccurate", ("tracking is inaccurate", "wrong tracking"), ("tracking",), ("Customer satisfaction risk", "Operational risk")),
    TaxonomyRule("Order Tracking", "Tracking unavailable", ("tracking stopped", "cannot track"), ("tracking",), ("Customer satisfaction risk",)),
    TaxonomyRule("Order Tracking", "Delivery status issue", ("delivery status", "status not updating"), ("status",), ("Operational risk",)),
    TaxonomyRule("Restaurant Experience", "Restaurant unavailable", ("restaurant unavailable", "restaurant closed"), ("restaurant",), ("Conversion risk",)),
    TaxonomyRule("Restaurant Experience", "Menu unavailable", ("menu unavailable", "menu missing"), ("menu",), ("Conversion risk",)),
    TaxonomyRule("Restaurant Experience", "Restaurant cancellation", ("restaurant cancelled", "restaurant canceled"), ("restaurant cancellation",), ("Operational risk",)),
    TaxonomyRule("Customer Support", "Slow response", ("support did not reply", "slow response"), ("support",), ("Customer satisfaction risk", "Retention risk")),
    TaxonomyRule("Customer Support", "Unhelpful support", ("support was unhelpful", "support has not resolved"), ("support",), ("Retention risk",)),
    TaxonomyRule("Customer Support", "Unable to contact support", ("cannot contact support", "unable to contact support"), ("support",), ("Operational risk",)),
    TaxonomyRule("Food Quality", "Cold food", ("food was cold", "cold food"), ("cold",), ("Customer satisfaction risk",)),
    TaxonomyRule("Food Quality", "Poor taste", ("poor taste", "tasted bad"), ("taste",), ("Customer satisfaction risk",)),
    TaxonomyRule("Food Quality", "Stale food", ("stale food", "not fresh"), ("stale",), ("Trust risk",)),
    TaxonomyRule("Food Quality", "Food safety", ("food poisoning", "unsafe food"), ("poisoning", "unsafe"), ("Trust risk",), ("food poisoning", "unsafe")),
    TaxonomyRule("Missing or Incorrect Items", "Missing item", ("item was missing", "items were missing", "missing item"), ("missing",), ("Trust risk", "Operational risk")),
    TaxonomyRule("Missing or Incorrect Items", "Wrong order", ("wrong order", "incorrect order"), ("wrong",), ("Trust risk", "Operational risk")),
    TaxonomyRule("Missing or Incorrect Items", "Incorrect quantity", ("incorrect quantity", "wrong quantity"), ("quantity",), ("Operational risk",)),
    TaxonomyRule("Fees and Charges", "High delivery fee", ("delivery fees are too high", "high delivery fee"), ("fee",), ("Conversion risk",)),
    TaxonomyRule("Fees and Charges", "Hidden charge", ("hidden charge", "unexpected charge"), ("charge",), ("Trust risk",)),
    TaxonomyRule("Fees and Charges", "Small-order fee", ("small order fee",), ("small-order",), ("Conversion risk",)),
    TaxonomyRule("Fees and Charges", "Surge pricing", ("surge pricing",), ("surge",), ("Conversion risk",)),
    TaxonomyRule("Subscription or Loyalty", "Membership benefit issue", ("subscription benefit", "membership benefit"), ("subscription", "membership"), ("Retention risk",)),
    TaxonomyRule("Subscription or Loyalty", "Loyalty points issue", ("loyalty points", "points missing"), ("loyalty",), ("Retention risk",)),
    TaxonomyRule("Subscription or Loyalty", "Subscription pricing", ("subscription pricing", "membership price"), ("subscription",), ("Revenue risk",)),
    TaxonomyRule("Feature Request", "Dark mode", ("add dark mode", "dark mode"), (), ("Low direct business risk",)),
    TaxonomyRule("Feature Request", "Scheduled delivery", ("scheduled delivery", "schedule delivery", "scheduled ordering"), (), ("Low direct business risk",)),
    TaxonomyRule("Feature Request", "Reorder", ("reorder option", "one-tap reorder"), (), ("Low direct business risk",)),
    TaxonomyRule("Feature Request", "Better filters", ("more filters", "better filters"), (), ("Low direct business risk",)),
    TaxonomyRule("Feature Request", "Personalization", ("personalized recommendations", "personalization option"), (), ("Low direct business risk",)),
    TaxonomyRule("Positive Feedback", "Fast delivery", ("delivery was fast", "arrived on time", "reached me on time"), ("fast",), ("Low direct business risk",)),
    TaxonomyRule("Positive Feedback", "Easy app experience", ("easy to use", "app is easy"), ("smooth",), ("Low direct business risk",)),
    TaxonomyRule("Positive Feedback", "Good support", ("support was polite", "support fixed"), ("helpful",), ("Low direct business risk",)),
    TaxonomyRule("Positive Feedback", "Good food", ("food tasted fresh", "great food", "food was delicious"), ("fresh", "delicious"), ("Low direct business risk",)),
    TaxonomyRule("Positive Feedback", "General praise", ("love this app", "excellent service", "great app"), ("great", "excellent"), ("Low direct business risk",)),
    TaxonomyRule("Other", "Ambiguous", (), ()),
)

PRIMARY_RISK_BY_THEME: dict[str, str] = {
    rule.theme: rule.business_risks[0] for rule in TAXONOMY
}
PRIMARY_RISK_BY_THEME.update({
    "Payment and Checkout": "Conversion risk",
    "Refunds and Cancellations": "Trust risk",
    "App Performance": "Conversion risk",
    "Delivery Experience": "Customer satisfaction risk",
    "Feature Request": "Low direct business risk",
    "Other": "Low direct business risk",
})

BUSINESS_RISK_SCORES: dict[str, float] = {
    "Revenue risk": 85.0, "Retention risk": 80.0, "Trust risk": 90.0,
    "Operational risk": 70.0, "Conversion risk": 80.0,
    "Customer satisfaction risk": 65.0, "Low direct business risk": 20.0,
}

CRITICAL_KEYWORDS: tuple[str, ...] = (
    "money deducted", "charged twice", "unable to order", "account blocked",
    "refund not received", "scam", "unsafe", "fraud", "food poisoning",
    "crash", "login impossible",
)
