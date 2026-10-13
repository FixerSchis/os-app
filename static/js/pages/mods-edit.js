window.addEventListener('DOMContentLoaded', function() {
    $('#item_types').select2({
        theme: 'bootstrap-5',
        width: '100%',
        placeholder: 'Select item types',
        allowClear: true
    });
    $('#required_skills, #granted_by_skills').select2({
        theme: 'bootstrap-5',
        width: '100%',
        placeholder: 'Select skills',
        allowClear: true
    });
});
