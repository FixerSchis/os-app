document.addEventListener('DOMContentLoaded', function() {
    if (window.jQuery) {
        initRuleTagSelects();
    }
    const stagesContainer = document.getElementById('stages-container');
    const addStageButton = document.getElementById('add-stage');
    let stageCount = parseInt(document.getElementById('stage-count').value) || 0;

    function createStageSection(stageNumber) {
        const template = `
            <div class="stage-section card mb-4">
                <div class="card-body">
                    <h5 class="card-title">Stage ${stageNumber}</h5>
                    <input type="hidden" name="stages" value="${stageNumber}">

                    <div class="form-group mb-3">
                        <label for="rp_effect_${stageNumber}">RP Effect</label>
                        <textarea class="form-control" id="rp_effect_${stageNumber}" name="rp_effect_${stageNumber}" rows="3" required></textarea>
                    </div>

                    <div class="form-group mb-3">
                        <label for="diagnosis_${stageNumber}">Diagnosis</label>
                        <textarea class="form-control" id="diagnosis_${stageNumber}" name="diagnosis_${stageNumber}" rows="3" required></textarea>
                    </div>

                    <div class="form-group mb-3">
                        <label for="cure_${stageNumber}">Cure</label>
                        <textarea class="form-control" id="cure_${stageNumber}" name="cure_${stageNumber}" rows="3" required></textarea>
                    </div>

                    <div class="form-group mb-3">
                        <label for="duration_${stageNumber}">Duration (events)</label>
                        <input type="number" class="form-control" id="duration_${stageNumber}" name="duration_${stageNumber}" value="0" min="0" required>
                    </div>
                </div>
                <div class="card-footer">
                    <button type="button" class="btn btn-outline-danger remove-stage" data-stage="${stageNumber}">
                        <i class="fas fa-trash"></i> Remove Stage
                    </button>
                </div>
            </div>
        `;

        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = template;
        return tempDiv.firstElementChild;
    }

    if (addStageButton) {
        addStageButton.addEventListener('click', function() {
            stageCount++;
            const stageSection = createStageSection(stageCount);
            stagesContainer.appendChild(stageSection);

            // Focus the first textarea of the new stage
            const firstTextarea = stageSection.querySelector('textarea');
            if (firstTextarea) {
                firstTextarea.focus();
            }
        });
    }

    const sheetRows = document.getElementById('stage-sheet-value-rows');
    const addSheetValue = document.getElementById('add-stage-sheet-value');
    if (sheetRows && addSheetValue) {
        addSheetValue.addEventListener('click', function() {
            const index = sheetRows.querySelectorAll('.stage-sheet-value-row').length;
            const row = document.createElement('div');
            row.className = 'row mb-2 stage-sheet-value-row';
            row.innerHTML = `
                <div class="col-md-3">
                    <label class="sr-only" for="stage_sheet_id_new_${index}">ID</label>
                    <input class="form-control" id="stage_sheet_id_new_${index}" name="stage_sheet_id[]" placeholder="ID, such as will">
                </div>
                <div class="col-md-5">
                    <label class="sr-only" for="stage_sheet_description_new_${index}">Description</label>
                    <input class="form-control" id="stage_sheet_description_new_${index}" name="stage_sheet_description[]" placeholder="Description, such as Will Points">
                </div>
                <div class="col-md-2">
                    <label class="sr-only" for="stage_sheet_value_new_${index}">Value per stage</label>
                    <input type="number" class="form-control" id="stage_sheet_value_new_${index}" name="stage_sheet_value[]" value="1" placeholder="Per stage">
                </div>
                <div class="col-md-2">
                    <button type="button" class="btn btn-danger btn-sm remove-stage-sheet-value" aria-label="Remove sheet value">Remove</button>
                </div>
            `;
            sheetRows.appendChild(row);
            row.querySelector('input').focus();
        });
        sheetRows.addEventListener('click', function(e) {
            const button = e.target.closest('.remove-stage-sheet-value');
            if (button) {
                button.closest('.stage-sheet-value-row').remove();
            }
        });
    }

    if (stagesContainer) {
        stagesContainer.addEventListener('click', function(e) {
            if (e.target.closest('.remove-stage')) {
                const stageSection = e.target.closest('.stage-section');
                if (stageSection) {
                    // Add a fade-out animation
                    stageSection.style.transition = 'opacity 0.3s ease-out';
                    stageSection.style.opacity = '0';

                    // Remove the element after the animation
                    setTimeout(() => {
                        stageSection.remove();
                    }, 300);
                }
            }
        });
    }
});
