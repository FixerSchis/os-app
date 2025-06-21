$(document).ready(function() {
    $('#show-previous').change(function() {
        const showPrevious = $(this).is(':checked');
        const currentUrl = new URL(window.location.href);
        currentUrl.searchParams.set('show_previous', showPrevious);
        window.location.href = currentUrl.toString();
    });
}); 