const bankBalance = getNumeric($('#downtime-form').data('bank-balance'));
const groupBankBalance = getNumeric($('#downtime-form').data('group-bank-balance'));

const steps = ['purchase', 'modifications', 'engineering', 'science', 'research', 'reputation'];
let currentStep = 0;
let stepErrors = {'purchase': false, 'modifications': false, 'engineering': false, 'science': false, 'research': false, 'reputation': false};
let visitedSteps = {'purchase': false, 'modifications': false, 'engineering': false, 'science': false, 'research': false, 'reputation': false};
let dirtySteps = {'purchase': false, 'modifications': false, 'engineering': false, 'science': false, 'research': false, 'reputation': false};

// Helper: set .is-invalid on select and its Select2 container
function setSelect2Invalid($select, isInvalid) {
    $select.toggleClass('is-invalid', isInvalid);
    // Find the Select2 container and its selection box
    let $container = $select.next('.select2-container');
    if (!$container.length) {
        $container = $select.parent().find('.select2-container');
    }
    $container.toggleClass('is-invalid', isInvalid);
    $container.find('.select2-selection').toggleClass('is-invalid', isInvalid);
}

// Helper: get numeric value from string or input
function getNumeric(val) {
    if (typeof val === 'string') return parseFloat(val.replace(/[^\d.\-]/g, '')) || 0;
    return Number(val) || 0;
}

// Helper function to get JSON data from hidden inputs
function getJsonData(elementId) {
    const element = document.getElementById(elementId);
    if (!element) {
        console.error(`Element with id ${elementId} not found`);
        return null;
    }
    try {
        return JSON.parse(element.value);
    } catch (e) {
        console.error(`Error parsing JSON from ${elementId}:`, e);
        return null;
    }
}

function validate() { 
    stepErrors['engineering'] = !validateEngineeringStep();
    stepErrors['science'] = !validateScienceStep();
}

// Sums up all chit costs from purchases and engineering actions and updates the display
window.updateTotalChitCost = function() {
    let total = 0;

    // --- Purchases ---
    // Each purchase row should have .purchase-row and a .purchase-cost input or display
    $('#purchase-blueprints-list .purchase-row').each(function() {
        let cost = 0;
        // Try to get cost from an input or data attribute
        const $costInput = $(this).find('#blueprint-cost-value');
        if ($costInput.length) {
            cost = parseInt($costInput.val(), 10) || 0;
        } else if ($(this).data('cost') !== undefined) {
            cost = parseInt($(this).data('cost'), 10) || 0;
        }
        total += cost;
    });

    // --- Engineering ---
    // For each engineering slot, if action is maintain or modify, add its cost
    $('.eng-slot-card').each(function() {
        const $card = $(this);
        const action = $card.find('.eng-action-select').val();
        if (action === 'maintain') {
            // Get cost from .eng-maintain-cost span
            const cost = parseInt($card.find('.eng-maintain-cost').text(), 10) || 0;
            total += cost;
        } else if (action === 'modify') {
            // Get cost from .eng-modify-cost span (if present)
            const cost = parseInt($card.find('.eng-modify-cost').text(), 10) || 0;
            total += cost;
        }
    });

    // Update the display
    $('#total-chit-cost').text(total > 0 ? `Total Cost: ${total} ec` : '');
};

// Call on page load
$(document).ready(function() {
    updateTotalChitCost();

    // Purchases: update on change
    $('#purchase-blueprints-list').on('input change', '.purchase-cost', updateTotalChitCost);
    $('#purchase-blueprints-list').on('change', '.purchase-row', updateTotalChitCost);

    // Engineering: update on action or cost change
    $('.eng-action-select').on('change', updateTotalChitCost);
    $('.eng-slot-card').on('input change', '.eng-maintain-cost, .eng-mod-cost', updateTotalChitCost);
});