$(document).ready(function() {
    $('.select2').select2({
        theme: 'bootstrap-5',
        width: '100%'
    });

    // Handle character selection
    $('#character_select').change(function() {
        var characterId = $(this).val();
        var currentUrl = new URL(window.location.href);
        if (characterId) {
            currentUrl.searchParams.set('character_id', characterId);
        } else {
            currentUrl.searchParams.delete('character_id');
        }
        window.location.href = currentUrl.toString();
    });

    // Handle group selection
    $('#group_select').change(function() {
        var groupId = $(this).val();
        var currentUrl = new URL(window.location.href);
        if (groupId) {
            currentUrl.searchParams.set('group_id', groupId);
        } else {
            currentUrl.searchParams.delete('group_id');
        }
        window.location.href = currentUrl.toString();
    });

    // Handle source account selection
    $('#source_type').change(function() {
        var option = $(this).find('option:selected');
        $('#source_id').val(option.data('id'));
    });

    // Handle target account selection
    $('#target_type').change(function() {
        var option = $(this).find('option:selected');
        $('#target_id').val(option.data('id'));
    });

    // Validate amount against source balance
    $('form').submit(function(e) {
        var sourceOption = $('#source_type option:selected');
        var sourceBalance = parseFloat(sourceOption.data('balance'));
        var amount = parseFloat($('#amount').val());

        if (amount > sourceBalance) {
            e.preventDefault();
            alert('Insufficient funds in source account');
        }
    });
});
