"""
Evaluation Framework
Runs the dataset (10 real prompts + 10 edge cases) through the pipeline and reports:
success rate, retries (repair actions) per request, failure types, latency.
"""
import json
import os
import sys
import shutil

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pipeline import run_pipeline


def run_eval():
    here = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(here, "dataset.json")) as f:
        dataset = json.load(f)

    results = []
    scratch_root = os.path.join(here, "_scratch_runs")
    if os.path.exists(scratch_root):
        shutil.rmtree(scratch_root)

    def run_one(prompt, category, idx):
        out_dir = os.path.join(scratch_root, f"{category}_{idx}")
        r = run_pipeline(prompt, output_dir=out_dir, generate_app=True)
        return {
            "category": category,
            "prompt": prompt,
            "status": r["status"],
            "retries": r.get("retries", 0),
            "latency_ms": r["latency_ms"],
            "assumptions": r.get("assumptions", []),
            "conflicts": r.get("conflicts", []),
            "execution_boots": r.get("execution", {}).get("boots") if "execution" in r else None,
        }

    for i, p in enumerate(dataset["real_prompts"]):
        results.append(run_one(p, "real", i))

    for i, ec in enumerate(dataset["edge_cases"]):
        results.append(run_one(ec["prompt"], f"edge_{ec['type']}", i))

    # --- Metrics ---
    total = len(results)
    succeeded = sum(1 for r in results if r["status"] == "success")
    failure_types = {}
    for r in results:
        if r["status"] != "success":
            failure_types[r["status"]] = failure_types.get(r["status"], 0) + 1

    avg_latency = round(sum(r["latency_ms"] for r in results) / total, 2)
    avg_retries = round(sum(r["retries"] for r in results) / total, 2)
    total_retries = sum(r["retries"] for r in results)

    summary = {
        "total_prompts": total,
        "success_rate": round(succeeded / total, 3),
        "succeeded": succeeded,
        "failed": total - succeeded,
        "failure_types": failure_types,
        "avg_latency_ms": avg_latency,
        "avg_repair_actions_per_request": avg_retries,
        "total_repair_actions": total_retries,
        "results": results,
    }

    out_path = os.path.join(here, "eval_results.json")
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)

    shutil.rmtree(scratch_root, ignore_errors=True)

    print(f"\n=== EVAL SUMMARY ===")
    print(f"Total prompts:        {total}")
    print(f"Success rate:         {summary['success_rate']*100:.1f}%  ({succeeded}/{total})")
    print(f"Avg latency:          {avg_latency} ms")
    print(f"Avg repair actions:   {avg_retries} per request")
    print(f"Failure types:        {failure_types}")
    print(f"\nPer-category breakdown:")
    cats = {}
    for r in results:
        cats.setdefault(r["category"], []).append(r["status"])
    for cat, statuses in cats.items():
        ok = sum(1 for s in statuses if s == "success")
        print(f"  {cat:20s} {ok}/{len(statuses)} success")
    print(f"\nFull results written to {out_path}")
    return summary


if __name__ == "__main__":
    run_eval()
