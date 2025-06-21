// Pending Wiki Changes page JS with CKEditor

document.addEventListener('DOMContentLoaded', function() {
    // Initialize CKEditor for changelog
    const changelogElement = document.getElementById('changelog');
    if (changelogElement && typeof ClassicEditor !== 'undefined') {
        const config = {
            ...window.ckeditorConfig,
            selector: '#changelog',
            toolbar: {
                items: [
                    'undo', 'redo',
                    '|', 'bold', 'italic',
                    '|', 'link', 'blockQuote',
                    '|', 'bulletedList', 'numberedList'
                ]
            },
            height: '200px'
        };

        ClassicEditor
            .create(changelogElement, config)
            .then(editor => {
                changelogElement.ckeditor = editor;

                // Add wiki pages button after the editor
                addWikiPagesButton(changelogElement, editor);

                // Update publish button when content changes
                editor.model.document.on('change:data', updatePublishButton);
            })
            .catch(error => {
                console.error('Failed to create CKEditor for changelog:', error);
                // Fallback to regular textarea
                changelogElement.style.height = '200px';
                changelogElement.addEventListener('input', updatePublishButton);
            });
    } else {
        // Fallback for when CKEditor is not available
        const changelog = document.getElementById('changelog');
        if (changelog) {
            changelog.addEventListener('input', updatePublishButton);
        }
    }

    // Initialize checkboxes
    document.querySelectorAll('.page-checkbox').forEach(cb => {
        cb.addEventListener('change', updatePublishButton);
    });

    // Initial state
    setTimeout(updatePublishButton, 500);

    // Select All / Deselect All logic
    const toggleBtn = document.getElementById('toggle-select-all');
    if (toggleBtn) {
        toggleBtn.addEventListener('click', function() {
            const checkboxes = document.querySelectorAll('.page-checkbox');
            const allChecked = Array.from(checkboxes).every(cb => cb.checked);
            checkboxes.forEach(cb => cb.checked = !allChecked);
            toggleBtn.textContent = allChecked ? 'Select All' : 'Deselect All';
            if (typeof updatePublishButton === 'function') updatePublishButton();
        });
    }

    // Toggle section changes (diffs) logic
    document.querySelectorAll('.toggle-section-btn').forEach(function(btn) {
        btn.addEventListener('click', function() {
            var target = document.getElementById(btn.getAttribute('data-target'));
            if (target.style.display === 'none' || target.style.display === '') {
                target.style.display = 'block';
                btn.textContent = 'Hide Changes';
            } else {
                target.style.display = 'none';
                btn.textContent = 'Show Changes';
            }
        });
    });
});

// Function to add wiki pages button
function addWikiPagesButton(textareaElement, editor) {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'btn btn-outline-primary btn-sm mt-2';
    button.innerHTML = '<i class="bi bi-link-45deg"></i> Insert Wiki Page Link';
    button.style.marginBottom = '10px';

    button.addEventListener('click', () => {
        showWikiPagesDialog(editor);
    });

    // Insert button after the textarea
    textareaElement.parentNode.insertBefore(button, textareaElement.nextSibling);
}

// Function to show wiki pages dialog
function showWikiPagesDialog(editor) {
    // Create modal dialog
    const modal = document.createElement('div');
    modal.className = 'ck-wiki-modal';
    modal.innerHTML = `
        <div class="ck-wiki-modal-content">
            <div class="ck-wiki-modal-header">
                <h3>Select Wiki Page</h3>
                <button type="button" class="ck-wiki-modal-close">&times;</button>
            </div>
            <div class="ck-wiki-modal-body">
                <input type="text" class="ck-wiki-search-input" placeholder="Search wiki pages...">
                <div class="ck-wiki-pages-list"></div>
            </div>
        </div>
    `;

    document.body.appendChild(modal);

    const searchInput = modal.querySelector('.ck-wiki-search-input');
    const pagesList = modal.querySelector('.ck-wiki-pages-list');
    const closeBtn = modal.querySelector('.ck-wiki-modal-close');

    let selectedIndex = -1;
    let currentPages = [];

    // Load initial pages
    loadWikiPages('', pagesList, editor, modal);

    // Handle search
    searchInput.addEventListener('input', () => {
        selectedIndex = -1;
        loadWikiPages(searchInput.value, pagesList, editor, modal);
    });

    // Handle keyboard navigation
    searchInput.addEventListener('keydown', (e) => {
        const items = pagesList.querySelectorAll('.ck-wiki-page-item');

        switch(e.key) {
            case 'ArrowDown':
                e.preventDefault();
                selectedIndex = Math.min(selectedIndex + 1, items.length - 1);
                updateSelection(items);
                break;
            case 'ArrowUp':
                e.preventDefault();
                selectedIndex = Math.max(selectedIndex - 1, -1);
                updateSelection(items);
                break;
            case 'Enter':
                e.preventDefault();
                if (selectedIndex >= 0 && selectedIndex < items.length) {
                    items[selectedIndex].click();
                }
                break;
            case 'Escape':
                e.preventDefault();
                document.body.removeChild(modal);
                break;
        }
    });

    // Handle close
    closeBtn.addEventListener('click', () => {
        document.body.removeChild(modal);
    });

    // Close on outside click
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            document.body.removeChild(modal);
        }
    });

    // Focus search input
    searchInput.focus();

    // Function to update selection highlighting
    function updateSelection(items) {
        items.forEach((item, index) => {
            if (index === selectedIndex) {
                item.classList.add('ck-wiki-page-item-selected');
            } else {
                item.classList.remove('ck-wiki-page-item-selected');
            }
        });
    }
}

// Function to load wiki pages from API
function loadWikiPages(query, pagesList, editor, modal) {
    const url = `/wiki/api/wiki-pages${query ? `?q=${encodeURIComponent(query)}` : ''}`;

    pagesList.innerHTML = '<div class="ck-wiki-loading">Loading...</div>';

    fetch(url)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(pages => {
            pagesList.innerHTML = '';

            if (pages.length === 0) {
                pagesList.innerHTML = '<div class="ck-wiki-no-results">No wiki pages found</div>';
                return;
            }

            pages.forEach((page, index) => {
                const item = document.createElement('div');
                item.className = 'ck-wiki-page-item';
                item.textContent = page.text;
                item.setAttribute('data-index', index);

                item.addEventListener('click', () => {
                    // Insert the wiki page link
                    const linkUrl = page.url;

                    // CKEditor will automatically use selected text or the URL as link text
                    editor.execute('link', linkUrl);

                    // Close the modal
                    document.body.removeChild(modal);
                });

                item.addEventListener('mouseenter', () => {
                    // Update selected index on hover
                    const items = pagesList.querySelectorAll('.ck-wiki-page-item');
                    items.forEach((item, idx) => {
                        if (idx === index) {
                            item.classList.add('ck-wiki-page-item-selected');
                        } else {
                            item.classList.remove('ck-wiki-page-item-selected');
                        }
                    });
                    selectedIndex = index;
                });

                pagesList.appendChild(item);
            });
        })
        .catch(error => {
            console.error('Failed to load wiki pages:', error);
            pagesList.innerHTML = '<div class="ck-wiki-error">Failed to load wiki pages. Please try again.</div>';
        });
}

function updatePublishButton() {
    const checkboxes = document.querySelectorAll('.page-checkbox');
    const changelogEditor = document.querySelector('#changelog')?.ckeditor;
    const changelog = changelogEditor ? changelogEditor.getData() : document.getElementById('changelog').value;
    const changelogText = changelog.replace(/<[^>]*>/g, '').trim();

    let anyChecked = false;
    checkboxes.forEach(cb => { if (cb.checked) anyChecked = true; });
    document.getElementById('publish-btn').disabled = !(anyChecked && changelogText.length > 0);
}
