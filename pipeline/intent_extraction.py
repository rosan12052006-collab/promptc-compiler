"""
Stage 1: Intent Extraction
Parses raw natural language prompt into a structured intermediate representation.
Deterministic, rule-based (regex + keyword taxonomy) -> $0 cost, 0 variance.
"""
import re

# --- Taxonomy: keyword -> feature ---
FEATURE_KEYWORDS = {
    "auth": ["login", "log in", "signup", "sign up", "authentication", "register", "logout", "sign in", "credentials", "password"],
    "rbac": ["role-based", "role based", "roles", "admin", "permission", "access control", "privileges", "authorization"],
    "payments": ["payment", "premium", "subscription", "billing", "stripe", "paywall", "plan", "checkout", "pricing", "paid", "free trial", "invoice payment", "charge"],
    "analytics": ["analytics", "report", "metrics", "insights", "statistics", "stats", "charts", "graphs", "kpi", "performance"],
    "dashboard": ["dashboard", "overview", "home screen", "summary", "main screen", "landing page", "home page"],
    "notifications": ["notification", "alert", "email reminder", "push notification", "notify", "reminder", "email alert"],
    "search": ["search", "filter", "query", "find", "lookup", "browse", "sort"],
    "chat": ["chat", "messaging", "inbox", "message", "conversation", "direct message", "dm"],
    "file_upload": ["upload", "attachment", "file storage", "document upload", "image upload", "media", "storage"],
    "calendar": ["calendar", "schedule", "scheduling", "booking", "appointment", "event", "timetable", "slot"],
    "inventory": ["inventory", "stock", "warehouse", "supply", "quantity", "track stock"],
    "export": ["export", "download", "csv", "pdf export", "report download", "generate report"],
    "map": ["map", "location", "gps", "geolocation", "address tracking", "nearby"],
    "qr_code": ["qr code", "qr", "barcode", "scan"],
    "audit": ["audit", "audit log", "activity log", "history", "track changes", "log"],
}

# Entity nouns — massively expanded taxonomy
ENTITY_KEYWORDS = {
    # CRM
    "contacts": "Contact", "contact": "Contact",
    "leads": "Lead", "lead": "Lead",
    "deals": "Deal", "deal": "Deal",
    "opportunities": "Opportunity", "opportunity": "Opportunity",
    "accounts": "Account", "account": "Account",

    # E-commerce / Finance
    "orders": "Order", "order": "Order",
    "products": "Product", "product": "Product",
    "invoices": "Invoice", "invoice": "Invoice",
    "payments": "Payment", "payment": "Payment",
    "transactions": "Transaction", "transaction": "Transaction",
    "subscriptions": "Subscription", "subscription": "Subscription",
    "coupons": "Coupon", "coupon": "Coupon",
    "cart": "Cart", "carts": "Cart",
    "refunds": "Refund", "refund": "Refund",
    "expenses": "Expense", "expense": "Expense",

    # Project / Task Management
    "teams": "Team", "team": "Team",
    "tasks": "Task", "task": "Task",
    "projects": "Project", "project": "Project",
    "milestones": "Milestone", "milestone": "Milestone",
    "sprints": "Sprint", "sprint": "Sprint",
    "issues": "Issue", "issue": "Issue",
    "tickets": "Ticket", "ticket": "Ticket",
    "bugs": "Bug", "bug": "Bug",
    "comments": "Comment", "comment": "Comment",

    # People / HR
    "customers": "Customer", "customer": "Customer",
    "users": "User", "user": "User",
    "employees": "Employee", "employee": "Employee",
    "staff": "Staff",
    "members": "Member", "member": "Member",
    "students": "Student", "student": "Student",
    "teachers": "Teacher", "teacher": "Teacher",
    "vendors": "Vendor", "vendor": "Vendor",
    "suppliers": "Supplier", "supplier": "Supplier",
    "candidates": "Candidate", "candidate": "Candidate",
    "applicants": "Applicant", "applicant": "Applicant",
    "drivers": "Driver", "driver": "Driver",
    "patients": "Patient", "patient": "Patient",
    "doctors": "Doctor", "doctor": "Doctor",
    "clients": "Client", "client": "Client",

    # Scheduling / Booking
    "appointments": "Appointment", "appointment": "Appointment",
    "bookings": "Booking", "booking": "Booking",
    "reservations": "Reservation", "reservation": "Reservation",
    "slots": "Slot", "slot": "Slot",
    "events": "Event", "event": "Event",
    "sessions": "Session", "session": "Session",
    "classes": "Class", "class": "Class",

    # Content / Media
    "posts": "Post", "post": "Post",
    "articles": "Article", "article": "Article",
    "blogs": "Blog", "blog": "Blog",
    "pages": "Page", "page": "Page",
    "categories": "Category", "category": "Category",
    "tags": "Tag", "tag": "Tag",
    "comments": "Comment",
    "reviews": "Review", "review": "Review",
    "ratings": "Rating", "rating": "Rating",
    "media": "Media",
    "files": "File", "file": "File",
    "documents": "Document", "document": "Document",
    "images": "Image", "image": "Image",

    # Logistics / Operations
    "deliveries": "Delivery", "delivery": "Delivery",
    "shipments": "Shipment", "shipment": "Shipment",
    "routes": "Route", "route": "Route",
    "vehicles": "Vehicle", "vehicle": "Vehicle",
    "jobs": "Job", "job": "Job",
    "services": "Service", "service": "Service",
    "requests": "Request", "request": "Request",
    "repairs": "Repair", "repair": "Repair",
    "assets": "Asset", "asset": "Asset",
    "equipment": "Equipment",
    "locations": "Location", "location": "Location",
    "branches": "Branch", "branch": "Branch",
    "warehouses": "Warehouse", "warehouse": "Warehouse",
    "rooms": "Room", "room": "Room",
    "floors": "Floor", "floor": "Floor",

    # Health / Fitness
    "workouts": "Workout", "workout": "Workout",
    "exercises": "Exercise", "exercise": "Exercise",
    "plans": "Plan", "plan": "Plan",
    "memberships": "Membership", "membership": "Membership",
    "prescriptions": "Prescription", "prescription": "Prescription",
    "diagnoses": "Diagnosis", "diagnosis": "Diagnosis",
    "records": "Record", "record": "Record",

    # Education
    "courses": "Course", "course": "Course",
    "lessons": "Lesson", "lesson": "Lesson",
    "assignments": "Assignment", "assignment": "Assignment",
    "grades": "Grade", "grade": "Grade",
    "quizzes": "Quiz", "quiz": "Quiz",
    "exams": "Exam", "exam": "Exam",
    "certificates": "Certificate", "certificate": "Certificate",
    "attendance": "Attendance",

    # Misc
    "reports": "Report", "report": "Report",
    "notifications": "Notification", "notification": "Notification",
    "messages": "Message", "message": "Message",
    "logs": "Log", "log": "Log",
    "settings": "Setting", "setting": "Setting",
    "feedback": "Feedback",
    "surveys": "Survey", "survey": "Survey",
    "polls": "Poll", "poll": "Poll",
    "notes": "Note", "note": "Note",
    "todos": "Todo", "todo": "Todo",
    "reminders": "Reminder", "reminder": "Reminder",
    "properties": "Property", "property": "Property",
    "listings": "Listing", "listing": "Listing",
    "items": "Item", "item": "Item",
    "packages": "Package", "package": "Package",
    "menus": "Menu", "menu": "Menu",
    "dishes": "Dish", "dish": "Dish",
    "ingredients": "Ingredient", "ingredient": "Ingredient",
    "recipes": "Recipe", "recipe": "Recipe",
}

ROLE_KEYWORDS = {
    "admin": "admin",
    "administrator": "admin",
    "manager": "manager",
    "supervisor": "manager",
    "user": "user",
    "member": "user",
    "guest": "guest",
    "customer": "customer",
    "client": "customer",
    "employee": "employee",
    "staff": "employee",
    "teacher": "teacher",
    "instructor": "teacher",
    "student": "student",
    "learner": "student",
    "driver": "driver",
    "doctor": "doctor",
    "patient": "patient",
    "vendor": "vendor",
    "owner": "admin",
    "moderator": "manager",
    "agent": "employee",
    "operator": "employee",
}

# Common English stopwords and non-entity words to skip during noun fallback
SKIP_WORDS = {
    "a", "an", "the", "and", "or", "but", "with", "for", "to", "of", "in",
    "on", "at", "by", "from", "as", "is", "are", "was", "be", "been",
    "can", "will", "should", "that", "this", "it", "its", "my", "we",
    "they", "their", "has", "have", "not", "no", "so", "do", "use",
    "build", "make", "create", "need", "want", "app", "application",
    "system", "platform", "tool", "website", "web", "mobile", "simple",
    "basic", "new", "good", "let", "me", "us", "our", "where", "which",
    "who", "what", "how", "when", "all", "any", "each", "some", "see",
    "get", "set", "also", "like", "just", "only", "more", "very", "cool",
    "nice", "great", "something", "anything", "everything", "manage",
    "track", "view", "show", "add", "edit", "delete", "update", "list",
    "dashboard", "login", "signup", "admin", "user", "role", "page",
    "feature", "support", "access", "data", "info", "information",
    "based", "type", "way", "thing", "stuff", "people", "person",
    # Adjectives that get mistaken for nouns
    "remote", "online", "digital", "smart", "auto", "real", "live",
    "local", "global", "custom", "multi", "single", "small", "large",
    "fast", "easy", "free", "open", "main", "full", "quick", "daily",
    "monthly", "annual", "internal", "external", "general", "special",
    "personal", "private", "public", "active", "total", "other",
    "different", "multiple", "various", "modern", "advanced", "complete",
}

# Words that are valid nouns but often appear as plurals - map to singular
PLURAL_FIXES = {
    "teamss": "Team",   # catch double-s bug
    "teams": "Team",
    "statuses": "Status",
    "analyses": "Analysis",
    "indices": "Index",
}

VAGUE_TOKENS_THRESHOLD = 2
CONFLICT_PATTERNS = [
    (r"no\s+login", "auth"),
]


def _to_singular(word: str) -> str:
    """Convert common plural forms to singular."""
    if word in PLURAL_FIXES:
        return PLURAL_FIXES[word]
    # -ies -> -y (e.g. deliveries -> delivery)
    if word.endswith("ies") and len(word) > 4:
        return word[:-3] + "y"
    # -es -> remove es (e.g. statuses -> status) only if result is 4+ chars
    if word.endswith("es") and len(word) > 5:
        return word[:-2]
    # -s -> remove s (e.g. teams -> team) only if result is 4+ chars
    if word.endswith("s") and not word.endswith("ss") and len(word) > 4:
        return word[:-1]
    return word


def _extract_noun_fallback(text: str) -> set:
    """
    When taxonomy matching finds no entities, extract candidate nouns from the
    prompt itself. Looks for words that could be domain entity names.
    Returns a set of capitalized entity name strings.
    """
    words = re.findall(r"\b[a-z][a-z]+\b", text.lower())
    candidates = set()
    for word in words:
        if word in SKIP_WORDS:
            continue
        if len(word) < 4:
            continue
        # Convert to singular form first
        singular = _to_singular(word)
        if singular in SKIP_WORDS or len(singular) < 3:
            continue
        candidates.add(singular.capitalize())
    return candidates


def extract_intent(prompt: str) -> dict:
    text = prompt.lower()

    # --- Feature extraction ---
    features = set()
    for feature, kws in FEATURE_KEYWORDS.items():
        if any(kw in text for kw in kws):
            features.add(feature)

    # --- Entity extraction from taxonomy ---
    entities = set()
    for kw, entity_name in ENTITY_KEYWORDS.items():
        if re.search(r"\b" + re.escape(kw) + r"\b", text):
            entities.add(entity_name)

    # --- Role extraction ---
    roles = set()
    for kw, role in ROLE_KEYWORDS.items():
        if re.search(r"\b" + re.escape(kw) + r"\b", text):
            roles.add(role)
    if "rbac" in features and not roles:
        roles.update(["admin", "user"])
    if "auth" in features and not roles:
        roles.add("user")

    # --- Conflict detection ---
    conflicts = []
    if "no login" in text and "auth" in features:
        conflicts.append("Prompt mentions both 'no login' and login-related auth keywords.")
    if "free" in text and "payments" in features and "premium" in text:
        conflicts.append("Prompt mentions both 'free' and 'premium/payments' — may indicate freemium model.")

    signal_count = len(features) + len(entities) + len(roles)
    is_vague = signal_count < VAGUE_TOKENS_THRESHOLD

    assumptions = []

    if is_vague:
        # Try noun fallback before giving up and defaulting to "Item"
        if not entities:
            fallback_entities = _extract_noun_fallback(text)
            if fallback_entities:
                # Pick up to 2 best candidates (shortest = most likely a real noun)
                chosen = sorted(fallback_entities, key=len)[:2]
                entities.update(chosen)
                assumptions.append(
                    f"No recognized domain entity detected -> inferred entity/entities from prompt nouns: "
                    f"{', '.join(chosen)}."
                )
            else:
                entities.add("Item")
                assumptions.append("No concrete domain entity detected -> defaulted to generic 'Item' entity.")

        if not features:
            features.add("dashboard")
            assumptions.append("No feature signals detected -> defaulted to a basic dashboard feature.")

        if not roles:
            roles.add("user")
            assumptions.append("No roles detected -> defaulted to single 'user' role.")

    # Recompute after fallback (confidence should reflect actual signal)
    signal_count = len(features) + len(entities) + len(roles)

    intent = {
        "raw_prompt": prompt,
        "features": sorted(features),
        "entities": sorted(entities),
        "roles": sorted(roles),
        "is_vague": is_vague,
        "conflicts": conflicts,
        "assumptions": assumptions,
        "confidence": round(min(1.0, signal_count / 6), 2),
    }
    return intent
