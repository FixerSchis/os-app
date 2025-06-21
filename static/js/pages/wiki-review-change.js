document.addEventListener('DOMContentLoaded', function() {
    const removeSectionButtons = document.querySelectorAll('.remove-section-btn');
    const removeSectionModal = new bootstrap.Modal(document.getElementById('removeSectionModal'));
    let sectionIdToRemove = null;
    removeSectionButtons.forEach(button => {
        button.addEventListener('click', function() {
            sectionIdToRemove = this.dataset.sectionId;
            removeSectionModal.show();
        });
    });
    document.getElementById('confirmRemoveSection').addEventListener('click', function() {
        if (sectionIdToRemove) {
            const form = document.querySelector('form');
            const input = document.createElement('input');
            input.type = 'hidden';
            input.name = 'remove_section_id';
            input.value = sectionIdToRemove;
            form.appendChild(input);
            form.submit();
        }
    });
}); 