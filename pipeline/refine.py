"""
Refinement Engine — handles mid-session requirement modifications.
Detects the type of change, patches only affected parts, returns a diff.
"""
from pipeline.intent_extraction import extract_intent


# Keywords that signal removal intent
REMOVE_SIGNALS = ["remove", "drop", "delete", "no more", "without", "get rid of", "don't need"]
# Keywords that signal addition intent
ADD_SIGNALS = ["add", "include", "also", "plus", "with", "need", "want"]


def detect_change_type(refinement: str) -> str:
    """Detect whether the refinement is adding, removing, or replacing."""
    text = refinement.lower()
    has_remove = any(kw in text for kw in REMOVE_SIGNALS)
    has_add = any(kw in text for kw in ADD_SIGNALS)

    if has_remove and not has_add:
        return "remove"
    elif has_remove and has_add:
        return "mixed"
    else:
        return "add"  # default — most refinements are additions


def compute_diff(old_intent: dict, new_intent: dict) -> dict:
    """Compute what was added and removed between two intents."""
    old_features = set(old_intent.get("features", []))
    new_features = set(new_intent.get("features", []))
    old_entities = set(old_intent.get("entities", []))
    new_entities = set(new_intent.get("entities", []))
    old_roles = set(old_intent.get("roles", []))
    new_roles = set(new_intent.get("roles", []))

    return {
        "features": {
            "added": sorted(new_features - old_features),
            "removed": sorted(old_features - new_features),
            "kept": sorted(old_features & new_features),
        },
        "entities": {
            "added": sorted(new_entities - old_entities),
            "removed": sorted(old_entities - new_entities),
            "kept": sorted(old_entities & new_entities),
        },
        "roles": {
            "added": sorted(new_roles - old_roles),
            "removed": sorted(old_roles - new_roles),
            "kept": sorted(old_roles & new_roles),
        },
    }


def merge_intents(old_intent: dict, refinement_text: str) -> tuple:
    """
    Intelligently merge old intent with refinement.
    Returns (merged_intent, diff, change_type).
    """
    new_intent = extract_intent(refinement_text)
    change_type = detect_change_type(refinement_text)

    if change_type == "remove":
        # Remove what the refinement mentions
        merged_features = sorted(set(old_intent.get("features", [])) - set(new_intent.get("features", [])))
        merged_entities = sorted(set(old_intent.get("entities", [])) - set(new_intent.get("entities", [])))
        merged_roles    = sorted(set(old_intent.get("roles", [])) - set(new_intent.get("roles", [])))
    elif change_type == "mixed":
        # Parse "add X remove Y" — add new ones, keep old ones, but remove explicitly mentioned
        merged_features = sorted(set(old_intent.get("features", [])) | set(new_intent.get("features", [])))
        merged_entities = sorted(set(old_intent.get("entities", [])) | set(new_intent.get("entities", [])))
        merged_roles    = sorted(set(old_intent.get("roles", [])) | set(new_intent.get("roles", [])))
        # Remove explicitly dropped items
        for kw in REMOVE_SIGNALS:
            if kw in refinement_text.lower():
                # Remove features that appear after remove keywords
                for f in new_intent.get("features", []):
                    if f in merged_features:
                        merged_features.remove(f)
    else:
        # Add — union of old and new
        merged_features = sorted(set(old_intent.get("features", [])) | set(new_intent.get("features", [])))
        merged_entities = sorted(set(old_intent.get("entities", [])) | set(new_intent.get("entities", [])))
        merged_roles    = sorted(set(old_intent.get("roles", [])) | set(new_intent.get("roles", [])))

    # Fallback — if merged has no entities, keep old
    if not merged_entities:
        merged_entities = old_intent.get("entities", [])
    if not merged_roles:
        merged_roles = old_intent.get("roles", ["user"])

    merged_intent = {
        "raw_prompt": old_intent.get("raw_prompt", "") + " | refined: " + refinement_text,
        "features": merged_features,
        "entities": merged_entities,
        "roles": merged_roles,
        "is_vague": False,
        "conflicts": old_intent.get("conflicts", []) + new_intent.get("conflicts", []),
        "assumptions": new_intent.get("assumptions", []),
        "confidence": round(min(1.0, (len(merged_features) + len(merged_entities) + len(merged_roles)) / 6), 2),
    }

    # Build merged prompt string for pipeline
    merged_prompt = _intent_to_prompt(merged_intent)

    diff = compute_diff(old_intent, {
        "features": merged_features,
        "entities": merged_entities,
        "roles": merged_roles,
    })

    return merged_prompt, merged_intent, diff, change_type


def _intent_to_prompt(intent: dict) -> str:
    """Convert a merged intent back into a natural language prompt for the pipeline."""
    parts = []
    if intent["entities"]:
        parts.append("entities: " + ", ".join(intent["entities"]))
    if intent["features"]:
        parts.append("features: " + ", ".join(intent["features"]))
    if intent["roles"]:
        parts.append("roles: " + ", ".join(intent["roles"]))
    return "App with " + "; ".join(parts)
