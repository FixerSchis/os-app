let purchaseRows = [];
const blueprints = JSON.parse($('#blueprints-data').val());

// Load existing purchases from the pack data
function loadExistingPurchases() {
    const packPurchases = $('#downtime-form').data('pack-purchases');
    if (packPurchases && Array.isArray(packPurchases)) {
        purchaseRows = packPurchases.map(purchase => ({
            blueprint_id: String(purchase.blueprint_id) // Convert to string for consistent comparison
        }));
    }
}

$('#add-blueprint-row').on('click', function() {
    purchaseRows.push({blueprint_id: ''});
    renderPurchaseRows();
    dirtyStep('purchase');
});

$('#purchase-blueprints-list').on('change', '.blueprint-select', function() {
    const idx = $(this).data('idx');
    purchaseRows[idx].blueprint_id = $(this).val();
    renderPurchaseRows();
    dirtyStep('purchase');
});

$('#purchase-blueprints-list').on('click', '.remove-blueprint-row', function() {
    const idx = $(this).data('idx');
    purchaseRows.splice(idx, 1);
    renderPurchaseRows();
    dirtyStep('purchase');
});

// Initialize with one row if the list exists
if ($('#purchase-blueprints-list').length) {
    loadExistingPurchases();
    if (purchaseRows.length === 0) {
        purchaseRows = [{blueprint_id: ''}];
    }
    renderPurchaseRows();
}

function renderPurchaseRows() {
    const $list = $('#purchase-blueprints-list');
    $list.empty();

    // Remove any existing purchase hidden inputs
    $('input[name="purchases[]"]').remove();

    purchaseRows.forEach((row, idx) => {
        const blueprintOptions = blueprints.map(bp => `<option value="${bp.id}" ${String(row.blueprint_id) === String(bp.id) ? 'selected' : ''}>${bp.name} (${bp.base_cost} ec)</option>`).join('');
        $list.append(`
            <div class="row align-items-center mb-2 purchase-row" data-idx="${idx}">
                <div class="col-10">
                    <select class="form-control blueprint-select" data-idx="${idx}">
                        <option value="">Select Blueprint</option>
                        ${blueprintOptions}
                    </select>
                </div>
                <div class="col-1">
                    <span class="blueprint-cost" data-idx="${idx}"></span>
                    <input type='hidden' id='blueprint-cost-value' data-idx="${idx}">
                </div>
                <div class="col-1">
                    <button type="button" class="btn btn-danger btn-sm remove-blueprint-row" data-idx="${idx}">&times;</button>
                </div>
            </div>
        `);

        // Add hidden input for form submission if a blueprint is selected
        if (row.blueprint_id) {
            const bp = blueprints.find(b => String(b.id) === String(row.blueprint_id));
            if (bp) {
                const jsonValue = JSON.stringify({
                    blueprint_id: bp.id,
                    name: bp.name,
                    cost: bp.base_cost
                });
                // Escape double quotes for HTML attribute
                const htmlSafeValue = jsonValue.replace(/"/g, '&quot;');
                $('#downtime-form').append(`<input type="hidden" name="purchases[]" value="${htmlSafeValue}">`);
            }
        }
    });

    // Initialize Select2 for all blueprint selects
    $('.blueprint-select').select2({
        width: '100%',
        placeholder: 'Select Blueprint',
        allowClear: true,
        theme: 'bootstrap4'
    });
    updatePurchaseCosts();
    syncPurchasedBlueprintsToPack();
    window.updateTotalChitCost();
}

function updatePurchaseCosts() {
    let total = 0;
    let valid = true;
    let errorMsg = '';
    const bankBalance = parseInt($('#downtime-form').data('bank-balance')) || 0;
    const groupBankBalance = parseInt($('#downtime-form').data('group-bank-balance')) || 0;
    const availableFunds = bankBalance + groupBankBalance;
    purchaseRows.forEach((row, idx) => {
        const bp = blueprints.find(b => String(b.id) === String(row.blueprint_id));
        const cost = bp ? bp.base_cost : 0;
        $(`.blueprint-cost[data-idx="${idx}"]`).text(bp ? cost + ' ec' : '');
        $(`#blueprint-cost-value[data-idx="${idx}"]`).val(bp ? cost : 0);
        if (!bp) valid = false;
        if (cost > availableFunds) {
            valid = false;
            $(`.blueprint-cost[data-idx="${idx}"]`).css('color', 'red');
        } else {
            $(`.blueprint-cost[data-idx="${idx}"]`).css('color', '');
        }
        total += cost;
    });
    $('#purchase-total-cost').text(total + ' ec');
    if (total > availableFunds) {
        valid = false;
        $('#purchase-total-cost').css('color', 'red');
    } else {
        $('#purchase-total-cost').css('color', '');
    }
    // Show error if any row is invalid or total exceeds funds
    if (!valid && errorMsg) {
        $('#purchase-error').text(errorMsg).show();
    } else {
        $('#purchase-error').hide();
    }
    window.updateTotalChitCost();
}

function syncPurchasedBlueprintsToPack() {
    // Count how many of each blueprint are purchased
    const purchasedCounts = {};
    purchaseRows.forEach(row => {
        if (row.blueprint_id) {
            purchasedCounts[row.blueprint_id] = (purchasedCounts[row.blueprint_id] || 0) + 1;
        }
    });
    // For each engineering slot's own select
    $('.eng-item-own-select').each(function() {
        const $select = $(this);
        // Remove all options with data-purchased attribute
        $select.find('option[data-purchased]').remove();
        // Add purchased blueprints as options, one per count
        Object.entries(purchasedCounts).forEach(([id, count]) => {
            const bp = blueprints.find(bp => String(bp.id) === String(id));
            for (let i = 1; i <= count; i++) {
                const value = `purchased-${id}-${i}`;
                const text = `${bp.name} (NEW ${i})`;
                $select.append(`<option value="${value}" data-purchased="1">${text}</option>`);
            }
        });
        // Refresh Select2
        $select.trigger('change.select2');
    });
}

// Call updateTotalChitCost when a purchase item is selected or removed
$('#purchase-blueprints-list').on('change', '.purchase-item-select', function() {
    window.updateTotalChitCost();
});
$('#purchase-blueprints-list').on('click', '.remove-purchase-row', function() {
    setTimeout(window.updateTotalChitCost, 0); // after row is removed
});
