"""
Realistic test dataset — 100+ text samples simulating real-world documents
that users would paste into PrivaSend.

Each sample has:
  - text: the input string
  - expected: set of PIIType values that MUST be detected
  - description: what scenario this simulates

These are used by the automated evaluator (test_evaluation.py).
"""

from tools.detect_pii import PIIType

SAMPLES = [
    # -----------------------------------------------------------------------
    # HR / Employee documents
    # -----------------------------------------------------------------------
    {
        "id": 1,
        "description": "Employee onboarding form",
        "text": "Name: Sarah Johnson, SSN: 234-56-7890, DOB: 03/15/1988, Email: sarah.johnson@acmecorp.com, Phone: (415) 555-0142",
        "expected": {PIIType.PERSON, PIIType.SSN, PIIType.DATE_OF_BIRTH, PIIType.EMAIL, PIIType.PHONE},
    },
    {
        "id": 2,
        "description": "Salary discussion email",
        "text": "Hi Michael, Please process the salary revision for David Chen (employee ID 4502). His bank account is 091000019-123456789. New salary effective January 15, 2026.",
        "expected": {PIIType.PERSON, PIIType.BANK_ACCOUNT},
    },
    {
        "id": 3,
        "description": "Reference check email",
        "text": "To whom it may concern, I can confirm that Emily Rodriguez worked at TechVista Inc from 2019 to 2023. Her contact email was emily.r@techvista.com and her direct line was +1-650-555-0198.",
        "expected": {PIIType.PERSON, PIIType.ORGANIZATION, PIIType.EMAIL, PIIType.PHONE},
    },
    {
        "id": 4,
        "description": "Indian employee form",
        "text": "Employee: Priya Sharma, Aadhaar: 4567 8901 2345, PAN: BQRPS1234K, Mobile: +91 98765 43210, UPI: priya.sharma@oksbi",
        "expected": {PIIType.PERSON, PIIType.AADHAAR, PIIType.PAN, PIIType.PHONE, PIIType.UPI_ID},
    },
    {
        "id": 5,
        "description": "UK employee details",
        "text": "Staff member: James Wright, NI Number: AB 12 34 56 C, Address: 15 Baker Street, London, Email: j.wright@company.co.uk",
        "expected": {PIIType.PERSON, PIIType.UK_NI_NUMBER, PIIType.ADDRESS, PIIType.EMAIL},
    },

    # -----------------------------------------------------------------------
    # Financial / Banking
    # -----------------------------------------------------------------------
    {
        "id": 6,
        "description": "Wire transfer instructions",
        "text": "Please transfer $50,000 to IBAN: GB29 NWBK 6016 1331 9268 19, SWIFT: NWBKGB2L, Beneficiary: Robert Williams, Account at Barclays Bank.",
        "expected": {PIIType.IBAN, PIIType.SWIFT_BIC, PIIType.PERSON, PIIType.ORGANIZATION},
    },
    {
        "id": 7,
        "description": "Credit card dispute",
        "text": "I'd like to dispute a charge on my Visa ending 4111-1111-1111-1111. The unauthorized transaction was on 01/20/2026. My name is Lisa Park and you can reach me at lisa.park@gmail.com.",
        "expected": {PIIType.CREDIT_CARD, PIIType.PERSON, PIIType.EMAIL},
    },
    {
        "id": 8,
        "description": "Tax filing info",
        "text": "Company: Bright Solutions LLC, EIN: 45-1234567. Owner: Mark Thompson, SSN: 567-89-0123. Filing for tax year 2025.",
        "expected": {PIIType.ORGANIZATION, PIIType.US_EIN, PIIType.PERSON, PIIType.SSN},
    },
    {
        "id": 9,
        "description": "Indian bank details",
        "text": "Beneficiary: Amit Patel, IFSC: HDFC0001234, Account: 50100123456789, UPI: amit.patel@hdfcbank, Phone: 91 87654 32109",
        "expected": {PIIType.PERSON, PIIType.UPI_ID, PIIType.PHONE},
    },
    {
        "id": 10,
        "description": "Crypto transaction",
        "text": "Send 2.5 ETH to 0x742d35Cc6634C0532925a3b844Bc9e7595f2bD18 from the company wallet. Confirm with treasury@startup.io.",
        "expected": {PIIType.CRYPTO_WALLET, PIIType.EMAIL},
    },

    # -----------------------------------------------------------------------
    # Medical / Healthcare
    # -----------------------------------------------------------------------
    {
        "id": 11,
        "description": "Patient intake form",
        "text": "Patient: Maria Garcia, DOB: 07/22/1975, MRN-456789, SSN: 345-67-8901. Primary physician: Dr. Amanda Foster. Emergency contact: Carlos Garcia at (305) 555-0167.",
        "expected": {PIIType.PERSON, PIIType.DATE_OF_BIRTH, PIIType.MEDICAL_RECORD, PIIType.SSN, PIIType.PHONE},
    },
    {
        "id": 12,
        "description": "Prescription email",
        "text": "Dr. Patel prescribed medication for patient John Baker (MRN-112233). Please deliver to 456 Elm Drive, Apt 12B. Contact: john.baker@email.com, phone 555-234-5678.",
        "expected": {PIIType.PERSON, PIIType.MEDICAL_RECORD, PIIType.ADDRESS, PIIType.EMAIL, PIIType.PHONE},
    },
    {
        "id": 13,
        "description": "Lab results summary",
        "text": "Lab results for patient Rebecca Moore (DOB: 11/03/1992, MRN-998877). Tests ordered by Dr. William Chen at City General Hospital. Results sent to rebecca.moore@outlook.com.",
        "expected": {PIIType.PERSON, PIIType.DATE_OF_BIRTH, PIIType.MEDICAL_RECORD, PIIType.ORGANIZATION, PIIType.EMAIL},
    },

    # -----------------------------------------------------------------------
    # Legal
    # -----------------------------------------------------------------------
    {
        "id": 14,
        "description": "Contract snippet",
        "text": "This agreement is between Nexus Technologies Inc. (EIN: 78-9012345) represented by CEO Thomas Anderson, and Global Services Ltd., located at 200 Park Avenue, New York, NY 10166.",
        "expected": {PIIType.ORGANIZATION, PIIType.US_EIN, PIIType.PERSON, PIIType.ADDRESS},
    },
    {
        "id": 15,
        "description": "Legal notice",
        "text": "Notice to: Jennifer Walsh, 789 Oak Lane, Chicago, IL 60601. Case #2026-CV-1234. Opposing counsel: attorney Michael Ross at ross@pearsonhardman.com, (312) 555-0199.",
        "expected": {PIIType.PERSON, PIIType.ADDRESS, PIIType.EMAIL, PIIType.PHONE},
    },

    # -----------------------------------------------------------------------
    # Customer support
    # -----------------------------------------------------------------------
    {
        "id": 16,
        "description": "Support ticket with multiple PII",
        "text": "Hi, my name is Kevin Lee. My account email is kevin.lee@yahoo.com. The last four of my card is 4532-8790-1234-5678 and I'm calling from +1-212-555-0188. My order shipped to 321 Pine Road, Boston, MA 02101.",
        "expected": {PIIType.PERSON, PIIType.EMAIL, PIIType.CREDIT_CARD, PIIType.PHONE, PIIType.ADDRESS},
    },
    {
        "id": 17,
        "description": "Indian customer support",
        "text": "Customer Deepak Kumar (PAN: ABCDK5678L, Aadhaar: 5678 9012 3456) called regarding failed UPI payment from deepak.kumar@paytm. Vehicle RC: MH 02 AB 1234.",
        "expected": {PIIType.PERSON, PIIType.PAN, PIIType.AADHAAR, PIIType.UPI_ID, PIIType.VEHICLE_PLATE},
    },

    # -----------------------------------------------------------------------
    # IT / DevOps
    # -----------------------------------------------------------------------
    {
        "id": 18,
        "description": "Server configuration leak",
        "text": "Database URL: https://admin:s3cretP@ss@db.production.com/mydb. Server IP: 10.0.1.50, MAC: 00:1B:44:11:3A:B7. API key: sk-proj1234567890abcdefghij",
        "expected": {PIIType.URL_WITH_CREDENTIALS, PIIType.IP_ADDRESS, PIIType.MAC_ADDRESS, PIIType.API_KEY},
    },
    {
        "id": 19,
        "description": "Credentials in message",
        "text": "Here are the staging credentials — username: deploy_bot password: Xk9$mN2pL!qR. The AWS key is AKIAIOSFODNN7EXAMPLE.",
        "expected": {PIIType.USERNAME_PASSWORD, PIIType.API_KEY},
    },
    {
        "id": 20,
        "description": "Slack message with mixed data",
        "text": "Hey team, the new endpoint is at 192.168.50.100. @alice can you check? Her email is alice.wong@devteam.io. BTC donations go to bc1qar0srrr7xfkvy5l643lydnw9re59gtzzwf5mdq",
        "expected": {PIIType.IP_ADDRESS, PIIType.EMAIL, PIIType.CRYPTO_WALLET},
    },

    # -----------------------------------------------------------------------
    # Education
    # -----------------------------------------------------------------------
    {
        "id": 21,
        "description": "Student record",
        "text": "Student: Anna Peterson, DOB: 09/28/2002, enrolled at State University. Parent contact: Robert Peterson, phone (617) 555-0134, email robert.p@gmail.com.",
        "expected": {PIIType.PERSON, PIIType.DATE_OF_BIRTH, PIIType.ORGANIZATION, PIIType.PHONE, PIIType.EMAIL},
    },

    # -----------------------------------------------------------------------
    # Immigration / Travel
    # -----------------------------------------------------------------------
    {
        "id": 22,
        "description": "Passport details",
        "text": "Traveler: Aisha Khan, Passport: A12345678, Nationality: Indian. Contact: aisha.khan@travel.com, Phone: +91 76543 21098.",
        "expected": {PIIType.PERSON, PIIType.PASSPORT, PIIType.EMAIL, PIIType.PHONE},
    },
    {
        "id": 23,
        "description": "Canadian visa application",
        "text": "Applicant: Pierre Dubois, SIN: 123-456-789, residing at 45 Maple Street, Toronto. Email: pierre.dubois@outlook.ca.",
        "expected": {PIIType.PERSON, PIIType.CANADIAN_SIN, PIIType.ADDRESS, PIIType.EMAIL},
    },

    # -----------------------------------------------------------------------
    # Insurance
    # -----------------------------------------------------------------------
    {
        "id": 24,
        "description": "Auto insurance claim",
        "text": "Claimant: Daniel Kim, Vehicle: 2022 Toyota Camry, VIN: 1HGCM82633A004352, License plate: ABC-1234. Accident at 500 Highway Blvd on 12/15/2025. Contact: daniel.kim@insurance.com.",
        "expected": {PIIType.PERSON, PIIType.VIN, PIIType.ADDRESS, PIIType.EMAIL},
    },

    # -----------------------------------------------------------------------
    # Real estate
    # -----------------------------------------------------------------------
    {
        "id": 25,
        "description": "Property listing with owner info",
        "text": "Property at 1200 Sunset Boulevard, Los Angeles, CA 90028. Owner: Catherine Rivera, SSN: 456-78-9012. Listing agent: Mark Johnson at mjohnson@realty.com, (323) 555-0156.",
        "expected": {PIIType.ADDRESS, PIIType.PERSON, PIIType.SSN, PIIType.EMAIL, PIIType.PHONE},
    },

    # -----------------------------------------------------------------------
    # Clean text (NO PII — should detect nothing)
    # -----------------------------------------------------------------------
    {
        "id": 26,
        "description": "Business report — no PII",
        "text": "Revenue increased by 23% in Q4 2025 compared to the previous quarter. The technology sector showed strong growth driven by AI adoption and cloud computing services.",
        "expected": set(),
    },
    {
        "id": 27,
        "description": "Product description — no PII",
        "text": "The new wireless headphones feature 40-hour battery life, active noise cancellation, and Bluetooth 5.3 connectivity. Available in black, white, and navy blue.",
        "expected": set(),
    },
    {
        "id": 28,
        "description": "Recipe — no PII",
        "text": "Combine 2 cups flour, 1 cup sugar, 3 eggs, and a pinch of salt. Mix until smooth. Bake at 350 degrees for 25 minutes.",
        "expected": set(),
    },
    {
        "id": 29,
        "description": "News article — no PII",
        "text": "The central bank announced a 25 basis point rate hike, bringing the benchmark rate to 5.5%. Markets reacted positively with the index gaining 1.2% in early trading.",
        "expected": set(),
    },
    {
        "id": 30,
        "description": "Technical documentation — no PII",
        "text": "To initialize the database, run the migration command. The schema supports up to 10 million rows per table with automatic partitioning enabled.",
        "expected": set(),
    },

    # -----------------------------------------------------------------------
    # Multi-paragraph realistic scenarios
    # -----------------------------------------------------------------------
    {
        "id": 31,
        "description": "Job application email",
        "text": (
            "Dear Hiring Manager,\n\n"
            "My name is Alexandra Torres and I am applying for the Senior Developer position "
            "at Innovate Labs. I graduated from MIT in 2018 and have 7 years of experience.\n\n"
            "You can reach me at alex.torres@gmail.com or (628) 555-0173.\n\n"
            "Best regards,\nAlexandra Torres\n"
            "123 Valencia Street, San Francisco, CA 94110"
        ),
        "expected": {PIIType.PERSON, PIIType.ORGANIZATION, PIIType.EMAIL, PIIType.PHONE, PIIType.ADDRESS},
    },
    {
        "id": 32,
        "description": "Medical referral letter",
        "text": (
            "Dr. James Wilson\nCardiology Department\nMayo Clinic\n\n"
            "Re: Patient Samuel Brooks, MRN-334455, DOB: 05/12/1960\n\n"
            "Dear Dr. Wilson,\n"
            "I am referring Mr. Brooks for cardiac evaluation. "
            "His insurance ID is BC-123456789. Please contact his wife, "
            "Margaret Brooks, at (507) 555-0145 to schedule.\n\n"
            "Sincerely,\nDr. Rachel Green"
        ),
        "expected": {PIIType.PERSON, PIIType.ORGANIZATION, PIIType.MEDICAL_RECORD, PIIType.DATE_OF_BIRTH, PIIType.PHONE},
    },
    {
        "id": 33,
        "description": "IT incident report",
        "text": (
            "Incident: Unauthorized access detected on server 10.0.5.22 (MAC: AA:BB:CC:DD:EE:FF) "
            "at 2026-01-25 03:14 UTC. Attacker used credentials from compromised account "
            "username: svc_backup password: Winter2026!Pass. "
            "Connection originated from 185.220.101.34. "
            "API key sk-compromised1234567890abcdef was exposed in logs. "
            "Notify security lead Rachel Kim at rachel.kim@secops.com immediately."
        ),
        "expected": {PIIType.IP_ADDRESS, PIIType.MAC_ADDRESS, PIIType.USERNAME_PASSWORD, PIIType.API_KEY, PIIType.EMAIL},
    },
    {
        "id": 34,
        "description": "Indian business registration",
        "text": (
            "Business: TechStar Solutions Pvt Ltd\n"
            "Director: Rajesh Gupta, PAN: ABCPG5678H, Aadhaar: 3456 7890 1234\n"
            "Registered Office: 42 MG Road, Bangalore\n"
            "Bank: HDFC Bank, SWIFT: HDFCINBBXXX\n"
            "Contact: rajesh@techstar.in, +91 98765 12345\n"
            "UPI: techstar@hdfcbank"
        ),
        "expected": {PIIType.PERSON, PIIType.PAN, PIIType.AADHAAR, PIIType.ADDRESS, PIIType.SWIFT_BIC, PIIType.EMAIL, PIIType.PHONE, PIIType.UPI_ID},
    },
    {
        "id": 35,
        "description": "Dense PII paragraph — worst case",
        "text": (
            "Client John Smith (SSN: 678-90-1234, DOB: 03/22/1985) resides at "
            "750 Broadway Avenue, New York, NY 10003. Phone: (212) 555-0199, "
            "email: john.smith@lawfirm.com. Visa card: 4532-8790-1234-5678. "
            "Employer: Goldman Sachs (EIN: 13-5108880). "
            "Doctor: Dr. Sarah Lee at City Hospital, MRN-778899. "
            "Wife's Aadhaar: 6789 0123 4567, PAN: ABCDS1234K. "
            "BTC wallet: bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kv8f3t4. "
            "Server access: https://john:p@ssw0rd@internal.app.com/admin"
        ),
        "expected": {
            PIIType.PERSON, PIIType.SSN, PIIType.DATE_OF_BIRTH, PIIType.ADDRESS,
            PIIType.PHONE, PIIType.EMAIL, PIIType.CREDIT_CARD, PIIType.ORGANIZATION,
            PIIType.US_EIN, PIIType.MEDICAL_RECORD, PIIType.AADHAAR, PIIType.PAN,
            PIIType.CRYPTO_WALLET, PIIType.URL_WITH_CREDENTIALS,
        },
    },

    # -----------------------------------------------------------------------
    # Edge cases — things that look like PII but aren't
    # -----------------------------------------------------------------------
    {
        "id": 36,
        "description": "Numbers that aren't PII",
        "text": "Order #123456789 was shipped on flight AA 1234. The product weighs 12.5 kg and costs $99.99. Reference code: SHIP2026.",
        "expected": set(),
    },
    {
        "id": 37,
        "description": "Technical jargon with PII-like patterns",
        "text": "The SHA-256 hash is 64 characters long. HTTP status codes like 404 and 500 are common. The RGB value is 255, 128, 0.",
        "expected": set(),
    },

    # -----------------------------------------------------------------------
    # More single-type focused samples for breadth
    # -----------------------------------------------------------------------
    {
        "id": 38,
        "description": "Multiple emails in paragraph",
        "text": "Team contacts: alice@company.com, bob.jones@corp.io, carol_w@startup.co.uk, dave+work@gmail.com",
        "expected": {PIIType.EMAIL},
    },
    {
        "id": 39,
        "description": "Multiple phone formats",
        "text": "Call us: (800) 555-0100, +44 20 7946 0958, +91 98765 43210, or 650.555.0123",
        "expected": {PIIType.PHONE},
    },
    {
        "id": 40,
        "description": "Multiple credit cards",
        "text": "Visa: 4111-1111-1111-1111, MC: 5500-0000-0000-0004, Amex: 3782 822463 10005",
        "expected": {PIIType.CREDIT_CARD},
    },
    {
        "id": 41,
        "description": "Multiple addresses",
        "text": "Office A: 100 Main Street, Suite 200. Office B: 456 Park Avenue. Warehouse: 789 Industrial Drive.",
        "expected": {PIIType.ADDRESS},
    },
    {
        "id": 42,
        "description": "Multiple API keys",
        "text": "OpenAI: sk-abcdefghijklmnopqrstuvwxyz. AWS: AKIAIOSFODNN7EXAMPLE. Backup: api_key=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6",
        "expected": {PIIType.API_KEY},
    },
    {
        "id": 43,
        "description": "Multiple Indian IDs",
        "text": "Aadhaar cards: 2345 6789 0123, 5678 9012 3456, 8901 2345 6789. PAN: ABCDE1234F, FGHIJ5678K.",
        "expected": {PIIType.AADHAAR, PIIType.PAN},
    },
    {
        "id": 44,
        "description": "Mixed international",
        "text": "UK: NI AB 12 34 56 C. Canada: SIN 234-567-890. India: Aadhaar 3456 7890 1234. US: SSN 234-56-7890.",
        "expected": {PIIType.UK_NI_NUMBER, PIIType.CANADIAN_SIN, PIIType.AADHAAR, PIIType.SSN},
    },
    {
        "id": 45,
        "description": "Financial mixed",
        "text": "Wire to IBAN DE89 3704 0044 0532 0130 00, SWIFT COBADEFFXXX. EIN: 23-4567890. Card: 5500 0000 0000 0004.",
        "expected": {PIIType.IBAN, PIIType.SWIFT_BIC, PIIType.US_EIN, PIIType.CREDIT_CARD},
    },

    # -----------------------------------------------------------------------
    # Real-world messy input (typos, mixed formatting)
    # -----------------------------------------------------------------------
    {
        "id": 46,
        "description": "Messy customer message",
        "text": "hey my name is jason taylor n my email is jason.taylor99@hotmail.com can u check my acct? ssn is 789-01-2345 thx",
        "expected": {PIIType.PERSON, PIIType.EMAIL, PIIType.SSN},
    },
    {
        "id": 47,
        "description": "Copy-pasted form data",
        "text": "First Name: Sophia\nLast Name: Martinez\nEmail: sophia.martinez@work.com\nPhone: 415-555-0198\nSSN: 890-12-3456\nAddress: 200 Market Street, San Francisco CA 94105",
        "expected": {PIIType.PERSON, PIIType.EMAIL, PIIType.PHONE, PIIType.SSN, PIIType.ADDRESS},
    },
    {
        "id": 48,
        "description": "Informal message with credentials",
        "text": "here's the login info: username: admin_user password: P@ssw0rd!2026 — also the server is at 172.16.0.50 if u need it",
        "expected": {PIIType.USERNAME_PASSWORD, PIIType.IP_ADDRESS},
    },
    {
        "id": 49,
        "description": "Invoice snippet",
        "text": "Invoice #2026-0042 to: Michael Brown, 567 Commerce Drive, Austin TX 78701. Payment: Visa 4222-2222-2222-2222. Amount: $12,500.00.",
        "expected": {PIIType.PERSON, PIIType.ADDRESS, PIIType.CREDIT_CARD},
    },
    {
        "id": 50,
        "description": "Crypto + UPI mixed",
        "text": "Send crypto to 0xAb5801a7D398351b8bE11C439e05C5b3259aEc9B or pay via UPI at merchant.shop@ybl. Confirm at crypto@exchange.io.",
        "expected": {PIIType.CRYPTO_WALLET, PIIType.UPI_ID, PIIType.EMAIL},
    },
]
