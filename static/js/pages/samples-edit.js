$(document).ready(function() {
    // Initialize Select2 for tags
    $('#tags').select2({
        theme: "bootstrap-5",
        tags: true,
        tokenSeparators: [',', ' '],
        placeholder: 'Select or type to add tags...'
    });

    $('#type').select2({
        theme: "bootstrap-5",
        placeholder: 'Select Type'
    });
}); 