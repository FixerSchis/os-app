function initSpeciesFilter(factionSelectId, speciesSelectId, userIsAdmin, userIsNpc) {
    const factionSelect = document.getElementById(factionSelectId);
    const speciesSelect = document.getElementById(speciesSelectId);
    if (!factionSelect || !speciesSelect) return;

    function filterSpecies() {
        if (userIsAdmin || userIsNpc) {
            // Show all species for admins and NPCs
            Array.from(speciesSelect.options).forEach(option => {
                option.style.display = '';
            });
            return;
        }

        const selectedFaction = factionSelect.value;

        // If no faction is selected, hide all species options except the placeholder
        if (!selectedFaction) {
            Array.from(speciesSelect.options).forEach(option => {
                if (!option.value) {
                    option.style.display = ''; // Show placeholder
                } else {
                    option.style.display = 'none'; // Hide all species
                }
            });
            // Reset species selection when no faction is selected
            speciesSelect.value = '';
            return;
        }

        // Filter species based on selected faction
        Array.from(speciesSelect.options).forEach(option => {
            if (!option.value) {
                option.style.display = ''; // Always show placeholder
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
                option.style.display = 'none'; // Hide on error for safety
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
