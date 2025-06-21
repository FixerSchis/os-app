document.addEventListener('DOMContentLoaded', function() {
  document.querySelectorAll('.toggle-diff-btn').forEach(function(btn) {
    btn.addEventListener('click', function() {
      var target = document.getElementById(btn.getAttribute('data-target'));
      if (target.style.display === 'none') {
        target.style.display = 'block';
        btn.textContent = 'Hide Diff';
      } else {
        target.style.display = 'none';
        btn.textContent = 'Show Diff';
      }
    });
  });
}); 