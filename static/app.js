const form = document.getElementById('career-form');
const resultSection = document.getElementById('result');
const recText = document.getElementById('rec-text');

// Display recommendation neatly
function displayRecommendation(data) {
  recText.innerHTML = '';

  if (!data || !data.careers || !data.courses || !data.next_steps) {
    recText.textContent = 'Sorry, recommendation format is invalid.';
    return;
  }

  const careersHtml = data.careers.map(c => `
    <li><strong>${c.name}</strong>: ${c.justification}</li>
  `).join('');

  const coursesHtml = data.courses.map(c => `
    <li><strong>${c.name}</strong>: ${c.description}</li>
  `).join('');

  const stepsHtml = data.next_steps.map(s => `
    <li><strong>${s.action}</strong>: ${s.details}</li>
  `).join('');

  recText.innerHTML = `
    <h3>🚀 Recommended Careers</h3>
    <ul>${careersHtml}</ul>
    <h3>📚 Suggested Courses</h3>
    <ul>${coursesHtml}</ul>
    <h3>👣 Your Next Steps</h3>
    <ul>${stepsHtml}</ul>
  `;
}

// Form submit
form.addEventListener('submit', async (e) => {
  e.preventDefault();
  const payload = {
    name: document.getElementById('name').value.trim(),
    email: document.getElementById('email').value.trim(),
    interests: document.getElementById('interests').value.trim(),
    strengths: document.getElementById('strengths').value.trim(),
    preferred_subjects: document.getElementById('preferred_subjects').value.trim(),
    career_goal: document.getElementById('career_goal').value.trim(),
  };

  recText.innerHTML = '<p>Thinking...</p>';
  resultSection.classList.remove('hidden');

  try {
    const res = await fetch('/career', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!res.ok) throw new Error(`Server responded with status: ${res.status}`);

    const data = await res.json();
    if (data.error) recText.textContent = 'Error: ' + data.error;
    else displayRecommendation(data.recommendation);

  } catch (err) {
    recText.textContent = 'Request failed: ' + err.message;
  }
});