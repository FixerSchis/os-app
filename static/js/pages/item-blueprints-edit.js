document.addEventListener('DOMContentLoaded', function() {
    function getModsData() {
        var el = document.getElementById('item-blueprint-mods-data');
        if (!el) return [];
        try {
            return JSON.parse(el.value);
        } catch (e) {
            return [];
        }
    }
    function initModSelect(select) {
        $(select).select2({
            theme: 'bootstrap-5',
            width: '100%',
            placeholder: 'Select mod...'
        });
    }
    // Initialize all current mod selects
    document.querySelectorAll('.mod-select').forEach(initModSelect);

    // Remove mod button
    function updateRemoveButtons() {
        var rows = document.querySelectorAll('.mod-row');
        rows.forEach(function(row, idx) {
            var btn = row.querySelector('.remove-mod');
            btn.style.display = '';
            btn.onclick = function() { row.remove(); updateRemoveButtons(); };
        });
    }
    updateRemoveButtons();

    // Add mod button
    document.getElementById('add-mod').addEventListener('click', function() {
        var mods = getModsData();
        var row = document.createElement('div');
        row.className = 'input-group d-flex align-items-center mb-2 mod-row';
        var select = document.createElement('select');
        select.className = 'form-select mod-select flex-grow-1';
        select.name = 'mods_applied[]';
        var option = document.createElement('option');
        option.value = '';
        option.disabled = true;
        option.selected = true;
        option.textContent = 'Select mod...';
        select.appendChild(option);
        mods.forEach(function(mod) {
            var opt = document.createElement('option');
            opt.value = mod.id;
            opt.textContent = mod.name;
            select.appendChild(opt);
        });
        var removeBtn = document.createElement('button');
        removeBtn.type = 'button';
        removeBtn.className = 'btn btn-outline-danger remove-mod flex-shrink-0';
        removeBtn.tabIndex = -1;
        removeBtn.innerHTML = '&times;';
        removeBtn.style.marginLeft = '0.5rem';
        removeBtn.addEventListener('click', function() {
            row.remove();
            updateRemoveButtons();
        });
        row.appendChild(select);
        row.appendChild(removeBtn);
        document.getElementById('mods-applied-list').appendChild(row);
        initModSelect(select);
        updateRemoveButtons();
    });
});
