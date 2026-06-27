"""
Stage 4: Validation + Repair Engine (CORE)
Detects: invalid JSON, missing keys, hallucinated fields, schema mismatches, logical inconsistencies.
Repairs surgically (targeted field-level fixes), not blind full retries.
"""
import json

# Minimal, dependency-free structural schema: required top-level keys -> required nested keys/type
MASTER_SCHEMA = {
    "ui_schema": {"type": dict, "required_keys": ["pages"], "pages_type": list},
    "api_schema": {"type": dict, "required_keys": ["endpoints"], "endpoints_type": list},
    "db_schema": {"type": dict, "required_keys": ["tables"], "tables_type": dict},
    "auth_schema": {"type": dict, "required_keys": ["roles", "permissions"]},
    "business_rules": {"type": list},
}


class SchemaValidationError(Exception):
    def __init__(self, message, path=None):
        super().__init__(message)
        self.path = path or []


def _validate_master_schema(config: dict):
    """Dependency-free structural validator standing in for jsonschema.validate()."""
    for key, rules in MASTER_SCHEMA.items():
        if key not in config:
            raise SchemaValidationError(f"missing top-level key '{key}'", path=[key])
        if not isinstance(config[key], rules["type"]):
            raise SchemaValidationError(f"key '{key}' has wrong type", path=[key])
        for rk in rules.get("required_keys", []):
            if rk not in config[key]:
                raise SchemaValidationError(f"'{key}.{rk}' is required", path=[key, rk])
    return True


class RepairLog:
    def __init__(self):
        self.actions = []

    def log(self, action: str):
        self.actions.append(action)


def validate_and_repair(config: dict) -> tuple[dict, RepairLog, bool]:
    """
    Returns (repaired_config, repair_log, is_valid_after_repair)
    """
    log = RepairLog()

    # 1. JSON validity (already a dict here, but simulate round-trip check
    #    for cases where config came from raw LLM text in a hybrid pipeline)
    try:
        json.dumps(config)
    except (TypeError, ValueError):
        log.log("FATAL: config not JSON-serializable, aborting repair")
        return config, log, False

    # 2. Structural validation against master schema -> targeted repair, not full regen
    try:
        _validate_master_schema(config)
    except SchemaValidationError as e:
        defaults = {
            "ui_schema": {"pages": []},
            "api_schema": {"endpoints": []},
            "db_schema": {"tables": {}},
            "auth_schema": {"roles": ["user"], "permissions": {}},
            "business_rules": [],
        }
        for key, default_val in defaults.items():
            if key not in config:
                config[key] = default_val
                log.log(f"REPAIR: missing top-level key '{key}' -> inserted default")

    # 3. Cross-layer consistency: API entity must have a DB table
    db_tables = set(config["db_schema"]["tables"].keys())
    api_entities = {ep["entity"].lower() + "s" for ep in config["api_schema"]["endpoints"] if "entity" in ep}
    orphan_api_entities = api_entities - db_tables
    for orphan in orphan_api_entities:
        config["db_schema"]["tables"][orphan] = {
            "columns": [{"name": "id", "type": "integer", "primary_key": True},
                        {"name": "name", "type": "string"}]
        }
        log.log(f"REPAIR: API referenced entity '{orphan}' with no DB table -> generated minimal table")

    # 4. UI pages binding to non-existent API paths -> hallucinated field check
    valid_api_paths = {ep["path"].split("/{")[0] for ep in config["api_schema"]["endpoints"]}
    for page in config["ui_schema"]["pages"]:
        for comp in page.get("components", []):
            bind = comp.get("binds_to_api")
            if bind and bind not in valid_api_paths:
                comp["binds_to_api"] = None
                log.log(f"REPAIR: UI component in page '{page['name']}' bound to non-existent API "
                        f"path '{bind}' -> unbound (hallucinated field removed)")

    # 5. Auth role consistency: every role used in business_rules/permissions must exist in roles list
    declared_roles = set(config["auth_schema"]["roles"])
    perm_roles = set(config["auth_schema"]["permissions"].keys())
    for r in perm_roles - declared_roles:
        config["auth_schema"]["roles"].append(r)
        log.log(f"REPAIR: permission matrix referenced undeclared role '{r}' -> added to roles list")

    # 6. Logical inconsistency: business rule references a page that doesn't exist
    page_names = {p["name"] for p in config["ui_schema"]["pages"]}
    for rule in config["business_rules"]:
        applies_to = rule.get("applies_to", [])
        bad_refs = [p for p in applies_to if p not in page_names]
        if bad_refs:
            rule["applies_to"] = [p for p in applies_to if p in page_names]
            log.log(f"REPAIR: business rule '{rule.get('rule')}' referenced non-existent page(s) "
                    f"{bad_refs} -> removed dangling references")

    # Final re-validation pass
    try:
        _validate_master_schema(config)
        is_valid = True
    except SchemaValidationError:
        is_valid = False
        log.log("FATAL: schema still invalid after repair pass")

    return config, log, is_valid
