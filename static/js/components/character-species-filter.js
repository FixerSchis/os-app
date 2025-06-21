function initSpeciesFilter(factionSelectId, speciesSelectId, userIsAdmin, userIsNpc) {
    const factionSelect = document.getElementById(factionSelectId);
    const speciesSelect = document.getElementById(speciesSelectId);
    if (!factionSelect || !speciesSelect) return;

    function filterSpecies() {
        if (userIsAdmin || userIsNpc) {
            // Show all species
            Array.from(speciesSelect.options).forEach(option => {
                option.style.display = '';
            });
            return;
        }
        const selectedFaction = factionSelect.value;
        Array.from(speciesSelect.options).forEach(option => {
            if (!option.value) {
                option.style.display = '';
                return;
            }
            try {
                const permittedFactions = JSON.parse(option.getAttribute('data-factions'));
                if (permittedFactions.includes(parseInt(selectedFaction))) {
                    option.style.display = '';
                } else {
                    option.style.display = 'none';
                }
            } catch (e) {
                console.error('Error parsing permitted factions:', e);
                option.style.display = '';
            }
        });
        // If the currently selected species is not permitted, reset selection
        if (speciesSelect.selectedOptions.length && speciesSelect.selectedOptions[0].style.display === 'none') {
            speciesSelect.value = '';
        }
    }

    factionSelect.addEventListener('change', filterSpecies);
    // Initial filter
    filterSpecies();
}
