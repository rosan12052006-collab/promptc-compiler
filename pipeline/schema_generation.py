"""
Stage 3: Schema Generation
Architecture -> concrete UI schema, API schema, DB schema, Auth schema.
"""

TYPE_MAP_DEFAULT = "string"
TYPE_OVERRIDES = {
    "amount": "number", "price": "number", "total": "number", "stock": "number", "quantity": "number",
    "due_date": "date", "datetime": "date",
    "status": "string", "stage": "string", "priority": "string",
}


def infer_type(field_name: str) -> str:
    return TYPE_OVERRIDES.get(field_name, TYPE_MAP_DEFAULT)


def generate_schemas(architecture: dict) -> dict:
    entities = architecture["entities"]

    # --- DB schema ---
    db_schema = {"tables": {}}
    for ent, meta in entities.items():
        table_name = ent.lower() + "s"
        columns = [{"name": "id", "type": "integer", "primary_key": True}]
        for f in meta["fields"]:
            col = {"name": f, "type": "integer" if f.endswith("_id") else infer_type(f)}
            if f.endswith("_id"):
                ref_entity = f[:-3].capitalize()
                col["foreign_key"] = f"{ref_entity.lower()}s.id" if ref_entity in entities else None
            columns.append(col)
        db_schema["tables"][table_name] = {"columns": columns}

    # --- API schema ---
    api_schema = {"endpoints": []}
    for ent, meta in entities.items():
        base = "/api/" + ent.lower() + "s"
        for method, path, desc in [
            ("GET", base, f"List {ent}s"),
            ("POST", base, f"Create {ent}"),
            ("GET", base + "/{id}", f"Get single {ent}"),
            ("PUT", base + "/{id}", f"Update {ent}"),
            ("DELETE", base + "/{id}", f"Delete {ent}"),
        ]:
            api_schema["endpoints"].append({
                "method": method,
                "path": path,
                "description": desc,
                "entity": ent,
                "auth_required": True,
                "request_fields": meta["fields"] if method in ("POST", "PUT") else [],
            })

    # --- UI schema ---
    ui_schema = {"pages": []}
    for page in architecture["pages"]:
        matching_entity = next((e for e, m in entities.items() if m["crud_page"] == page), None)
        if matching_entity:
            components = [
                {"type": "Table", "binds_to_api": f"/api/{matching_entity.lower()}s", "columns": entities[matching_entity]["fields"]},
                {"type": "Form", "binds_to_api": f"/api/{matching_entity.lower()}s", "fields": entities[matching_entity]["fields"]},
            ]
        else:
            components = [{"type": "Panel", "binds_to_api": None}]
        ui_schema["pages"].append({
            "name": page,
            "route": "/" + page.lower(),
            "components": components,
        })

    # --- Auth schema ---
    auth_schema = {
        "roles": architecture["roles"],
        "permissions": architecture["permissions"],
        "strategy": "session_token",  # deterministic default, no external billing/auth provider needed
    }

    return {
        "ui_schema": ui_schema,
        "api_schema": api_schema,
        "db_schema": db_schema,
        "auth_schema": auth_schema,
        "business_rules": architecture["business_rules"],
        "assumptions": architecture["assumptions"],
    }
