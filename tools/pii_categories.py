"""PII type to category mapping for UI grouping."""

from __future__ import annotations

from tools.detect_pii import PIIType

# Category definitions — used by frontend to group PII types
PII_CATEGORIES: dict[str, list[PIIType]] = {
    "Names": [
        PIIType.PERSON,
    ],
    "Contact": [
        PIIType.EMAIL,
        PIIType.PHONE,
        PIIType.UPI_ID,
    ],
    "IDs": [
        PIIType.SSN,
        PIIType.AADHAAR,
        PIIType.PAN,
        PIIType.PASSPORT,
        PIIType.DRIVERS_LICENSE,
        PIIType.UK_NI_NUMBER,
        PIIType.CANADIAN_SIN,
        PIIType.US_EIN,
        PIIType.MEDICAL_RECORD,
    ],
    "Addresses": [
        PIIType.ADDRESS,
        PIIType.LOCATION,
    ],
    "Financial": [
        PIIType.CREDIT_CARD,
        PIIType.IBAN,
        PIIType.BANK_ACCOUNT,
        PIIType.SWIFT_BIC,
    ],
    "Credentials": [
        PIIType.API_KEY,
        PIIType.USERNAME_PASSWORD,
        PIIType.CREDENTIAL,
        PIIType.URL_WITH_CREDENTIALS,
        PIIType.CRYPTO_WALLET,
    ],
    "Technical": [
        PIIType.IP_ADDRESS,
        PIIType.MAC_ADDRESS,
        PIIType.VIN,
        PIIType.VEHICLE_PLATE,
    ],
    "Other": [
        PIIType.DATE_OF_BIRTH,
        PIIType.DATE_TIME,
        PIIType.ORGANIZATION,
        PIIType.MEDICAL_CONDITION,
    ],
}

# Build reverse lookup at module load time
_TYPE_TO_CATEGORY: dict[PIIType, str] = {}
for _cat, _types in PII_CATEGORIES.items():
    for _pii_type in _types:
        _TYPE_TO_CATEGORY[_pii_type] = _cat


def get_category(pii_type: PIIType | str) -> str:
    """Get the category name for a PII type.

    Args:
        pii_type: Either a PIIType enum or its string value

    Returns:
        Category name (e.g., "Names", "Contact", "IDs")
        Falls back to "Other" for unknown types
    """
    if isinstance(pii_type, str):
        try:
            pii_type = PIIType(pii_type)
        except ValueError:
            return "Other"
    return _TYPE_TO_CATEGORY.get(pii_type, "Other")


def get_category_order() -> list[str]:
    """Get category names in display order."""
    return list(PII_CATEGORIES.keys())
