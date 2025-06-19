// Reputation Step JS
$(document).ready(function() {
    // --- Reputation Step: Load saved data ---
    let packReputation = $('#downtime-form').data('pack-reputation');
    if (typeof packReputation === 'string') {
        try {
            packReputation = JSON.parse(packReputation || '[]');
        } catch (e) {
            packReputation = [];
        }
    } else {
        packReputation = packReputation || [];
    }
    if (packReputation.length > 0) {
        // Only one question per downtime, so use the first
        const rep = packReputation[0];
        if (rep && typeof rep === 'object') {
            if (rep.faction_id) {
                $('#reputation-faction-select').val(rep.faction_id.toString());
            }
            if (rep.question) {
                $('#reputation-question').val(rep.question);
            }
        }
    }
});

// Save reputation step on form submit
$('#downtime-form').on('submit', function() {
    // Remove any previous reputation hidden inputs
    $('input[name="reputation"], input[name="reputation[]"]').remove();
    const factionId = $('#reputation-faction-select').val();
    const question = $('#reputation-question').val();
    if (factionId && question) {
        const repObj = { faction_id: factionId, question: question };
        $('<input>').attr({
            type: 'hidden',
            name: 'reputation[]',
            value: JSON.stringify(repObj)
        }).appendTo(this);
    }
}); 