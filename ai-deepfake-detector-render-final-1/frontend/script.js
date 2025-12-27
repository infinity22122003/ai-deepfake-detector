document.getElementById('checkBtn').addEventListener('click', upload);

async function upload() {
  const f = document.getElementById('file');
  const resultEl = document.getElementById('result');
  resultEl.textContent = '';

  if (!f.files.length) {
    resultEl.textContent = 'Please select an image file.';
    return;
  }

  const file = f.files[0];
  const fd = new FormData();
  fd.append('file', file);

  try {
    const res = await fetch('/detect-image', {
      method: 'POST',
      body: fd,
    });

    if (!res.ok) {
      const err = await res.json().catch(()=>({detail: 'Unknown error'}));
      resultEl.textContent = 'Error: ' + (err.detail || res.statusText || JSON.stringify(err));
      return;
    }

    const data = await res.json();
    resultEl.innerHTML = `Result: ${data.result}\nConfidence: ${data.confidence}%\nMessage: ${data.message}`;
  } catch (e) {
    resultEl.textContent = 'Request failed: ' + e.message;
  }
}
