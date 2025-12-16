const form = document.getElementById("career-form");
const result = document.getElementById("result");
const recText = document.getElementById("rec-text");
const statusBox = document.getElementById("status");

/* =========================
   UTIL
========================= */
function cleanText(t) {
  return t ? t.replace(/\s+/g, " ").trim() : "";
}

/* =========================
   AI STATUS
========================= */
document.addEventListener("DOMContentLoaded", updateStatus);

async function updateStatus() {
  try {
    const res = await fetch("/api-status");
    const s = await res.json();

    if (s.model_responded && s.model_parsed) {
      statusBox.innerHTML = "🟢 AI System: Online";
    } else if (s.model_responded) {
      statusBox.innerHTML = "🟡 AI System: Online (Fallback Active)";
    } else {
      statusBox.innerHTML = "🔴 AI System: Ready";
    }
  } catch {
    statusBox.innerHTML = "🔴 AI System: Offline";
  }
}

/* =========================
   UPSKILL (VERTICAL LAYOUT)
========================= */
function renderUpskill(u) {
  return `
    <div class="upskill-card upskill-vertical">

      <a href="${u.video.url}" target="_blank">
        <img src="${u.video.thumbnail}" class="upskill-thumb" />
      </a>

      <div class="upskill-content">
        <h4>${u.title}</h4>

        <p class="upskill-meta">
          🎥 <strong>Video Platform:</strong> ${u.video.platform}<br>
          ▶️ <a href="${u.video.url}" target="_blank">Watch full video</a>
        </p>

        <p class="upskill-desc">
          ${cleanText(u.description)}
        </p>

        <div class="upskill-platforms">
          <strong>🌐 Online Learning Platforms:</strong>
          <ul>
            ${u.platforms.map(p => `
              <li>
                <a href="${p[1]}" target="_blank"><strong>${p[0]}</strong></a>
                <span class="platform-info">
                  ✓ Structured learning paths<br>
                  ✓ Quizzes & assignments<br>
                  ✓ Certificates (platform dependent)<br>
                  ⭐ Avg Rating: 4.4 / 5
                </span>
              </li>
            `).join("")}
          </ul>
        </div>
      </div>
    </div>
  `;
}

/* =========================
   MAIN RENDER
========================= */
function showRecommendation(data) {
  updateStatus();

  const score = Math.round(data.confidence_score?.overall || 0);

  recText.innerHTML = `
    <h3>🚀 Careers</h3>
    <ul>${data.careers.map(c =>
      `<li><strong>${c.name}</strong>: ${cleanText(c.justification)}</li>`
    ).join("")}</ul>

    <h3>📚 Courses</h3>
    <ul>${data.courses.map(c =>
      `<li><strong>${c.name}</strong>: ${cleanText(c.description)}</li>`
    ).join("")}</ul>

    <h3>👣 Next Steps</h3>
    <ul>${data.next_steps.map(n =>
      `<li><strong>${n.action}</strong>: ${cleanText(n.details)}</li>`
    ).join("")}</ul>

    <h3>📊 Career Confidence Score</h3>
    <p><strong>${score}%</strong> — ${cleanText(data.confidence_score.explanation)}</p>

    <h3>🔥 Upskill (Recommended Learning)</h3>
    ${renderUpskill(data.upskill)}
  `;
}

/* =========================
   FORM SUBMIT
========================= */
form.addEventListener("submit", async (e) => {
  e.preventDefault();

  const payload = {
    interests: interests.value,
    strengths: strengths.value,
    preferred_subjects: preferred_subjects.value,
    career_goal: career_goal.value
  };

  recText.innerHTML = "⏳ Generating recommendations...";
  result.classList.remove("hidden");

  const res = await fetch("/career", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });

  const json = await res.json();
  showRecommendation(json.recommendation);
});
