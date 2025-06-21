document.addEventListener('DOMContentLoaded', function() {
    var allConditionsInput = document.getElementById('all-conditions-json');
    if (!allConditionsInput) return;
    var allConditions = [];
    try {
        allConditions = JSON.parse(allConditionsInput.value);
    } catch (e) {
        return;
    }
    var selectCondition = document.getElementById('add_condition_id');
    var selectStage = document.getElementById('add_condition_stage');
    var inputDuration = document.getElementById('add_condition_duration');
    if (selectCondition && selectStage) {
        selectCondition.addEventListener('change', function() {
            var condId = parseInt(this.value);
            selectStage.innerHTML = '<option value="">Stage...</option>';
            if (!condId) return;
            var cond = allConditions.find(function(c) { return c.id === condId; });
            if (cond && cond.stages) {
                cond.stages.sort(function(a, b) { return a.stage_number - b.stage_number; }).forEach(function(stage) {
                    var opt = document.createElement('option');
                    opt.value = stage.stage_number;
                    opt.textContent = 'Stage ' + stage.stage_number;
                    selectStage.appendChild(opt);
                });
            }
            // Reset duration field
            if (inputDuration) inputDuration.value = '';
        });
        selectStage.addEventListener('change', function() {
            var condId = parseInt(selectCondition.value);
            var stageNum = parseInt(this.value);
            if (!condId || !stageNum) return;
            var cond = allConditions.find(function(c) { return c.id === condId; });
            if (cond && cond.stages) {
                var stage = cond.stages.find(function(s) { return s.stage_number === stageNum; });
                if (stage && inputDuration) {
                    inputDuration.value = stage.duration;
                }
            }
        });
    }
}); 