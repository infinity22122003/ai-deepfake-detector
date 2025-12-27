const form = document.getElementById('uploadForm');
const fileInput = document.getElementById('fileInput');
const resultEl = document.getElementById('result');
const scoreEl = document.getElementById('score');
const labelEl = document.getElementById('label');
const detailsEl = document.getElementById('details');
const frameScoresEl = document.getElementById('frameScores');
const errorEl = document.getElementById('error');
const submitBtn = document.getElementById('submitBtn');

form.addEventListener('submit', async (e) => {
  e.preventDefault();
  errorEl.hidden = true;
  resultEl.hidden = true;
  detailsEl.style.display = 'none';
  frameScoresEl.textContent = '';

  const file = fileInput.files[0];
  if (!file) return;

  submitBtn.disabled = true;
  submitBtn.textContent = 'Analyzing...';

  try {
    const fd = new FormData();
    fd.append('file', file, file.name);
    const resp = await fetch('/predict', { method: 'POST', body: fd });
    if (!resp.ok) {
      const err = await resp.json().catch(()=>({detail: 'Unknown error'}));
      throw new Error(err.detail || 'Server error');
    }
    const data = await resp.json();
    scoreEl.textContent = `Score: ${data.score.toFixed(4)} (0 = real, 1 = fake)`;
    labelEl.textContent = `Label: ${data.label}`;
    if (Array.isArray(data.frame_scores) && data.frame_scores.length > 1) {
      detailsEl.style.display = 'block';
      frameScoresEl.textContent = JSON.stringify(data.frame_scores, null, 2);
    }
    resultEl.hidden = false;
  } catch (err) {
    errorEl.hidden = false;
    errorEl.textContent = `Error: ${err.message}`;
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = 'Analyze';
  }
});
