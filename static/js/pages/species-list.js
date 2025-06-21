$(document).ready(function() {
    // Initialize select2
    $('#faction-filter').select2({
        theme: 'bootstrap-5',
        width: '100%',
        placeholder: 'Filter by faction...',
        allowClear: true
    });

    // Filter function
    function filterSpecies() {
        var selectedFaction = $('#faction-filter').val();
        
        if (!selectedFaction) {
            // Show all species if no faction is selected
            $('.species-row').show();
            return;
        }

        // Convert selectedFaction to number for comparison
        selectedFaction = parseInt(selectedFaction);

        $('.species-row').each(function() {
            var factions = $(this).data('factions');
            if (factions.includes(selectedFaction)) {
                $(this).show();
            } else {
                $(this).hide();
            }
        });
    }

    // Bind filter function to select change
    $('#faction-filter').on('change', filterSpecies);
}); 