// Minimal dashboard interactivity for Director Dashboard
// Wait for DOM to be ready

document.addEventListener('DOMContentLoaded', function () {
  // Add a simple hover effect for action cards (for touch devices, add focus effect)
  var actionCards = document.querySelectorAll('.action-card');
  actionCards.forEach(function(card) {
    card.addEventListener('mousedown', function() {
      card.classList.add('active');
    });
    card.addEventListener('mouseup', function() {
      card.classList.remove('active');
    });
    card.addEventListener('mouseleave', function() {
      card.classList.remove('active');
    });
    // Optional: add keyboard accessibility
    card.addEventListener('keydown', function(e) {
      if (e.key === 'Enter' || e.key === ' ') {
        card.classList.add('active');
      }
    });
    card.addEventListener('keyup', function(e) {
      if (e.key === 'Enter' || e.key === ' ') {
        card.classList.remove('active');
      }
    });
  });
}); 