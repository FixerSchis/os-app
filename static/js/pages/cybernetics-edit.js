$(document).ready(function() {
    const scienceDowntimeInput = document.getElementById('adds_science_downtime');
    const scienceTypeGroup = document.getElementById('science_type_group');
    const scienceTypeSelect = document.getElementById('science_type');

    function toggleScienceType() {
        if (parseInt(scienceDowntimeInput.value) > 0) {
            scienceTypeGroup.style.display = 'block';
            scienceTypeSelect.required = true;
        } else {
            scienceTypeGroup.style.display = 'none';
            scienceTypeSelect.required = false;
            scienceTypeSelect.value = '';
        }
    }

    scienceDowntimeInput.addEventListener('change', toggleScienceType);
    toggleScienceType(); // Initial state
});
