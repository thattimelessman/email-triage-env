TASKS = {
    "easy": {
        "id": "easy",
        "description": "Classify a single email as urgent, normal, or spam.",
        "emails": [
            {
                "id": "e1",
                "subject": "URGENT: Server is down",
                "body": "Our production server has crashed. Customers cannot access the site. Please fix immediately.",
                "sender": "ops@company.com"
            }
        ],
        "correct_labels": {"e1": "urgent"},
        "correct_departments": {"e1": "engineering"}
    },
    "medium": {
        "id": "medium",
        "description": "Classify 5 emails and assign each to the correct department.",
        "emails": [
            {"id": "m1", "subject": "Invoice #4521 overdue", "body": "Your payment of $500 is overdue by 30 days.", "sender": "billing@vendor.com"},
            {"id": "m2", "subject": "New feature request", "body": "Can you add dark mode to the app?", "sender": "customer@gmail.com"},
            {"id": "m3", "subject": "Congratulations! You won!", "body": "Click here to claim your free iPhone. Limited time offer!!!", "sender": "noreply@prizes.xyz"},
            {"id": "m4", "subject": "Team standup cancelled", "body": "No standup today, everyone is heads down on the release.", "sender": "manager@company.com"},
            {"id": "m5", "subject": "CRITICAL: Database breach detected", "body": "Unauthorized access detected on DB server at 3AM. Immediate action required.", "sender": "security@company.com"}
        ],
        "correct_labels": {"m1": "normal", "m2": "normal", "m3": "spam", "m4": "normal", "m5": "urgent"},
        "correct_departments": {"m1": "finance", "m2": "product", "m3": "spam", "m4": "engineering", "m5": "security"}
    },
    "hard": {
        "id": "hard",
        "description": "Classify 10 emails, assign departments, and identify the phishing email.",
        "emails": [
            {"id": "h1", "subject": "Quarterly report ready", "body": "Please find attached Q3 financial report for your review.", "sender": "cfo@company.com"},
            {"id": "h2", "subject": "Your account will be suspended", "body": "Click here immediately to verify your bank account or it will be suspended.", "sender": "support@bank-secure-login.xyz"},
            {"id": "h3", "subject": "New hire onboarding", "body": "Welcome John! Please complete your onboarding documents by Friday.", "sender": "hr@company.com"},
            {"id": "h4", "subject": "URGENT: CEO needs gift cards", "body": "Hi, this is the CEO. Buy 10 x $100 Amazon gift cards and send codes to me urgently. Keep this confidential.", "sender": "ceo.company@gmail.com"},
            {"id": "h5", "subject": "Server CPU at 98%", "body": "Alert: Production server CPU usage has been above 95% for 10 minutes.", "sender": "monitoring@company.com"},
            {"id": "h6", "subject": "Office party next Friday", "body": "Join us for the end of year celebration at 5pm in the main hall.", "sender": "events@company.com"},
            {"id": "h7", "subject": "RE: Contract renewal", "body": "We have reviewed the terms and are ready to proceed with the renewal.", "sender": "legal@partner.com"},
            {"id": "h8", "subject": "Free vacation offer inside!", "body": "You have been selected for a FREE 7-day vacation. Click to claim!", "sender": "offers@travel-deals.biz"},
            {"id": "h9", "subject": "Pull request needs review", "body": "PR #234 is ready for code review. Changes affect the payment module.", "sender": "dev@company.com"},
            {"id": "h10", "subject": "Password reset request", "body": "A password reset was requested for your account. If this was not you, ignore this email.", "sender": "noreply@company.com"}
        ],
        "correct_labels": {
            "h1": "normal", "h2": "spam", "h3": "normal", "h4": "spam",
            "h5": "urgent", "h6": "normal", "h7": "normal", "h8": "spam",
            "h9": "normal", "h10": "normal"
        },
        "correct_departments": {
            "h1": "finance", "h2": "spam", "h3": "hr", "h4": "spam",
            "h5": "engineering", "h6": "hr", "h7": "legal", "h8": "spam",
            "h9": "engineering", "h10": "security"
        },
        "phishing_ids": ["h2", "h4"]
    }
}