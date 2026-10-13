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
            $(this).find('.ability-starting-choices input[name^="ability_choice_type"]').attr('name', 'ability_choice_type_' + i + '[]');
            $(this).find('.ability-starting-choices input[name^="ability_choice_count"]').attr('name', 'ability_choice_count_' + i + '[]');
            $(this).find('.ability-skill-pairs select[name^="ability_pair_trigger"]').attr('name', 'ability_pair_trigger_' + i + '[]');
            $(this).find('.ability-skill-pairs select[name^="ability_pair_granted"]').attr('name', 'ability_pair_granted_' + i + '[]');
            $(this).find('.ability-rank-caps select[name^="ability_rank_cap_skill"]').attr('name', 'ability_rank_cap_skill_' + i + '[]');
            $(this).find('.ability-rank-caps input[name^="ability_rank_cap_limit"]').attr('name', 'ability_rank_cap_limit_' + i + '[]');
            $(this).find('.ability-skill-bans select').attr('name', 'ability_banned_skills_' + i + '[]');
            $(this).find('.ability-condition-timing input').attr('name', 'ability_condition_progress_rate_' + i);
            $(this).find('.ability-tags select').attr('name', 'ability_tags_' + i + '[]');
            $(this).find('.ability-sheet-values input[name^="ability_sheet_id"]').attr('name', 'ability_sheet_id_' + i + '[]');
            $(this).find('.ability-sheet-values input[name^="ability_sheet_description"]').attr('name', 'ability_sheet_description_' + i + '[]');
            $(this).find('.ability-sheet-values input[name^="ability_sheet_value"]').attr('name', 'ability_sheet_value_' + i + '[]');
            $(this).find('[name^="ability_additional_group_income"]').attr('name', 'ability_additional_group_income_' + i);
            $(this).find('.ability-skill-discounts select.select2-multiple').attr('name', 'ability_discount_skills_' + i + '[]');
            $(this).find('.ability-skill-discounts input[type=number]').attr('name', 'ability_discount_value_' + i);
            $(this).find('.ability-starting-item select').attr('name', 'ability_starting_item_blueprint_' + i);
            $(this).find('.ability-starting-reputation select').attr('name', 'ability_starting_reputation_faction_' + i);
            $(this).find('.ability-starting-reputation input[type=number]').attr('name', 'ability_starting_reputation_value_' + i);
            $(this).find('.ability-starting-condition select').attr('name', 'ability_starting_condition_' + i);
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
        placeholder: 'Select an option...',
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
        block.find('.ability-starting-item select').prop('required', false);
        block.find('.ability-starting-reputation select').prop('required', false);
        block.find('.ability-starting-reputation input[type=number]').prop('required', false);
        block.find('.ability-starting-condition select').prop('required', false);
        if ($(this).val() === 'starting_skills') {
            block.find('.ability-starting-skills').show();
        } else if ($(this).val() === 'starting_skill_choices') {
            block.find('.ability-starting-choices').show();
        } else if ($(this).val() === 'first_skill_pair') {
            block.find('.ability-skill-pairs').show();
        } else if ($(this).val() === 'skill_rank_caps') {
            block.find('.ability-rank-caps').show();
        } else if ($(this).val() === 'skill_bans') {
            block.find('.ability-skill-bans').show();
        } else if ($(this).val() === 'condition_timing') {
            block.find('.ability-condition-timing').show();
        } else if ($(this).val() === 'group_income') {
            block.find('.ability-group-income').show();
        } else if ($(this).val() === 'skill_discounts') {
            block.find('.ability-skill-discounts').show();
            // Only add required if visible
            block.find('.ability-skill-discounts input[type=number]').prop('required', true);
        } else if ($(this).val() === 'starting_item') {
            block.find('.ability-starting-item').show();
            // Only add required if visible
            block.find('.ability-starting-item select').prop('required', true);
        } else if ($(this).val() === 'starting_reputation') {
            block.find('.ability-starting-reputation').show();
            // Only add required if visible
            block.find('.ability-starting-reputation select').prop('required', true);
            block.find('.ability-starting-reputation input[type=number]').prop('required', true);
        } else if ($(this).val() === 'starting_condition') {
            block.find('.ability-starting-condition').show();
            block.find('.ability-starting-condition select').prop('required', true);
        }
    });

    // After attaching the change handler, trigger change on all ability-type-selects to set required attributes correctly
    $('.ability-type-select').trigger('change');

    function skillPairRow() {
        var options = window.SKILL_OPTIONS_HTML || '';
        return $(`
            <div class="row mb-2 skill-pair-row">
                <div class="col-md-5">
                    <select class="form-control" name="ability_pair_trigger_0[]" title="Skill they buy">
                        <option value="">Skill they buy</option>
                        ${options}
                    </select>
                </div>
                <div class="col-md-5">
                    <select class="form-control" name="ability_pair_granted_0[]" title="Skill they receive">
                        <option value="">Skill they receive</option>
                        ${options}
                    </select>
                </div>
                <div class="col-md-2">
                    <button type="button" class="btn btn-danger btn-sm remove-skill-pair" aria-label="Remove pair">Remove</button>
                </div>
            </div>
        `);
    }

    $(document).on('click', '.add-skill-pair', function() {
        $(this).closest('.ability-skill-pairs').find('.skill-pair-rows').append(skillPairRow());
        reindexAbilities();
    });

    $(document).on('click', '.remove-skill-pair', function() {
        $(this).closest('.skill-pair-row').remove();
        reindexAbilities();
    });

    function rankCapRow() {
        var options = window.SKILL_OPTIONS_HTML || '';
        return $(`
            <div class="row mb-2 rank-cap-row">
                <div class="col-md-6">
                    <select class="form-control" name="ability_rank_cap_skill_0[]" title="Skill">
                        <option value="">Skill</option>
                        ${options}
                    </select>
                </div>
                <div class="col-md-3">
                    <input type="number" class="form-control" name="ability_rank_cap_limit_0[]" min="1" placeholder="Maximum ranks" title="Maximum ranks">
                </div>
                <div class="col-md-2">
                    <button type="button" class="btn btn-danger btn-sm remove-rank-cap" aria-label="Remove rank cap">Remove</button>
                </div>
            </div>
        `);
    }

    $(document).on('click', '.add-rank-cap', function() {
        $(this).closest('.ability-rank-caps').find('.rank-cap-rows').append(rankCapRow());
        reindexAbilities();
    });

    $(document).on('click', '.remove-rank-cap', function() {
        $(this).closest('.rank-cap-row').remove();
        reindexAbilities();
    });

    function sheetValueRow() {
        return $(`
            <div class="row mb-2 sheet-value-row">
                <div class="col-md-3">
                    <input class="form-control" name="ability_sheet_id_0[]" placeholder="ID, such as psi" title="ID">
                </div>
                <div class="col-md-5">
                    <input class="form-control" name="ability_sheet_description_0[]" placeholder="Description, such as Psi Points" title="Description">
                </div>
                <div class="col-md-2">
                    <input type="number" class="form-control" name="ability_sheet_value_0[]" placeholder="Value" title="Value">
                </div>
                <div class="col-md-2">
                    <button type="button" class="btn btn-danger btn-sm remove-sheet-value" aria-label="Remove sheet value">Remove</button>
                </div>
            </div>
        `);
    }

    $(document).on('click', '.add-sheet-value', function() {
        $(this).closest('.ability-sheet-values').find('.sheet-value-rows').append(sheetValueRow());
        reindexAbilities();
    });

    $(document).on('click', '.remove-sheet-value', function() {
        $(this).closest('.sheet-value-row').remove();
        reindexAbilities();
    });

    // Add/remove ability blocks
    $('#add-ability').click(function() {
        var idx = $('#abilities-list .ability-block').length;
        var skillsOptions = window.SKILL_OPTIONS_HTML || '';
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
            </div>
            <div class="form-group mb-2 ability-extra ability-starting-skills" style="display:none;">
                <label>Starting Skills</label>
                <select class="form-control select2-multiple" name="ability_starting_skills_${idx}[]" multiple>
                    ${skillsOptions}
                </select>
            </div>
            <div class="form-group mb-2 ability-extra ability-starting-choices" style="display:none;">
                <label>Starting skill choices</label>
                <div class="row mb-2">
                    <div class="col-md-6">
                        <input class="form-control" name="ability_choice_type_${idx}[]" placeholder="Skill type, such as standard_program">
                    </div>
                    <div class="col-md-3">
                        <input type="number" class="form-control" name="ability_choice_count_${idx}[]" placeholder="How many" min="1">
                    </div>
                </div>
                <div class="row mb-2">
                    <div class="col-md-6">
                        <input class="form-control" name="ability_choice_type_${idx}[]" placeholder="Skill type, such as advanced_program">
                    </div>
                    <div class="col-md-3">
                        <input type="number" class="form-control" name="ability_choice_count_${idx}[]" placeholder="How many" min="1">
                    </div>
                </div>
            </div>
            <div class="form-group mb-2 ability-extra ability-group-income" style="display:none;">
                <label>Additional Group Income (EC)</label>
                <input type="number" class="form-control" name="ability_additional_group_income_${idx}" value="0" min="0" placeholder="0">
            </div>
            <div class="form-group mb-2 ability-extra ability-skill-pairs" style="display:none;">
                <label>First skill from this group grants its pair</label>
                <div class="skill-pair-rows"></div>
                <button type="button" class="btn btn-secondary btn-sm add-skill-pair">Add pair</button>
            </div>
            <div class="form-group mb-2 ability-extra ability-rank-caps" style="display:none;">
                <label>Maximum ranks for this species</label>
                <div class="rank-cap-rows"></div>
                <button type="button" class="btn btn-secondary btn-sm add-rank-cap">Add cap</button>
            </div>
            <div class="form-group mb-2 ability-extra ability-skill-bans" style="display:none;">
                <label>Banned skills</label>
                <select class="form-control select2-multiple" name="ability_banned_skills_${idx}[]" multiple>
                    ${skillsOptions}
                </select>
            </div>
            <div class="form-group mb-2 ability-extra ability-condition-timing" style="display:none;">
                <label>Events consumed per event</label>
                <input type="number" class="form-control" name="ability_condition_progress_rate_${idx}" min="0.01" step="any" placeholder="1">
                <small class="form-text text-muted">2 finishes a stage in half the stated time. 4 is a quarter of the time. 0.5 makes it last twice as long. This applies to conditions that share a tag.</small>
            </div>
            <div class="form-group mb-2 ability-tags">
                <label>Tags</label>
                <select class="form-control rule-tag-select" name="ability_tags_${idx}[]" multiple title="Select or add tags"></select>
                <small class="form-text text-muted">Search for a tag, or type a new one. Saving stores a new tag so later searches can find it.</small>
            </div>
            <div class="form-group mb-2 ability-sheet-values">
                <label>Character sheet values</label>
                <div class="sheet-value-rows"></div>
                <button type="button" class="btn btn-secondary btn-sm add-sheet-value">Add sheet value</button>
                <small class="form-text text-muted">Added to skill values with the same ID on the character sheet. Psionic Potential and rank 6 path skills use psi.</small>
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
            <div class="form-group mb-2 ability-extra ability-starting-item" style="display:none;">
                <label>Starting Item Blueprint</label>
                <select class="form-control" name="ability_starting_item_blueprint_${idx}">
                    <option value="">Select Item Blueprint</option>
                </select>
            </div>
            <div class="form-group mb-2 ability-extra ability-starting-reputation" style="display:none;">
                <label>Starting Reputation - Faction</label>
                <select class="form-control" name="ability_starting_reputation_faction_${idx}">
                    <option value="">Select Faction</option>
                </select>
            </div>
            <div class="form-group mb-2 ability-extra ability-starting-reputation" style="display:none;">
                <label>Starting Reputation - Value</label>
                <input type="number" class="form-control" name="ability_starting_reputation_value_${idx}" placeholder="0">
            </div>
            <div class="form-group mb-2 ability-extra ability-starting-condition" style="display:none;">
                <label>Starting condition</label>
                <select class="form-control" name="ability_starting_condition_${idx}">${window.CONDITION_OPTIONS_HTML || ''}</select>
                <small class="form-text text-muted">Players choose the starting stage when they create the character. The lowest choice is stage 1.</small>
            </div>
            <div class="form-group mb-2">
                <label>Description *</label>
                <textarea class="form-control" name="ability_description_${idx}" required></textarea>
                <div class="col-md-4 mb-2">
                    <button type="button" class="btn btn-danger remove-ability">Remove</button>
                </div>
            </div>
        </div>
        `);
        // Replace placeholder with actual options from a global variable
        block.find('select.ability-type-select').html(window.ABILITY_TYPE_OPTIONS_HTML || '');

        // Populate item blueprint options
        var itemBlueprintSelect = block.find('select[name^="ability_starting_item_blueprint"]');
        if (window.ITEM_BLUEPRINTS) {
            itemBlueprintSelect.append('<option value="">Select Item Blueprint</option>');
            window.ITEM_BLUEPRINTS.forEach(function(blueprint) {
                itemBlueprintSelect.append('<option value="' + blueprint.id + '">' + blueprint.name + ' (' + blueprint.item_type_name + ')</option>');
            });
        }

        // Populate faction options for reputation dropdown
        var reputationFactionSelect = block.find('select[name^="ability_starting_reputation_faction"]');
        if (window.FACTIONS) {
            reputationFactionSelect.append('<option value="">Select Faction</option>');
            window.FACTIONS.forEach(function(faction) {
                reputationFactionSelect.append('<option value="' + faction.id + '">' + faction.name + '</option>');
            });
        }

        $('#abilities-list').append(block);
        block.find('.select2-multiple').select2({
            theme: 'bootstrap-5',
            width: '100%',
            placeholder: 'Select skills...',
            allowClear: true
        });
        // Initialize Select2 for the new item blueprint select
        block.find('select[name^="ability_starting_item_blueprint"]').addClass('select2-single').select2({
            theme: 'bootstrap-5',
            width: '100%',
            placeholder: 'Select Item Blueprint...',
            allowClear: true
        });
        // Initialize Select2 for the new reputation faction select
        block.find('select[name^="ability_starting_reputation_faction"]').addClass('select2-single').select2({
            theme: 'bootstrap-5',
            width: '100%',
            placeholder: 'Select Faction...',
            allowClear: true
        });
        // Remove 'required' from all Select2 fields in the new block
        block.find('.select2-multiple, .select2-single').removeAttr('required');
        reindexAbilities();
        initRuleTagSelects(block);
    });

    $(document).on('click', '.remove-ability', function() {
        $(this).closest('.ability-block').remove();
        reindexAbilities();
    });

    // Initial reindex in case of server-rendered abilities
    reindexAbilities();
    initRuleTagSelects();

    function toggleExtraHitsPerToughness() {
        var show = $('#body_hits_type').val() === 'global';
        $('#extra-hits-per-toughness-group').toggle(show);
    }
    $('#body_hits_type').on('change', toggleExtraHitsPerToughness);
    toggleExtraHitsPerToughness();

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
