document.addEventListener('DOMContentLoaded', function() {
    // Toggle chevron direction on collapse
    document.querySelectorAll('.condition-card .card-header').forEach(function(header) {
        header.addEventListener('click', function() {
            var chevron = header.querySelector('i.fas');
            var collapseId = header.getAttribute('data-bs-target');
            var collapseEl = document.querySelector(collapseId);
            if (collapseEl.classList.contains('show')) {
                chevron.classList.remove('fa-chevron-up');
                chevron.classList.add('fa-chevron-down');
            } else {
                chevron.classList.remove('fa-chevron-down');
                chevron.classList.add('fa-chevron-up');
            }
        });
    });

    // Handle print button clicks
    document.querySelectorAll('.print-condition-btn').forEach(function(button) {
        button.addEventListener('click', function() {
            const conditionId = this.dataset.conditionId;
            
            // Call the print endpoint
            fetch(`/templates/conditions/${conditionId}/print`)
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        alert(data.error);
                        return;
                    }
                    
                    // Open PDF in new tab
                    const pdfData = data.pdf;
                    const blob = new Blob([Uint8Array.from(atob(pdfData), c => c.charCodeAt(0))], { type: 'application/pdf' });
                    const url = window.URL.createObjectURL(blob);
                    window.open(url, '_blank');
                    // Clean up the URL after a short delay to ensure it's loaded in the new tab
                    setTimeout(() => window.URL.revokeObjectURL(url), 1000);
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('An error occurred while generating the PDF.');
                });
        });
    });
}); 