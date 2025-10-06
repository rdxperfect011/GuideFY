const form = document.getElementById('career-form');
const resultSection = document.getElementById('result');
const recText = document.getElementById('rec-text');

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

  recText.textContent = 'Thinking...';
  resultSection.classList.remove('hidden');

  try {
    const res = await fetch('/career', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    if(data.error){
      recText.textContent = 'Error: ' + data.error;
    } else {
      recText.textContent = JSON.stringify(data.recommendation, null, 2);
    }
  } catch(err){
    recText.textContent = 'Request failed: ' + err.message;
  }
});