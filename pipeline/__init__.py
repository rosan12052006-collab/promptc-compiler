"""
Pipeline Orchestrator
Intent Extraction -> System Design -> Schema Generation -> Validation/Repair -> Execution
"""
import time
import os
from .intent_extraction import extract_intent
from .system_design import design_system
from .schema_generation import generate_schemas
from .validation_repair import validate_and_repair
from .runtime_executor import generate_runtime_app, execution_self_check


def run_pipeline(prompt: str, output_dir: str = None, generate_app: bool = True) -> dict:
    t0 = time.time()
    trace = {}

    intent = extract_intent(prompt)
    trace["intent"] = intent

    if intent["is_vague"] and len(intent["assumptions"]) == 0:
        # Truly empty signal even after defaulting attempt -> ask for clarification instead of guessing wildly
        return {
            "status": "needs_clarification",
            "message": "Prompt is too underspecified. Please specify at least one entity "
                        "(e.g. 'contacts', 'orders') or a feature (e.g. 'login', 'dashboard').",
            "trace": trace,
            "latency_ms": round((time.time() - t0) * 1000, 1),
        }

    architecture = design_system(intent)
    trace["architecture"] = architecture

    config = generate_schemas(architecture)
    trace["pre_repair_config"] = {k: v for k, v in config.items() if k != "assumptions"}

    repaired_config, repair_log, is_valid = validate_and_repair(config)
    trace["repair_actions"] = repair_log.actions
    trace["is_valid"] = is_valid

    result = {
        "status": "success" if is_valid else "failed_validation",
        "config": repaired_config,
        "assumptions": intent.get("assumptions", []),
        "conflicts": intent.get("conflicts", []),
        "repair_actions": repair_log.actions,
        "retries": len(repair_log.actions),  # targeted repairs, counted in lieu of blind retries
        "trace": trace,
    }

    if generate_app and is_valid:
        out_dir = output_dir or os.path.join("generated_app")
        gen_info = generate_runtime_app(repaired_config, out_dir)
        check = execution_self_check(out_dir)
        result["execution"] = {**gen_info, **check}
        result["status"] = "success" if check["compiles"] else "failed_execution"

    result["latency_ms"] = round((time.time() - t0) * 1000, 1)
    return result
