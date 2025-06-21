document.getElementById('layoutForm').addEventListener('submit', function(e) {
    e.preventDefault();
    
    const formData = {
        is_landscape: document.getElementById('is_landscape').checked,
        has_back_side: document.getElementById('has_back_side').checked,
        width_mm: parseFloat(document.getElementById('width_mm').value),
        height_mm: parseFloat(document.getElementById('height_mm').value),
        items_per_row: parseInt(document.getElementById('items_per_row').value),
        items_per_column: parseInt(document.getElementById('items_per_column').value),
        margin_top_mm: parseFloat(document.getElementById('margin_top_mm').value),
        margin_bottom_mm: parseFloat(document.getElementById('margin_bottom_mm').value),
        margin_left_mm: parseFloat(document.getElementById('margin_left_mm').value),
        margin_right_mm: parseFloat(document.getElementById('margin_right_mm').value),
        gap_horizontal_mm: parseFloat(document.getElementById('gap_horizontal_mm').value),
        gap_vertical_mm: parseFloat(document.getElementById('gap_vertical_mm').value)
    };

    fetch(window.location.pathname, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            throw new Error(data.error);
        }
        window.location.href = "/templates/list";
    })
    .catch(error => {
        console.error('Error saving layout settings:', error);
        alert('Error saving layout settings: ' + error.message);
    });
});

// Print preview functionality
document.querySelector('.preview-btn').addEventListener('click', function() {
    const templateId = this.dataset.templateId;
    const formData = {
        is_landscape: document.getElementById('is_landscape').checked,
        has_back_side: document.getElementById('has_back_side').checked,
        width_mm: parseFloat(document.getElementById('width_mm').value),
        height_mm: parseFloat(document.getElementById('height_mm').value),
        items_per_row: parseInt(document.getElementById('items_per_row').value),
        items_per_column: parseInt(document.getElementById('items_per_column').value),
        margin_top_mm: parseFloat(document.getElementById('margin_top_mm').value),
        margin_bottom_mm: parseFloat(document.getElementById('margin_bottom_mm').value),
        margin_left_mm: parseFloat(document.getElementById('margin_left_mm').value),
        margin_right_mm: parseFloat(document.getElementById('margin_right_mm').value),
        gap_horizontal_mm: parseFloat(document.getElementById('gap_horizontal_mm').value),
        gap_vertical_mm: parseFloat(document.getElementById('gap_vertical_mm').value)
    };

    fetch(`/templates/api/${templateId}/print_preview`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            throw new Error(data.error);
        }
        // Open PDF in new window
        const pdfData = data.pdf;
        const blob = new Blob([Uint8Array.from(atob(pdfData), c => c.charCodeAt(0))], { type: 'application/pdf' });
        const url = URL.createObjectURL(blob);
        window.open(url, '_blank');
    })
    .catch(error => {
        console.error('Error generating print preview:', error);
        alert('Error generating print preview: ' + error.message);
    });
}); 