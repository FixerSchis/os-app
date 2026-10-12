$(document).ready(function() {
    $('.select2').select2({
        theme: 'bootstrap-5',
        width: '100%'
    });

    // --- Remove redirect logic for character/group selection ---
    // (No longer needed, as regular users don't use dropdowns)

    // --- Balance display logic for admins (and anyone with dropdowns) ---
    function setupBalanceDisplay(selectId, balanceDisplayId, balanceSpanId, accountIdField, balanceInputField) {
        const select = document.getElementById(selectId);
        const display = document.getElementById(balanceDisplayId);
        const balanceSpan = document.getElementById(balanceSpanId);
        const accountId = document.getElementById(accountIdField);
        const balanceInput = document.getElementById(balanceInputField);

        if (select) {
            $(select).on('change', function() {
                const selectedOption = this.options[this.selectedIndex];
                let balance = '';
                let accountIdValue = '';

                if (selectedOption && selectedOption.value) {
                    balance = selectedOption.getAttribute('data-balance');
                    accountIdValue = selectedOption.value;
                }

                if (balance) {
                    balanceSpan.textContent = balance;
                    display.style.display = 'block';

                    // Update hidden fields for admin forms
                    if (accountId) {
                        accountId.value = accountIdValue;
                    }
                    if (balanceInput) {
                        balanceInput.value = balance;
                    }
                } else {
                    display.style.display = 'none';

                    // Clear hidden fields
                    if (accountId) {
                        accountId.value = '';
                    }
                    if (balanceInput) {
                        balanceInput.value = '';
                    }
                }
            });
        }
    }
    setupBalanceDisplay('character_select', 'character_balance_display', 'character_balance', 'character_account_id', 'character_balance_input');
    setupBalanceDisplay('group_select', 'group_balance_display', 'group_balance', 'group_account_id', 'group_balance_input');

    function setAccountFields(selectSelector, typeSelector, idSelector) {
        var value = $(selectSelector).val() || '';
        var separator = value.indexOf('_');
        if (separator === -1) {
            $(typeSelector).val('');
            $(idSelector).val('');
            return;
        }
        $(typeSelector).val(value.slice(0, separator));
        $(idSelector).val(value.slice(separator + 1));
    }

    function syncTransferAccounts() {
        if ($('#source_account').length) {
            setAccountFields('#source_account', '#source_type_hidden', '#source_id_hidden');
        }
        setAccountFields('#target_account', '#target_type_hidden', '#target_id_hidden');
    }

    $('#source_account, #target_account').on('change select2:select select2:clear', syncTransferAccounts);

    $('#transfer-form').submit(function(e) {
        syncTransferAccounts();

        var sourceOption = $('#source_account option:selected');
        var sourceBalance = parseFloat(sourceOption.data('balance'));
        var amount = parseFloat($('#amount').val());

        if (sourceBalance && amount > sourceBalance) {
            e.preventDefault();
            alert('Insufficient funds in source account');
        }
    });
});
