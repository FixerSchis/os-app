document.addEventListener('DOMContentLoaded', function() {
    const toggleButtons = document.querySelectorAll('.toggle-description');
    toggleButtons.forEach(button => {
        button.addEventListener('click', function() {
            const skillId = this.getAttribute('data-skill-id');
            const descriptionRow = document.getElementById('description-' + skillId);
            if (descriptionRow) {
                if (descriptionRow.style.display === 'none') {
                    descriptionRow.style.display = 'table-row';
                    this.textContent = 'Hide';
                } else {
                    descriptionRow.style.display = 'none';
                    this.textContent = 'Details';
                }
            }
        });
    });
}); 