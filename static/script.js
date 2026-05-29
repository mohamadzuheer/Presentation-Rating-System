const rubricWeights = {
  problem_clarity: 25,
  market_potential: 20,
  uniqueness_insight: 20,
  feasibility: 15,
  pitch_delivery: 10,
  work_interest: 10
};

function updateRubricScore() {
  let completed = 0;
  let weightedTotal = 0;

  Object.entries(rubricWeights).forEach(([field, weight]) => {
    const selected = document.querySelector(`input[name="${field}"]:checked`);
    if (selected) {
      completed += 1;
      weightedTotal += Number(selected.value) * weight;
    }
  });

  const scoreEl = document.getElementById('weightedScore');
  const submitBtn = document.getElementById('submitBtn');

  if (scoreEl) {
    scoreEl.textContent = completed === Object.keys(rubricWeights).length
      ? (weightedTotal / 100 * 5).toFixed(2)
      : '--';
  }

  if (submitBtn) {
    submitBtn.disabled = completed !== Object.keys(rubricWeights).length;
  }
}

document.addEventListener('DOMContentLoaded', function() {
  document.querySelectorAll('.rubric-score input').forEach(input => {
    input.addEventListener('change', updateRubricScore);
  });

  const form = document.getElementById('ratingForm');
  if (form) {
    form.addEventListener('submit', function(e) {
      const allScored = Object.keys(rubricWeights).every(field => {
        return document.querySelector(`input[name="${field}"]:checked`);
      });

      if (!allScored) {
        e.preventDefault();
        alert('Please score every rubric criterion before submitting.');
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
