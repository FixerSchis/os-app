document.addEventListener('DOMContentLoaded', function() {
    const statusFilter = document.getElementById('status-filter');
    const statusRows = document.querySelectorAll('.status-row');
    
    if (statusFilter) {
        statusFilter.addEventListener('change', function() {
            const selectedStatus = this.value;
            
            statusRows.forEach(row => {
                if (row.dataset.status === selectedStatus) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
        });
    }
});

$(document).ready(function() {
    // Initialize Select2
    $('#event-select').select2({
        theme: 'bootstrap4',
        placeholder: 'Select an event...',
        allowClear: true
    });

    // Load available events
    $.get('/events/get_events', {
        has_finished: true,
        has_downtime: false,
        event_type: 'mainline'
    }, function(data) {
        const events = data.events;
        const select = $('#event-select');
        
        events.forEach(function(event) {
            const option = new Option(
                `Event ${event.event_number} - ${event.name} (Ended: ${event.end_date})`,
                event.id,
                false,
                false
            );
            select.append(option);
        });
        
        // Trigger change to update Select2
        select.trigger('change');
    });
}); 