// Toggle artefact item functionality
function toggleArtefactItem() {
    var type = document.getElementById('type').value;
    var group = document.getElementById('artefact-item-group');
    group.style.display = (type === 'artefact') ? 'block' : 'none';
}

// Toggle between existing and new item
function toggleArtefactOption() {
    var existing = document.getElementById('existing-item-select');
    var createNew = document.getElementById('new-item-type-select');
    var selected = document.querySelector('input[name="artefact_option"]:checked').value;
    if (selected === 'existing') {
        existing.style.display = 'block';
        createNew.style.display = 'none';
    } else {
        existing.style.display = 'none';
        createNew.style.display = 'block';
    }
}

// Set initial display on page load
window.addEventListener('DOMContentLoaded', function() {
    toggleArtefactItem();
    // Toggle between existing and new item
    var radios = document.querySelectorAll('input[name="artefact_option"]');
    radios.forEach(function(radio) {
        radio.addEventListener('change', toggleArtefactOption);
    });
    toggleArtefactOption();
});

// jQuery functionality for Select2 and additional toggles
$(document).ready(function() {
    // Show/hide artefact item group based on type
    function toggleArtefactItem() {
        if ($('#type').val() === 'artefact') {
            $('#artefact-item-group').show();
        } else {
            $('#artefact-item-group').hide();
        }
    }
    $('#type').on('change', toggleArtefactItem);
    toggleArtefactItem();

    // Show/hide selects based on radio
    function toggleArtefactOption() {
        if ($('input[name="artefact_option"]:checked').val() === 'existing') {
            $('#existing-item-select').show();
            $('#new-item-type-select').hide();
        } else {
            $('#existing-item-select').hide();
            $('#new-item-type-select').show();
        }
    }
    $('input[name="artefact_option"]').on('change', toggleArtefactOption);
    toggleArtefactOption();

    // Restore Select2
    $('#item_id').select2({
        theme: 'bootstrap-5',
        width: '100%',
        placeholder: 'Select an item',
        allowClear: true
    });
    $('#item_type_id').select2({
        theme: 'bootstrap-5',
        width: '100%',
        placeholder: 'Select an item type',
        allowClear: true
    });
}); 