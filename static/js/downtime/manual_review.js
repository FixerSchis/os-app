$(document).ready(function() {
    const form = document.getElementById('manual-review-form');
    const confirmComplete = document.getElementById('confirm_complete');
    
    // Handle form submission
    form.addEventListener('submit', function(e) {
        if (confirmComplete.checked) {
            // Check if all required fields are filled
            const requiredFields = form.querySelectorAll('[required]');
            let allFilled = true;
            
            requiredFields.forEach(field => {
                if (!field.value.trim()) {
                    allFilled = false;
                }
            });
            
            if (!allFilled) {
                e.preventDefault();
                alert('Please fill in all required fields before confirming completion.');
                return;
            }
        }
        // Always update stages-json before submit
        const container = $('#stages-container');
        const stages = getStagesData(container);
        $('#stages-json').val(JSON.stringify(stages));
        console.log('Saving stages-json:', JSON.stringify(stages));
        console.log('Saved stages-json:', $('#stages-json').val());
        form.submit();
    });

    // Initialize approve/decline options for the single invention
    function updateApproveDeclineUI() {
        const approveChecked = $("#approve").is(":checked");
        const declineChecked = $("#decline").is(":checked");
        $("#decline_response").toggle(declineChecked);
        $("#approve_options").toggle(approveChecked);
        if (approveChecked) {
            // Show/hide new/improve fields
            const isNew = $("#new_invention").is(":checked");
            $("#new_invention_fields").toggle(isNew);
            $("#improve_invention_fields").toggle(!isNew);
        } else {
            $("#new_invention_fields").hide();
            $("#improve_invention_fields").hide();
        }
    }

    // Handle approve/decline radio buttons
    $("input[name='invention_review']").on('change', function() {
        updateApproveDeclineUI();
        if ($(this).val() === 'approve') {
            $("#invention_response").val('');
        }
    });

    // Handle invention type radio buttons
    $("input[name='invention_type']").on('change', function() {
        updateApproveDeclineUI();
    });

    // On page load, trigger change events to ensure correct UI state
    $("input[name='invention_review']:checked").trigger('change');
    $("input[name='invention_type']:checked").trigger('change');

    // Initialize stages for each invention
    $('.new-invention-fields').each(function() {
        const index = $(this).attr('id').split('_')[1];
        const container = $(`#stages-container_${index}`);
        const initialStagesJson = $(`#initial-stages-json-${index}`).val();
        
        if (initialStagesJson) {
            try {
                const stages = JSON.parse(initialStagesJson);
                if (Array.isArray(stages)) {
                    stages.forEach(stage => {
                        container.append(createStageHtml(stage));
                    });
                    // Trigger change event on all requirement types to show appropriate fields
                    container.find('.requirement-type').trigger('change');
                    // Initialize select2 for any existing sample tags
                    container.find('.sample-tag').select2({
                        tags: true,
                        width: '100%',
                        allowClear: true
                    });
                }
            } catch (e) {
                console.error('Error parsing initial stages:', e);
            }
        }
    });
});

// Helper function to get stages data from a container
function getStagesData(container) {
    if (!container || container.length === 0) return [];
    const stages = [];
    container.find('.stage').each(function(index) {
        const stageEl = $(this);
        const stage = {
            stage_number: index + 1,
            name: stageEl.find('.stage-name').val(),
            description: stageEl.find('.stage-description').val(),
            unlock_requirements: []
        };
        stageEl.find('.requirement').each(function() {
            const reqEl = $(this);
            const requirement = {
                requirement_type: reqEl.find('.requirement-type').val(),
                amount: parseInt(reqEl.find('.requirement-amount').val())
            };
            
            if (requirement.requirement_type === 'science') {
                requirement.science_type = reqEl.find('.science-type').val();
            } else if (requirement.requirement_type === 'item') {
                requirement.item_type = reqEl.find('.item-type').val();
            } else if (requirement.requirement_type === 'exotic') {
                requirement.exotic_type = reqEl.find('.exotic-type').val();
            } else if (requirement.requirement_type === 'sample') {
                requirement.sample_tag = reqEl.find('.sample-tag').val();
                requirement.requires_researched = reqEl.find('.requires-researched').is(':checked');
            }
            
            stage.unlock_requirements.push(requirement);
        });
        stages.push(stage);
    });
    return stages;
} 