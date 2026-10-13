document.addEventListener('DOMContentLoaded', function() {
    const modeRows = document.getElementById('mode-rows');
    const addMode = document.getElementById('add-mode');
    if (!modeRows || !addMode) {
        return;
    }
    addMode.addEventListener('click', function() {
        const index = modeRows.querySelectorAll('.mode-row').length;
        const row = document.createElement('div');
        row.className = 'row mb-2 mode-row';
        row.innerHTML = `
            <div class="col-md-3">
                <label class="sr-only" for="mode_name_new_${index}">Mode</label>
                <input class="form-control" id="mode_name_new_${index}" name="mode_name[]" placeholder="Mode, such as TREAT">
            </div>
            <div class="col-md-7">
                <label class="sr-only" for="mode_effect_new_${index}">Effect</label>
                <textarea class="form-control" id="mode_effect_new_${index}" name="mode_effect[]" rows="2" placeholder="Effect of a dose in this mode"></textarea>
            </div>
            <div class="col-md-2">
                <button type="button" class="btn btn-danger btn-sm remove-mode" aria-label="Remove mode">Remove</button>
            </div>
        `;
        modeRows.appendChild(row);
        row.querySelector('input').focus();
    });
    modeRows.addEventListener('click', function(e) {
        const button = e.target.closest('.remove-mode');
        if (button) {
            button.closest('.mode-row').remove();
        }
    });
});
