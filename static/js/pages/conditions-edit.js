document.addEventListener('DOMContentLoaded', function() {
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
