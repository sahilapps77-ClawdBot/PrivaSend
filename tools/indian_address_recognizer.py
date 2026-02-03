"""Custom Presidio recognizers for Indian addresses and localities."""

from __future__ import annotations

from presidio_analyzer import Pattern, PatternRecognizer


# Indian states and union territories
INDIAN_STATES = [
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
    "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka",
    "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya", "Mizoram",
    "Nagaland", "Odisha", "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu",
    "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand", "West Bengal",
    # Union territories
    "Andaman and Nicobar", "Chandigarh", "Dadra and Nagar Haveli",
    "Daman and Diu", "Delhi", "Jammu and Kashmir", "Ladakh",
    "Lakshadweep", "Puducherry",
]

# Major Indian cities
INDIAN_CITIES = [
    "Mumbai", "Delhi", "Bangalore", "Bengaluru", "Hyderabad", "Ahmedabad",
    "Chennai", "Kolkata", "Pune", "Jaipur", "Lucknow", "Kanpur", "Nagpur",
    "Indore", "Thane", "Bhopal", "Visakhapatnam", "Patna", "Vadodara",
    "Ghaziabad", "Ludhiana", "Agra", "Nashik", "Faridabad", "Meerut",
    "Rajkot", "Varanasi", "Srinagar", "Aurangabad", "Dhanbad", "Amritsar",
    "Allahabad", "Prayagraj", "Ranchi", "Howrah", "Coimbatore", "Jabalpur",
    "Gwalior", "Vijayawada", "Jodhpur", "Madurai", "Raipur", "Kota",
    "Chandigarh", "Guwahati", "Solapur", "Hubli", "Mysore", "Mysuru",
    "Tiruchirappalli", "Bareilly", "Moradabad", "Tiruppur", "Gurugram",
    "Gurgaon", "Noida", "Greater Noida", "Faridabad", "Dwarka", "Rohini",
    "Mohali", "Panchkula",
]

# Well-known Delhi/NCR localities
KNOWN_LOCALITIES = [
    "Model Town", "Lajpat Nagar", "Defence Colony", "Greater Kailash",
    "Saket", "Vasant Kunj", "Hauz Khas", "Connaught Place", "Karol Bagh",
    "Rajouri Garden", "Pitampura", "Janakpuri", "Dwarka", "Rohini",
    "Paschim Vihar", "Vikaspuri", "Tilak Nagar", "Moti Nagar",
    "Preet Vihar", "Laxmi Nagar", "Shahdara", "Mayur Vihar",
    "Vasant Vihar", "Chanakyapuri", "South Extension", "Green Park",
    "Malviya Nagar", "Nehru Place", "Kalkaji", "East of Kailash",
    "Civil Lines", "Kamla Nagar", "Patel Nagar", "Rajendra Nagar",
    "Indirapuram", "Vaishali", "Kaushambi", "Crossing Republik",
    "Sector Alpha", "Sector Beta", "Sector Gamma",
    "Andheri", "Bandra", "Juhu", "Powai", "Worli", "Dadar",
    "Borivali", "Malad", "Goregaon", "Kandivali", "Versova",
    "Koramangala", "Whitefield", "Indiranagar", "Jayanagar",
    "BTM Layout", "HSR Layout", "Electronic City", "Marathahalli",
    "Anna Nagar", "T Nagar", "Adyar", "Velachery", "Besant Nagar",
    "Salt Lake", "New Town", "Park Street", "Ballygunge",
]

# Locality suffixes common in Indian addresses
LOCALITY_SUFFIXES = (
    "Colony|Nagar|Vihar|Enclave|Extension|Ext|Phase|Block|Pocket|Park|"
    "Bagh|Puram|Puri|Kunj|Market|Chowk|Bazaar|Marg|Road|Layout|"
    "Garden|Heights|Apartments|Society|Complex|Township|Residency|"
    "Towers|Plaza|Arcade|Circle|Gate|Ganj|Sarai|Mohalla|Wadi|"
    "Sector|Scheme|Mahal|Bhawan|Mandir|Chowki"
)


def create_indian_recognizers() -> list[PatternRecognizer]:
    """Create all Indian address/locality Presidio recognizers."""
    recognizers = []

    # 1. Indian PIN code (6 digits, starts with 1-9)
    #    Context: nearby Indian city/state names boost confidence
    pin_context = [s.lower() for s in INDIAN_STATES + INDIAN_CITIES]
    recognizers.append(PatternRecognizer(
        supported_entity="IN_ADDRESS",
        name="IndianPINCode",
        patterns=[
            Pattern(
                name="pin_code",
                regex=r"\b[1-9]\d{5}\b",
                score=0.40,
            ),
        ],
        context=pin_context,
        supported_language="en",
    ))

    # 2. Sector addresses (Sector 15, Noida etc.)
    sector_cities = "|".join([
        "Noida", "Gurugram", "Gurgaon", "Chandigarh", "Faridabad",
        "Dwarka", "Rohini", "Mohali", "Panchkula", "Greater Noida",
    ])
    recognizers.append(PatternRecognizer(
        supported_entity="IN_ADDRESS",
        name="IndianSectorAddress",
        patterns=[
            Pattern(
                name="sector_with_city",
                regex=rf"\bSector[\s\-]?\d{{1,3}}(?:\s*,?\s*(?:{sector_cities}))\b",
                score=0.85,
            ),
            Pattern(
                name="sector_standalone",
                regex=r"\bSector[\s\-]?\d{1,3}\b",
                score=0.50,
            ),
        ],
        context=pin_context,
        supported_language="en",
    ))

    # 3. Known localities (high confidence)
    locality_pattern = "|".join(
        loc.replace(" ", r"\s+") for loc in KNOWN_LOCALITIES
    )
    recognizers.append(PatternRecognizer(
        supported_entity="IN_ADDRESS",
        name="IndianKnownLocality",
        patterns=[
            Pattern(
                name="known_locality",
                regex=rf"\b(?:{locality_pattern})\b",
                score=0.75,
            ),
        ],
        context=pin_context,
        supported_language="en",
    ))

    # 4. Locality suffix patterns (Model Town, Lajpat Nagar, etc.)
    recognizers.append(PatternRecognizer(
        supported_entity="IN_ADDRESS",
        name="IndianLocalitySuffix",
        patterns=[
            Pattern(
                name="locality_suffix",
                regex=rf"\b[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+){{0,2}}\s+(?:{LOCALITY_SUFFIXES})\b",
                score=0.65,
            ),
        ],
        context=pin_context,
        supported_language="en",
    ))

    return recognizers
