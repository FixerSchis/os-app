// Events purchase page JavaScript functionality

// Global variables - will be initialized from template data
let PRICES = {};
let cart = [];
let validationTimeout = null;
let eventId = '';
let hasMultipleChars = false;
let currentUserId = '';
let currentUserName = '';
let singleActiveCharacterPk = '';
let singleActiveCharacterName = '';
let activeCharacterId = '';
let lastFetchedTicket = null;
let userEventStatus = {}; // To store { userId: { has_adult_ticket, has_crew_ticket } }
let isEditingExistingTicket = false; // Track if we're editing an existing ticket

// URL endpoints - will be set from template
let validateCharacterUrl = '';
let getUserEventStatusUrl = '';
let characterGroupStatusUrl = '';
let getCharacterTicketUrl = '';
let getUserTicketUrl = '';

// Ticket type values - will be set from template
let ticketTypeValues = {};

// Initialize the purchase page functionality
function initializePurchasePage(config) {
    // Set configuration values from template
    PRICES = config.prices;
    eventId = config.eventId;
    hasMultipleChars = config.hasMultipleChars;
    currentUserId = config.currentUserId;
    currentUserName = config.currentUserName;
    singleActiveCharacterPk = config.singleActiveCharacterPk;
    singleActiveCharacterName = config.singleActiveCharacterName;
    activeCharacterId = config.activeCharacterId;
    validateCharacterUrl = config.validateCharacterUrl;
    getUserEventStatusUrl = config.getUserEventStatusUrl;
    characterGroupStatusUrl = config.characterGroupStatusUrl;
    getCharacterTicketUrl = config.getCharacterTicketUrl;
    getUserTicketUrl = config.getUserTicketUrl;
    ticketTypeValues = config.ticketTypeValues;

    // Pre-fetch status for the current user
    fetchUserEventStatus(currentUserId);

    // Set up event listeners
    setupEventListeners();
}

function setupEventListeners() {
    // Handle character ID validation
    const characterIdInput = document.getElementById('character_id');
    if (characterIdInput) {
        characterIdInput.addEventListener('input', handleCharacterIdInput);
        characterIdInput.addEventListener('change', onCharacterChange);
    }

    // Handle ticket recipient changes
    const ticketForSelf = document.getElementById('ticket_for_self');
    const ticketForOther = document.getElementById('ticket_for_other');
    if (ticketForSelf) {
        ticketForSelf.addEventListener('change', onCharacterChange);
        ticketForSelf.addEventListener('change', updateFormFields);
    }
    if (ticketForOther) {
        ticketForOther.addEventListener('change', onCharacterChange);
        ticketForOther.addEventListener('change', updateFormFields);
    }

    // Handle ticket type changes
    const ticketTypeSelect = document.getElementById('ticket_type');
    if (ticketTypeSelect) {
        ticketTypeSelect.addEventListener('change', updateFormFields);
    }

    // Initialize form fields on page load
    window.addEventListener('DOMContentLoaded', updateFormFields);
}

// New function to fetch user's ticket status for the event
function fetchUserEventStatus(userId) {
    if (!userId) return;
    fetch(`${getUserEventStatusUrl}?event_id=${eventId}&user_id=${userId}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                userEventStatus[userId] = {
                    has_adult_ticket: data.has_adult_ticket,
                    has_crew_ticket: data.has_crew_ticket
                };
            }
        });
}

// Helper to get a user-friendly name for error messages
function getFriendlyUserName(targetUserId, recipientName) {
    return parseInt(targetUserId) === parseInt(currentUserId) ? 'You' : recipientName;
}

function formatPrice(price) {
    return '£' + price.toFixed(2);
}

function getTicketPrice(ticketType) {
    switch(ticketType) {
        case ticketTypeValues.ADULT: return PRICES.adult;
        case ticketTypeValues.CHILD_12_15: return PRICES.child_12_15;
        case ticketTypeValues.CHILD_7_11: return PRICES.child_7_11;
        case ticketTypeValues.CHILD_UNDER_7: return PRICES.child_under_7;
        case ticketTypeValues.CREW: return 0;
        default: return 0;
    }
}

// Handle character ID validation
function handleCharacterIdInput() {
    const characterId = this.value.trim();
    const statusElement = document.getElementById('character_id_status');
    const nameElement = document.getElementById('character_name');

    // Clear previous timeout
    if (validationTimeout) {
        clearTimeout(validationTimeout);
    }

    // Reset status
    statusElement.innerHTML = '<i class="fas fa-question text-muted"></i>';
    nameElement.style.display = 'none';

    // Clear existing ticket info when character ID changes
    hideExistingTicketInfo();
    // Reset disables and warnings
    document.getElementById('has_meal_ticket')?.removeAttribute('disabled');
    document.getElementById('has_meal_ticket')?.removeAttribute('title');
    document.getElementById('ticket_type').querySelectorAll('option').forEach(opt => {
        opt.removeAttribute('disabled');
        opt.removeAttribute('title');
    });
    document.getElementById('requires_bunk')?.removeAttribute('disabled');
    document.getElementById('requires_bunk')?.removeAttribute('title');

    // Validate format
    if (!/^\d+\.\d+$/.test(characterId)) {
        statusElement.innerHTML = '<i class="fas fa-times text-danger"></i>';
        return;
    }

    // Set loading state
    statusElement.innerHTML = '<i class="fas fa-spinner fa-spin text-muted"></i>';

    // Debounce validation
    validationTimeout = setTimeout(() => {
        fetch(`${validateCharacterUrl}?character_id=${encodeURIComponent(characterId)}`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    statusElement.innerHTML = '<i class="fas fa-check text-success"></i>';
                    nameElement.textContent = data.character_name;
                    nameElement.style.display = 'block';

                    // Fetch user's event ticket status
                    const userId = characterId.split('.')[0];
                    fetchUserEventStatus(userId);

                    // Check if this is the user's own character
                    const expectedOwnChar = currentUserId + '.' + activeCharacterId;
                    if (characterId === expectedOwnChar && hasMultipleChars) {
                        document.getElementById('ticket_for_self').checked = true;
                        document.getElementById('character_id_section').style.display = 'none';
                        document.getElementById('character_id').value = '';
                        nameElement.style.display = 'none';
                        statusElement.innerHTML = '<i class="fas fa-question text-muted"></i>';
                        showFlashMessage('Switched to "Myself" since you entered your own character.', 'info');
                    }

                    // Check group status for own characters too
                    if (characterId === expectedOwnChar) {
                        fetchCharacterGroupStatus(characterId);
                    }

                    // Fetch ticket info for the new character
                    fetchAndApplyCharacterTicket(characterId);

                    // Check if character has a group
                    fetchCharacterGroupStatus(characterId);
                } else {
                    statusElement.innerHTML = '<i class="fas fa-times text-danger"></i>';
                    nameElement.style.display = 'none';
                }
            })
            .catch(error => {
                statusElement.innerHTML = '<i class="fas fa-times text-danger"></i>';
                nameElement.style.display = 'none';
            });
    }, 500); // 500ms debounce
}

function showExistingTicketInfo(ticket) {
    let infoBox = document.getElementById('existing_ticket_info');
    if (!infoBox) {
        infoBox = document.createElement('div');
        infoBox.id = 'existing_ticket_info';
        infoBox.className = 'alert alert-info mt-2';
        document.getElementById('ticketForm').prepend(infoBox);
    }
    infoBox.innerHTML = `<strong>Existing Ticket:</strong><br>
        Type: ${ticket.ticket_type}<br>
        Meal Ticket: ${ticket.meal_ticket ? 'Yes' : 'No'}<br>
        Requires Bunk: ${ticket.requires_bunk ? 'Yes' : 'No'}<br>
        Price Paid: £${parseFloat(ticket.price_paid).toFixed(2)}`;
}

function hideExistingTicketInfo() {
    document.getElementById('existing_ticket_info')?.remove();
    // Reset editing flag when hiding existing ticket info
    isEditingExistingTicket = false;
}

function fetchCharacterGroupStatus(characterId) {
    if (!characterId) return;
    fetch(`${characterGroupStatusUrl}?character_id=${encodeURIComponent(characterId)}`)
        .then(response => response.json())
        .then(data => {
            if (!data.success) return;

            if (!data.has_group) {
                showGroupWarning(data.character_name);
            } else {
                hideGroupWarning();
            }
        })
        .catch(error => {
            console.error('Error checking character group status:', error);
        });
}

function showGroupWarning(characterName) {
    let warningBox = document.getElementById('group_warning');
    if (!warningBox) {
        warningBox = document.createElement('div');
        warningBox.id = 'group_warning';
        warningBox.className = 'alert alert-warning mt-2';
        document.getElementById('ticketForm').prepend(warningBox);
    }
    warningBox.innerHTML = `<strong>Warning:</strong> Character '${characterName}' is not in a group. Characters must be in a group before purchasing tickets.`;
}

function hideGroupWarning() {
    document.getElementById('group_warning')?.remove();
}

function fetchAndApplyCharacterTicket(characterId) {
    if (!characterId) return;
    fetch(`${getCharacterTicketUrl}?event_id=${eventId}&character_id=${encodeURIComponent(characterId)}`)
        .then(response => response.json())
        .then(data => {
            if (!data.success) return;
            const ticket = data.ticket;
            lastFetchedTicket = ticket;
            if (!ticket) {
                // Reset disables and warnings
                document.getElementById('has_meal_ticket')?.removeAttribute('disabled');
                document.getElementById('has_meal_ticket')?.removeAttribute('title');
                document.getElementById('ticket_type').querySelectorAll('option').forEach(opt => {
                    opt.removeAttribute('disabled');
                    opt.removeAttribute('title');
                });
                document.getElementById('requires_bunk')?.removeAttribute('disabled');
                document.getElementById('requires_bunk')?.removeAttribute('title');
                hideExistingTicketInfo();
                return;
            }
            applyTicketData(ticket);
        });
}

function fetchAndApplyUserTicket(userId) {
    if (!userId) return;
    fetch(`${getUserTicketUrl}?event_id=${eventId}&user_id=${encodeURIComponent(userId)}`)
        .then(response => response.json())
        .then(data => {
            if (!data.success) return;
            const ticket = data.ticket;
            lastFetchedTicket = ticket;
            if (!ticket) {
                // Reset disables and warnings
                document.getElementById('has_meal_ticket')?.removeAttribute('disabled');
                document.getElementById('has_meal_ticket')?.removeAttribute('title');
                document.getElementById('ticket_type').querySelectorAll('option').forEach(opt => {
                    opt.removeAttribute('disabled');
                    opt.removeAttribute('title');
                });
                document.getElementById('requires_bunk')?.removeAttribute('disabled');
                document.getElementById('requires_bunk')?.removeAttribute('title');
                hideExistingTicketInfo();
                return;
            }
            applyTicketData(ticket);
        });
}

function applyTicketData(ticket) {
    // Mark that we're editing an existing ticket
    isEditingExistingTicket = true;

    // Pre-select fields
    document.getElementById('ticket_type').value = ticket.ticket_type;
    if (document.getElementById('has_meal_ticket')) {
        if (ticket.meal_ticket) {
            document.getElementById('has_meal_ticket').setAttribute('checked', 'checked');
        } else {
            document.getElementById('has_meal_ticket').removeAttribute('checked');
        }
    }
    if (document.getElementById('requires_bunk')) {
        if (ticket.requires_bunk) {
            document.getElementById('requires_bunk').setAttribute('checked', 'checked');
        } else {
            document.getElementById('requires_bunk').removeAttribute('checked');
        }
    }
    // Disable meal ticket if already purchased
    if (ticket.meal_ticket) {
        document.getElementById('has_meal_ticket')?.setAttribute('disabled', 'disabled');
        document.getElementById('has_meal_ticket')?.setAttribute('title', 'Meal ticket already purchased. For refunds, contact event organisers.');
    } else {
        document.getElementById('has_meal_ticket')?.removeAttribute('disabled');
        document.getElementById('has_meal_ticket')?.removeAttribute('title');
    }
    // For existing tickets, don't prevent downgrading - allow editing
    const ticketTypeSelect = document.getElementById('ticket_type');
    ticketTypeSelect.querySelectorAll('option').forEach(opt => {
        opt.removeAttribute('disabled');
        opt.removeAttribute('title');
    });
    showExistingTicketInfo(ticket);
}

// Call fetchAndApplyCharacterTicket when character changes
function onCharacterChange() {
    // Clear existing ticket info when switching recipients
    hideExistingTicketInfo();
    // Reset disables and warnings
    document.getElementById('has_meal_ticket')?.removeAttribute('disabled');
    document.getElementById('has_meal_ticket')?.removeAttribute('title');
    document.getElementById('ticket_type').querySelectorAll('option').forEach(opt => {
        opt.removeAttribute('disabled');
        opt.removeAttribute('title');
    });
    document.getElementById('requires_bunk')?.removeAttribute('disabled');
    document.getElementById('requires_bunk')?.removeAttribute('title');

    let characterId = null;
    if (document.getElementById('ticket_for_self')?.checked) {
        characterId = currentUserId + '.' + activeCharacterId;
    } else {
        characterId = document.getElementById('character_id').value.trim();
    }
    fetchAndApplyCharacterTicket(characterId);

    // Check group status when character changes (only for adult tickets)
    const ticketType = document.getElementById('ticket_type').value;
    if (characterId && ticketType === 'adult') {
        fetchCharacterGroupStatus(characterId);
    } else {
        hideGroupWarning();
    }
}

function updateFormFields() {
    const ticketType = document.getElementById('ticket_type').value;
    const ticketForSelf = document.getElementById('ticket_for_self')?.checked;

    // Clear existing ticket info when switching ticket types
    const previousTicketType = document.getElementById('ticket_type').getAttribute('data-previous-type');
    if (previousTicketType && previousTicketType !== ticketType) {
        hideExistingTicketInfo();
        // Reset disables and warnings
        document.getElementById('has_meal_ticket')?.removeAttribute('disabled');
        document.getElementById('has_meal_ticket')?.removeAttribute('title');
        document.getElementById('ticket_type').querySelectorAll('option').forEach(opt => {
            opt.removeAttribute('disabled');
            opt.removeAttribute('title');
        });
        document.getElementById('requires_bunk')?.removeAttribute('disabled');
        document.getElementById('requires_bunk')?.removeAttribute('title');
        // Reset editing flag when switching ticket types
        isEditingExistingTicket = false;
    }
    document.getElementById('ticket_type').setAttribute('data-previous-type', ticketType);

    // Hide all conditional fields by default
    document.getElementById('character_id_section').style.display = 'none';
    document.getElementById('child_name_section').style.display = 'none';
    document.getElementById('self_character_selection_section').style.display = 'none';

    // Re-enable "Someone Else" option by default (will be disabled for crew)
    if (document.getElementById('ticket_for_other')) {
        document.getElementById('ticket_for_other').disabled = false;
    }

    // Adult: show character selection
    if (ticketType === 'adult') {
        document.getElementById('ticket_recipient_section').style.display = '';

        // If user has no active character, disable "Myself" option
        if (!singleActiveCharacterPk && !hasMultipleChars) {
            if (document.getElementById('ticket_for_self')) {
                document.getElementById('ticket_for_self').disabled = true;
                document.getElementById('ticket_for_self').title = 'You need an active character to purchase adult tickets for yourself';
            }
            if (document.getElementById('ticket_for_other')) {
                document.getElementById('ticket_for_other').checked = true;
            }
        } else {
            if (document.getElementById('ticket_for_self')) {
                document.getElementById('ticket_for_self').disabled = false;
                document.getElementById('ticket_for_self').removeAttribute('title');
            }
        }

        if (ticketForSelf) {
            if (hasMultipleChars) {
                document.getElementById('self_character_selection_section').style.display = '';
            }
            document.getElementById('character_id_section').style.display = 'none';
            // Fetch existing ticket info for current character when switching to adult
            if (previousTicketType && previousTicketType !== ticketType) {
                onCharacterChange();
            }
        } else {
            document.getElementById('character_id_section').style.display = '';
        }
    }
    // Crew: only allow self, hide character selection and recipient toggle
    else if (ticketType === 'crew') {
        document.getElementById('ticket_recipient_section').style.display = 'none';
        if (document.getElementById('ticket_for_other')) {
            document.getElementById('ticket_for_self').checked = true;
            document.getElementById('ticket_for_other').disabled = true;
        }
        document.getElementById('character_id_section').style.display = 'none';
        // Fetch existing ticket info for current user when switching to crew
        if (previousTicketType && previousTicketType !== ticketType) {
            fetchAndApplyUserTicket(currentUserId);
        }
    }
    // Child: require child name, hide character selection and recipient toggle
    if (["child_12_15", "child_7_11", "child_under_7"].includes(ticketType)) {
        document.getElementById('ticket_recipient_section').style.display = 'none';
        document.getElementById('child_name_section').style.display = '';
        document.getElementById('character_id_section').style.display = 'none';
    }
}

function showFlashMessage(message, type = 'error') {
    // Create flash message container if it doesn't exist
    let flashContainer = document.getElementById('flash-messages');
    if (!flashContainer) {
        flashContainer = document.createElement('div');
        flashContainer.id = 'flash-messages';
        flashContainer.className = 'position-fixed top-0 start-50 translate-middle-x p-3';
        flashContainer.style.zIndex = '1050';
        document.body.appendChild(flashContainer);
    }

    // Create flash message element
    const flashElement = document.createElement('div');
    flashElement.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show`;
    flashElement.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

    // Add to container
    flashContainer.appendChild(flashElement);

    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (flashElement.parentNode) {
            flashElement.remove();
        }
    }, 5000);
}

function addToCart() {
    const ticketType = document.getElementById('ticket_type').value;
    const ticketType_name = document.getElementById('ticket_type').options[document.getElementById('ticket_type').selectedIndex].text;
    const mealTicket = document.getElementById('has_meal_ticket')?.checked || false;
    const requiresBunk = document.getElementById('requires_bunk')?.checked || false;
    let ticketFor = 'self';

    // Only check the toggle if it's visible (adult tickets)
    if (document.getElementById('ticket_recipient_section').style.display !== 'none') {
        if (document.getElementById('ticket_for_other')?.checked) {
            ticketFor = 'other';
        }
    }

    let characterId = null;
    let selfCharacterId = null;
    let childName = null;
    let recipientName = 'N/A'; // Default value
    let targetUserId = null;

    // Adult: require character selection
    if (ticketType === 'adult') {
        if (ticketFor === 'other') {
            characterId = document.getElementById('character_id').value.trim();
            if (!characterId) {
                showFlashMessage('Please enter a valid character ID.');
                return;
            }
            recipientName = document.getElementById('character_name').textContent || `Character ID: ${characterId}`;
            targetUserId = characterId.split('.')[0];
        } else { // ticketFor === 'self'
            // Check if user has an active character
            if (!singleActiveCharacterPk && !hasMultipleChars) {
                showFlashMessage('You need an active character to purchase adult tickets for yourself. You can purchase crew tickets for yourself or enter a character ID to purchase adult tickets for others.');
                return;
            }
            if (hasMultipleChars) {
                const select = document.getElementById('self_character_select');
                selfCharacterId = select.value;
                recipientName = select.options[select.selectedIndex].text;
            } else {
                selfCharacterId = singleActiveCharacterPk;
                recipientName = singleActiveCharacterName;
            }
            targetUserId = currentUserId;
        }

        const friendlyName = getFriendlyUserName(targetUserId, recipientName);
        const status = userEventStatus[targetUserId] || {};

        // Skip validation if we're editing an existing ticket
        if (!isEditingExistingTicket) {
            if (status.has_adult_ticket) {
                showFlashMessage(`${friendlyName} already ha${parseInt(targetUserId) === parseInt(currentUserId) ? 've' : 's'} an adult ticket for this event.`);
                return;
            }
            if (status.has_crew_ticket) {
                showFlashMessage(`${friendlyName} already ha${parseInt(targetUserId) === parseInt(currentUserId) ? 've' : 's'} a crew ticket and cannot also have an adult ticket.`);
                return;
            }
            if (cart.some(i => i.ticketType === 'adult' && i.targetUserId === targetUserId)) {
                showFlashMessage(`${friendlyName} already has an adult ticket in your cart.`);
                return;
            }
        }
    }

    // Add to cart
    const cartItem = {
        ticketType: ticketType,
        ticketType_name: ticketType_name,
        mealTicket: mealTicket,
        requiresBunk: requiresBunk,
        ticketFor: ticketFor,
        characterId: characterId,
        selfCharacterId: selfCharacterId,
        childName: childName,
        recipientName: recipientName,
        targetUserId: targetUserId,
        price: getTicketPrice(ticketType) + (mealTicket ? PRICES.meal_ticket : 0)
    };

    cart.push(cartItem);
    updateCartDisplay();
    resetFormFields();
}

function updateCartDisplay() {
    const cartContainer = document.getElementById('cartItems');
    const subtotalElement = document.getElementById('subtotal');
    const totalElement = document.getElementById('total');
    const checkoutBtn = document.getElementById('checkoutBtn');

    cartContainer.innerHTML = '';
    let subtotal = 0;

    cart.forEach((item, index) => {
        const itemElement = document.createElement('div');
        itemElement.className = 'cart-item mb-2 p-2 border rounded';
        itemElement.innerHTML = `
            <div class="d-flex justify-content-between align-items-start">
                <div>
                    <strong>${item.ticketType_name}</strong><br>
                    <small>${item.recipientName}</small>
                    ${item.mealTicket ? '<br><small class="text-success">+ Meal Ticket</small>' : ''}
                    ${item.requiresBunk ? '<br><small class="text-info">+ Bunk Required</small>' : ''}
                </div>
                <div class="text-end">
                    <strong>£${item.price.toFixed(2)}</strong><br>
                    <button type="button" class="btn btn-sm btn-outline-danger" onclick="removeFromCart(${index})">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
        `;
        cartContainer.appendChild(itemElement);
        subtotal += item.price;
    });

    subtotalElement.textContent = `£${subtotal.toFixed(2)}`;
    totalElement.textContent = `£${subtotal.toFixed(2)}`;
    checkoutBtn.disabled = cart.length === 0;

    // Update hidden cart input
    document.getElementById('cart').value = JSON.stringify(cart);
}

function removeFromCart(index) {
    cart.splice(index, 1);
    updateCartDisplay();
    resetFormFields();
}

function resetFormFields() {
    // Reset form
    document.getElementById('ticketForm').reset();

    // Reset character ID validation
    const characterIdInput = document.getElementById('character_id');
    if (characterIdInput) {
        characterIdInput.value = '';
        document.getElementById('character_id_status').innerHTML = '<i class="fas fa-question text-muted"></i>';
        document.getElementById('character_name').style.display = 'none';
    }

    // Hide existing ticket info
    hideExistingTicketInfo();

    // Reset disables and warnings
    document.getElementById('has_meal_ticket')?.removeAttribute('disabled');
    document.getElementById('has_meal_ticket')?.removeAttribute('title');
    document.getElementById('ticket_type').querySelectorAll('option').forEach(opt => {
        opt.removeAttribute('disabled');
        opt.removeAttribute('title');
    });
    document.getElementById('requires_bunk')?.removeAttribute('disabled');
    document.getElementById('requires_bunk')?.removeAttribute('title');

    // Hide group warning
    hideGroupWarning();
}
