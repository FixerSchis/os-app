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

    // --- The rest of the banking logic (transfers, etc) can remain as needed ---
    // Handle source account selection
    $('#source_account').change(function() {
        var option = $(this).find('option:selected');
        var value = option.val();
        if (value) {
            var parts = value.split('_');
            $('#source_type_hidden').val(parts[0]);
            $('#source_id_hidden').val(parts[1]);
        } else {
            $('#source_type_hidden').val('');
            $('#source_id_hidden').val('');
        }
    });

    // Handle target account selection
    $('#target_account').change(function() {
        var option = $(this).find('option:selected');
        var value = option.val();
        if (value) {
            var parts = value.split('_');
            $('#target_type_hidden').val(parts[0]);
            $('#target_id_hidden').val(parts[1]);
        } else {
            $('#target_type_hidden').val('');
            $('#target_id_hidden').val('');
        }
    });

    // Validate amount against source balance
    $('form').submit(function(e) {
        var sourceOption = $('#source_account option:selected');
        var sourceBalance = parseFloat(sourceOption.data('balance'));
        var amount = parseFloat($('#amount').val());

        if (sourceBalance && amount > sourceBalance) {
            e.preventDefault();
            alert('Insufficient funds in source account');
        }
    });
});
