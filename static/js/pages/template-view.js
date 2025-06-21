document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.template-content').forEach(function(el) {
        const cssB64 = el.getAttribute('data-css-b64');
        if (cssB64) {
            const css = atob(cssB64);
            const style = document.createElement('style');
            style.textContent = css;
            el.insertBefore(style, el.firstChild);
        }
    });
});

$(document).ready(function() {
    $('.print-btn').on('click', function() {
        const templateType = $(this).data('template-type');
        const id = $(this).data('id');
        let endpoint;
        
        if (templateType === 'character_sheet') {
            endpoint = `/templates/print/character/${id}`;
        } else if (templateType === 'item_card') {
            endpoint = `/templates/print/item/${id}`;
        } else {
            console.error('Unknown template type:', templateType);
            return;
        }
        
        fetch(endpoint, {
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