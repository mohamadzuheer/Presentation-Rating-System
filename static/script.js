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

  Object.keys(rubricWeights).forEach(field => {
    const selected = document.querySelector(`input[name="${field}"]:checked`);
    if (selected) {
      completed += 1;
    }
  });

  const submitBtn = document.getElementById('submitBtn');

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
