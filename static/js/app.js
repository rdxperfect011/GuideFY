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
 * Helper to render styled status
 * @param {string} type - 'success', 'warning', or 'error'
 * @param {string} message - Text to display
 */
function renderStatus(type, message) {
  statusBox.innerHTML = `
        <div class="status-indicator status-${type}">
            <div class="status-dot"></div>
            <span>${message}</span>
        </div>
    `;
}

/**
 * Fetches AI health status from backend
 * Updates indicator color and text
 */
async function updateStatus() {
  try {
    const res = await fetch("/api-status");
    const status = await res.json();

    if (status.model_responded && status.model_parsed) {
      renderStatus("success", "AI System: Online");
    }
    else if (status.model_responded && !status.model_parsed) {
      renderStatus("warning", "AI System: Online (Fallback Active)");
    }
    else if (status.api_key_loaded) {
      renderStatus("warning", "AI System: Ready");
    }
    else {
      renderStatus("error", "AI System: API Key Missing");
    }
  } catch (error) {
    renderStatus("error", "AI System: Offline");
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
 * Renders full recommendation output with futuristic tech design
 */
function showRecommendation(data) {
  updateStatus(); // refresh AI indicator after response

  const score = Math.round(data?.confidence_score?.overall || 0);

  // LIGHTBULB HERO SECTION
  const heroHTML = `
    <div class="hero-lightbulb">
      <div class="lightbulb-container">
        <svg class="lightbulb-svg" viewBox="0 0 24 24">
          <path d="M9,21A1,1 0 0,0 10,22H14A1,1 0 0,0 15,21V20H9V21M12,2A7,7 0 0,0 5,9C5,11.38 6.19,13.47 8,14.74V17A1,1 0 0,0 9,18H15A1,1 0 0,0 16,17V14.74C17.81,13.47 19,11.38 19,9A7,7 0 0,0 12,2Z" />
        </svg>
      </div>
      <div class="score-display">
        <div class="score-percentage" id="animated-score">0%</div>
        <div class="score-label">Career Potential Illuminated</div>
        <p class="score-explanation">${cleanText(data?.confidence_score?.explanation)}</p>
      </div>
    </div>
  `;

  // FLOW CONNECTOR COMPONENT
  const connector = `
    <div class="flow-connector">
      <div class="connector-line">
        <div class="connector-arrow"></div>
      </div>
    </div>
  `;

  // CAREERS FLOW SECTION
  const careersHTML = (data.careers || []).map((c, i) => {
    const category = i % 3 === 0 ? 'tech' : (i % 3 === 1 ? 'business' : 'creative');
    return `
      <div class="career-card card-${category}">
        <h4>${cleanText(c.name)}</h4>
        <p>${cleanText(c.justification)}</p>
      </div>
    `;
  }).join("");

  // COURSES SECTION
  const coursesHTML = (data.courses || []).map(c => `
    <div class="course-item">
      <h4>${cleanText(c.name)}</h4>
      <p>${cleanText(c.description)}</p>
    </div>
  `).join("");

  // NEXT STEPS
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
    <div class="results-section reveal-animation cascading-reveal">
      ${heroHTML}
      
      ${connector}

      <div class="glass-card">
        <h3>🚀 Career Pathways</h3>
        <div class="career-grid">
          ${careersHTML || "<p>No career recommendations available</p>"}
        </div>
      </div>

      ${connector}

      <div class="glass-card">
        <h3>📚 Recommended Courses</h3>
        <div class="course-list">
          ${coursesHTML || "<p>No course recommendations available</p>"}
        </div>
      </div>

      ${connector}

      <div class="glass-card">
        <h3>👣 Strategy & Next Steps</h3>
        <div class="steps-list">
          ${stepsHTML || "<p>No steps available</p>"}
        </div>
      </div>

      ${connector}

      <div class="glass-card">
        <h3>🔥 Upskill (Recommended Learning)</h3>
        ${renderUpskill(data.upskill)}
      </div>
    </div>
  `;

  // ANIMATE SCORE COUNTER
  animateValue("animated-score", 0, score, 2000);
}

/**
 * Utility to animate counter values
 */
function animateValue(id, start, end, duration) {
  const obj = document.getElementById(id);
  if (!obj) return;

  const range = end - start;
  let current = start;
  const increment = end > start ? 1 : -1;
  const stepTime = Math.abs(Math.floor(duration / range));

  const timer = setInterval(() => {
    current += increment;
    obj.innerHTML = current + "%";
    if (current == end) {
      clearInterval(timer);
    }
  }, stepTime);
}

// FORM SUBMISSION HANDLER
form.addEventListener("submit", async (e) => {
  e.preventDefault();

  // Show Neural Analysis loading state
  renderStatus("warning", "AI System: Processing...");

  recText.innerHTML = `
    <div class="loading-tactical">
        <div class="neural-visual">
            <div class="neural-ring neural-ring-1"></div>
            <div class="neural-ring neural-ring-2"></div>
            <div class="neural-core"></div>
        </div>
        <div class="loading-text-cycling" id="loading-text">INITIALIZING NEURAL LINK...</div>
        <div class="progress-container">
            <div class="progress-bar-fill" id="progress-fill"></div>
        </div>
        <p class="progress-percentage" id="progress-text">AI MODEL PROCESSING</p>
    </div>
  `;
  result.classList.remove("hidden");
  result.scrollIntoView({ behavior: 'smooth' });

  // Simulate progress bar
  const progressBar = document.getElementById("progress-fill");
  const loadingText = document.getElementById("loading-text");
  const progressText = document.getElementById("progress-text");

  let progress = 0;
  const messages = [
    "DIAGNOSING CAREER TRAJECTORY...",
    "ANALYZING SKILL VECTORS...",
    "SYNTHESIZING MARKET DATA...",
    "CALCULATING SUCCESS PROBABILITY...",
    "GENERATING OPTIMAL PATHWAYS..."
  ];

  const progressInterval = setInterval(() => {
    if (progress < 90) {
      progress += Math.random() * 5;
      if (progress > 90) progress = 90;

      if (progressBar) progressBar.style.width = `${progress}%`;

      // Cycle text based on progress chunk
      if (loadingText) {
        const msgIndex = Math.floor((progress / 100) * messages.length);
        loadingText.innerText = messages[msgIndex] || messages[messages.length - 1];
      }
    }
  }, 200);

  const payload = {
    interests: document.getElementById("interests").value,
    strengths: document.getElementById("strengths").value,
    preferred_subjects: document.getElementById("preferred_subjects").value,
    career_goal: document.getElementById("career_goal").value
  };

  try {
    const res = await fetch("/career", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    const json = await res.json();

    // Complete the bar before showing results
    clearInterval(progressInterval);
    if (progressBar) progressBar.style.width = "100%";
    if (loadingText) loadingText.innerText = "COMPLETE";

    setTimeout(() => {
      showRecommendation(json.recommendation);
    }, 500); // Short delay to let user see 100%

  } catch (error) {
    clearInterval(progressInterval);
    recText.innerHTML = "❌ Failed to load recommendations.";
    renderStatus("error", "AI System: Offline");
    console.error(error);
  }
});
