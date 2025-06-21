// Wiki Editor JavaScript with CKEditor

// Global variables for wiki editor
let sections = [];
let AVAILABLE_ROLES = [];
let FACTIONS = [];
let SPECIES = [];
let SKILLS = [];
let TAGS = [];
let CYBERNETICS = [];

// Global CKEditor configuration to disable cloud features
window.ckeditorConfig = {
    language: 'en',
    toolbar: {
        items: [
            'undo', 'redo',
            '|', 'heading',
            '|', 'bold', 'italic',
            '|', 'link', 'blockQuote', 'insertTable',
            '|', 'bulletedList', 'numberedList'
        ]
    },
    heading: {
        options: [
            { model: 'paragraph', title: 'Paragraph', class: 'ck-heading_paragraph' },
            { model: 'heading1', view: 'h1', title: 'Heading 1', class: 'ck-heading_heading1' },
            { model: 'heading2', view: 'h2', title: 'Heading 2', class: 'ck-heading_heading2' },
            { model: 'heading3', view: 'h3', title: 'Heading 3', class: 'ck-heading_heading3' },
            { model: 'heading4', view: 'h4', title: 'Heading 4', class: 'ck-heading_heading4' }
        ]
    },
    table: {
        contentToolbar: [
            'tableColumn',
            'tableRow',
            'mergeTableCells'
        ]
    },
    link: {
        addTargetToExternalLinks: true,
        defaultProtocol: 'https://',
        decorators: {
            openInNewTab: {
                mode: 'manual',
                label: 'Open in new tab',
                attributes: {
                    target: '_blank',
                    rel: 'noopener noreferrer'
                }
            }
        }
    },
    removePlugins: ['CKFinderUploadAdapter', 'CKFinder', 'EasyImage', 'Image', 'ImageCaption', 'ImageStyle', 'ImageToolbar', 'ImageUpload']
};

// Helper to safely parse JSON from a hidden input's data-json attribute, defaulting to [] or {}
function safeParseJSONDataAttr(selector, fallback) {
    const element = document.querySelector(selector);
    if (!element) return fallback;
    try {
        return JSON.parse(element.getAttribute('data-json') || '[]');
    } catch (e) {
        console.warn('Failed to parse JSON from', selector, e);
        return fallback;
    }
}

function initWikiEditor() {
    // Load data from hidden inputs
    sections = safeParseJSONDataAttr('#sections-data', []);
    AVAILABLE_ROLES = safeParseJSONDataAttr('#available-roles-data', []);
    FACTIONS = safeParseJSONDataAttr('#factions-data', []);
    SPECIES = safeParseJSONDataAttr('#species-data', []);
    SKILLS = safeParseJSONDataAttr('#skills-data', []);
    TAGS = safeParseJSONDataAttr('#tags-data', []);
    CYBERNETICS = safeParseJSONDataAttr('#cybernetics-data', []);

    if (sections.length === 0) {
        sections = [{ 
            id: null, 
            title: '', 
            content: '', 
            order: 0,
            restriction_type: '', 
            restriction_value: '' 
        }];
    }

    renderSections();
    loadRestrictionOptions();
}

function loadRestrictionOptions() {
    // Load restriction options from server if not already loaded
    if (AVAILABLE_ROLES.length === 0) {
        fetch('/wiki/restriction-options')
            .then(response => response.json())
            .then(data => {
                AVAILABLE_ROLES = data.roles || [];
                FACTIONS = data.factions || [];
                SPECIES = data.species || [];
                SKILLS = data.skills || [];
                TAGS = data.tags || [];
                CYBERNETICS = data.cybernetics || [];
                renderSections();
            })
            .catch(error => {
                console.error('Failed to load restriction options:', error);
            });
    }
}

function renderSections() {
    const list = document.getElementById('sections-list');
    if (!list) return;

    list.innerHTML = '';
    sections.forEach((section, idx) => {
        const wrapper = document.createElement('div');
        wrapper.className = 'section-wrapper mb-3 p-3 border rounded';
        wrapper.innerHTML = `
            <div class="row align-items-end mb-2">
                <div class="col-md-4 mb-2 mb-md-0">
                    <label for="section-restriction-type-${idx}" class="form-label fw-bold">Restriction</label>
                    <select id="section-restriction-type-${idx}" class="form-select restriction-type" onchange="updateRestrictionType(${idx})">
                        <option value="">No Restriction</option>
                        <option value="role" ${section.restriction_type === 'role' ? 'selected' : ''}>Role</option>
                        <option value="faction" ${section.restriction_type === 'faction' ? 'selected' : ''}>Faction</option>
                        <option value="species" ${section.restriction_type === 'species' ? 'selected' : ''}>Species</option>
                        <option value="skill" ${section.restriction_type === 'skill' ? 'selected' : ''}>Skill</option>
                        <option value="tag" ${section.restriction_type === 'tag' ? 'selected' : ''}>Tag</option>
                        <option value="cybernetic" ${section.restriction_type === 'cybernetic' ? 'selected' : ''}>Cybernetic</option>
                        <option value="reputation" ${section.restriction_type === 'reputation' ? 'selected' : ''}>Reputation</option>
                    </select>
                </div>
                <div class="col-md-8 d-flex flex-column justify-content-end">
                    <label class="form-label fw-bold">Restriction Value</label>
                    <span id="restriction-value-container-${idx}" class="restriction-value-container" style="min-height:38px;display:block;">
                        ${renderRestrictionValueField(section, idx)}
                    </span>
                </div>
            </div>
            <textarea id="section-content-${idx}">${section.content || ''}</textarea>
            <div class="mt-3">
                ${sections.length > 1 ? `<button type="button" class="btn btn-danger btn-small me-2" onclick="deleteSection(${idx})">Delete</button>` : ''}
                <button type="button" class="btn btn-primary btn-small me-2" onclick="moveSection(${idx}, -1)">↑</button>
                <button type="button" class="btn btn-primary btn-small me-2" onclick="moveSection(${idx}, 1)">↓</button>
                <button type="button" class="btn btn-success btn-small" onclick="addSectionHere(${idx})">Add Section Here</button>
            </div>
        `;
        list.appendChild(wrapper);
    });

    // Initialize CKEditor for all textareas
    setTimeout(() => {
        document.querySelectorAll('textarea[id^="section-content-"]').forEach(el => {
            const config = { ...window.ckeditorConfig };
            config.selector = '#' + el.id;
            config.height = 350;
            
            ClassicEditor
                .create(el, config)
                .then(editor => {
                    // Store editor reference
                    el.ckeditor = editor;
                    
                    // Add wiki pages button after the editor
                    addWikiPagesButton(el, editor);
                    
                    // Update section content when editor changes
                    editor.model.document.on('change:data', () => {
                        const idx = parseInt(el.id.split('-').pop());
                        sections[idx].content = editor.getData();
                    });
                })
                .catch(error => {
                    console.error('Failed to create CKEditor:', error);
                    // Fallback to regular textarea
                    el.style.height = '300px';
                    el.style.fontFamily = 'monospace';
                });
        });

        // Initialize Select2 for restriction multi-selects
        initializeSelect2();
    }, 100);
}

function initializeSelect2() {
    // Initialize Select2 for restriction multi-selects
    document.querySelectorAll('.restriction-multiselect').forEach(function(sel) {
        let idx = parseInt(sel.id.split('-').pop());
        let section = sections[idx];
        let data = [];
        let selected = [];
        
        if (section.restriction_type === 'faction') {
            data = FACTIONS.map(f => ({id: f.id, text: f.name}));
            selected = section.restriction_value ? JSON.parse(section.restriction_value) : [];
        } else if (section.restriction_type === 'species') {
            data = SPECIES.map(s => ({id: s.id, text: s.name}));
            selected = section.restriction_value ? JSON.parse(section.restriction_value) : [];
        } else if (section.restriction_type === 'skill') {
            data = SKILLS.map(s => ({id: s.id, text: s.name}));
            selected = section.restriction_value ? JSON.parse(section.restriction_value) : [];
        }
        
        $(sel).select2({
            data: data,
            width: 'resolve',
            placeholder: 'Select...',
            allowClear: true
        });
        $(sel).val(selected).trigger('change');
        $(sel).on('change', function() {
            const val = $(this).val();
            sections[idx].restriction_value = JSON.stringify(val && val.length ? val : []);
        });
    });

    // Initialize Select2 for tags with tag creation
    document.querySelectorAll('.restriction-multiselect-tags').forEach(function(sel) {
        let idx = parseInt(sel.id.split('-').pop());
        let section = sections[idx];
        let data = TAGS.map(t => ({id: t.id, text: t.name}));
        let selected = section.restriction_value ? JSON.parse(section.restriction_value) : [];
        
        $(sel).select2({
            data: data,
            width: 'resolve',
            placeholder: 'Select or create tags...',
            allowClear: true,
            tags: true,
            createTag: function(params) {
                return {
                    id: params.term,
                    text: params.term,
                    newTag: true
                };
            }
        });
        $(sel).val(selected).trigger('change');
        $(sel).on('change', function() {
            const val = $(this).val();
            sections[idx].restriction_value = JSON.stringify(val && val.length ? val : []);
        });
    });

    // Initialize Select2 for reputation faction
    document.querySelectorAll('.reputation-faction').forEach(function(sel) {
        $(sel).select2({
            width: 'resolve',
            placeholder: 'Select Faction',
            allowClear: true,
            minimumResultsForSearch: 10
        });
        
        let idx = parseInt(sel.id.split('-')[4]);
        let section = sections[idx];
        if (section.restriction_type === 'reputation' && section.restriction_value) {
            try {
                const values = JSON.parse(section.restriction_value);
                if (values.length === 2) {
                    $(sel).val(values[0].toString()).trigger('change');
                }
            } catch (e) {}
        }
        
        $(sel).on('change', function() {
            let idx = parseInt(this.id.split('-')[4]);
            let section = sections[idx];
            let minRep = $(this).closest('.row').find('.reputation-value').val();
            section.restriction_value = JSON.stringify([parseInt($(this).val()), parseInt(minRep)]);
        });
    });

    // Initialize reputation value inputs
    document.querySelectorAll('.reputation-value').forEach(function(inp) {
        $(inp).on('input', function() {
            let idx = parseInt(this.id.split('-')[4]);
            let section = sections[idx];
            let factionId = $(this).closest('.row').find('.reputation-faction').val();
            section.restriction_value = JSON.stringify([parseInt(factionId), parseInt($(this).val())]);
        });
    });

    // Initialize Select2 for cybernetics
    document.querySelectorAll('.restriction-multiselect-cybernetics').forEach(function(sel) {
        let idx = parseInt(sel.id.split('-').pop());
        let section = sections[idx];
        let data = CYBERNETICS.map(c => ({id: c.id, text: c.name}));
        let selected = section.restriction_value ? JSON.parse(section.restriction_value) : [];
        
        $(sel).select2({
            data: data,
            width: 'resolve',
            placeholder: 'Select cybernetics...',
            allowClear: true,
            tags: false
        });
        $(sel).val(selected).trigger('change');
        $(sel).on('change', function() {
            const val = $(this).val();
            sections[idx].restriction_value = JSON.stringify(val && val.length ? val : []);
        });
    });
}

function renderRestrictionValueField(section, idx) {
    switch (section.restriction_type) {
        case 'role':
            let options = AVAILABLE_ROLES.filter(role => role.value !== 'owner' && role.value !== 'admin').map(role => 
                `<option value="${role.value}" ${section.restriction_value === role.value ? 'selected' : ''}>${role.label}</option>`
            ).join('');
            return `<select id="section-restriction-value-${idx}" class="form-control restriction-select" onchange="updateRestrictionValue(${idx})" style="margin-left: 8px;">
                <option value="">Select Role</option>
                ${options}
            </select>`;
        case 'faction':
            return `<select id="section-restriction-value-${idx}" class="form-control restriction-multiselect" multiple style="margin-left: 8px; width: 300px;"></select>`;
        case 'species':
            return `<select id="section-restriction-value-${idx}" class="form-control restriction-multiselect" multiple style="margin-left: 8px; width: 300px;"></select>`;
        case 'skill':
            return `<select id="section-restriction-value-${idx}" class="form-control restriction-multiselect" multiple style="margin-left: 8px; width: 300px;"></select>`;
        case 'tag':
            return `<select id="section-restriction-value-${idx}" class="form-control restriction-multiselect-tags" multiple style="margin-left: 8px; width: 300px;"></select>`;
        case 'cybernetic':
            return `<select id="section-restriction-value-${idx}" class="form-control restriction-multiselect-cybernetics" multiple style="margin-left: 8px; width: 300px;"></select>`;
        case 'reputation':
            return `<div class="row">
                <div class="col-md-6">
                    <select id="section-restriction-value-${idx}-faction" class="form-control reputation-faction" style="margin-left: 8px; width: 300px;">
                        <option value="">Select Faction</option>
                        ${FACTIONS.map(f => `<option value="${f.id}">${f.name}</option>`).join('')}
                    </select>
                </div>
                <div class="col-md-6">
                    <input type="number" id="section-restriction-value-${idx}-value" class="form-control reputation-value" value="${section.restriction_value ? (JSON.parse(section.restriction_value)[1] || 1) : 1}" min="-100" max="100">
                </div>
            </div>`;
        default:
            return ``;
    }
}

// Global functions for section management
window.addSectionHere = function(idx) {
    sections.splice(idx + 1, 0, { 
        id: null, 
        title: '', 
        content: '', 
        order: idx + 1,
        restriction_type: '', 
        restriction_value: '' 
    });
    renderSections();
}

window.deleteSection = function(idx) {
    if (sections.length === 1) {
        showSectionAlert('You cannot delete the only section on a wiki page.', 'danger');
        return;
    }
    // Store deleted section for undo
    const deletedSection = sections[idx];
    sections.splice(idx, 1);
    renderSections();
    showSectionAlert('Section deleted. <a href="#" id="undo-delete-section" class="alert-link">Undo</a>', 'warning', function() {
        sections.splice(idx, 0, deletedSection);
        renderSections();
        showSectionAlert('Section restored.', 'success', null, 2000);
    });
}

window.moveSection = function(idx, direction) {
    const newIdx = idx + direction;
    if (newIdx >= 0 && newIdx < sections.length) {
        [sections[idx], sections[newIdx]] = [sections[newIdx], sections[idx]];
        renderSections();
    }
}

window.updateRestrictionType = function(idx) {
    const select = document.getElementById(`section-restriction-type-${idx}`);
    sections[idx].restriction_type = select.value;
    sections[idx].restriction_value = '';
    renderSections();
}

window.updateRestrictionValue = function(idx) {
    const select = document.getElementById(`section-restriction-value-${idx}`);
    sections[idx].restriction_value = select.value;
}

function gatherSectionData() {
    // Update section content from CKEditor instances
    document.querySelectorAll('textarea[id^="section-content-"]').forEach(el => {
        const idx = parseInt(el.id.split('-').pop());
        if (el.ckeditor) {
            sections[idx].content = el.ckeditor.getData();
        } else {
            sections[idx].content = el.value;
        }
        // Ensure each section has the required fields
        sections[idx].order = idx;
        if (!sections[idx].title) {
            sections[idx].title = '';
        }
        if (!sections[idx].id) {
            sections[idx].id = null;
        }
    });
    
    return sections;
}

function saveWiki() {
    gatherSectionData();
    
    // Prepare data as JSON
    const data = {
        sections: sections
    };
    
    // Add other form data
    const title = document.getElementById('title')?.value;
    const slug = document.getElementById('slug')?.value;
    const tags = $('#wiki-tags').val();
    
    if (title) data.title = title;
    if (slug) data.slug = slug;
    if (tags) data.tags = tags;
    
    fetch(window.location.href, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            window.location.href = data.redirect_url || data.redirect;
        } else {
            alert('Error saving wiki: ' + (data.error || 'Unknown error'));
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error saving wiki. Please try again.');
    });
}

// Show a non-blocking alert at the top of the page
function showSectionAlert(message, type = 'info', undoCallback = null, timeout = 5000) {
    let alertDiv = document.getElementById('section-alert');
    if (!alertDiv) {
        alertDiv = document.createElement('div');
        alertDiv.id = 'section-alert';
        alertDiv.style.position = 'fixed';
        alertDiv.style.top = '0';
        alertDiv.style.left = '0';
        alertDiv.style.right = '0';
        alertDiv.style.zIndex = '2000';
        alertDiv.style.display = 'flex';
        alertDiv.style.justifyContent = 'center';
        alertDiv.style.pointerEvents = 'none';
        document.body.appendChild(alertDiv);
    }
    alertDiv.innerHTML = `<div class="alert alert-${type} mt-3" style="max-width: 600px; pointer-events: auto;">${message}</div>`;
    alertDiv.style.display = 'flex';
    let undoLink = document.getElementById('undo-delete-section');
    let timer = setTimeout(() => {
        alertDiv.style.display = 'none';
    }, timeout);
    if (undoLink && typeof undoCallback === 'function') {
        undoLink.onclick = function(e) {
            e.preventDefault();
            clearTimeout(timer);
            alertDiv.style.display = 'none';
            undoCallback();
        };
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    initWikiEditor();
    
    // Handle form submission
    const form = document.getElementById('wiki-edit-form');
    if (form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            saveWiki();
        });
    }
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