const form = document.getElementById("career-form");
const result = document.getElementById("result");
const recText = document.getElementById("rec-text");
const statusBox = document.getElementById("status");

// UTILITY FUNCTIONS
/**
 * Cleans text coming from backend or AI
 * Prevents undefined / extra spaces from breaking UI
 */
function cleanText(text) {
  if (!text || text === "undefined") return "Not available";
  return text.replace(/\s+/g, " ").trim();
}
// AI STATUS INDICATOR
/**
 * Fetches AI health status from backend
 * Updates indicator color and text
 */
async function updateStatus() {
  try {
    const res = await fetch("/api-status");
    const status = await res.json();

    if (status.model_responded && status.model_parsed) {
      statusBox.innerHTML = "🟢 AI System: Online";
    } 
    else if (status.model_responded && !status.model_parsed) {
      statusBox.innerHTML = "🟡 AI System: Online (Fallback Active)";
    } 
    else if (status.api_key_loaded) {
      statusBox.innerHTML = "🟡 AI System: Ready";
    } 
    else {
      statusBox.innerHTML = "🔴 AI System: API Key Missing";
    }
  } catch (error) {
    statusBox.innerHTML = "🔴 AI System: Offline";
  }
}

// Run once when page loads
document.addEventListener("DOMContentLoaded", updateStatus);

// UPSKILL SECTION RENDERING
/**
 * Renders upskill content (videos + platforms)
 * Always safe due to backend fallback
 */
function renderUpskill(u) {
  if (!u) return "";

  const videosHTML = (u.videos || []).map(v => `
    <div class="video-box">
      <a href="${v.url}" target="_blank" rel="noopener">
        <img src="${v.thumbnail}" class="upskill-thumb" />
      </a>
      <p><strong>🎥 ${cleanText(v.platform)}</strong></p>
      <p class="video-desc">${cleanText(v.explanation)}</p>
    </div>
  `).join("");

  const platformsHTML = (u.platforms || []).map(p => `
    <li>
      <a href="${p.url}" target="_blank" rel="noopener">
        <strong>${cleanText(p.name)}</strong>
      </a>
      <div class="platform-info">
        ⭐ Avg Rating: 4.4 / 5 • Certificate: ${cleanText(p.certificate || "Available")}<br>
        🧠 <strong>Best for:</strong> ${cleanText(p.best_for || "Skill development")}<br>
        ⏱ <strong>Duration:</strong> ${cleanText(p.duration || "Self-paced")}<br>
        📚 <strong>Learning Type:</strong> ${cleanText(p.learning_type || "Online learning")}<br>
        📄 ${cleanText(p.details || "Professional online learning platform")}
      </div>
    </li>
  `).join("");

  return `
    <div class="upskill-card">
      <h4>🔥 ${cleanText(u.title)}</h4>
      <p>${cleanText(u.description)}</p>

      <div class="video-grid">
        ${videosHTML || "<p>No videos available</p>"}
      </div>

      <div class="upskill-platforms">
        <strong>🌐 Online Learning Platforms</strong>
        <ul>
          ${platformsHTML || "<li>No platforms available</li>"}
        </ul>
      </div>
    </div>
  `;
}
// MAIN RESULT RENDER
/**
 * Renders full recommendation output
 */
function showRecommendation(data) {
  updateStatus(); // refresh AI indicator after response

  const score = Math.round(data?.confidence_score?.overall || 0);

  recText.innerHTML = `
    <h3>🚀 Careers</h3>
    <ul>
      ${(data.careers || []).map(c =>
        `<li><strong>${cleanText(c.name)}</strong>: ${cleanText(c.justification)}</li>`
      ).join("")}
    </ul>

    <h3>📚 Courses</h3>
    <ul>
      ${(data.courses || []).map(c =>
        `<li><strong>${cleanText(c.name)}</strong>: ${cleanText(c.description)}</li>`
      ).join("")}
    </ul>

    <h3>👣 Next Steps</h3>
    <ul>
      ${(data.next_steps || []).map(n =>
        `<li><strong>${cleanText(n.action)}</strong>: ${cleanText(n.details)}</li>`
      ).join("")}
    </ul>

    <h3>📊 Career Confidence Score</h3>
    <p>
      <strong>${score}%</strong> — 
      ${cleanText(data?.confidence_score?.explanation)}
    </p>

    <h3>🔥 Upskill (Recommended Learning)</h3>
    ${renderUpskill(data.upskill)}
  `;
}

// FORM SUBMISSION HANDLER
form.addEventListener("submit", async (e) => {
  e.preventDefault();

  // Show loading state
  statusBox.innerHTML = "🟡 AI System: Processing...";
  recText.innerHTML = "⏳ Generating recommendations...";
  result.classList.remove("hidden");

  const payload = {
    interests: interests.value,
    strengths: strengths.value,
    preferred_subjects: preferred_subjects.value,
    career_goal: career_goal.value
  };

  try {
    const res = await fetch("/career", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    const json = await res.json();
    showRecommendation(json.recommendation);

  } catch (error) {
    recText.innerHTML = "❌ Failed to load recommendations.";
    statusBox.innerHTML = "🔴 AI System: Offline";
  }
});
