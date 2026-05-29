// Rating button selection logic
function selectRating(value) {
  // Update hidden input
  document.getElementById('ratingScore').value = value;

  // Highlight selected button
  document.querySelectorAll('.rating-btn').forEach(btn => {
    btn.classList.toggle('selected', parseInt(btn.dataset.value) === value);
  });

  // Update display text
  const textEl = document.getElementById('ratingSelectedText');
  textEl.textContent = `You selected: ${value} / 10`;
  textEl.classList.add('chosen');

  // Enable submit button
  const submitBtn = document.getElementById('submitBtn');
  if (submitBtn) submitBtn.disabled = false;
}

// Prevent double submission
document.addEventListener('DOMContentLoaded', function() {
  const form = document.getElementById('ratingForm');
  if (form) {
    form.addEventListener('submit', function(e) {
      const score = document.getElementById('ratingScore').value;
      if (!score) {
        e.preventDefault();
        alert('Please select a rating before submitting.');
        return;
      }
      const btn = document.getElementById('submitBtn');
      if (btn) {
        btn.disabled = true;
        btn.textContent = 'Submitting...';
      }
    });
  }
});
