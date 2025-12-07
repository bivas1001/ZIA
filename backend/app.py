from flask import Flask, request, jsonify, render_template
import os


from knowledge.store import (
    init_db,
    search_knowledge,
    save_qa,
    export_packets,
    import_packets,
)
from ai_engine.intent import detect_intent
from ai_engine.similarity import is_similar_enough
from ai_engine.rules import fallback_answer

app = Flask(__name__)

# ✅ Flask 3.x compatible initialization
init_db()


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/health", methods=["GET"])
def health():
    """
    Simple health-check endpoint.
    """
    return jsonify({"status": "ok", "message": "ZIA backend running"}), 200


@app.route("/ask", methods=["POST"])
def ask():
    """
    Main endpoint:
    Input JSON: { "question": "..." }
    Output JSON:
      {
        "answer": "...",
        "source": "local_knowledge" | "rule_engine" | "unknown",
        "confidence": 0.xx,
        "intent": "general_qa" | "note_create" | ...
      }
    """
    data = request.get_json(silent=True) or {}
    question = (data.get("question") or "").strip()

    if not question:
        return jsonify({"error": "Missing 'question'"}), 400

    # 1. Detect intent (very simple offline logic – implemented in ai_engine/intent.py)
    intent = detect_intent(question)

    # 2. Try to find an existing answer in local knowledge
    best_match = search_knowledge(question)

    if best_match and is_similar_enough(question, best_match["question"]):
        # We found a good enough answer in our local DB
        return jsonify(
            {
                "answer": best_match["answer"],
                "source": "local_knowledge",
                "confidence": best_match["confidence"],
                "intent": intent,
            }
        )

    # 3. No good match in knowledge → use rule-based fallback
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

    # 4. Completely unknown → ask user to teach later
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
    """
    Endpoint to teach the assistant a new Q&A pair.

    Input JSON:
      {
        "question": "...",
        "answer": "...",
        "topic": "optional-topic"
      }
    Output JSON:
      {
        "status": "saved",
        "id": "k_123",
        "question": "...",
        "answer": "...",
        "topic": "..."
      }
    """
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
    """
    Export local knowledge as 'knowledge packets'
    that can be sent to another device (peer-to-peer sync).

    Output JSON:
      {
        "device_id": "...",
        "packets": [ ... ]
      }
    """
    packets, device_id = export_packets()

    return jsonify(
        {
            "device_id": device_id,
            "packets": packets,
        }
    ), 200


@app.route("/sync/import", methods=["POST"])
def sync_import():
    """
    Import knowledge packets from another device.

    Input JSON:
      {
        "device_id": "peer-id",
        "packets": [ ... ]
      }
    Output JSON:
      {
        "status": "ok",
        "merged": <int>,      # how many packets merged
        "skipped": <int>      # how many ignored (duplicates / lower confidence)
      }
    """
    data = request.get_json(silent=True) or {}

    peer_id = (data.get("device_id") or "").strip()
    packets = data.get("packets") or []

    if not isinstance(packets, list):
        return jsonify({"error": "'packets' must be a list"}), 400

    merged_count, skipped_count = import_packets(packets, peer_id=peer_id or None)

    return jsonify(
        {
            "status": "ok",
            "merged": merged_count,
            "skipped": skipped_count,
        }
    ), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

