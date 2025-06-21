window.addEventListener('DOMContentLoaded', function() {
    var initialSlug = '';
    try {
        initialSlug = document.getElementById('wiki_page').value;
    } catch (e) {}
    initWikiPageAutocomplete({
        inputId: 'wiki_page_autocomplete',
        hiddenInputId: 'wiki_page',
        suggestionsId: 'wiki-page-suggestions',
        apiUrl: '/wiki/_internal_pages',
        initialSlug: initialSlug
    });
});

$(document).ready(function() {
    function reindexAbilities() {
        $('#abilities-list .ability-block').each(function(i) {
            $(this).find('[name^="ability_name"]').attr('name', 'ability_name_' + i);
            $(this).find('[name^="ability_type"]').attr('name', 'ability_type_' + i);
            $(this).find('[name^="ability_description"]').attr('name', 'ability_description_' + i);
            $(this).find('.ability-starting-skills select').attr('name', 'ability_starting_skills_' + i + '[]');
            $(this).find('.ability-skill-discounts select.select2-multiple').attr('name', 'ability_discount_skills_' + i + '[]');
            $(this).find('.ability-skill-discounts input[type=number]').attr('name', 'ability_discount_value_' + i);
        });
    }

    // Initialize Select2 for all multiple select elements
    $('.select2-multiple').each(function() {
        let config = {
            theme: 'bootstrap-5',
            width: '100%',
            allowClear: true
        };

        // Add specific configuration based on the select element
        if ($(this).attr('id') === 'keywords') {
            config.tags = true;
            config.tokenSeparators = [',', ' '];
            config.placeholder = 'Enter keywords...';
            config.createTag = function(params) {
                var term = $.trim(params.term);
                if (term === '') {
                    return null;
                }
                return {
                    id: term,
                    text: term,
                    newTag: true
                };
            };
        } else if ($(this).attr('id') === 'permitted_factions') {
            config.placeholder = 'Select factions...';
        } else {
            config.placeholder = 'Select items...';
        }

        $(this).select2(config);
    });

    $('.select2-single').select2({
        theme: 'bootstrap-5',
        width: '100%',
        placeholder: 'Select a skill...',
        allowClear: true
    });

    // Remove 'required' from all Select2 fields on page load
    $('.select2-multiple, .select2-single').removeAttr('required');

    // Populate all ability-type-select dropdowns on page load
    $('.ability-type-select').each(function() {
        var selected = $(this).data('selected');
        $(this).html(window.ABILITY_TYPE_OPTIONS_HTML || '');
        if (selected !== undefined) {
            $(this).val(selected.toString());
        }
    });

    // Ability type change handler
    $(document).on('change', '.ability-type-select', function() {
        var block = $(this).closest('.ability-block');
        block.find('.ability-extra').hide();
        // Remove required from all discount value inputs in this block
        block.find('.ability-skill-discounts input[type=number]').prop('required', false);
        if ($(this).val() === 'starting_skills') {
            block.find('.ability-starting-skills').show();
        } else if ($(this).val() === 'skill_discounts') {
            block.find('.ability-skill-discounts').show();
            // Only add required if visible
            block.find('.ability-skill-discounts input[type=number]').prop('required', true);
        }
    });

    // After attaching the change handler, trigger change on all ability-type-selects to set required attributes correctly
    $('.ability-type-select').trigger('change');

    // Add/remove ability blocks
    $('#add-ability').click(function() {
        var idx = $('#abilities-list .ability-block').length;
        var skillsOptions = $('#abilities-list .ability-block:first .ability-starting-skills select').html() || '';
        var block = $(
        `<div class="ability-block card mb-3 p-3">
            <div class="form-row mb-2">
                <div class="col-md-4 mb-2">
                    <label>Name *</label>
                    <input type="text" class="form-control" name="ability_name_${idx}" required>
                </div>
                <div class="col-md-4 mb-2">
                    <label>Type *</label>
                    <select class="form-control ability-type-select" name="ability_type_${idx}" required>
                        ABILITY_TYPE_OPTIONS_PLACEHOLDER
                    </select>
                </div>
                <div class="col-md-4 mb-2">
                    <button type="button" class="btn btn-danger remove-ability">Remove</button>
                </div>
            </div>
            <div class="form-group mb-2">
                <label>Description *</label>
                <textarea class="form-control" name="ability_description_${idx}" required></textarea>
            </div>
            <div class="form-group mb-2 ability-extra ability-starting-skills" style="display:none;">
                <label>Starting Skills</label>
                <select class="form-control select2-multiple" name="ability_starting_skills_${idx}[]" multiple>
                    ${skillsOptions}
                </select>
            </div>
            <div class="form-group mb-2 ability-extra ability-skill-discounts" style="display:none;">
                <label>Skill Discounts</label>
                <div class="mb-2">
                    <label>Discounted Skills</label>
                    <select class="form-control select2-multiple" name="ability_discount_skills_${idx}[]" multiple>
                        ${skillsOptions}
                    </select>
                </div>
                <div class="mb-2">
                    <label>Discount Value</label>
                    <input type="number" class="form-control" name="ability_discount_value_${idx}" placeholder="Discount">
                </div>
            </div>
        </div>
        `);
        // Replace placeholder with actual options from a global variable
        block.find('select.ability-type-select').html(window.ABILITY_TYPE_OPTIONS_HTML || '');
        $('#abilities-list').append(block);
        block.find('.select2-multiple').select2({
            theme: 'bootstrap-5',
            width: '100%',
            placeholder: 'Select skills...',
            allowClear: true
        });
        // Remove 'required' from all Select2 fields in the new block
        block.find('.select2-multiple, .select2-single').removeAttr('required');
        reindexAbilities();
    });

    $(document).on('click', '.remove-ability', function() {
        $(this).closest('.ability-block').remove();
        reindexAbilities();
    });

    // Initial reindex in case of server-rendered abilities
    reindexAbilities();

    $('form.settings-form').on('submit', function(e) {
        let valid = true;
        // Check permitted factions
        if ($('#permitted_factions').length && (!$('#permitted_factions').val() || $('#permitted_factions').val().length === 0)) {
            valid = false;
            alert('Please select at least one permitted faction.');
            $('#permitted_factions').select2('open');
        }
        // Check all visible ability discount value inputs
        $('.ability-skill-discounts:visible input[type=number]').each(function() {
            if (!$(this).val()) {
                valid = false;
                alert('Please enter a discount value for all visible skill discounts.');
                $(this).focus();
                return false;
            }
        });
        if (!valid) e.preventDefault();
    });
});
