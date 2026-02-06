// DOM Elements
const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('file-input');
const filePreview = document.getElementById('file-preview');
const fileName = document.getElementById('file-name');
const fileSize = document.getElementById('file-size');
const removeFileBtn = document.getElementById('remove-file');
const analyzeBtn = document.getElementById('analyze-btn');
const loading = document.getElementById('loading');
const uploadSection = document.getElementById('upload-section');
const resultsSection = document.getElementById('results-section');
const analyzeAnotherBtn = document.getElementById('analyze-another');

let selectedFile = null;

// Drag and drop handlers
dropZone.addEventListener('dragover', (e) => {
  e.preventDefault();
  dropZone.classList.add('drag-over');
});

dropZone.addEventListener('dragleave', () => {
  dropZone.classList.remove('drag-over');
});

dropZone.addEventListener('drop', (e) => {
  e.preventDefault();
  dropZone.classList.remove('drag-over');

  const files = e.dataTransfer.files;
  if (files.length > 0) {
    handleFileSelect(files[0]);
  }
});

// File input handler
fileInput.addEventListener('change', (e) => {
  if (e.target.files.length > 0) {
    handleFileSelect(e.target.files[0]);
  }
});

// Handle file selection
/**
 * Validates and processes the selected file
 * @param {File} file - The file object selected by user
 */
function handleFileSelect(file) {
  // Validate file type
  const allowedTypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'application/msword'];
  if (!allowedTypes.includes(file.type)) {
    alert('Please upload a PDF or DOCX file.');
    return;
  }

  // Validate file size (10MB max)
  if (file.size > 10 * 1024 * 1024) {
    alert('File size must be less than 10MB.');
    return;
  }

  selectedFile = file;

  // Update UI
  fileName.textContent = file.name;
  fileSize.textContent = formatFileSize(file.size);

  dropZone.classList.add('hidden');
  filePreview.classList.remove('hidden');
}

// Remove file
removeFileBtn.addEventListener('click', () => {
  selectedFile = null;
  fileInput.value = '';
  dropZone.classList.remove('hidden');
  filePreview.classList.add('hidden');
});

// Analyze resume
analyzeBtn.addEventListener('click', async () => {
  if (!selectedFile) return;

  // Show loading
  filePreview.classList.add('hidden');
  loading.classList.remove('hidden');

  try {
    const formData = new FormData();
    formData.append('resume', selectedFile);

    const response = await fetch('/resume-analyze', {
      method: 'POST',
      body: formData
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || 'Failed to analyze resume');
    }

    // Hide loading and upload section
    loading.classList.add('hidden');
    uploadSection.classList.add('hidden');

    // Display results
    displayResults(data);
    resultsSection.classList.remove('hidden');

    // Scroll to results
    resultsSection.scrollIntoView({ behavior: 'smooth' });

  } catch (error) {
    console.error('Error:', error);
    alert(error.message || 'Failed to analyze resume. Please try again.');

    // Reset UI
    loading.classList.add('hidden');
    filePreview.classList.remove('hidden');
  }
});

// Analyze another resume
analyzeAnotherBtn.addEventListener('click', () => {
  selectedFile = null;
  fileInput.value = '';

  resultsSection.classList.add('hidden');
  uploadSection.classList.remove('hidden');
  dropZone.classList.remove('hidden');
  filePreview.classList.add('hidden');

  // Scroll to top
  window.scrollTo({ top: 0, behavior: 'smooth' });
});

// Display results
/**
 * Renders the analysis results into the DOM
 * @param {Object} data - The analysis data from backend
 */
function displayResults(data) {
  // ATS Score
  const atsScore = data.ats_score;
  const scoreCircle = document.getElementById('score-circle');
  const scoreNumber = document.getElementById('ats-score');
  const scoreDescription = document.getElementById('score-description');

  // Animate score
  setTimeout(() => {
    scoreNumber.textContent = atsScore;
    const circumference = 2 * Math.PI * 90;
    const offset = circumference - (atsScore / 100) * circumference;
    scoreCircle.style.strokeDashoffset = offset;
  }, 100);

  // Score description
  if (atsScore >= 80) {
    scoreDescription.textContent = 'Excellent! Your resume is highly optimized for ATS systems.';
  } else if (atsScore >= 60) {
    scoreDescription.textContent = 'Good! Your resume has solid ATS compatibility with room for improvement.';
  } else if (atsScore >= 40) {
    scoreDescription.textContent = 'Fair. Your resume needs optimization to pass through ATS filters.';
  } else {
    scoreDescription.textContent = 'Needs improvement. Your resume may struggle with ATS systems.';
  }

  // Add gradient definition for score circle
  if (!document.getElementById('scoreGradient')) {
    const svg = document.querySelector('.score-circle');
    const defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
    const gradient = document.createElementNS('http://www.w3.org/2000/svg', 'linearGradient');
    gradient.setAttribute('id', 'scoreGradient');
    gradient.setAttribute('x1', '0%');
    gradient.setAttribute('y1', '0%');
    gradient.setAttribute('x2', '100%');
    gradient.setAttribute('y2', '100%');

    const stop1 = document.createElementNS('http://www.w3.org/2000/svg', 'stop');
    stop1.setAttribute('offset', '0%');
    stop1.setAttribute('style', 'stop-color:var(--accent-purple);stop-opacity:1');

    const stop2 = document.createElementNS('http://www.w3.org/2000/svg', 'stop');
    stop2.setAttribute('offset', '100%');
    stop2.setAttribute('style', 'stop-color:var(--accent-pink);stop-opacity:1');

    gradient.appendChild(stop1);
    gradient.appendChild(stop2);
    defs.appendChild(gradient);
    svg.insertBefore(defs, svg.firstChild);
  }

  // Strengths
  const strengthsList = document.getElementById('strengths-list');
  strengthsList.innerHTML = '';
  data.analysis.strengths.forEach(strength => {
    const item = document.createElement('div');
    item.className = 'list-item';
    item.textContent = strength;
    strengthsList.appendChild(item);
  });

  // Weaknesses
  const weaknessesList = document.getElementById('weaknesses-list');
  weaknessesList.innerHTML = '';
  data.analysis.weaknesses.forEach(weakness => {
    const item = document.createElement('div');
    item.className = 'list-item weakness';
    item.textContent = weakness;
    weaknessesList.appendChild(item);
  });

  // Technical Keywords
  const technicalKeywords = document.getElementById('technical-keywords');
  technicalKeywords.innerHTML = '';
  if (data.keywords_found.technical_skills && data.keywords_found.technical_skills.length > 0) {
    data.keywords_found.technical_skills.forEach(keyword => {
      const tag = document.createElement('span');
      tag.className = 'keyword-tag';
      tag.textContent = keyword;
      technicalKeywords.appendChild(tag);
    });
  } else {
    technicalKeywords.innerHTML = '<p style="color: var(--text-tertiary);">No technical keywords found</p>';
  }

  // Missing Keywords
  const missingKeywords = document.getElementById('missing-keywords');
  missingKeywords.innerHTML = '';
  if (data.analysis.missing_keywords && data.analysis.missing_keywords.length > 0) {
    data.analysis.missing_keywords.forEach(keyword => {
      const tag = document.createElement('span');
      tag.className = 'keyword-tag missing';
      tag.textContent = keyword;
      missingKeywords.appendChild(tag);
    });
  } else {
    missingKeywords.innerHTML = '<p style="color: var(--text-tertiary);">No critical keywords missing</p>';
  }

  // Action Items
  const actionItems = document.getElementById('action-items');
  actionItems.innerHTML = '';
  data.analysis.action_items.forEach(item => {
    const actionDiv = document.createElement('div');
    actionDiv.className = 'action-item';

    const badge = document.createElement('span');
    badge.className = `priority-badge priority-${item.priority}`;
    badge.textContent = item.priority;

    const text = document.createElement('div');
    text.className = 'action-text';
    text.textContent = item.item;

    actionDiv.appendChild(badge);
    actionDiv.appendChild(text);
    actionItems.appendChild(actionDiv);
  });

  // Overall Impression
  const overallImpression = document.getElementById('overall-impression');
  overallImpression.textContent = data.analysis.overall_impression;
}

// Utility function to format file size
/**
 * Formats bytes into readable string (KB, MB)
 * @param {number} bytes - Size in bytes
 * @returns {string} Formatted string
 */
function formatFileSize(bytes) {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}
