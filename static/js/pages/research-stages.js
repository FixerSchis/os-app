// Dynamic research stage and requirement editing for research admin UI
// Requires Select2 for item blueprints and exotics

$(document).ready(function() {
    // Initialize stages from initial data
    const initialStagesJson = $('#initial-stages-json').val();
    if (initialStagesJson) {
        try {
            const stages = JSON.parse(initialStagesJson);
            stages.forEach(stage => {
                $('#stages-container').append(createStageHtml(stage));
            });
            updateStageNumbers();
            updateDeleteButtons();
            // Trigger change event on all requirement types to show appropriate fields
            $('.requirement-type').trigger('change');
            // Initialize select2 for any existing sample tags
            $('.sample-tag').select2({
                tags: true,
                width: '100%',
                allowClear: true
            });
        } catch (e) {
            console.error('Error parsing initial stages:', e);
        }
    }

    // Add new stage
    $('#add-stage').on('click', function() {
        const stageCount = $('.stage').length;
        const newStage = {
            stage_number: stageCount + 1,
            name: `Stage ${stageCount + 1}`,
            description: '',
            unlock_requirements: []
        };
        $('#stages-container').append(createStageHtml(newStage));
        updateStageNumbers();
        updateDeleteButtons();
    });

    // Delete stage
    $(document).on('click', '.delete-stage', function() {
        const stageEl = $(this).closest('.stage');
        stageEl.remove();
            updateStageNumbers();
        updateDeleteButtons();
    });

    // Add requirement
    $(document).on('click', '.add-requirement', function() {
        const stageEl = $(this).closest('.stage');
        const requirementsContainer = stageEl.find('.requirements-container');
        const newRequirement = {
            requirement_type: 'science',
            amount: 1,
            science_type: null,
            item_type: null,
            exotic_type: null,
            sample_tag: null,
            requires_researched: false
        };
        const requirementHtml = createRequirementHtml(newRequirement);
        requirementsContainer.append(requirementHtml);
        // Show the science type group for the new requirement
        requirementsContainer.find('.requirement:last-child .science-type-group').show();
    });

    // Delete requirement
    $(document).on('click', '.delete-requirement', function() {
        $(this).closest('.requirement').remove();
    });

    // Handle requirement type change
    $(document).on('change', '.requirement-type', function() {
        const reqEl = $(this).closest('.requirement');
        const type = $(this).val();

        // Hide all type-specific groups
        reqEl.find('.science-type-group, .item-type-group, .exotic-type-group, .sample-tag-group, .requires-researched-group').hide();

        // Show relevant groups based on type
        if (type === 'science') {
            reqEl.find('.science-type-group').show();
        } else if (type === 'item') {
            reqEl.find('.item-type-group').show();
        } else if (type === 'exotic') {
            reqEl.find('.exotic-type-group').show();
        } else if (type === 'sample') {
            reqEl.find('.sample-tag-group, .requires-researched-group').show();
            // Initialize select2 for the sample tag field
            reqEl.find('.sample-tag').select2({
                tags: true,
                width: '100%'
            });
        }
    });

    // Update stage numbers
    function updateStageNumbers() {
        $('.stage').each(function(index) {
            $(this).attr('data-stage-number', index + 1);
            $(this).find('h3').text(`Stage ${index + 1}`);
        });
    }

    // Update delete buttons visibility based on stage count
    function updateDeleteButtons() {
        const stageCount = $('.stage').length;
        if (stageCount <= 1) {
            $('.delete-stage').hide();
        } else {
            $('.delete-stage').show();
        }
    }

    // Form submission
    $('form').on('submit', function(e) {
        e.preventDefault();
        const stagesData = getStagesData();
        $('#stages-json').val(JSON.stringify(stagesData));
        this.submit();
    });
});

function createStageHtml(stage) {
    const isSingleStage = $('.stage').length === 0;
    return `
        <div class="stage mb-4 p-3 border rounded" data-stage-number="${stage.stage_number}">
            <div class="d-flex justify-content-between align-items-center mb-3">
                <h3 class="h5 mb-0">Stage ${stage.stage_number}</h3>
                <button type="button" class="btn btn-danger btn-sm delete-stage" ${isSingleStage ? 'style="display: none;"' : ''}>
                    <i class="fas fa-trash"></i>
                </button>
            </div>
            <div class="mb-3">
                <label class="form-label">Stage Name</label>
                <input type="text" class="form-control stage-name" value="${stage.name}" required>
            </div>
            <div class="mb-3">
                <label class="form-label">Description</label>
                <textarea class="form-control stage-description" rows="3">${stage.description || ''}</textarea>
            </div>
            <div class="requirements-container">
                ${stage.unlock_requirements.map(req => createRequirementHtml(req)).join('')}
            </div>
            <button type="button" class="btn btn-outline-primary btn-sm add-requirement">
                <i class="fas fa-plus"></i> Add Requirement
            </button>
        </div>
    `;
}

function createRequirementHtml(requirement) {
    return `
        <div class="requirement">
            <button type="button" class="btn btn-danger btn-sm delete-requirement float-end">
                <i class="fas fa-trash"></i>
            </button>
            <div class="row">
                <div class="col-md-4 mb-2">
                    <select class="form-select requirement-type">
                        ${window.REQUIREMENT_TYPE_OPTIONS_HTML.replace('value="' + requirement.requirement_type + '"', 'value="' + requirement.requirement_type + '" selected')}
                    </select>
                </div>
                <div class="col-md-2 mb-2">
                    <input type="number" class="form-control requirement-amount" value="${requirement.amount}" min="1" required>
                </div>
                <div class="col-md-6 mb-2 science-type-group" style="display: ${requirement.requirement_type === 'science' ? 'block' : 'none'}">
                    <select class="form-select science-type">
                        ${window.SCIENCE_TYPE_OPTIONS_HTML.replace('value="' + requirement.science_type + '"', 'value="' + requirement.science_type + '" selected')}
                    </select>
                </div>
                <div class="col-md-6 mb-2 item-type-group" style="display: ${requirement.requirement_type === 'item' ? 'block' : 'none'}">
                    <select class="form-select item-type">
                        ${window.ITEM_TYPE_OPTIONS_HTML.replace('value="' + requirement.item_type + '"', 'value="' + requirement.item_type + '" selected')}
                    </select>
                </div>
                <div class="col-md-6 mb-2 exotic-type-group" style="display: ${requirement.requirement_type === 'exotic' ? 'block' : 'none'}">
                    <select class="form-select exotic-type">
                        ${window.EXOTIC_TYPE_OPTIONS_HTML.replace('value="' + requirement.exotic_type + '"', 'value="' + requirement.exotic_type + '" selected')}
                    </select>
                </div>
                <div class="col-md-3 mb-2 sample-tag-group" style="display: ${requirement.requirement_type === 'sample' ? 'block' : 'none'}">
                    <select class="form-select sample-tag">
                        ${window.SAMPLE_TAG_OPTIONS_HTML.replace('value="' + requirement.sample_tag + '"', 'value="' + requirement.sample_tag + '" selected')}
                    </select>
                </div>
                <div class="col-md-3 mb-2 requires-researched-group" style="display: ${requirement.requirement_type === 'sample' ? 'block' : 'none'}">
                    <div class="form-check mt-4">
                        <input class="form-check-input requires-researched" type="checkbox" ${requirement.requires_researched ? 'checked' : ''}>
                        <label class="form-check-label">Researched</label>
                    </div>
                </div>
            </div>
        </div>
    `;
}

function getStagesData() {
    const stages = [];
    document.querySelectorAll('.stage').forEach((stageEl, index) => {
        const stage = {
            stage_number: index + 1,
            name: stageEl.querySelector('.stage-name').value,
            description: stageEl.querySelector('.stage-description').value,
            unlock_requirements: []
        };
        stageEl.querySelectorAll('.requirement').forEach(reqEl => {
            const requirement = {
                requirement_type: reqEl.querySelector('.requirement-type').value,
                amount: parseInt(reqEl.querySelector('.requirement-amount').value)
            };
            if (requirement.requirement_type === 'science') {
                requirement.science_type = reqEl.querySelector('.science-type').value;
            } else if (requirement.requirement_type === 'item') {
                requirement.item_type = reqEl.querySelector('.item-type').value;
            } else if (requirement.requirement_type === 'exotic') {
                requirement.exotic_type = reqEl.querySelector('.exotic-type').value;
            } else if (requirement.requirement_type === 'sample') {
                requirement.sample_tag = reqEl.querySelector('.sample-tag').value;
                requirement.requires_researched = reqEl.querySelector('.requires-researched').checked;
            }
            stage.unlock_requirements.push(requirement);
        });
        stages.push(stage);
    });
    return stages;
    }

    // --- Moved from template: Artefact item toggling logic ---
    function toggleArtefactItem() {
        var typeElem = document.getElementById('type');
        var group = document.getElementById('artefact-item-group');
        if (!typeElem || !group) return;
        var type = typeElem.value;
        group.style.display = (type === 'artefact') ? 'block' : 'none';
    }

    function toggleArtefactOption() {
        var existing = document.getElementById('existing-item-select');
        var createNew = document.getElementById('new-item-type-select');
        var selectedRadio = document.querySelector('input[name="artefact_option"]:checked');
        if (!existing || !createNew || !selectedRadio) return;
        var selected = selectedRadio.value;
        if (selected === 'existing') {
            existing.style.display = 'block';
            createNew.style.display = 'none';
        } else {
            existing.style.display = 'none';
            createNew.style.display = 'block';
        }
    }

    window.addEventListener('DOMContentLoaded', function() {
        toggleArtefactItem();
        var radios = document.querySelectorAll('input[name="artefact_option"]');
        radios.forEach(function(radio) {
            radio.addEventListener('change', toggleArtefactOption);
        });
        toggleArtefactOption();
        var typeElem = document.getElementById('type');
        if (typeElem) {
            typeElem.addEventListener('change', toggleArtefactItem);
    }
});
