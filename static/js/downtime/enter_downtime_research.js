let researchCardCount = 0;

// Parse project data from hidden fields
let myProjects = [];
let groupProjects = [];
try {
    myProjects = JSON.parse($('#my-projects-data').val() || '[]');
    groupProjects = JSON.parse($('#group-projects-data').val() || '[]');
} catch (e) {
    console.error('Failed to parse project data:', e);
}

let currentCharacterId = $('#current-character-id').val();

const packItems = getJsonData('pack-items-json');
const availableSamples = getJsonData('available-samples-json');
const packExotics = getJsonData('pack-exotics-json');

initResearchCards();

function initResearchCards() {
    let packResearch = $('#downtime-form').data('pack-research');
    if (typeof packResearch === 'string') {
        packResearch = JSON.parse(packResearch || '[]');
    } else {
        packResearch = packResearch || [];
    }
    packResearch.forEach(function(research) {
        addResearchProjectCard();
        const $card = $('#research-projects-list .research-assist-card:last');
        // Set project source
        $card.find('.btn-toggle-project-source .btn[data-project-source="' + research.project_source + '"]').click();
        if (research.project_source === 'my' || research.project_source === 'group') {
            const $projectSelect = $card.find('.research-project-select[data-project-source="' + research.project_source + '"]');
            $projectSelect.val(research.project_id).trigger('change');
        } else if (research.project_source === 'id') {
            $card.find('.research-project-id-input').val(research.project_id);
        }
        // Set support target
        $card.find('.btn-toggle-support-target .btn[data-support-target="' + research.support_target + '"]').click();
        if (research.support_target === 'group') {
            $card.find('.support-group-member-select').val(research.support_target_id).trigger('change');
        } else if (research.support_target === 'other') {
            $card.find('.support-other-id-input').val(research.support_target_id);
        }
        // Fetch and render research requirements to show appropriate fields
        fetchAndRenderResearchRequirements($card);
        // Set contributed exotics
        if (research.contributed_exotics) {
            research.contributed_exotics.forEach(function(exotic) {
                $card.find('.exotic-requirement-slot[data-exotic-id="' + exotic.id + '"]').find('.exotic-select').val(exotic.quantity).trigger('change');
            });
        }
        // Set contributed items
        if (research.contributed_items) {
            research.contributed_items.forEach(function(itemId) {
                $card.find('.item-requirement-slot[data-item-id="' + itemId + '"]').find('.item-select').prop('checked', true);
            });
        }
        // Set contributed samples
        if (research.contributed_samples) {
            research.contributed_samples.forEach(function(sampleId) {
                $card.find('.sample-requirement-slot[data-sample-id="' + sampleId + '"]').find('.sample-select').prop('checked', true);
            });
        }
    });
}

// Handler for Add Project button
$('#add-research-project').on('click', function() {
    addResearchProjectCard();
});

$(document).on('click', '.remove-research-card', function() {
    $(this).closest('.research-assist-card').remove();
});

$(document).on('click', '.research-assist-card .btn-toggle-project-source .btn', function() {
    var $btn = $(this);
    var $group = $btn.closest('.btn-toggle-project-source');
    $group.find('.btn').removeClass('active');
    $btn.addClass('active');
    var source = $btn.data('project-source');
    var $card = $btn.closest('.research-assist-card');
    $card.find('.project-select-row').hide();
    $card.find('.project-select-row[data-project-source="' + source + '"]').show();
    clearResearchRequirements($card);
});

$(document).on('click', '.research-assist-card .btn-toggle-support-target .btn', function() {
    var $btn = $(this);
    var $group = $btn.closest('.btn-toggle-support-target');
    $group.find('.btn').removeClass('active');
    $btn.addClass('active');
    var target = $btn.data('support-target');
    var $card = $btn.closest('.research-assist-card');
    $card.find('.support-target-row').hide();
    $card.find('.support-target-row[data-support-target="' + target + '"]').show();
    clearResearchRequirements($card);
});

$(document).on('change input', '.research-assist-card .research-project-select, .research-assist-card .research-project-id-input, .research-assist-card .support-group-member-select, .research-assist-card .support-other-id-input', function() {
    var $card = $(this).closest('.research-assist-card');
    validateResearchCard($card);
    fetchAndRenderResearchRequirements($card);
});

$(document).on('click', '.research-assist-card .btn-toggle-project-source .btn, .research-assist-card .btn-toggle-support-target .btn', function() {
    var $card = $(this).closest('.research-assist-card');
    fetchAndRenderResearchRequirements($card);
});

function getProjectOptions(projects) {
    return projects.map(function(cr) {
        return `<option value="${cr.research_id}">${cr.project_name}${cr.character_name ? ' (' + cr.character_name + ')' : ''}</option>`;
    }).join('');
}

function getGroupMemberOptions(members) {
    return members.map(function(m) {
        return `<option value="${m.player_id}.${m.id}">${m.name}</option>`;
    }).join('');
}

function addResearchProjectCard() {
    researchCardCount++;
    const cardId = 'research-card-' + researchCardCount;
    const myProjectOptions = getProjectOptions(myProjects || []);
    const groupProjectOptions = getProjectOptions(groupProjects || []);
    const groupMemberOptions = getGroupMemberOptions(window.GROUP_MEMBERS || []);
    const cardHtml = `
    <div class="card mb-3 research-assist-card" id="${cardId}">
        <div class="card-body">
            <div class="d-flex justify-content-between align-items-center mb-2">
                <strong>Research Project</strong>
                <button type="button" class="btn btn-outline-danger btn-sm remove-research-card">Remove</button>
            </div>
            <div class="row mb-2">
                <div class="col-md-4">
                    <label>Project Source</label>
                    <div class="btn-group btn-toggle-project-source" role="group">
                        <button type="button" class="btn btn-outline-primary active" data-project-source="my">My Projects</button>
                        <button type="button" class="btn btn-outline-primary" data-project-source="group">Group Projects</button>
                        <button type="button" class="btn btn-outline-primary" data-project-source="id">Enter ID</button>
                    </div>
                </div>
                <div class="col-md-4 project-select-row" data-project-source="my">
                    <label>Project</label>
                    <select class="form-control select2 research-project-select" data-project-source="my">
                        <option value="">Select a project</option>
                        ${myProjectOptions}
                    </select>
                </div>
                <div class="col-md-4 project-select-row" data-project-source="group" style="display:none;">
                    <label>Project</label>
                    <select class="form-control select2 research-project-select" data-project-source="group">
                        <option value="">Select a project</option>
                        ${groupProjectOptions}
                    </select>
                </div>
                <div class="col-md-4 project-select-row" data-project-source="id" style="display:none;">
                    <label>Project ID</label>
                    <input type="text" class="form-control research-project-id-input" placeholder="Enter project ID">
                </div>
            </div>
            <div class="row mb-2">
                <div class="col-md-4">
                    <label>Support Target</label>
                    <div class="btn-group btn-toggle-support-target" role="group">
                        <button type="button" class="btn btn-outline-primary active" data-support-target="self">Self</button>
                        <button type="button" class="btn btn-outline-primary" data-support-target="group">Group Member</button>
                        <button type="button" class="btn btn-outline-primary" data-support-target="other">Enter ID</button>
                    </div>
                </div>
                <div class="col-md-4 support-target-row" data-support-target="group" style="display:none;">
                    <label>Group Member</label>
                    <select class="form-control select2 support-group-member-select">
                        <option value="">Select a group member</option>
                        ${groupMemberOptions}
                    </select>
                </div>
                <div class="col-md-4 support-target-row" data-support-target="other" style="display:none;">
                    <label>PlayerID.CharacterID</label>
                    <input type="text" class="form-control support-other-id-input" placeholder="PlayerID.CharacterID">
                </div>
            </div>
            <div class="research-requirements-list mt-3"></div>
            <div class="text-danger research-project-error mt-2" style="display:none;"></div>
        </div>
    </div>`;
    $('#research-projects-list').append(cardHtml);
    $('#' + cardId + ' .select2').select2({ width: '100%' });
    // Mark the project select as invalid initially
    const $newCard = $('#' + cardId);
    const $projectSelect = $newCard.find('.research-project-select[data-project-source="my"]');
    setSelect2Invalid($projectSelect, true);
}

function clearResearchRequirements($card) {
    $card.find('.research-requirements-list').empty();
    $card.find('.research-project-error').hide();
}

function validateResearchCard($card) {
    // Remove previous status icons/names
    $card.find('.research-project-id-status, .support-target-status').remove();
    $card.find('.research-project-id-input, .support-other-id-input').removeClass('is-valid is-invalid');
    setSelect2Invalid($card.find('.support-group-member-select'), false);
    setSelect2Invalid($card.find('.research-project-select'), false);
    // Project validation
    var source = $card.find('.btn-toggle-project-source .btn.active').data('project-source');
    var projectId = '';
    if (source === 'my' || source === 'group') {
        projectId = $card.find('.research-project-select[data-project-source="' + source + '"]').val();
    } else if (source === 'id') {
        projectId = $card.find('.research-project-id-input').val();
    }
    if (source === 'id') {
        var $input = $card.find('.research-project-id-input');
        if (!projectId) {
            $input.addClass('is-invalid');
        }
    } else {
        var $select = $card.find('.research-project-select[data-project-source="' + source + '"]');
        setSelect2Invalid($select, !projectId);
    }
    // Support target validation
    var targetType = $card.find('.btn-toggle-support-target .btn.active').data('support-target');
    if (targetType === 'group') {
        var $groupSelect = $card.find('.support-group-member-select');
        setSelect2Invalid($groupSelect, !$groupSelect.val());
    } else if (targetType === 'other') {
        var $targetInput = $card.find('.support-other-id-input');
        if (!$targetInput.val()) {
            $targetInput.addClass('is-invalid');
        }
    }
}

function fetchAndRenderResearchRequirements($card) {
    var source = $card.find('.btn-toggle-project-source .btn.active').data('project-source');
    var projectId = '';
    if (source === 'my' || source === 'group') {
        projectId = $card.find('.research-project-select[data-project-source="' + source + '"]').val();
    } else if (source === 'id') {
        projectId = $card.find('.research-project-id-input').val();
    }
    var targetType = $card.find('.btn-toggle-support-target .btn.active').data('support-target');
    var targetId = '';
    if (targetType === 'self') {
        targetId = currentCharacterId;
    } else if (targetType === 'group') {
        targetId = $card.find('.support-group-member-select').val();
    } else if (targetType === 'other') {
        targetId = $card.find('.support-other-id-input').val();
    }
    // Remove previous status icons/names
    $card.find('.research-project-id-status, .support-target-status').remove();
    $card.find('.research-project-id-input, .support-other-id-input').removeClass('is-valid is-invalid');
    setSelect2Invalid($card.find('.support-group-member-select'), false);
    setSelect2Invalid($card.find('.research-project-select'), false);
    if (!projectId && (source === 'my' || source === 'group')) {
        setSelect2Invalid($card.find('.research-project-select[data-project-source="' + source + '"]'), true);
    }
    if (!projectId && source === 'id') {
        $card.find('.research-project-id-input').addClass('is-invalid');
    }
    if (targetType === 'group' && !$card.find('.support-group-member-select').val()) {
        setSelect2Invalid($card.find('.support-group-member-select'), true);
    }
    if (targetType === 'other' && !$card.find('.support-other-id-input').val()) {
        $card.find('.support-other-id-input').addClass('is-invalid');
    }
    if (!projectId || !targetId) {
        clearResearchRequirements($card);
        return;
    }
    $.get('/db/research/project_info', { project_id: projectId, character_id: targetId }, function(resp) {
        // Remove previous status icons/names
        $card.find('.research-project-id-status, .support-target-status').remove();
        $card.find('.research-project-id-input, .support-other-id-input').removeClass('is-valid is-invalid');
        setSelect2Invalid($card.find('.support-group-member-select'), false);
        setSelect2Invalid($card.find('.research-project-select'), false);
        // Project ID validation (for 'id' source)
        if (source === 'id') {
            var $input = $card.find('.research-project-id-input');
            if (resp.found) {
                $input.removeClass('is-invalid').addClass('is-valid');
                $input.after('<span class="research-project-id-status" style="color:green;font-weight:bold;">&#10003; ' + (resp.project_name || 'Found') + '</span>');
            } else {
                $input.removeClass('is-valid').addClass('is-invalid');
                $input.after('<span class="research-project-id-status" style="color:red;font-weight:bold;">&#10007; Not found</span>');
            }
        } else {
            var $select = $card.find('.research-project-select[data-project-source="' + source + '"]');
            setSelect2Invalid($select, !resp.found);
        }
        // Support target validation
        if (targetType === 'group') {
            var $groupSelect = $card.find('.support-group-member-select');
            if (resp.valid && resp.character_name) {
                setSelect2Invalid($groupSelect, false);
                var $groupSelect2 = $groupSelect.next('.select2');
                if ($groupSelect2.length) {
                    $groupSelect2.find('.support-target-status').remove();
                    $groupSelect2.find('.select2-selection').append('<span class="support-target-status" style="color:green;font-weight:bold;position:absolute;right:10px;top:8px;">&#10003; ' + resp.character_name + '</span>');
                }
            } else {
                setSelect2Invalid($groupSelect, true);
                var $groupSelect2 = $groupSelect.next('.select2');
                if ($groupSelect2.length) {
                    $groupSelect2.find('.support-target-status').remove();
                    $groupSelect2.find('.select2-selection').append('<span class="support-target-status" style="color:red;font-weight:bold;position:absolute;right:10px;top:8px;">&#10007; Not found</span>');
                }
            }
        } else if (targetType === 'other') {
            var $targetInput = $card.find('.support-other-id-input');
            if (resp.valid && resp.character_name) {
                $targetInput.removeClass('is-invalid').addClass('is-valid');
                $targetInput.after('<span class="support-target-status" style="color:green;font-weight:bold;">&#10003; ' + resp.character_name + '</span>');
            } else if ($targetInput.val()) {
                $targetInput.removeClass('is-valid').addClass('is-invalid');
                $targetInput.after('<span class="support-target-status" style="color:red;font-weight:bold;">&#10007; Not found</span>');
            }
        }
        if (!resp.found || !resp.valid) {
            $card.find('.research-requirements-list').empty();
            $card.find('.research-project-error').text(resp.error || 'Not eligible to assist with this project.').show();
            return;
        }
        $card.find('.research-project-error').hide();
        renderResearchRequirements($card, resp.stage_requirements);
    });
}

function renderResearchRequirements($card, requirements) {
    var $list = $card.find('.research-requirements-list');
    $list.empty();
    requirements.forEach(function(req, idx) {
        let slotHtml = '';
        if (req.requirement_type === 'exotic') {
            slotHtml = renderExoticRequirementSlot(req, idx);
        } else if (req.requirement_type === 'item') {
            slotHtml = renderItemRequirementSlot(req, idx);
        } else if (req.requirement_type === 'sample') {
            slotHtml = renderSampleRequirementSlot(req, idx);
        }
        $list.append(slotHtml);
    });
    $list.find('.select2').select2({ width: '100%' });
}

function renderExoticRequirementSlot(req, idx) {
    // Exotics from pack matching exotic_type
    let options = '<option value="">Select Exotic</option>';
    if (packExotics) {
        packExotics.forEach(function(exotic) {
            if (exotic.id == req.exotic_type) {
                options += `<option value="${exotic.id}">${exotic.name}</option>`;
            }
        });
    }
    return `<div class="mb-2">
        <label>Exotic (${req.exotic_name})</label>
        <select class="form-control select2 research-exotic-select" data-req-idx="${idx}">
            ${options}
        </select>
    </div>`;
}

function renderItemRequirementSlot(req, idx) {
    // Items from pack and group members matching item_type
    let options = '<option value="">Select Item</option>';
    (packItems || []).forEach(function(item) {
        if (item.type == req.item_type) {
            options += `<option value="${item.id}">${item.name}</option>`;
        }
    });
    return `<div class="mb-2">
        <label>Item (${req.item_name})</label>
        <select class="form-control select2 research-item-select" data-req-idx="${idx}">
            ${options}
        </select>
    </div>`;
}

function renderSampleRequirementSlot(req, idx) {
    // Samples from group inventory or pack matching sample_tag and requires_researched
    let options = '<option value="">Select Sample</option>';
    (availableSamples || []).forEach(function(sample) {
        let hasTag = !req.sample_tag || (sample.tags && sample.tags.includes(req.sample_tag));
        let researchedOk = !req.requires_researched || sample.is_researched;
        if (hasTag && researchedOk) {
            options += `<option value="${sample.id}">${sample.name}${sample.is_researched ? ' (Researched)' : ''}</option>`;
        }
    });
    return `<div class="mb-2">
        <label>Sample (${req.sample_tag}${req.requires_researched ? ', Researched' : ''})</label>
        <select class="form-control select2 research-sample-select" data-req-idx="${idx}">
            ${options}
        </select>
    </div>`;
}

// Track selected exotics for each research card
function getResearchCardExoticSelections($card) {
    const selections = [];
    $card.find('.research-exotic-select').each(function() {
        selections.push($(this).val());
    });
    return selections;
}

// Mark exotic select as valid/invalid on change
$(document).on('change', '.research-exotic-select', function() {
    const $select = $(this);
    setSelect2Invalid($select, !$select.val());
    // Optionally, update hidden field for form submission
    const $card = $select.closest('.research-assist-card');
    syncResearchExoticSelections($card);
});

// Store selected exotics in hidden field for form submission
function syncResearchExoticSelections($card) {
    // Remove any previous hidden fields
    $card.find('input[name="research_exotics[]"]').remove();
    $card.find('.research-exotic-select').each(function() {
        const val = $(this).val();
        if (val) {
            $card.append('<input type="hidden" name="research_exotics[]" value="' + val + '">');
        }
    });
}

// Validate all required exotics are selected before submission
function validateResearchExoticsStep() {
    let valid = true;
    $('.research-assist-card').each(function() {
        const $card = $(this);
        $card.find('.research-exotic-select').each(function() {
            const $select = $(this);
            if (!$select.val()) {
                setSelect2Invalid($select, true);
                valid = false;
            } else {
                setSelect2Invalid($select, false);
            }
        });
    });
    return valid;
}

function collectResearchData() {
    const researchData = [];
    $('#research-projects-list .research-assist-card').each(function() {
        const $card = $(this);
        const research = {
            project_source: $card.find('.btn-toggle-project-source .btn.active').data('project-source'),
            project_id: $card.find('.research-project-select').val() || $card.find('.research-project-id-input').val(),
            support_target: $card.find('.btn-toggle-support-target .btn.active').data('support-target'),
            support_target_id: $card.find('.support-group-member-select').val() || $card.find('.support-other-id-input').val(),
            contributed_exotics: [],
            contributed_items: [],
            contributed_samples: []
        };
        // Collect contributed exotics
        $card.find('.exotic-requirement-slot').each(function() {
            const $slot = $(this);
            const exoticId = $slot.data('exotic-id');
            const quantity = parseInt($slot.find('.exotic-select').val()) || 0;
            if (quantity > 0) {
                research.contributed_exotics.push({ id: exoticId, quantity: quantity });
            }
        });
        // Collect contributed items
        $card.find('.item-requirement-slot .item-select:checked').each(function() {
            const itemId = $(this).closest('.item-requirement-slot').data('item-id');
            research.contributed_items.push(itemId);
        });
        // Collect contributed samples
        $card.find('.sample-requirement-slot .sample-select:checked').each(function() {
            const sampleId = $(this).closest('.sample-requirement-slot').data('sample-id');
            research.contributed_samples.push(sampleId);
        });
        researchData.push(research);
    });
    // Ensure researchData is not wrapped in an array
    return researchData.length === 1 ? researchData[0] : researchData;
}

$('#downtime-form').on('submit', function() {
    // Remove any previous research hidden inputs
    $('input[name="research"], input[name="research[]"]').remove();
    const researchData = collectResearchData();
    $('<input>').attr({
        type: 'hidden',
        name: 'research[]',
        value: JSON.stringify(researchData)
    }).appendTo(this);
});