function implantSlotKey(value) {
    return (value || '').toString().trim().toLowerCase();
}

function takenImplantSlots($select) {
    const taken = {};
    const preset = $select.data('occupiedSlots') || {};
    Object.keys(preset).forEach(function(slot) {
        taken[implantSlotKey(slot)] = String(preset[slot]);
    });
    ($select.val() || []).forEach(function(id) {
        const option = $select.find('option').filter(function() {
            return this.value === String(id);
        })[0];
        if (!option) {
            return;
        }
        const slot = implantSlotKey($(option).data('slot'));
        if (slot) {
            taken[slot] = String(id);
        }
    });
    return taken;
}

function showImplantSlotWarning($select, message) {
    const holder = $select.closest('.form-group, .card-body').find('.implant-slot-warning').first();
    if (!holder.length) {
        return;
    }
    if (message) {
        holder.text(message).removeClass('d-none');
    } else {
        holder.text('').addClass('d-none');
    }
}

function refreshImplantSlotOptions($select) {
    const taken = takenImplantSlots($select);
    const selected = new Set(($select.val() || []).map(String));
    $select.find('option').each(function() {
        const slot = implantSlotKey($(this).data('slot'));
        const blocked = Boolean(
            slot && taken[slot] && taken[slot] !== this.value && !selected.has(this.value)
        );
        this.disabled = blocked;
    });
}

function bindImplantSlotSelect($select) {
    refreshImplantSlotOptions($select);
    $select.on('select2:opening', function() {
        refreshImplantSlotOptions($select);
    });
    $select.on('select2:selecting', function(e) {
        const option = e.params.args.data.element;
        const slot = implantSlotKey(option ? $(option).data('slot') : '');
        const taken = takenImplantSlots($select);
        const id = String(e.params.args.data.id);
        if (slot && taken[slot] && taken[slot] !== id) {
            e.preventDefault();
            const label = option ? ($(option).data('slot') || slot) : slot;
            showImplantSlotWarning($select, 'The ' + label + ' slot is already in use.');
        }
    });
    $select.on('change', function() {
        refreshImplantSlotOptions($select);
        showImplantSlotWarning($select, '');
    });
}

$(document).ready(function() {
    $('.select2-cybernetics').each(function() {
        bindImplantSlotSelect($(this));
    });
});
