$(document).ready(function() {
    $('.print-sample-btn').on('click', function() {
        const sampleId = $(this).data('sample-id');
        fetch(`/templates/print/sample/${sampleId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                alert(data.error);
                return;
            }
            // Open PDF in new window
            const byteCharacters = atob(data.pdf_base64);
            const byteNumbers = new Array(byteCharacters.length);
            for (let i = 0; i < byteCharacters.length; i++) {
                byteNumbers[i] = byteCharacters.charCodeAt(i);
            }
            const byteArray = new Uint8Array(byteNumbers);
            const blob = new Blob([byteArray], { type: 'application/pdf' });
            const pdfUrl = URL.createObjectURL(blob);
            const newWindow = window.open(pdfUrl, '_blank');
            newWindow.addEventListener('load', () => {
                setTimeout(() => {
                    URL.revokeObjectURL(pdfUrl);
                }, 1000);
            });
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Failed to generate PDF');
        });
    });
});
