const form = document.getElementById("career-form");
const result = document.getElementById("result");
const recText = document.getElementById("rec-text");

// Show recommendation results
function showRecommendation({ careers, courses, next_steps }) {
  if (!careers || !courses || !next_steps) {
    recText.textContent = "⚠️ Invalid response format.";
    return;
  }

  const toList = (items, key1, key2) =>
    items.map(i => `<li><strong>${i[key1]}</strong>: ${i[key2]}</li>`).join("");

  recText.innerHTML = `
    <h3>🚀 Careers</h3><ul>${toList(careers, "name", "justification")}</ul>
    <h3>📚 Courses</h3><ul>${toList(courses, "name", "description")}</ul>
    <h3>👣 Next Steps</h3><ul>${toList(next_steps, "action", "details")}</ul>
  `;
}

// Handle form submission
form.addEventListener("submit", async (e) => {
  e.preventDefault();

  const payload = ["name", "email", "interests", "strengths", "preferred_subjects", "career_goal"]
    .reduce((obj, id) => ({ ...obj, [id]: document.getElementById(id).value.trim() }), {});

  recText.innerHTML = "<p>⏳ Thinking...</p>";
  result.classList.remove("hidden");

  try {
    const res = await fetch("/career", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!res.ok) throw new Error(`Server error: ${res.status}`);

    const data = await res.json();
    data.error ? recText.textContent = `❌ ${data.error}` : showRecommendation(data.recommendation);

  } catch (err) {
    recText.textContent = `⚠️ Request failed: ${err.message}`;
  }
});
