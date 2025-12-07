// frontend/script.js
//
// Frontend logic for Zero-Internet AI Assistant
// Communicates with backend APIs
// Simulates peer-to-peer sync by copy/paste

const API_BASE = "";

const responseBox = document.getElementById("response");
const questionInput = document.getElementById("question");
const syncTextarea = document.getElementById("syncData");

async function askQuestion() {
    const question = questionInput.value.trim();
    if (!question) return;

    responseBox.textContent = "Thinking…";

    try {
        const res = await fetch(`${API_BASE}/ask`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ question })
        });

        const data = await res.json();

        responseBox.innerHTML = `
            <strong>Answer:</strong> ${data.answer}<br>
            <small>
                source: ${data.source} |
                confidence: ${data.confidence} |
                intent: ${data.intent}
            </small>
        `;
    } catch (err) {
        responseBox.textContent = "Backend not reachable (offline demo mode).";
    }
}

async function exportKnowledge() {
    responseBox.textContent = "Exporting knowledge…";

    try {
        const res = await fetch(`${API_BASE}/sync/export`);
        const data = await res.json();

        syncTextarea.value = JSON.stringify(data, null, 2);
        responseBox.textContent = "Knowledge exported. Copy & paste to another device.";
    } catch {
        responseBox.textContent = "Cannot export knowledge.";
    }
}

async function importKnowledge() {
    if (!syncTextarea.value.trim()) {
        responseBox.textContent = "Paste knowledge packets first.";
        return;
    }

    try {
        const payload = JSON.parse(syncTextarea.value);

        const res = await fetch(`${API_BASE}/sync/import`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        const data = await res.json();

        responseBox.textContent =
            `Sync complete. Merged: ${data.merged}, Skipped: ${data.skipped}`;
    } catch {
        responseBox.textContent = "Invalid sync data.";
    }
}
