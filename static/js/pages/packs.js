// Packs page JavaScript

document.addEventListener('DOMContentLoaded', function() {
    let currentCharacterId = null;
    let currentGroupId = null;
    let currentEventId = document.getElementById('event-id-data').getAttribute('data-event-id');

    // Load lookup data from data attributes
    const lookupDataElement = document.getElementById('lookup-data');
    const itemBlueprints = JSON.parse(lookupDataElement.getAttribute('data-item-blueprints') || '{}');
    const items = JSON.parse(lookupDataElement.getAttribute('data-items') || '{}');
    const exoticSubstances = JSON.parse(lookupDataElement.getAttribute('data-exotic-substances') || '{}');
    const medicaments = JSON.parse(lookupDataElement.getAttribute('data-medicaments') || '{}');
    const samples = JSON.parse(lookupDataElement.getAttribute('data-samples') || '{}');
    const characterIncomeEc = JSON.parse(lookupDataElement.getAttribute('data-character-income-ec') || '0');

    // Print functions
    window.printCharacterSheets = function() {
        const url = `/events/${currentEventId}/packs/print/character-sheets`;
        window.open(url, '_blank');
        bootstrap.Modal.getInstance(document.getElementById('printModal')).hide();
    };

    window.printCharacterIdBadges = function() {
        const url = `/events/${currentEventId}/packs/print/character-id-badges`;
        window.open(url, '_blank');
        bootstrap.Modal.getInstance(document.getElementById('printModal')).hide();
    };

    window.printItems = function() {
        const url = `/events/${currentEventId}/packs/print/items`;
        window.open(url, '_blank');
        bootstrap.Modal.getInstance(document.getElementById('printModal')).hide();
    };

    window.printMedicaments = function() {
        const url = `/events/${currentEventId}/packs/print/medicaments`;
        window.open(url, '_blank');
        bootstrap.Modal.getInstance(document.getElementById('printModal')).hide();
    };

    window.viewCharacterPack = function(button) {
        currentCharacterId = button.getAttribute('data-character-id');
        const packDataElement = document.getElementById(`pack-data-${currentCharacterId}`);
        if (!packDataElement) return;
        const packData = packDataElement.getAttribute('data-pack');
        const userName = packDataElement.getAttribute('data-user-name');
        const characterName = packDataElement.getAttribute('data-character-name');
        const userId = packDataElement.getAttribute('data-user-id');
        const characterId = packDataElement.getAttribute('data-character-id');
        if (!packData) return;
        let packDataObj;
        try { packDataObj = JSON.parse(packData); } catch (e) { return; }
        // Update modal title
        const modalTitle = document.querySelector('#characterPackModal .modal-title');
        modalTitle.textContent = `${userName}, ${characterName}, ${userId}.${characterId}`;
        // Build content
        let content = '<div class="row">' +
            '<div class="col-md-6">' +
                '<h6>Pack Contents</h6>';
        // Energy Chits
        content += '<div class="mb-3">' +
            '<label class="form-check-label">' +
                '<input type="checkbox" class="form-check-input" id="energy_chits" ' + (packDataObj.energy_chits ? 'checked' : '') + '>' +
                'Energy Chits (' + characterIncomeEc + ')' +
            '</label>' +
        '</div>';
        // Items
        if (packDataObj.items && packDataObj.items.length > 0) {
            content += '<div class="mb-3">' +
                '<h6>Items (' + packDataObj.items.length + ')</h6>' +
                '<ul class="list-group mt-2">';
            packDataObj.items.forEach(function(itemId) {
                const item = items[itemId];
                if (item) {
                    content += '<li class="list-group-item">' +
                        '<input type="checkbox" class="form-check-input me-2" id="item_' + itemId + '">' +
                        item.blueprint_name + ' (' + item.full_code + ')' +
                    '</li>';
                }
            });
            content += '</ul></div>';
        }
        // Samples
        if (packDataObj.samples && packDataObj.samples.length > 0) {
            content += '<div class="mb-3">' +
                '<h6>Samples (' + packDataObj.samples.length + ')</h6>' +
                '<ul class="list-group mt-2">';
            packDataObj.samples.forEach(function(sampleId) {
                const sample = samples[sampleId];
                if (sample) {
                    content += '<li class="list-group-item">' +
                        '<input type="checkbox" class="form-check-input me-2" id="sample_' + sampleId + '">' +
                        sample.name +
                    '</li>';
                }
            });
            content += '</ul></div>';
        }
        // Exotics
        if (packDataObj.exotics && packDataObj.exotics.length > 0) {
            content += '<div class="mb-3">' +
                '<h6>Exotics (' + packDataObj.exotics.length + ')</h6>' +
                '<ul class="list-group mt-2">';
            packDataObj.exotics.forEach(function(exoticId) {
                const exotic = exoticSubstances[exoticId];
                if (exotic) {
                    const amount = packDataObj.completion[`exotic_${exoticId}_amount`] || 1;
                    content += '<li class="list-group-item">' +
                        '<input type="checkbox" class="form-check-input me-2" id="exotic_' + exoticId + '">' +
                        exotic.name + ' (' + amount + ')' +
                    '</li>';
                }
            });
            content += '</ul></div>';
        }
        // Medicaments
        if (packDataObj.medicaments && packDataObj.medicaments.length > 0) {
            content += '<div class="mb-3">' +
                '<h6>Medicaments (' + packDataObj.medicaments.length + ')</h6>' +
                '<ul class="list-group mt-2">';
            packDataObj.medicaments.forEach(function(medicamentId) {
                const medicament = medicaments[medicamentId];
                if (medicament) {
                    const amount = packDataObj.completion[`medicament_${medicamentId}_amount`] || 1;
                    content += '<li class="list-group-item">' +
                        '<input type="checkbox" class="form-check-input me-2" id="medicament_' + medicamentId + '">' +
                        medicament.name + ' (' + amount + ')' +
                    '</li>';
                }
            });
            content += '</ul></div>';
        }
        content += '</div>' +
            '<div class="col-md-6">' +
                '<h6>Documents</h6>' +
                '<div class="mb-3">' +
                    '<label class="form-check-label">' +
                        '<input type="checkbox" class="form-check-input" id="character_sheet" ' + (packDataObj.completion && packDataObj.completion.character_sheet ? 'checked' : '') + '>' +
                        'Character Sheet' +
                    '</label>' +
                '</div>' +
                '<div class="mb-3">' +
                    '<label class="form-check-label">' +
                        '<input type="checkbox" class="form-check-input" id="character_id_badge" ' + (packDataObj.completion && packDataObj.completion.character_id_badge ? 'checked' : '') + '>' +
                        'Character ID Badge' +
                    '</label>' +
                '</div>' +
            '</div>' +
        '</div>';
        document.getElementById('characterPackContent').innerHTML = content;
        // Pre-check checkboxes after content is set
        if (packDataObj.completion) {
            if (document.getElementById('energy_chits')) {
                document.getElementById('energy_chits').checked = !!packDataObj.completion.energy_chits;
            }
            if (document.getElementById('character_sheet')) {
                document.getElementById('character_sheet').checked = !!packDataObj.completion.character_sheet;
            }
            if (document.getElementById('character_id_badge')) {
                document.getElementById('character_id_badge').checked = !!packDataObj.completion.character_id_badge;
            }
            Object.keys(packDataObj.completion).forEach(function(key) {
                if (key.startsWith('item_') || key.startsWith('sample_') || key.startsWith('exotic_') || key.startsWith('medicament_')) {
                    const checkbox = document.getElementById(key);
                    if (checkbox) {
                        checkbox.checked = !!packDataObj.completion[key];
                    }
                }
            });
        }
        new bootstrap.Modal(document.getElementById('characterPackModal')).show();
    };

    window.viewGroupPack = function(button) {
        const groupId = button.getAttribute('data-group-id');
        currentGroupId = groupId;
        const packDataElement = document.getElementById(`group-pack-data-${groupId}`);
        if (!packDataElement) return;
        const packData = packDataElement.getAttribute('data-pack');
        const charactersData = packDataElement.getAttribute('data-characters');
        if (!packData || !charactersData) return;
        let packDataObj, characters;
        try { packDataObj = JSON.parse(packData); characters = JSON.parse(charactersData); } catch (e) { return; }
        let content = '<div class="mb-3">' +
            '<h6>Group Members Attending</h6>' +
            '<ul class="list-group">';
        characters.forEach(function(char) {
            content += '<li class="list-group-item">' +
                char.user.first_name + ' ' + char.user.surname + ' - ' + char.character.name + ' (' + char.species.name + ')' +
            '</li>';
        });
        content += '</ul></div>';
        if (!packDataObj.is_generated) {
            content += '<div class="mb-3">' +
                '<button class="btn btn-warning" onclick="generateGroupPack()">Generate Pack Contents</button>' +
            '</div>';
        } else {
            content += '<div class="row">' +
                '<div class="col-md-6">' +
                    '<h6>Pack Contents</h6>';
            content += '<div class="mb-3">' +
                '<label class="form-check-label">' +
                    '<input type="checkbox" class="form-check-input" id="energy_chits" ' + (packDataObj.energy_chits ? 'checked' : '') + '>' +
                    'Energy Chits (' + characterIncomeEc + ')' +
                '</label>' +
            '</div>';
            if (packDataObj.items && packDataObj.items.length > 0) {
                content += '<div class="mb-3">' +
                    '<h6>Items (' + packDataObj.items.length + ')</h6>' +
                    '<ul class="list-group mt-2">';
                packDataObj.items.forEach(function(itemId) {
                    const item = items[itemId];
                    if (item) {
                        content += '<li class="list-group-item">' +
                            '<input type="checkbox" class="form-check-input me-2" id="item_' + itemId + '">' +
                            item.blueprint_name + ' (' + item.full_code + ')' +
                        '</li>';
                    }
                });
                content += '</ul></div>';
            }
            if (packDataObj.samples && packDataObj.samples.length > 0) {
                content += '<div class="mb-3">' +
                    '<h6>Samples (' + packDataObj.samples.length + ')</h6>' +
                    '<ul class="list-group mt-2">';
                packDataObj.samples.forEach(function(sampleId) {
                    const sample = samples[sampleId];
                    if (sample) {
                        content += '<li class="list-group-item">' +
                            '<input type="checkbox" class="form-check-input me-2" id="sample_' + sampleId + '">' +
                            sample.name +
                        '</li>';
                    }
                });
                content += '</ul></div>';
            }
            if (packDataObj.exotics && packDataObj.exotics.length > 0) {
                content += '<div class="mb-3">' +
                    '<h6>Exotics (' + packDataObj.exotics.length + ')</h6>' +
                    '<ul class="list-group mt-2">';
                packDataObj.exotics.forEach(function(exoticId) {
                    const exotic = exoticSubstances[exoticId];
                    if (exotic) {
                        const amount = packDataObj.completion[`exotic_${exoticId}_amount`] || 1;
                        content += '<li class="list-group-item">' +
                            '<input type="checkbox" class="form-check-input me-2" id="exotic_' + exoticId + '">' +
                            exotic.name + ' (' + amount + ')' +
                        '</li>';
                    }
                });
                content += '</ul></div>';
            }
            if (packDataObj.medicaments && packDataObj.medicaments.length > 0) {
                content += '<div class="mb-3">' +
                    '<h6>Medicaments (' + packDataObj.medicaments.length + ')</h6>' +
                    '<ul class="list-group mt-2">';
                packDataObj.medicaments.forEach(function(medicamentId) {
                    const medicament = medicaments[medicamentId];
                    if (medicament) {
                        const amount = packDataObj.completion[`medicament_${medicamentId}_amount`] || 1;
                        content += '<li class="list-group-item">' +
                            '<input type="checkbox" class="form-check-input me-2" id="medicament_' + medicamentId + '">' +
                            medicament.name + ' (' + amount + ')' +
                        '</li>';
                    }
                });
                content += '</ul></div>';
            }
            content += '</div>' +
            '</div>';
        }
        document.getElementById('groupPackContent').innerHTML = content;
        if (packDataObj.completion) {
            if (document.getElementById('energy_chits')) {
                document.getElementById('energy_chits').checked = !!packDataObj.completion.energy_chits;
            }
            Object.keys(packDataObj.completion).forEach(function(key) {
                if (key.startsWith('item_') || key.startsWith('sample_') || key.startsWith('exotic_') || key.startsWith('medicament_')) {
                    const checkbox = document.getElementById(key);
                    if (checkbox) {
                        checkbox.checked = !!packDataObj.completion[key];
                    }
                }
            });
        }
        new bootstrap.Modal(document.getElementById('groupPackModal')).show();
    };

    window.generateGroupPack = function() {
        fetch(`/events/${currentEventId}/packs/group/${currentGroupId}/generate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const button = document.querySelector(`[data-group-id="${currentGroupId}"]`);
                if (button) {
                    button.setAttribute('data-pack-data', JSON.stringify(data.pack));
                    viewGroupPack(button);
                }
            }
        })
        .catch(error => {
            alert('Failed to generate group pack');
        });
    };

    window.saveCharacterPack = function() {
        const completion = {};
        completion.energy_chits = document.getElementById('energy_chits')?.checked || false;
        completion.character_sheet = document.getElementById('character_sheet')?.checked || false;
        completion.character_id_badge = document.getElementById('character_id_badge')?.checked || false;
        document.querySelectorAll('input[id^="item_"]').forEach(function(checkbox) {
            completion[checkbox.id] = checkbox.checked;
        });
        document.querySelectorAll('input[id^="sample_"]').forEach(function(checkbox) {
            completion[checkbox.id] = checkbox.checked;
        });
        document.querySelectorAll('input[id^="exotic_"]').forEach(function(checkbox) {
            completion[checkbox.id] = checkbox.checked;
        });
        document.querySelectorAll('input[id^="medicament_"]').forEach(function(checkbox) {
            completion[checkbox.id] = checkbox.checked;
        });
        fetch(`/events/${currentEventId}/packs/character/${currentCharacterId}/update`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ completion })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                location.reload();
            } else {
                alert('Failed to save pack progress');
            }
        })
        .catch(error => {
            alert('Failed to save pack progress');
        });
    };

    window.saveGroupPack = function() {
        const completion = {};
        completion.energy_chits = document.getElementById('energy_chits')?.checked || false;
        document.querySelectorAll('#groupPackContent input[id^="item_"]').forEach(function(checkbox) {
            completion[checkbox.id] = checkbox.checked;
        });
        document.querySelectorAll('#groupPackContent input[id^="sample_"]').forEach(function(checkbox) {
            completion[checkbox.id] = checkbox.checked;
        });
        document.querySelectorAll('#groupPackContent input[id^="exotic_"]').forEach(function(checkbox) {
            completion[checkbox.id] = checkbox.checked;
        });
        document.querySelectorAll('#groupPackContent input[id^="medicament_"]').forEach(function(checkbox) {
            completion[checkbox.id] = checkbox.checked;
        });
        fetch(`/events/${currentEventId}/packs/group/${currentGroupId}/update`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ completion: completion })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                bootstrap.Modal.getInstance(document.getElementById('groupPackModal')).hide();
                location.reload();
            }
        })
        .catch(error => {
            alert('Failed to save group pack');
        });
    };
});
