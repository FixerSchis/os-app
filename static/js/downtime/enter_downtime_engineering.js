 $('.eng-item-own-select, .eng-item-group-select').select2({
    width: '100%',
    placeholder: 'Select an item',
    allowClear: true,
    theme: 'bootstrap4'
});
$('.eng-mod-select').select2({
    width: '100%',
    placeholder: 'Select a modification',
    allowClear: true,
    theme: 'bootstrap4'
});

// Show/hide maintain/modify rows based on action
$('.eng-action-select').on('change', function() {
    var slot = $(this).data('slot');
    var action = $(this).val();
    var $card = $(this).closest('.eng-slot-card');
    $card.find('.eng-maintain-row').toggle(action === 'maintain');
    $card.find('.eng-modify-row').toggle(action === 'modify');
    dirtyStep('engineering');
    updateEngCost(slot);
});

// Toggle item source
$('.btn-toggle-group .btn').on('click', function() {
    var $btn = $(this);
    var slot = $btn.data('slot');
    var source = $btn.data('toggle-source');
    $btn.siblings().removeClass('active');
    $btn.addClass('active');
    $('.eng-item-row[data-slot="' + slot + '"]').hide();
    $('.eng-item-row[data-slot="' + slot + '"][data-source="' + source + '"]').show();
    dirtyStep('engineering');
    updateEngCost(slot);
});

// Listen for changes on all item selects/inputs and mod select
$(document).on('change', '.eng-item-own-select, .eng-item-group-select, .eng-mod-select', function() {
    var slot = $(this).data('slot');
    dirtyStep('engineering');
    updateEngCost(slot);
});

// Debounce for manual item code lookup
var manualItemTimers = {};
$(document).on('input', '.eng-item-manual', function() {
    var $input = $(this);
    var slot = $input.data('slot');
    clearTimeout(manualItemTimers[slot]);
    manualItemTimers[slot] = setTimeout(function() {
        checkManualItem($input, slot);
    }, 400);
    dirtyStep('engineering');
});

$(document).on('blur', '.eng-item-manual', function() {
    var $input = $(this);
    var slot = $input.data('slot');
    checkManualItem($input, slot);
});

function checkManualItem($input, slot) {
    var code = $input.val().trim();
    var $status = $('.manual-item-status[data-slot="' + slot + '"]');
    var $hiddenId = $('.manual-item-id[data-slot="' + slot + '"]');
    if (!code) {
        $status.html('').css('color', '');
        $hiddenId.val('');
        updateEngCost(slot);
        return;
    }
    $.ajax({
        url: '/db/items/find_by_code',
        method: 'GET',
        data: { full_code: code, requires_pack: true },
        success: function(resp) {
            $status.html('<span style="color:green;font-weight:bold;">&#10003;</span> ' + (resp.name || resp.full_code));
            $hiddenId.val(resp.id);
            updateEngCost(slot);
        },
        error: function() {
            $status.html('<span style="color:red;font-weight:bold;">&#10007;</span>');
            $hiddenId.val('');
            updateEngCost(slot);
        }
    });
}

function updateEngCost(slot) {
    var $card = $('.eng-slot-card').eq(slot);
    var action = $card.find('.eng-action-select').val();
    if (!action) {
        $card.find('.eng-maintain-cost, .eng-modify-cost').text('');
        updateStepperBar();
        return;
    }
    // Determine item source
    var source = $card.find('.btn-toggle-group .btn.active').data('toggle-source');
    var item_id = null;
    var blueprint_id = null;
    var unique_val = null;
    if (source === 'own') {
        var val = $card.find('.eng-item-own-select').val();
        if (val && val.startsWith('purchased-')) {
            // Value format: purchased-<blueprint_id>-<n>
            var parts = val.split('-');
            blueprint_id = parts[1];
            unique_val = val;
        } else {
            item_id = val;
            unique_val = val;
        }
    } else if (source === 'group') {
        item_id = $card.find('.eng-item-group-select').val();
        unique_val = item_id;
    } else if (source === 'manual') {
        item_id = $card.find('.manual-item-id[data-slot="' + slot + '"]').val();
        unique_val = item_id;
        if (!item_id) {
            $card.find('.eng-maintain-cost, .eng-modify-cost').text('Enter a valid item ID');
            updateStepperBar();
            return;
        }
    }
    if (!item_id && !blueprint_id) {
        $card.find('.eng-maintain-cost, .eng-modify-cost').text('');
        updateStepperBar();
        return;
    }
    // Count how many times this item/blueprint instance has been selected for modification in previous slots
    var mods = 0;
    for (var i = 0; i < slot; i++) {
        var prevCard = $('.eng-slot-card').eq(i);
        var prevAction = prevCard.find('.eng-action-select').val();
        var prevSource = prevCard.find('.btn-toggle-group .btn.active').data('toggle-source');
        var prevVal = null;
        if (prevSource === 'own') {
            prevVal = prevCard.find('.eng-item-own-select').val();
        } else if (prevSource === 'group') {
            prevVal = prevCard.find('.eng-item-group-select').val();
        } else if (prevSource === 'manual') {
            prevVal = prevCard.find('.manual-item-id[data-slot="' + i + '"]').val();
        }
        if (prevAction === 'modify' && prevVal && prevVal === unique_val) {
            mods++;
        }
    }
    var postData = {
        action: action,
        mods: mods
    };
    if (item_id) postData.item_id = item_id;
    if (blueprint_id) postData.blueprint_id = blueprint_id;
    $.ajax({
        url: '/db/items/engineering_cost',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify(postData),
        success: function(resp) {
            if (action === 'maintain') {
                $card.find('.eng-maintain-cost').text(resp.cost + ' ec');
            } else if (action === 'modify') {
                $card.find('.eng-modify-cost').text(resp.cost + ' ec');
            }
            updateStepperBar();
            afterEngCostUpdate();
        },
        error: function(xhr) {
            var msg = 'Error';
            if (xhr.responseJSON && xhr.responseJSON.error) {
                msg = xhr.responseJSON.error;
            }
            if (action === 'maintain') {
                $card.find('.eng-maintain-cost').text(msg);
            } else if (action === 'modify') {
                $card.find('.eng-modify-cost').text(msg);
            }
            updateStepperBar();
            afterEngCostUpdate();
        }
    });
}

function validateEngineeringStep() {
    let valid = true;
    let error = '';
    // For each engineering slot
    $('.eng-slot-card').each(function() {
        const $card = $(this);
        const action = $card.find('.eng-action-select').val();
        // Reset validation
        $card.find('.eng-action-select, .eng-item-manual, .eng-mod-select').removeClass('is-invalid');
        setSelect2Invalid($card.find('.eng-item-own-select'), false);
        setSelect2Invalid($card.find('.eng-item-group-select'), false);
        setSelect2Invalid($card.find('.eng-mod-select'), false);
        $card.find('.eng-maintain-cost, .eng-modify-cost').css('color', '');
        if (action === 'maintain' || action === 'modify') {
            // Determine item source
            const source = $card.find('.btn-toggle-group .btn.active').data('toggle-source');
            let itemSelected = false;
            if (source === 'own') {
                itemSelected = !!$card.find('.eng-item-own-select').val();
                setSelect2Invalid($card.find('.eng-item-own-select'), !itemSelected);
            } else if (source === 'group') {
                itemSelected = !!$card.find('.eng-item-group-select').val();
                setSelect2Invalid($card.find('.eng-item-group-select'), !itemSelected);
            } else if (source === 'manual') {
                itemSelected = !!$card.find('.manual-item-id').val();
                $card.find('.eng-item-manual').toggleClass('is-invalid', !itemSelected);
            }
            if (!itemSelected) {
                valid = false;
                error = 'Select an item for each engineering action.';
            }
            // If modification, require mod selection
            if (action === 'modify') {
                const modSelected = !!$card.find('.eng-mod-select').val();
                setSelect2Invalid($card.find('.eng-mod-select'), !modSelected);
                if (!modSelected) {
                    valid = false;
                    error = 'Select a modification for each modification action.';
                }
            }
            // Check cost
            let cost = 0;
            if (action === 'maintain') {
                cost = getNumeric($card.find('.eng-maintain-cost').text());
                if (cost > bankBalance + groupBankBalance) {
                    $card.find('.eng-maintain-cost').css('color', 'red');
                    valid = false;
                    error = 'Insufficient funds for maintenance.';
                }
            } else if (action === 'modify') {
                cost = getNumeric($card.find('.eng-modify-cost').text());
                if (cost > bankBalance + groupBankBalance) {
                    $card.find('.eng-modify-cost').css('color', 'red');
                    valid = false;
                    error = 'Insufficient funds for modification.';
                }
            }
        }
    });
    return valid;
}

// Call updateTotalChitCost after engineering cost is calculated
function afterEngCostUpdate() {
    window.updateTotalChitCost();
}

$('#downtime-form').on('submit', function() {
    // Remove previous engineering[] hidden inputs
    $('input[name="engineering[]"]').remove();

    // For each engineering slot
    $('.eng-slot-card').each(function(slot) {
        const $card = $(this);
        const action = $card.find('.eng-action-select').val();
        // Determine item source and value
        const source = $card.find('.btn-toggle-group .btn.active').data('toggle-source');
        let item_id = null, blueprint_id = null, mod_id = null, full_code = null;
        if (source === 'own') {
            const val = $card.find('.eng-item-own-select').val();
            if (val && val.startsWith('purchased-')) {
                blueprint_id = val.split('-')[1];
            } else {
                item_id = val;
            }
        } else if (source === 'group') {
            item_id = $card.find('.eng-item-group-select').val();
        } else if (source === 'manual') {
            item_id = $card.find('.manual-item-id[data-slot="' + slot + '"]').val();
            full_code = $card.find('.eng-item-manual[data-slot="' + slot + '"]').val();
        }
        if (action === 'modify') {
            mod_id = $card.find('.eng-mod-select').val();
        }
        // Build the object
        const engObj = {
            action: action,
            source: source,
            item_id: item_id,
            blueprint_id: blueprint_id,
            mod_id: mod_id
        };
        if (source === 'manual') {
            engObj.full_code = full_code;
        }
        // Only add if action is set
        if (action) {
            const jsonValue = JSON.stringify(engObj);
            const htmlSafeValue = jsonValue.replace(/"/g, '&quot;');
            $('#downtime-form').append(`<input type="hidden" name="engineering[]" value="${htmlSafeValue}">`);
        }
        // Disable original fields
        $card.find('select, input').prop('disabled', true);
    });
});

$(document).ready(function() {
    // Ensure correct show/hide of maintain/modify fields on load
    $('.eng-action-select').each(function() {
        $(this).trigger('change');
    });
});
