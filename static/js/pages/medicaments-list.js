document.addEventListener('DOMContentLoaded', function() {
    // Handle print button clicks
    document.querySelectorAll('.print-medicament-btn').forEach(function(button) {
        button.addEventListener('click', function() {
            const medicamentId = this.dataset.medicamentId;

            // Call the print endpoint
            fetch(`/templates/medicaments/${medicamentId}/print`)
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
