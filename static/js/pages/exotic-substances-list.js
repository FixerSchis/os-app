document.addEventListener('DOMContentLoaded', function() {
    const printSheetButtons = document.querySelectorAll('.print-sheet-btn');

    printSheetButtons.forEach(button => {
        button.addEventListener('click', function() {
            const exoticId = this.dataset.exoticId;
            printExoticSheet(exoticId);
        });
    });
});

// Function to print a full sheet of a single exotic substance
function printExoticSheet(exoticId) {
    // Call the print endpoint for a single exotic substance
    fetch(`/templates/print/exotics-sheet`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            exotic_ids: [exoticId]
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert(data.error);
            return;
        }

        // Open PDF in new tab
        const pdfData = data.pdf_base64;
        const byteCharacters = atob(pdfData);
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
}
