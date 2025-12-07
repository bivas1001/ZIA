import sqlite3
import uuid
import time
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ✅ Railway & local safe DB directory
DB_DIR = os.path.join(BASE_DIR, "..", "database")
os.makedirs(DB_DIR, exist_ok=True)

DB_PATH = os.path.join(DB_DIR, "assistant.db")

DEVICE_ID = str(uuid.uuid4())[:8]

# -------------------------
# DATABASE INITIALIZATION
# -------------------------

def get_connection():
    return sqlite3.connect(DB_PATH)


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS knowledge (
            id TEXT PRIMARY KEY,
            question TEXT NOT NULL,
            answer TEXT NOT NULL,
            topic TEXT,
            confidence REAL,
            source TEXT,
            created_at INTEGER
        )
        """
    )

    conn.commit()
    conn.close()


# -------------------------
# CORE OPERATIONS
# -------------------------

def save_qa(question, answer, topic=None, confidence=0.6, source="local"):
    record_id = f"k_{uuid.uuid4().hex[:10]}"
    timestamp = int(time.time())

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO knowledge (id, question, answer, topic, confidence, source, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (record_id, question, answer, topic, confidence, source, timestamp),
    )

    conn.commit()
    conn.close()

    return {
        "id": record_id,
        "question": question,
        "answer": answer,
        "topic": topic,
        "confidence": confidence,
    }


def search_knowledge(query):
    """
    Very lightweight search:
    - Fetch all questions
    - Return the closest one (exact/partial match for MVP)
    """
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT id, question, answer, confidence FROM knowledge")
    rows = cur.fetchall()

    conn.close()

    query_lower = query.lower()

    for row in rows:
        if query_lower in row[1].lower():
            return {
                "id": row[0],
                "question": row[1],
                "answer": row[2],
                "confidence": row[3],
            }

    return None


# -------------------------
# SYNC (EXPORT / IMPORT)
# -------------------------

def export_packets():
    """
    Export local knowledge into transferable packets.
    """
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT id, question, answer, topic, confidence, created_at
        FROM knowledge
        """
    )

    packets = []

    for row in cur.fetchall():
        packets.append(
            {
                "id": row[0],
                "question": row[1],
                "answer": row[2],
                "topic": row[3],
                "confidence": row[4],
                "timestamp": row[5],
            }
        )

    conn.close()
    return packets, DEVICE_ID


def import_packets(packets, peer_id=None):
    """
    Merge incoming packets intelligently.
    Rules:
    - Skip duplicate IDs
    - Prefer higher confidence answers
    """
    merged = 0
    skipped = 0

    conn = get_connection()
    cur = conn.cursor()

    for pkt in packets:
        pkt_id = pkt.get("id")
        pkt_conf = pkt.get("confidence", 0.0)

        cur.execute("SELECT confidence FROM knowledge WHERE id = ?", (pkt_id,))
        existing = cur.fetchone()

        if existing:
            # Duplicate found
            if pkt_conf > existing[0]:
                cur.execute(
                    """
                    UPDATE knowledge
                    SET question = ?, answer = ?, topic = ?, confidence = ?, source = ?
                    WHERE id = ?
                    """,
                    (
                        pkt.get("question"),
                        pkt.get("answer"),
                        pkt.get("topic"),
                        pkt_conf,
                        f"peer:{peer_id}",
                        pkt_id,
                    ),
                )
                merged += 1
            else:
                skipped += 1
        else:
            # New packet
            cur.execute(
                """
                INSERT INTO knowledge (id, question, answer, topic, confidence, source, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    pkt_id,
                    pkt.get("question"),
                    pkt.get("answer"),
                    pkt.get("topic"),
                    pkt_conf,
                    f"peer:{peer_id}",
                    pkt.get("timestamp", int(time.time())),
                ),
            )
            merged += 1

    conn.commit()
    conn.close()

    return merged, skipped
