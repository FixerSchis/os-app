// Stage details toggle functionality
document.addEventListener('DOMContentLoaded', function() {
    document.body.addEventListener('click', function(event) {
        var btn = event.target.closest('.stage-details-toggle');
        if (!btn) return;
        var icon = btn.querySelector('i.fas');
        var targetId = btn.getAttribute('data-details-target');
        var target = document.querySelector(targetId);
        console.log('Details button clicked:', btn, 'Target:', target);
        if (!target) return;
        if (target.style.display === 'none' || target.style.display === '') {
            target.style.display = 'block';
            icon.classList.remove('fa-chevron-down');
            icon.classList.add('fa-chevron-up');
        } else {
            target.style.display = 'none';
            icon.classList.remove('fa-chevron-up');
            icon.classList.add('fa-chevron-down');
        }
    });
});

// Progress bar initialization
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.progress-bar').forEach(function(bar) {
        var percent = parseInt(bar.getAttribute('data-progress'));
        bar.style.width = percent + '%';
    });
});

// Initialize Select2 for sample selection
document.addEventListener('DOMContentLoaded', function() {
    const sampleSelect = document.getElementById('add_sample_id');
    if (sampleSelect) {
        $(sampleSelect).select2({
            placeholder: 'Choose a sample...',
            allowClear: true,
            width: '100%'
        }).on('select2:open', function() {
            // Apply dark mode styling if dark mode is active
            const isDarkMode = document.documentElement.getAttribute('data-theme') === 'dark';
            if (isDarkMode) {
                $('.select2-container--bootstrap-5').addClass('select2-dark');
                $('.select2-dropdown').addClass('select2-dark');
            }
        });
    }
});

// Initialize species filter
document.addEventListener('DOMContentLoaded', function() {
    // Get user role information from the script tag
    const jsVariables = document.getElementById('js-variables');
    if (jsVariables) {
        try {
            const userInfo = JSON.parse(jsVariables.textContent);
            const userIsAdmin = userInfo.userIsAdmin || false;
            const userIsNpc = userInfo.userIsNpc || false;

            // Initialize the species filter
            initSpeciesFilter('faction', 'species_id', userIsAdmin, userIsNpc);
            initCreationChoiceTooltips();
            showStartingSkillPicks();
        } catch (e) {
            console.error('Error parsing user info:', e);
            // Fallback: initialize without admin privileges
            initSpeciesFilter('faction', 'species_id', false, false);
            initCreationChoiceTooltips();
            showStartingSkillPicks();
        }
    } else {
        // Fallback: initialize without admin privileges
        initSpeciesFilter('faction', 'species_id', false, false);
        initCreationChoiceTooltips();
        showStartingSkillPicks();
    }
});

function currentSpeciesId() {
    const speciesSelect = document.getElementById('species_id');
    if (speciesSelect && speciesSelect.value) {
        return speciesSelect.value;
    }
    const hidden = document.querySelector('input[name="species_id"]');
    return hidden ? hidden.value : '';
}

function showStartingSkillPicks() {
    const speciesId = String(currentSpeciesId());
    document.querySelectorAll('.starting-skill-panel, .starting-condition-panel').forEach(function(panel) {
        const match = panel.dataset.speciesId === speciesId;
        panel.style.display = match ? '' : 'none';
        panel.dataset.active = match ? 'true' : 'false';
        panel.querySelectorAll('input, select').forEach(function(input) {
            input.disabled = !match;
        });
    });
    refreshCreationChoices();
}

function initCreationChoiceTooltips() {
    if (typeof bootstrap === 'undefined' || !bootstrap.Tooltip) {
        return;
    }
    document.querySelectorAll('#character-creation-choices [data-bs-toggle="tooltip"]').forEach(
        function(el) {
            if (!bootstrap.Tooltip.getInstance(el)) {
                new bootstrap.Tooltip(el, { container: 'body' });
            }
        }
    );
}

function refreshCreationChoices() {
    const section = document.getElementById('character-creation-choices');
    if (!section) {
        return;
    }
    const active = section.querySelector('.creation-choice-panel[data-active="true"]');
    section.style.display = active ? '' : 'none';
}

function reindexCharacterAbilities() {
    document.querySelectorAll('#character-abilities-list .character-ability-block').forEach(
        function(block, index) {
            block.querySelectorAll('[name], [id], label[for]').forEach(function(el) {
                ['name', 'id', 'htmlFor'].forEach(function(attr) {
                    const value = el[attr];
                    if (value) {
                        el[attr] = value.replace(/_\d+$/, '_' + index);
                    }
                });
            });
        }
    );
}

document.addEventListener('click', function(event) {
    const addButton = event.target.closest('#add-character-ability');
    if (addButton) {
        const list = document.getElementById('character-abilities-list');
        const template = document.getElementById('character-ability-template');
        list.appendChild(template.content.cloneNode(true));
        reindexCharacterAbilities();
        return;
    }
    const removeButton = event.target.closest('.remove-character-ability');
    if (!removeButton) {
        return;
    }
    const block = removeButton.closest('.character-ability-block');
    if (block) {
        block.remove();
        reindexCharacterAbilities();
    }
});

document.addEventListener('change', function(event) {
    if (event.target && event.target.id === 'species_id') {
        showStartingSkillPicks();
    }
    if (!event.target || !event.target.classList.contains('starting-skill-pick')) {
        return;
    }
    if (!event.target.checked) {
        return;
    }
    const skillType = event.target.dataset.skillType;
    const max = parseInt(event.target.dataset.max, 10);
    const panel = event.target.closest('.starting-skill-panel');
    const checked = panel.querySelectorAll(
        '.starting-skill-pick[data-skill-type="' + skillType + '"]:checked'
    );
    if (checked.length > max) {
        event.target.checked = false;
    }
});
