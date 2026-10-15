"""Insurance premium calculation and quote-book utilities."""

import math
import os
import secrets
import ssl
import tarfile
import urllib.request
from datetime import date, datetime
from urllib.parse import urlparse

from defusedxml import ElementTree as ET


quotes = {}
HOST = "127.0.0.1"
UNDERWRITER_TOKEN = os.environ.get("UNDERWRITER_TOKEN", "")
LOG_FILE = "premium_quotes.log"
BASE_RATES = {"health": 5000, "motor": 3000, "life": 8000}


# These parameters preserve the existing public calling interface.
# pylint: disable=too-many-arguments,too-many-positional-arguments
def calculate_premium(
    policy_type,
    age,
    sum_insured,
    smoker,
    claims,
    discounts=None,
):
    """Calculate a premium without mutating caller-provided values."""
    if discounts is None:
        discounts = []
    if policy_type not in BASE_RATES:
        raise ValueError(f"Unknown policy type: {policy_type}")
    if age < 0 or sum_insured < 0 or claims < 0:
        raise ValueError("Age, sum insured, and claims cannot be negative")
    if not isinstance(smoker, bool):
        raise TypeError("Smoker must be True or False")

    premium = BASE_RATES[policy_type] + sum_insured * 0.002
    if age > 45:
        premium *= 1.5
    if smoker:
        premium *= 1.3
    premium += claims * 1000
    premium -= sum(discounts)
    return max(0.0, premium)


def age_from_dob(dob):
    """Return the age for a date in DD-MM-YYYY format."""
    born = datetime.strptime(dob, "%d-%m-%Y").date()
    today = date.today()
    if born > today:
        raise ValueError("Date of birth cannot be in the future")
    return today.year - born.year - (
        (today.month, today.day) < (born.month, born.day)
    )


def policy_number():
    """Generate a policy number using a cryptographically secure token."""
    return f"POL-{secrets.randbelow(900000) + 100000}"


def save_quote(name, premium):
    """Store a quote in memory and append it to the quote log."""
    number = policy_number()
    while number in quotes:
        number = policy_number()
    quotes[number] = {"name": name, "premium": premium}
    with open(LOG_FILE, "a", encoding="utf-8") as quote_file:
        quote_file.write(f"{number},{name},{premium:.2f}\n")
    return number


def import_policies(xml_text):
    """Import valid policy records from partner XML."""
    root = ET.fromstring(xml_text)
    result = []
    for policy in root.findall("policy"):
        try:
            result.append(
                (
                    policy.get("type"),
                    int(policy.get("age")),
                    int(policy.get("sum")),
                )
            )
        except (TypeError, ValueError):
            continue
    return result


def fetch_rates(url):
    """Download rates using the default certificate-verifying TLS context."""
    if urlparse(url).scheme not in {"http", "https"}:
        raise ValueError("Rate URLs must use HTTP or HTTPS")
    context = ssl.create_default_context()
    # The scheme is validated above, so B310 is a false positive here.
    with urllib.request.urlopen(  # nosec B310
        url, context=context, timeout=10
    ) as response:
        return response.read()


def import_claim_documents(archive_path):
    """Safely extract customer claim documents without path traversal."""
    os.makedirs("claims_docs", exist_ok=True)
    with tarfile.open(archive_path) as archive:
        archive.extractall("claims_docs", filter="data")


def monthly_instalment(premium, months=12):
    """Return the monthly instalment, rounded up to the next paisa.

    Rounding up guarantees the instalments never collect less than the
    premium (flooring 8000 / 12 to 666 would lose Rs. 8 a year).
    """
    if months <= 0:
        raise ValueError("Months must be greater than zero")
    # Round first so float noise (e.g. 110.00000000000001) is not rounded up.
    return math.ceil(round(premium * 100 / months, 6)) / 100


def is_authorised(token):
    """Check an underwriter token supplied through the environment."""
    return bool(UNDERWRITER_TOKEN) and secrets.compare_digest(
        token, UNDERWRITER_TOKEN
    )


def renewal_due(start, years=1):
    """Return the renewal date for a YYYY-MM-DD start date."""
    start_date = datetime.strptime(start, "%Y-%m-%d").date()
    try:
        renewal = start_date.replace(year=start_date.year + years)
    except ValueError:
        renewal = start_date.replace(
            year=start_date.year + years, month=2, day=28
        )
    return renewal.strftime("%Y-%m-%d")


def print_quotes():
    """Print all quotes currently held in the quote book."""
    print("===== Quote Book =====")
    for index, number in enumerate(quotes, start=1):
        quote = quotes[number]
        print(index, number, quote["name"], "Rs.", quote["premium"])


def main():
    """Run the sample calculator workflow."""
    p1 = calculate_premium("health", 30, 500000, False, 0)
    p2 = calculate_premium("health", 30, 500000, False, 0)
    p3 = calculate_premium("motor", 50, 800000, False, 0)
    p4 = calculate_premium(
        "life", 25, 100000, False, 0, [3000, 3000, 3000]
    )
    print("Quote 1:", p1)
    print("Quote 2 (same customer details):", p2)
    print("Non-smoker aged 50:", p3)
    print("Life with stacked discounts:", p4)
    print("Age from DOB 31-12-1990:", age_from_dob("31-12-1990"))
    print("Monthly instalment:", monthly_instalment(p3))
    print("Renewal due:", renewal_due("2025-03-15"))
    print(
        "Imported:",
        import_policies(
            "<policies><policy type='health' age='40' sum='300000'/>"
            "<policy type='motor' age='abc' sum='1'/></policies>"
        ),
    )
    print("Saved as:", save_quote("Kiran", p1))
    print(
        "Authorised:",
        is_authorised(os.environ.get("UNDERWRITER_TOKEN", "")),
    )
    print("Server would listen on", HOST)
    print_quotes()


if __name__ == "__main__":
    main()
