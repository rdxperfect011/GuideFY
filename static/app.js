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
    <div class="video-card">
      <a href="${v.url}" target="_blank" rel="noopener">
        <img src="${v.thumbnail}" class="video-thumbnail" alt="Video thumbnail" />
      </a>
      <div class="video-info">
        <span class="video-platform">${cleanText(v.platform)}</span>
        <p class="video-explanation">${cleanText(v.explanation)}</p>
      </div>
    </div>
  `).join("");

  const platformsHTML = (u.platforms || []).map(p => `
    <div class="course-item">
      <h4>
        <a href="${p.url}" target="_blank" rel="noopener">
          ${cleanText(p.name)}
        </a>
      </h4>
      <p>
        ⭐ Avg Rating: 4.4 / 5 • Certificate: ${cleanText(p.certificate || "Available")}<br>
        🧠 <strong>Best for:</strong> ${cleanText(p.best_for || "Skill development")}<br>
        ⏱ <strong>Duration:</strong> ${cleanText(p.duration || "Self-paced")}<br>
        📚 <strong>Learning Type:</strong> ${cleanText(p.learning_type || "Online learning")}<br>
        📄 ${cleanText(p.details || "Professional online learning platform")}
      </p>
    </div>
  `).join("");

  return `
    <div class="upskill-section">
      <div class="upskill-header">
        <h3 class="upskill-title">${cleanText(u.title)}</h3>
        <p class="upskill-description">${cleanText(u.description)}</p>
      </div>

      ${videosHTML ? `<div class="video-grid">${videosHTML}</div>` : ""}

      ${platformsHTML ? `
        <div class="course-list">
          <h4>🌐 Online Learning Platforms</h4>
          ${platformsHTML}
        </div>
      ` : ""}
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

  // Careers section with career-grid
  const careersHTML = (data.careers || []).map(c => `
    <div class="career-card">
      <h4>${cleanText(c.name)}</h4>
      <p>${cleanText(c.justification)}</p>
    </div>
  `).join("");

  // Courses section with course-list
  const coursesHTML = (data.courses || []).map(c => `
    <div class="course-item">
      <h4>${cleanText(c.name)}</h4>
      <p>${cleanText(c.description)}</p>
    </div>
  `).join("");

  // Next steps with steps-list
  const stepsHTML = (data.next_steps || []).map((n, index) => `
    <div class="step-item">
      <div class="step-number">${index + 1}</div>
      <div class="step-content">
        <h4>${cleanText(n.action)}</h4>
        <p>${cleanText(n.details)}</p>
      </div>
    </div>
  `).join("");

  recText.innerHTML = `
    <div class="results-section">
      <div class="glass-card">
        <h3>🚀 Recommended Careers</h3>
        <div class="career-grid">
          ${careersHTML || "<p>No career recommendations available</p>"}
        </div>
      </div>

      <div class="glass-card">
        <h3>📚 Recommended Courses</h3>
        <div class="course-list">
          ${coursesHTML || "<p>No course recommendations available</p>"}
        </div>
      </div>

      <div class="glass-card">
        <h3>👣 Next Steps</h3>
        <div class="steps-list">
          ${stepsHTML || "<p>No steps available</p>"}
        </div>
      </div>

      <div class="glass-card score-card">
        <h3>📊 Career Confidence Score</h3>
        <div class="score-value">${score}%</div>
        <p class="score-explanation">${cleanText(data?.confidence_score?.explanation)}</p>
      </div>

      <div class="glass-card">
        <h3>🔥 Upskill (Recommended Learning)</h3>
        ${renderUpskill(data.upskill)}
      </div>
    </div>
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
