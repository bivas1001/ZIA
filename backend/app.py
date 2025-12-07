from flask import Flask, request, jsonify, render_template
import os

# ✅ FIXED IMPORT PATHS (IMPORTANT)
from backend.knowledge.store import (
    init_db,
    search_knowledge,
    save_qa,
    export_packets,
    import_packets,
)
from backend.ai_engine.intent import detect_intent
from backend.ai_engine.similarity import is_similar_enough
from backend.ai_engine.rules import fallback_answer

app = Flask(
    __name__,
    template_folder="templates",
    static_folder="static",
)

# ✅ Initialize DB at startup
init_db()


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "message": "ZIA backend running"}), 200


@app.route("/ask", methods=["POST"])
def ask():
    data = request.get_json(silent=True) or {}
    question = (data.get("question") or "").strip()

    if not question:
        return jsonify({"error": "Missing 'question'"}), 400

    intent = detect_intent(question)
    best_match = search_knowledge(question)

    if best_match and is_similar_enough(question, best_match["question"]):
        return jsonify(
            {
                "answer": best_match["answer"],
                "source": "local_knowledge",
                "confidence": best_match["confidence"],
                "intent": intent,
            }
        )

    fallback = fallback_answer(question, intent)
    if fallback is not None:
        return jsonify(
            {
                "answer": fallback,
                "source": "rule_engine",
                "confidence": 0.5,
                "intent": intent,
            }
        )

    return jsonify(
        {
            "answer": "I don't know this yet. You can teach me using /teach.",
            "source": "unknown",
            "confidence": 0.0,
            "intent": intent,
        }
    )


@app.route("/teach", methods=["POST"])
def teach():
    data = request.get_json(silent=True) or {}
    question = (data.get("question") or "").strip()
    answer = (data.get("answer") or "").strip()
    topic = (data.get("topic") or "").strip() or None

    if not question or not answer:
        return jsonify({"error": "Both 'question' and 'answer' are required"}), 400

    record = save_qa(question=question, answer=answer, topic=topic)

    return jsonify(
        {
            "status": "saved",
            "id": record["id"],
            "question": record["question"],
            "answer": record["answer"],
            "topic": record["topic"],
        }
    ), 201


@app.route("/sync/export", methods=["GET"])
def sync_export():
    packets, device_id = export_packets()
    return jsonify({"device_id": device_id, "packets": packets}), 200


@app.route("/sync/import", methods=["POST"])
def sync_import():
    data = request.get_json(silent=True) or {}
    peer_id = (data.get("device_id") or "").strip()
    packets = data.get("packets") or []

    if not isinstance(packets, list):
        return jsonify({"error": "'packets' must be a list"}), 400

    merged, skipped = import_packets(packets, peer_id=peer_id or None)
    return jsonify({"status": "ok", "merged": merged, "skipped": skipped}), 200


# ✅ Gunicorn entrypoint
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
