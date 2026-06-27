"""
Web server for promptc — natural language to app compiler.
Run: pip install flask && python server.py
"""
from flask import Flask, request, jsonify, render_template
from pipeline import run_pipeline
from pipeline.intent_extraction import extract_intent
from pipeline.refine import merge_intents
import os

app = Flask(__name__)

# In-memory session store
_sessions = {}


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/generate", methods=["POST"])
def generate():
    data = request.get_json(force=True) or {}
    prompt = data.get("prompt", "").strip()
    session_id = data.get("session_id", "default")

    if not prompt:
        return jsonify({"status": "error", "message": "prompt is required"}), 400

    out_dir = os.path.join("generated_app")
    result = run_pipeline(prompt, output_dir=out_dir, generate_app=True)

    # Store intent for this session
    _sessions[session_id] = {
        "original_prompt": prompt,
        "intent": extract_intent(prompt),
        "history": [prompt],
    }

    return jsonify(result)


@app.route("/api/refine", methods=["POST"])
def refine():
    """
    Handles mid-session requirement modifications.
    Detects change type (add/remove/mixed), patches only affected parts,
    returns diff showing exactly what changed.
    """
    data = request.get_json(force=True) or {}
    refinement = data.get("prompt", "").strip()
    session_id = data.get("session_id", "default")

    if not refinement:
        return jsonify({"status": "error", "message": "refinement is required"}), 400

    previous = _sessions.get(session_id)
    if not previous:
        # No session — treat as fresh compile
        out_dir = os.path.join("generated_app")
        result = run_pipeline(refinement, output_dir=out_dir, generate_app=True)
        _sessions[session_id] = {
            "original_prompt": refinement,
            "intent": extract_intent(refinement),
            "history": [refinement],
        }
        return jsonify({**result, "refined": False, "note": "No previous session — compiled fresh."})

    # Smart merge
    merged_prompt, merged_intent, diff, change_type = merge_intents(
        previous["intent"], refinement
    )

    # Run full pipeline on merged prompt
    out_dir = os.path.join("generated_app")
    result = run_pipeline(merged_prompt, output_dir=out_dir, generate_app=True)

    # Update session
    previous["intent"] = merged_intent
    previous["history"].append(refinement)
    _sessions[session_id] = previous

    # Attach refinement metadata to response
    result["refined"] = True
    result["change_type"] = change_type
    result["diff"] = diff
    result["history"] = previous["history"]
    result["note"] = f"Refined from: '{previous['original_prompt']}'"

    return jsonify(result)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=7000)
