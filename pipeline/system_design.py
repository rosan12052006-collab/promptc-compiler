"""
Stage 2: System Design Layer
Converts structured intent -> app architecture (entities w/ fields, pages, flows, role-permission matrix).
"""

# Default field templates per known entity type (extendable)
DEFAULT_FIELDS = {
    # CRM
    "Contact": ["name", "email", "phone", "company"],
    "Lead": ["name", "email", "status", "source"],
    "Deal": ["title", "amount", "stage", "contact_id"],
    "Opportunity": ["title", "amount", "stage", "probability"],
    "Account": ["name", "email", "phone", "industry"],

    # E-commerce / Finance
    "Order": ["product_id", "quantity", "total", "status"],
    "Product": ["name", "price", "stock", "description"],
    "Invoice": ["amount", "due_date", "status", "customer_id"],
    "Payment": ["amount", "method", "status", "order_id"],
    "Transaction": ["amount", "type", "status", "reference"],
    "Subscription": ["plan", "status", "start_date", "end_date"],
    "Coupon": ["code", "discount", "expiry_date", "status"],
    "Cart": ["customer_id", "total", "status"],
    "Refund": ["amount", "reason", "status", "order_id"],
    "Expense": ["title", "amount", "category", "date"],

    # Project / Task Management
    "Task": ["title", "due_date", "status", "assignee_id"],
    "Project": ["name", "description", "status", "due_date"],
    "Milestone": ["title", "due_date", "status", "project_id"],
    "Sprint": ["name", "start_date", "end_date", "status"],
    "Issue": ["title", "description", "status", "priority"],
    "Ticket": ["subject", "status", "priority", "assignee_id"],
    "Bug": ["title", "description", "severity", "status"],
    "Comment": ["content", "author_id", "created_at"],

    # People / HR
    "Customer": ["name", "email", "phone"],
    "User": ["name", "email", "role", "status"],
    "Employee": ["name", "email", "department", "role"],
    "Staff": ["name", "email", "position", "department"],
    "Member": ["name", "email", "membership_type", "status"],
    "Student": ["name", "email", "grade", "enrollment_date"],
    "Teacher": ["name", "email", "subject", "department"],
    "Vendor": ["name", "email", "phone", "category"],
    "Supplier": ["name", "email", "phone", "address"],
    "Candidate": ["name", "email", "position", "status"],
    "Applicant": ["name", "email", "position", "status"],
    "Driver": ["name", "email", "phone", "license_number"],
    "Patient": ["name", "email", "date_of_birth", "phone"],
    "Doctor": ["name", "email", "specialization", "phone"],
    "Client": ["name", "email", "phone", "company"],

    # Scheduling / Booking
    "Appointment": ["title", "datetime", "customer_id", "status"],
    "Booking": ["resource", "datetime", "customer_id", "status"],
    "Reservation": ["resource", "datetime", "customer_id", "status"],
    "Slot": ["datetime", "duration", "status", "resource_id"],
    "Event": ["title", "datetime", "location", "description"],
    "Session": ["title", "datetime", "duration", "status"],
    "Class": ["title", "datetime", "instructor_id", "capacity"],

    # Content / Media
    "Post": ["title", "content", "author_id", "status"],
    "Article": ["title", "content", "author_id", "published_at"],
    "Blog": ["title", "content", "author_id", "status"],
    "Page": ["title", "content", "route", "status"],
    "Category": ["name", "description", "parent_id"],
    "Tag": ["name", "slug"],
    "Review": ["rating", "content", "author_id", "product_id"],
    "Rating": ["score", "author_id", "target_id"],
    "Media": ["filename", "type", "url", "size"],
    "File": ["filename", "type", "url", "size"],
    "Document": ["title", "filename", "url", "uploaded_by"],
    "Image": ["filename", "url", "alt_text", "size"],

    # Logistics / Operations
    "Delivery": ["order_id", "address", "status", "scheduled_date"],
    "Shipment": ["order_id", "carrier", "tracking_number", "status"],
    "Route": ["name", "origin", "destination", "distance"],
    "Vehicle": ["make", "model", "plate_number", "status"],
    "Job": ["title", "description", "status", "assigned_to"],
    "Service": ["name", "description", "price", "duration"],
    "Request": ["title", "description", "status", "requester_id"],
    "Repair": ["title", "description", "status", "assigned_to"],
    "Asset": ["name", "type", "status", "location"],
    "Equipment": ["name", "type", "status", "location"],
    "Location": ["name", "address", "latitude", "longitude"],
    "Branch": ["name", "address", "phone", "manager_id"],
    "Warehouse": ["name", "address", "capacity", "manager_id"],
    "Room": ["name", "capacity", "status", "floor"],
    "Floor": ["number", "name", "building_id"],

    # Health / Fitness
    "Workout": ["title", "duration", "difficulty", "category"],
    "Exercise": ["name", "sets", "reps", "muscle_group"],
    "Plan": ["name", "description", "duration", "price"],
    "Membership": ["type", "status", "start_date", "end_date"],
    "Prescription": ["medication", "dosage", "patient_id", "doctor_id"],
    "Diagnosis": ["condition", "notes", "patient_id", "doctor_id"],
    "Record": ["type", "content", "patient_id", "created_at"],

    # Education
    "Course": ["title", "description", "instructor_id", "status"],
    "Lesson": ["title", "content", "course_id", "order"],
    "Assignment": ["title", "description", "due_date", "course_id"],
    "Grade": ["score", "student_id", "assignment_id"],
    "Quiz": ["title", "course_id", "due_date", "time_limit"],
    "Exam": ["title", "course_id", "date", "duration"],
    "Certificate": ["title", "student_id", "issued_date", "course_id"],
    "Attendance": ["student_id", "date", "status", "course_id"],

    # Misc
    "Report": ["title", "type", "generated_at", "created_by"],
    "Notification": ["title", "message", "type", "user_id"],
    "Message": ["content", "sender_id", "receiver_id", "read"],
    "Log": ["action", "user_id", "timestamp", "details"],
    "Setting": ["key", "value", "description"],
    "Feedback": ["content", "rating", "user_id", "created_at"],
    "Survey": ["title", "description", "status", "created_by"],
    "Poll": ["question", "options", "status", "created_by"],
    "Note": ["title", "content", "author_id", "created_at"],
    "Todo": ["title", "status", "due_date", "user_id"],
    "Reminder": ["title", "datetime", "user_id", "status"],
    "Property": ["name", "address", "type", "status"],
    "Listing": ["title", "description", "price", "status"],
    "Item": ["name", "description", "status"],
    "Package": ["name", "description", "price", "status"],
    "Menu": ["name", "description", "category"],
    "Dish": ["name", "price", "description", "category_id"],
    "Ingredient": ["name", "quantity", "unit", "dish_id"],
    "Recipe": ["title", "ingredients", "instructions", "difficulty"],
}

FEATURE_TO_PAGE = {
    "auth": ["Login", "Signup"],
    "dashboard": ["Dashboard"],
    "analytics": ["Analytics"],
    "payments": ["Billing", "PlanSelection"],
    "rbac": [],
    "notifications": ["Notifications"],
    "search": [],
    "chat": ["Inbox"],
    "file_upload": [],
    "calendar": ["Calendar"],
    "inventory": [],
    "export": [],
    "map": ["Map"],
    "qr_code": [],
    "audit": ["ActivityLog"],
}


def design_system(intent: dict) -> dict:
    entities = {}
    for ent in intent["entities"]:
        # Use known fields or fall back to sensible generic fields based on entity name
        fields = DEFAULT_FIELDS.get(ent)
        if not fields:
            # Smart generic fallback: name + description + status always make sense
            fields = ["name", "description", "status"]
        entities[ent] = {
            "fields": fields,
            "crud_page": f"{ent}List",
        }

    pages = []
    for feature in intent["features"]:
        pages.extend(FEATURE_TO_PAGE.get(feature, []))
    for ent in entities:
        pages.append(entities[ent]["crud_page"])
    pages = sorted(set(pages))

    # Role -> permission matrix
    roles = intent["roles"] or ["user"]
    permissions = {}
    for role in roles:
        if role == "admin":
            perms = {"read": "*", "write": "*", "delete": "*"}
            if "analytics" in intent["features"]:
                perms["view_analytics"] = True
        elif role == "guest":
            perms = {"read": "public", "write": [], "delete": []}
        elif role in ("manager", "supervisor"):
            perms = {"read": "*", "write": "*", "delete": "own"}
        elif role in ("teacher", "instructor"):
            perms = {"read": "*", "write": "own", "delete": "own"}
        else:
            perms = {"read": "own", "write": "own", "delete": "own"}
        permissions[role] = perms

    business_rules = []
    if "payments" in intent["features"]:
        business_rules.append({
            "rule": "premium_gating",
            "description": "Non-premium users are restricted from premium-only pages/features.",
            "applies_to": [p for p in pages if p in ("Analytics", "Billing")] or ["Dashboard"],
        })
    if "rbac" in intent["features"] and "Analytics" in pages:
        business_rules.append({
            "rule": "admin_only_analytics",
            "description": "Only 'admin' role may access the Analytics page.",
            "applies_to": ["Analytics"],
        })
    if "calendar" in intent["features"]:
        business_rules.append({
            "rule": "calendar_access",
            "description": "Users can only view and manage their own calendar entries.",
            "applies_to": ["Calendar"],
        })

    architecture = {
        "entities": entities,
        "pages": pages,
        "roles": roles,
        "permissions": permissions,
        "business_rules": business_rules,
        "assumptions": intent.get("assumptions", []),
    }
    return architecture
