$(document).ready(function() {
    // Initialize Select2 for group search
    $('#groupSearch').select2({
        placeholder: 'Search for groups...',
        allowClear: true,
        ajax: {
            url: '/api/groups/search',
            dataType: 'json',
            delay: 250,
            data: function(params) {
                return {
                    q: params.term,
                    page: params.page || 1
                };
            },
            processResults: function(data, params) {
                params.page = params.page || 1;

                return {
                    results: data.items.map(function(item) {
                        return {
                            id: item.id,
                            text: item.name + ' (' + item.group_type + ')'
                        };
                    }),
                    pagination: {
                        more: data.has_more
                    }
                };
            },
            cache: true
        },
        minimumInputLength: 2
    });

    // Handle group selection
    $('#groupSearch').on('select2:select', function(e) {
        var data = e.params.data;
        var groupId = data.id;

        // Show join request form
        $('#groupSearchResults').show();
        $('#groupsList').html(`
            <div class="card">
                <div class="card-body">
                    <h5>${data.text}</h5>
                    <p class="text-muted">Request to join this group?</p>
                    <form method="POST" action="/groups/${groupId}/join-request">
                        <input type="hidden" name="character_id" value="${getCurrentCharacterId()}">
                        <input type="hidden" name="admin_view" value="false">
                        <button type="submit" class="btn btn-primary">Send Join Request</button>
                    </form>
                </div>
            </div>
        `);
    });

    // Clear results when search is cleared
    $('#groupSearch').on('select2:clear', function() {
        $('#groupSearchResults').hide();
        $('#groupsList').empty();
    });
});

document.addEventListener('DOMContentLoaded', function() {
    const leaveBtn = document.querySelector('.leave-btn');
    const disbandBtn = document.querySelector('.disband-btn');
    const groupActionModal = new bootstrap.Modal(document.getElementById('groupActionModal'));
    const groupActionForm = document.getElementById('groupActionForm');
    const groupActionWarning = document.getElementById('groupActionWarning');
    if (leaveBtn) {
        leaveBtn.addEventListener('click', function() {
            groupActionForm.action = this.dataset.leaveUrl;
            groupActionWarning.textContent = this.dataset.warning;
            groupActionModal.show();
        });
    }
    if (disbandBtn) {
        disbandBtn.addEventListener('click', function() {
            groupActionForm.action = this.dataset.disbandUrl;
            groupActionWarning.textContent = this.dataset.warning;
            groupActionModal.show();
        });
    }
});

function getCurrentCharacterId() {
    // Get character ID from URL parameters or form
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get('character_id') || $('input[name="character_id"]').val();
}
