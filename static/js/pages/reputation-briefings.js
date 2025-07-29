// Reputation Briefings JavaScript

let levelCounter = 0;

document.addEventListener('DOMContentLoaded', function() {
    // Initialize Select2
    $('.select2').select2({
        theme: 'bootstrap4',
        width: '100%'
    });

    // Add level button functionality
    const addLevelBtn = document.getElementById('add-level');
    if (addLevelBtn) {
        addLevelBtn.addEventListener('click', function() {
            addLevel();
        });
    }

    // Form validation
    const form = document.getElementById('briefing-form');
    if (form) {
        form.addEventListener('submit', function(e) {
            if (!validateForm()) {
                e.preventDefault();
                return false;
            }
        });
    }
});

function addLevel(reputationRequired = '', content = '') {
    const container = document.getElementById('levels-container');
    const levelDiv = document.createElement('div');
    levelDiv.className = 'level-form';
    levelDiv.id = `level-${levelCounter}`;

    levelDiv.innerHTML = `
        <div class="d-flex justify-content-between align-items-center mb-3">
            <h6>Level ${levelCounter + 1}</h6>
            <button type="button" class="btn btn-sm btn-outline-danger btn-remove" onclick="removeLevel(${levelCounter})">
                <i class="fas fa-trash"></i> Remove
            </button>
        </div>
        <div class="row">
            <div class="col-md-3">
                <div class="form-group">
                    <label for="reputation_required_${levelCounter}">Reputation Required *</label>
                    <input type="number"
                           name="reputation_required_${levelCounter}"
                           id="reputation_required_${levelCounter}"
                           class="form-control"
                           min="1"
                           value="${reputationRequired}"
                           required>
                    <small class="form-text text-muted">Minimum reputation required for this level</small>
                </div>
            </div>
            <div class="col-md-9">
                <div class="form-group">
                    <label for="content_${levelCounter}">Content *</label>
                    <textarea name="content_${levelCounter}"
                              id="content_${levelCounter}"
                              class="form-control"
                              rows="4"
                              required
                              placeholder="Enter the briefing content for this reputation level...">${content}</textarea>
                    <small class="form-text text-muted">The briefing content for characters with this reputation or higher</small>
                </div>
            </div>
        </div>
    `;

    container.appendChild(levelDiv);
    levelCounter++;

    // Update the add level button text
    updateAddLevelButton();
}

function removeLevel(levelIndex) {
    const levelDiv = document.getElementById(`level-${levelIndex}`);
    if (levelDiv) {
        levelDiv.remove();
        updateAddLevelButton();
    }
}

function updateAddLevelButton() {
    const addLevelBtn = document.getElementById('add-level');
    if (addLevelBtn) {
        const levelCount = document.querySelectorAll('.level-form').length;
        addLevelBtn.innerHTML = `<i class="fas fa-plus"></i> Add Level (${levelCount + 1})`;
    }
}

function validateForm() {
    // Check if at least one level exists
    const levelForms = document.querySelectorAll('.level-form');
    if (levelForms.length === 0) {
        alert('At least one level is required.');
        return false;
    }

    // Validate each level
    for (let i = 0; i < levelCounter; i++) {
        const reputationInput = document.getElementById(`reputation_required_${i}`);
        const contentInput = document.getElementById(`content_${i}`);

        if (reputationInput && contentInput) {
            const reputation = reputationInput.value.trim();
            const content = contentInput.value.trim();

            if (reputation && content) {
                // Check if reputation is a valid number
                if (isNaN(reputation) || parseInt(reputation) < 1) {
                    alert(`Reputation required must be a number greater than 0 for level ${i + 1}.`);
                    return false;
                }
            } else if (reputation || content) {
                // If one field is filled but not the other
                alert(`Both reputation required and content must be filled for level ${i + 1}.`);
                return false;
            }
        }
    }

    return true;
}

// Auto-resize textareas
document.addEventListener('input', function(e) {
    if (e.target.tagName === 'TEXTAREA') {
        e.target.style.height = 'auto';
        e.target.style.height = e.target.scrollHeight + 'px';
    }
});
