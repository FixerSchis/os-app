$(document).ready(function() {
    // Initialize Select2 for backup selection
    $('#backup-select').select2({
        placeholder: 'Select a backup to restore...',
        allowClear: true
    });

    // Handle backup selection
    $('#backup-select').on('change', function() {
        const selectedValue = $(this).val();
        $('#restore-backup-btn').prop('disabled', !selectedValue);
    });

    // Create backup functionality
    $('#create-backup-btn').on('click', function() {
        const btn = $(this);
        btn.addClass('loading');
        btn.prop('disabled', true);

        $.ajax({
            url: '/tools/database/create-backup',
            method: 'POST',
            success: function(response) {
                if (response.success) {
                    showAlert('Backup created successfully: ' + response.filename, 'success');
                    // Reload page to update backup list
                    setTimeout(function() {
                        location.reload();
                    }, 1500);
                } else {
                    showAlert('Error creating backup: ' + response.error, 'error');
                }
            },
            error: function(xhr) {
                const response = xhr.responseJSON || {};
                showAlert('Error creating backup: ' + (response.error || 'Unknown error'), 'error');
            },
            complete: function() {
                btn.removeClass('loading');
                btn.prop('disabled', false);
            }
        });
    });

    // Restore backup functionality
    $('#restore-backup-btn').on('click', function() {
        const selectedBackup = $('#backup-select').val();
        if (!selectedBackup) {
            showAlert('Please select a backup to restore', 'error');
            return;
        }

        if (!confirm('Are you sure you want to restore this backup? This will overwrite the current database.')) {
            return;
        }

        const btn = $(this);
        btn.addClass('loading');
        btn.prop('disabled', true);

        $.ajax({
            url: '/tools/database/restore-backup',
            method: 'POST',
            data: {
                backup_filename: selectedBackup
            },
            success: function(response) {
                if (response.success) {
                    showAlert('Database restored successfully', 'success');
                    // Reload page to reflect changes
                    setTimeout(function() {
                        location.reload();
                    }, 1500);
                } else {
                    showAlert('Error restoring backup: ' + response.error, 'error');
                }
            },
            error: function(xhr) {
                const response = xhr.responseJSON || {};
                showAlert('Error restoring backup: ' + (response.error || 'Unknown error'), 'error');
            },
            complete: function() {
                btn.removeClass('loading');
                btn.prop('disabled', false);
            }
        });
    });

    function showAlert(message, type) {
        const alertClass = type === 'success' ? 'alert-success' : 'alert-error';
        const alert = $('<div class="alert ' + alertClass + '">' + message + '</div>');

        $('.container').prepend(alert);

        // Auto-remove after 5 seconds
        setTimeout(function() {
            alert.fadeOut(function() {
                $(this).remove();
            });
        }, 5000);
    }
});
