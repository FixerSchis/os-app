// Data tab on the template editor: the values previews are rendered with.

function getTemplatePreviewData() {
    const panel = document.getElementById('preview-data-panel');
    if (!panel) {
        return null;
    }
    const data = {};
    panel.querySelectorAll('[data-preview-field]').forEach(input => {
        const field = input.dataset.previewField;
        if (input.multiple) {
            data[field] = Array.from(input.selectedOptions).map(option => option.value);
        } else {
            data[field] = input.value;
        }
    });
    panel.querySelectorAll('[data-preview-list]').forEach(list => {
        data[list.dataset.previewList] = Array.from(list.querySelectorAll('.preview-row')).map(row => {
            const values = {};
            row.querySelectorAll('[data-preview-key]').forEach(input => {
                values[input.dataset.previewKey] = input.value;
            });
            return values;
        });
    });
    return data;
}

function clearTemplatePreviewData(panel) {
    panel.querySelectorAll('[data-preview-field]').forEach(input => {
        if (input.multiple) {
            Array.from(input.options).forEach(option => { option.selected = false; });
        } else {
            input.value = '';
        }
    });
    panel.querySelectorAll('[data-preview-list]').forEach(list => { list.innerHTML = ''; });
}

document.addEventListener('DOMContentLoaded', function() {
    const panel = document.getElementById('preview-data-panel');
    if (!panel) {
        return;
    }

    panel.addEventListener('click', function(event) {
        const addButton = event.target.closest('[data-preview-add]');
        if (addButton) {
            const name = addButton.dataset.previewAdd;
            const rowTemplate = panel.querySelector(`template[data-preview-row-template="${name}"]`);
            const list = panel.querySelector(`[data-preview-list="${name}"]`);
            list.appendChild(rowTemplate.content.cloneNode(true));
            const firstInput = list.lastElementChild.querySelector('select, input, textarea');
            if (firstInput) {
                firstInput.focus();
            }
            debouncedUpdatePreview();
            return;
        }

        const removeButton = event.target.closest('.preview-remove-row');
        if (removeButton) {
            removeButton.closest('.preview-row').remove();
            debouncedUpdatePreview();
            return;
        }

        if (event.target.id === 'preview-data-reset') {
            clearTemplatePreviewData(panel);
            debouncedUpdatePreview();
        }
    });

    panel.addEventListener('input', debouncedUpdatePreview);
    panel.addEventListener('change', debouncedUpdatePreview);
});
