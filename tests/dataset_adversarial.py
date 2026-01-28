"""
Adversarial test dataset — Edge cases designed to trick the detection engine.

These test obfuscated PII, unusual formats, boundary conditions, and
things that LOOK like PII but aren't (false positive traps).
"""

from tools.detect_pii import PIIType

SAMPLES = [
    # -----------------------------------------------------------------------
    # Obfuscated PII — common ways people try to hide data
    # -----------------------------------------------------------------------
    {
        "id": "ADV-01",
        "description": "Spaced-out email",
        "text": "Email me at john . doe @ example . com",
        "expected": set(),  # Our engine won't catch this — known limitation
        "notes": "Known gap: spaced-out emails bypass regex",
    },
    {
        "id": "ADV-02",
        "description": "Obfuscated email with [at] and [dot]",
        "text": "Send to john [at] example [dot] com",
        "expected": set(),  # Known limitation
        "notes": "Known gap: bracket-obfuscated emails",
    },
    {
        "id": "ADV-03",
        "description": "Spelled-out phone number",
        "text": "Call me at five five five, one two three, four five six seven",
        "expected": set(),  # Known limitation — would need NLP
        "notes": "Known gap: spelled-out numbers",
    },
    {
        "id": "ADV-04",
        "description": "SSN with spaces instead of dashes",
        "text": "My social security number is 123 45 6789",
        "expected": set(),  # Might partially match
        "notes": "SSN with spaces — may or may not match depending on patterns",
    },

    # -----------------------------------------------------------------------
    # Things that LOOK like PII but aren't (false positive traps)
    # -----------------------------------------------------------------------
    {
        "id": "ADV-05",
        "description": "Product codes that look like credit cards",
        "text": "SKU: 4111-2222-3333-4444. Model number: 5500-1000-2000-3000.",
        "expected": set(),
        "notes": "Product codes matching CC format — acceptable false positive",
        "acceptable_false_positives": {PIIType.CREDIT_CARD},
    },
    {
        "id": "ADV-06",
        "description": "ISBN that looks like SSN",
        "text": "The book ISBN is 978-45-6789. Published in 2025.",
        "expected": set(),
        "notes": "ISBN prefix matching SSN format",
        "acceptable_false_positives": {PIIType.SSN},
    },
    {
        "id": "ADV-07",
        "description": "Version numbers that look like IPs",
        "text": "Software version 10.0.1.50 was released today. Update from 192.0.0.1 to see changes.",
        "expected": set(),
        "notes": "Version numbers matching IP format — acceptable FP for 10.0.1.50",
        "acceptable_false_positives": {PIIType.IP_ADDRESS},
    },
    {
        "id": "ADV-08",
        "description": "Normal words matching patterns",
        "text": "The STUDENT1234F scored well. ABCDE is a common sequence. The WORKER went home.",
        "expected": set(),
        "notes": "STUDENT1234F matches PAN format",
        "acceptable_false_positives": {PIIType.PAN},
    },
    {
        "id": "ADV-09",
        "description": "Date that looks like DOB",
        "text": "The report was published on 01/15/2025 and updated on 03/20/2026.",
        "expected": set(),
        "notes": "Publication dates matching DOB format — acceptable FP",
        "acceptable_false_positives": {PIIType.DATE_OF_BIRTH},
    },
    {
        "id": "ADV-10",
        "description": "Random 12-digit number that looks like Aadhaar",
        "text": "Transaction ID: 2345 6789 0123. Reference: 8901 2345 6789.",
        "expected": set(),
        "notes": "Transaction IDs matching Aadhaar format — acceptable FP",
        "acceptable_false_positives": {PIIType.AADHAAR},
    },

    # -----------------------------------------------------------------------
    # Boundary cases
    # -----------------------------------------------------------------------
    {
        "id": "ADV-11",
        "description": "Empty string",
        "text": "",
        "expected": set(),
    },
    {
        "id": "ADV-12",
        "description": "Only whitespace",
        "text": "   \n\t\n   ",
        "expected": set(),
    },
    {
        "id": "ADV-13",
        "description": "Single character",
        "text": "A",
        "expected": set(),
    },
    {
        "id": "ADV-14",
        "description": "Very long text with no PII",
        "text": "The quick brown fox jumps over the lazy dog. " * 100,
        "expected": set(),
    },
    {
        "id": "ADV-15",
        "description": "PII at very start of text",
        "text": "john@example.com is my email address",
        "expected": {PIIType.EMAIL},
    },
    {
        "id": "ADV-16",
        "description": "PII at very end of text",
        "text": "My email address is john@example.com",
        "expected": {PIIType.EMAIL},
    },
    {
        "id": "ADV-17",
        "description": "PII surrounded by special characters",
        "text": "***john@example.com*** | (555-123-4567) | [123-45-6789]",
        "expected": {PIIType.EMAIL, PIIType.PHONE, PIIType.SSN},
    },
    {
        "id": "ADV-18",
        "description": "PII in ALL CAPS",
        "text": "EMAIL: JOHN@EXAMPLE.COM, PHONE: 555-123-4567",
        "expected": {PIIType.EMAIL, PIIType.PHONE},
    },

    # -----------------------------------------------------------------------
    # Mixed languages / Unicode
    # -----------------------------------------------------------------------
    {
        "id": "ADV-19",
        "description": "PII mixed with Hindi text",
        "text": "मेरा नाम राहुल है। Email: rahul@example.com, Phone: +91 98765 43210, Aadhaar: 4567 8901 2345",
        "expected": {PIIType.EMAIL, PIIType.PHONE, PIIType.AADHAAR},
    },
    {
        "id": "ADV-20",
        "description": "PII in JSON-like format",
        "text": '{"name": "John Smith", "email": "john@test.com", "ssn": "234-56-7890", "phone": "555-123-4567"}',
        "expected": {PIIType.EMAIL, PIIType.SSN, PIIType.PHONE},
    },
    {
        "id": "ADV-21",
        "description": "PII in CSV format",
        "text": "Name,Email,SSN,Phone\nJohn Smith,john@test.com,234-56-7890,555-123-4567\nJane Doe,jane@test.com,345-67-8901,555-234-5678",
        "expected": {PIIType.EMAIL, PIIType.SSN, PIIType.PHONE},
    },
    {
        "id": "ADV-22",
        "description": "PII in XML-like format",
        "text": "<person><name>John Smith</name><email>john@test.com</email><ssn>234-56-7890</ssn></person>",
        "expected": {PIIType.EMAIL, PIIType.SSN},
    },

    # -----------------------------------------------------------------------
    # Overlapping / Adjacent PII
    # -----------------------------------------------------------------------
    {
        "id": "ADV-23",
        "description": "Name immediately followed by email",
        "text": "John Smith john.smith@example.com",
        "expected": {PIIType.PERSON, PIIType.EMAIL},
    },
    {
        "id": "ADV-24",
        "description": "Multiple PII no separation",
        "text": "SSN:123-45-6789Phone:555-123-4567Email:test@mail.com",
        "expected": {PIIType.SSN, PIIType.PHONE, PIIType.EMAIL},
    },
    {
        "id": "ADV-25",
        "description": "Same value appears twice",
        "text": "Primary email: john@test.com. Confirm email: john@test.com.",
        "expected": {PIIType.EMAIL},
    },

    # -----------------------------------------------------------------------
    # Real-world adversarial — actual patterns people paste
    # -----------------------------------------------------------------------
    {
        "id": "ADV-26",
        "description": "Redacted text re-pasted (should not double-detect)",
        "text": "Contact [EMAIL_1] at [PHONE_1]. Their SSN is [SSN_1].",
        "expected": set(),
        "notes": "Already redacted text should not trigger detection",
    },
    {
        "id": "ADV-27",
        "description": "SQL query with PII",
        "text": "SELECT * FROM users WHERE email = 'john@test.com' AND ssn = '234-56-7890' AND phone = '555-123-4567';",
        "expected": {PIIType.EMAIL, PIIType.SSN, PIIType.PHONE},
    },
    {
        "id": "ADV-28",
        "description": "Log file entry",
        "text": "[2026-01-28 14:30:22] User login: email=alice@company.com ip=10.0.1.50 user_agent=Mozilla/5.0",
        "expected": {PIIType.EMAIL, PIIType.IP_ADDRESS},
    },
    {
        "id": "ADV-29",
        "description": "Markdown formatted document",
        "text": "# Employee: **John Smith**\n- Email: `john@test.com`\n- Phone: `555-123-4567`\n- SSN: `234-56-7890`",
        "expected": {PIIType.EMAIL, PIIType.PHONE, PIIType.SSN},
    },
    {
        "id": "ADV-30",
        "description": "URL parameters with PII",
        "text": "https://app.com/profile?email=john@test.com&phone=5551234567&name=John+Smith",
        "expected": {PIIType.EMAIL},
        "notes": "Phone in URL params may not match (no separators), name is URL-encoded",
    },
]
