"""
Merchant name normalization — deterministic, no AI.

Produces two outputs:
  merchant_key:          stable lowercase key for grouping (e.g., "netflix")
  merchant_display_name: human-readable name (e.g., "Netflix")

Rules applied (in order):
  1. Uppercase + trim
  2. Remove noise tokens (POS, DEBIT, CARD, PURCHASE, #, etc.)
  3. Remove trailing numeric IDs / reference numbers
  4. Collapse whitespace
  5. Derive display name (title case) and key (lowercase)
"""
import re

# Noise tokens to strip (case-insensitive, matched as whole words)
_NOISE_TOKENS = {
    "POS", "DEBIT", "CREDIT", "CARD", "PURCHASE", "PAYMENT",
    "CHECKCARD", "CHECK", "ACH", "VISA", "MASTERCARD", "AMEX",
    "SQ", "TST", "PP", "PAYPAL", "RECURRING", "AUTOPAY",
    "ONLINE", "MOBILE", "INST", "XFER", "WEB", "PMNT",
    "DDA", "PMT", "DR", "CR", "INT", "EXT",
}

# Regex: reference numbers, trailing digits, hash codes
_REF_PATTERN = re.compile(r'#\S+|\b\d{4,}\b|\*+\S*')

# Regex: non-alphanumeric (except spaces)
_NON_ALPHA = re.compile(r'[^A-Z0-9 ]')

# Regex: multiple spaces
_MULTI_SPACE = re.compile(r'\s{2,}')


def normalize_merchant(raw_description: str, plaid_merchant_name: str = None) -> dict:
    """
    Normalize a transaction description into a stable merchant key
    and a human-readable display name.

    Args:
        raw_description:    Transaction description from bank/Plaid
        plaid_merchant_name: Plaid's parsed merchant_name (if available)

    Returns:
        {
            "merchant_key": "netflix",
            "merchant_display_name": "Netflix"
        }
    """
    # Prefer Plaid's parsed merchant name if available and non-empty
    source = (plaid_merchant_name or "").strip()
    if not source:
        source = (raw_description or "").strip()

    if not source:
        return {"merchant_key": "unknown", "merchant_display_name": "Unknown"}

    # Step 1: Uppercase
    text = source.upper().strip()

    # Step 2: Remove reference numbers and hash codes
    text = _REF_PATTERN.sub("", text)

    # Step 3: Remove non-alphanumeric characters (keep spaces)
    text = _NON_ALPHA.sub(" ", text)

    # Step 4: Remove noise tokens
    words = text.split()
    cleaned = [w for w in words if w not in _NOISE_TOKENS]

    # Step 5: Collapse whitespace
    text = " ".join(cleaned).strip()

    # Step 6: Remove trailing standalone digits (e.g., "UBER 072515")
    text = re.sub(r'\s+\d{1,6}$', '', text)

    # Fallback if everything was stripped
    if not text:
        text = source.upper().strip()[:50]

    # Produce outputs
    merchant_key = _MULTI_SPACE.sub(" ", text).strip().lower().replace(" ", "_")
    merchant_display_name = text.title()

    return {
        "merchant_key": merchant_key,
        "merchant_display_name": merchant_display_name,
    }
