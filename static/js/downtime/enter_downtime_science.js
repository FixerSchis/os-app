initScienceSlots();

$('.science-sample-select').select2({
    width: '100%',
    placeholder: 'Select a sample',
    allowClear: true,
    theme: 'bootstrap4'
});

$('.science-teach-project-select').select2({
    width: '100%',
    placeholder: 'Select a project',
    allowClear: true,
    theme: 'bootstrap4'
});

$('.science-teach-to-group-select').select2({
    width: '100%',
    placeholder: 'Select a group member',
    allowClear: true,
    theme: 'bootstrap4'
});

function initScienceSlots() {
    $('.science-action-select').each(function() {
        toggleScienceFields($(this));
    });
    initTeachToFields();
    
    // Validate any existing teach invention actions
    $('.science-slot-card').each(function() {
        const $card = $(this);
        const action = $card.find('.science-action-select').val();
        if (action === 'teach_invention') {
            const $idInput = $card.find('.science-teach-to-id-input');
            if ($idInput.val() && $idInput.val().includes('.')) {
                $idInput.trigger('input');
            }
        }
    });
}

// Initialize teach-to fields visibility
function initTeachToFields() {
    $('.btn-toggle-teach-to').each(function() {
        var $group = $(this);
        var teachTo = $group.find('.btn.active').data('teach-to');
        var $card = $group.closest('.science-slot-card');
        
        // First hide everything
        $card.find('.science-teach-to-group-select, .science-teach-to-id-input').hide();
        $card.find('.science-teach-to-group-select').next('.select2-container').hide();
        
        // Then show only what's needed
        if (teachTo === 'group') {
            $card.find('.science-teach-to-group-select').show();
            $card.find('.science-teach-to-group-select').next('.select2-container').show();
        } else if (teachTo === 'other') {
            $card.find('.science-teach-to-id-input').show();
        }
    });
}

// Initialize select2 for all dropdowns
$(document).ready(function() {
    $('.science-teach-project-select').select2({
        width: '100%',
        placeholder: 'Select a project',
        allowClear: true,
        theme: 'bootstrap4'
    });
    
    $('.science-teach-to-group-select').select2({
        width: '100%',
        placeholder: 'Select a group member',
        allowClear: true,
        theme: 'bootstrap4'
    });

    $('.science-project-select').select2({
        width: '100%',
        placeholder: 'Select a project',
        allowClear: true,
        theme: 'bootstrap4'
    });

    $('.science-research-for-group-select').select2({
        width: '100%',
        placeholder: 'Select a group member',
        allowClear: true,
        theme: 'bootstrap4'
    });
    
    // Initialize visibility after select2 is set up
    initScienceSlots();
});

// Science action selection changes
$(document).on('change', '.science-action-select', function() {
    toggleScienceFields($(this));
    dirtyStep('science');
});

function toggleScienceFields($select) {
    var $card = $select.closest('.science-slot-card');
    var action = $select.val();
    $card.find('.science-theorise-fields, .science-research-sample-fields, .science-research-project-fields, .science-teach-invention-fields').hide();
    if (action === 'theorise') {
        $card.find('.science-theorise-fields').show();
    } else if (action === 'research_sample') {
        $card.find('.science-research-sample-fields').show();
    } else if (action === 'research_project') {
        $card.find('.science-research-project-fields').show();
    } else if (action === 'teach_invention') {
        $card.find('.science-teach-invention-fields').show();
    }
}

// Project source toggle
$(document).on('click', '.btn-toggle-project-source .btn', function() {
    var $btn = $(this);
    var $group = $btn.closest('.btn-toggle-project-source');
    $group.find('.btn').removeClass('active');
    $btn.addClass('active');
    var source = $btn.data('project-source');
    var $card = $btn.closest('.science-slot-card');
    $card.find('.project-select-row').hide();
    $card.find('.project-select-row[data-project-source="' + source + '"]').show();
    dirtyStep('science');
});

// Research for toggle
$(document).on('click', '.btn-toggle-research-for .btn', function() {
    var $btn = $(this);
    var $group = $btn.closest('.btn-toggle-research-for');
    $group.find('.btn').removeClass('active');
    $btn.addClass('active');
    var researchFor = $btn.data('research-for');
    var $card = $btn.closest('.science-slot-card');
    $card.find('.science-research-for-group-select, .science-research-for-id-input').hide();
    if (researchFor === 'group') {
        $card.find('.science-research-for-group-select').show();
    } else if (researchFor === 'other') {
        $card.find('.science-research-for-id-input').show();
    }
    dirtyStep('science');
});

// Science project select change
$(document).on('change input', '.science-project-select, .science-project-id-input, .science-research-for-group-select, .science-research-for-id-input', function() {
    var $card = $(this).closest('.science-slot-card');
    var source = $card.find('.btn-toggle-project-source .btn.active').data('project-source');
    var projectId = '';
    if (source === 'my' || source === 'group') {
        projectId = $card.find('.science-project-select[data-project-source="' + source + '"]').val();
    } else if (source === 'id') {
        projectId = $card.find('.science-project-id-input').val();
    }
    // Remove previous status icons/names
    $card.find('.science-project-id-status, .science-research-for-status').remove();
    $card.find('.science-project-id-input, .science-research-for-id-input').removeClass('is-valid is-invalid');
    if (projectId) {
        // Get research for target
        var researchFor = $card.find('.btn-toggle-research-for .btn.active').data('research-for');
        var targetCharId = null;
        if (researchFor === 'self') {
            var playerId = $('#downtime-form').data('player-id');
            var charId = $('#downtime-form').data('character-id');
            targetCharId = playerId + '.' + charId;
        } else if (researchFor === 'group') {
            var groupCharId = $card.find('.science-research-for-group-select').val();
            var groupPlayerId = $card.find('.science-research-for-group-select option:selected').data('player-id');
            if (groupCharId && groupPlayerId) {
                targetCharId = groupPlayerId + '.' + groupCharId;
            }
        } else if (researchFor === 'other') {
            var idVal = $card.find('.science-research-for-id-input').val();
            if (idVal && idVal.includes('.')) {
                targetCharId = idVal;
            }
        }
        // Hide science type row by default
        $card.find('.science-project-science-type-row').hide();
        $card.find('.science-project-error').hide();
        // Reset validation state
        setSelect2Invalid($card.find('.science-project-select'), false);
        setSelect2Invalid($card.find('.science-project-science-type-select'), false);
        // Get project info
        $.get('/db/research/project_info', { project_id: projectId, character_id: targetCharId }, function(resp) {
            // Remove previous status icons/names
            $card.find('.science-project-id-status, .science-research-for-status').remove();
            $card.find('.science-project-id-input, .science-research-for-id-input').removeClass('is-valid is-invalid');
            // Project ID validation (for 'id' source)
            if (source === 'id') {
                var $input = $card.find('.science-project-id-input');
                if (resp.found) {
                    $input.addClass('is-valid');
                    $input.after('<span class="science-project-id-status" style="color:green;font-weight:bold;">&#10003; ' + (resp.project_name || 'Found') + '</span>');
                } else {
                    $input.addClass('is-invalid');
                    $input.after('<span class="science-project-id-status" style="color:red;font-weight:bold;">&#10007; Not found</span>');
                }
            }
            // Research for ID validation (for 'other' target)
            if (researchFor === 'other') {
                var $targetInput = $card.find('.science-research-for-id-input');
                if (resp.valid && resp.character_name) {
                    $targetInput.addClass('is-valid');
                    $targetInput.after('<span class="science-research-for-status" style="color:green;font-weight:bold;">&#10003; ' + resp.character_name + '</span>');
                } else if ($targetInput.val()) {
                    $targetInput.addClass('is-invalid');
                    $targetInput.after('<span class="science-research-for-status" style="color:red;font-weight:bold;">&#10007; Not found</span>');
                }
            }
            if (resp.found && resp.valid) {
                var scienceType = $card.data('science-type');
                var requirements = resp.stage_requirements || [];
                var requiredTypes = requirements.filter(r => r.requirement_type === 'science').map(r => r.science_type);
                if (scienceType === 'generic') {
                    var $typeSelect = $card.find('.science-project-science-type-select');
                    $typeSelect.empty();
                    $typeSelect.append('<option value="">Select a science type</option>');
                    requiredTypes.forEach(function(st) {
                        if (st) $typeSelect.append('<option value="' + st + '">' + (window.ScienceTypeDescriptions ? window.ScienceTypeDescriptions[st] : st) + '</option>');
                    });
                    $card.find('.science-project-science-type-row').show();
                    // Mark as invalid if no type selected
                    if (!$typeSelect.val()) {
                        setSelect2Invalid($typeSelect, true);
                    }
                } else {
                    // Only show error if the project requires specific science types and this type isn't one of them
                    // If the project requires generic science, any type is valid
                    var hasGenericRequirement = requiredTypes.includes('generic');
                    var hasSpecificRequirement = requiredTypes.includes(scienceType);
                    if (!hasGenericRequirement && !hasSpecificRequirement) {
                        $card.find('.science-project-error').text('This project does not require the selected science type at the current stage.').show();
                        setSelect2Invalid($card.find('.science-project-select'), true);
                    }
                }
            } else {
                setSelect2Invalid($card.find('.science-project-select'), true);
                $card.find('.science-project-error').text(resp.error || 'Project not found.').show();
            }
        });
    } else {
        $card.find('.science-project-science-type-row').hide();
        $card.find('.science-project-id-status, .science-research-for-status').remove();
        $card.find('.science-project-id-input, .science-research-for-id-input').removeClass('is-valid is-invalid');
    }
    dirtyStep('science');
});

// Science theorise fields change
$(document).on('input', '.science-theorise-fields input, .science-theorise-fields textarea', function() {
    dirtyStep('science');
});

// Science synthesize type select change
$(document).on('change', '.science-synthesize-type-select', function() {
    dirtyStep('science');
});

// Science sample select change
$(document).on('change', '.science-sample-select', function() {
    dirtyStep('science');
});

// Add change handler for science type select
$(document).on('change', '.science-project-science-type-select', function() {
    var $select = $(this);
    var $card = $select.closest('.science-slot-card');
    if ($select.val()) {
        setSelect2Invalid($select, false);
    } else {
        setSelect2Invalid($select, true);
    }
    dirtyStep('science');
});

// Add change handler for group member select
$(document).on('change', '.science-research-for-group-select', function() {
    var $select = $(this);
    if ($select.val()) {
        setSelect2Invalid($select, false);
    } else {
        setSelect2Invalid($select, true);
    }
    dirtyStep('science');
});

// Teach to toggle
$(document).on('click', '.btn-toggle-teach-to .btn', function() {
    var $btn = $(this);
    var $group = $btn.closest('.btn-toggle-teach-to');
    $group.find('.btn').removeClass('active');
    $btn.addClass('active');
    var teachTo = $btn.data('teach-to');
    var $card = $btn.closest('.science-slot-card');
    
    // Hide both containers and their select2 containers
    $card.find('.science-teach-to-group-select, .science-teach-to-id-input').hide();
    $card.find('.science-teach-to-group-select').next('.select2-container').hide();
    // Remove any status messages
    $card.find('.science-teach-to-status').remove();
    $card.find('.science-teach-to-id-input').removeClass('is-valid is-invalid');
    
    if (teachTo === 'group') {
        $card.find('.science-teach-to-group-select').show();
        $card.find('.science-teach-to-group-select').next('.select2-container').show();
    } else if (teachTo === 'other') {
        $card.find('.science-teach-to-id-input').show();
    }
    dirtyStep('science');
});

// Teach project select change
$(document).on('change', '.science-teach-project-select', function() {
    var $select = $(this);
    var $card = $select.closest('.science-slot-card');
    if ($select.val()) {
        setSelect2Invalid($select, false);
        // If we have a character ID entered, revalidate it
        var $idInput = $card.find('.science-teach-to-id-input');
        if ($idInput.val() && $idInput.val().includes('.')) {
            $idInput.trigger('input');
        }
    } else {
        setSelect2Invalid($select, true);
        // Clear any validation status
        $card.find('.science-teach-to-status').remove();
        $card.find('.science-teach-to-id-input').removeClass('is-valid is-invalid');
    }
    dirtyStep('science');
});

// Teach to ID input change
$(document).on('input', '.science-teach-to-id-input', function() {
    var $input = $(this);
    var $card = $input.closest('.science-slot-card');
    var idVal = $input.val();
    var projectId = $card.find('.science-teach-project-select').val();
    var teachingCharId = $('#downtime-form').data('character-id');
    
    // Remove previous status
    $card.find('.science-teach-to-status').remove();
    $input.removeClass('is-valid is-invalid');
    
    if (idVal && idVal.includes('.') && projectId) {
        // Get character info and validate teaching
        $.get('/db/research/can_teach_character', { 
            project_id: projectId,
            character_id: idVal,
            teaching_character_id: teachingCharId
        }, function(resp) {
            // Remove previous status
            $card.find('.science-teach-to-status').remove();
            $input.removeClass('is-valid is-invalid');
            
            if (resp.valid) {
                $input.addClass('is-valid');
                $input.after('<span class="science-teach-to-status" style="color:green;font-weight:bold;">&#10003; ' + resp.character_name + ' - ' + resp.message + '</span>');
            } else {
                $input.addClass('is-invalid');
                $input.after('<span class="science-teach-to-status" style="color:red;font-weight:bold;">&#10007; ' + resp.error + '</span>');
            }
        });
    }
    dirtyStep('science');
});

function validateScienceStep() {
    let valid = true;
    let error = '';
    let theoriseCount = 0;
    
    // First pass: count theorise actions
    $('.science-slot-card').each(function() {
        const $card = $(this);
        const action = $card.find('.science-action-select').val();
        if (action === 'theorise') {
            theoriseCount++;
        }
    });
    
    // Second pass: validate each slot
    $('.science-slot-card').each(function() {
        const $card = $(this);
        const action = $card.find('.science-action-select').val();
        if (action) {
            // Reset validation
            $card.find('.science-action-select, input, select, textarea').removeClass('is-invalid');
            setSelect2Invalid($card.find('select'), false);
            
            if (action === 'theorise') {
                const name = $card.find('input[name^="science_theorise_name_"]').val();
                const desc = $card.find('textarea[name^="science_theorise_desc_"]').val();
                if (!name || !desc) {
                    valid = false;
                    error = 'Fill in all fields for each theorise action.';
                }
            } else if (action === 'synthesize') {
                // If generic, require type selection
                var synthTypeSelect = $card.find('select.science-synthesize-type-select');
                if (synthTypeSelect.length && !synthTypeSelect.val()) {
                    setSelect2Invalid(synthTypeSelect, true);
                    valid = false;
                    error = 'Select a science type for each synthesis.';
                }
            } else if (action === 'research_sample') {
                const sample = $card.find('select.science-sample-select').val();
                if (!sample) {
                    setSelect2Invalid($card.find('select.science-sample-select'), true);
                    valid = false;
                    error = 'Select a sample for each research action.';
                }
            } else if (action === 'teach_invention') {
                const project = $card.find('select.science-teach-project-select').val();
                if (!project) {
                    setSelect2Invalid($card.find('select.science-teach-project-select'), true);
                    valid = false;
                    error = 'Select a project to teach.';
                }
                const teachTo = $card.find('.btn-toggle-teach-to .btn.active').data('teach-to');
                if (teachTo === 'group') {
                    const groupMember = $card.find('select.science-teach-to-group-select').val();
                    if (!groupMember) {
                        setSelect2Invalid($card.find('select.science-teach-to-group-select'), true);
                        valid = false;
                        error = 'Select a group member to teach to.';
                    }
                } else if (teachTo === 'other') {
                    const otherId = $card.find('input.science-teach-to-id-input').val();
                    if (!otherId || !otherId.match(/^\d+\.\d+$/)) {
                        $card.find('input.science-teach-to-id-input').addClass('is-invalid');
                        valid = false;
                        error = 'Enter a valid PlayerID.CharacterID.';
                    }
                }
            }
        }
    });
    stepErrors['science'] = valid ? null : error;
    return valid;
}

// Form submission
$('#downtime-form').on('submit', function() {
    // Remove previous science[] hidden inputs
    $('input[name="science[]"]').remove();

    // For each science slot
    $('.science-slot-card').each(function(slot) {
        const $card = $(this);
        const action = $card.find('.science-action-select').val();
        const scienceType = $card.data('science-type');
        let obj = { action: action, science_type: scienceType };

        if (action === 'theorise') {
            obj.theorise_name = $card.find('input[name^="science_theorise_name_"]').val();
            obj.theorise_desc = $card.find('textarea[name^="science_theorise_desc_"]').val();
        } else if (action === 'synthesize') {
            obj.synthesize_type = $card.find('select.science-synthesize-type-select').val();
        } else if (action === 'research_sample') {
            obj.sample_id = $card.find('select.science-sample-select').val();
        } else if (action === 'research_project') {
            obj.project_source = $card.find('.btn-toggle-project-source .btn.active').data('project-source');
            if (obj.project_source === 'my' || obj.project_source === 'group') {
                obj.project_id = $card.find('.science-project-select[data-project-source="' + obj.project_source + '"]').val();
            } else if (obj.project_source === 'id') {
                obj.project_id = $card.find('.science-project-id-input').val();
            }
            obj.research_for = $card.find('.btn-toggle-research-for .btn.active').data('research-for');
            if (obj.research_for === 'group') {
                obj.research_for_id = $card.find('.science-research-for-group-select').val();
            } else if (obj.research_for === 'other') {
                obj.research_for_id = $card.find('.science-research-for-id-input').val();
            }
            obj.science_type_select = $card.find('.science-project-science-type-select').val();
        } else if (action === 'teach_invention') {
            obj.project_id = $card.find('select.science-teach-project-select').val();
            obj.teach_to = $card.find('.btn-toggle-teach-to .btn.active').data('teach-to');
            if (obj.teach_to === 'group') {
                obj.teach_to_id = $card.find('select.science-teach-to-group-select').val();
            } else if (obj.teach_to === 'other') {
                obj.teach_to_id = $card.find('input.science-teach-to-id-input').val();
            }
        }

        // Only add if action is set
        if (action) {
            const jsonValue = JSON.stringify(obj);
            const htmlSafeValue = jsonValue.replace(/"/g, '&quot;');
            $('#downtime-form').append(`<input type="hidden" name="science[]" value="${htmlSafeValue}">`);
        }

        // Disable original fields
        $card.find('select, input, textarea').prop('disabled', true);
    });
});