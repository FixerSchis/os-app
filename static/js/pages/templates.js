// Template management JavaScript

// Global variables for live preview
let previewTimeout = null;
let lastValidHtml = '';
let lastValidCss = '';
let isPreviewUpdating = false;

let monacoEditor = null;
let currentMonacoTab = 'front';
let monacoContents = {
    front: '',
    back: '',
    css: ''
};

// Template type constants for future extensibility
const TEMPLATE_TYPES = {
    CHARACTER_SHEET: 'character_sheet',
    CHARACTER_ID: 'character_id',
    ITEM_CARD: 'item_card',
    MEDICAMENT_CARD: 'medicament_card',
    CONDITION_CARD: 'condition_card',
    EXOTIC_SUBSTANCE_LABEL: 'exotic_substance_label'
};

// Get current template type from the page
function getCurrentTemplateType() {
    const form = document.getElementById('templateForm');
    if (form && form.dataset.templateType) {
        return form.dataset.templateType;
    }
    
    const preview = document.getElementById('frontPreview');
    if (preview && preview.dataset.templateType) {
        return preview.dataset.templateType;
    }
    
    return TEMPLATE_TYPES.CHARACTER_SHEET; // Default fallback
}

// Template type-specific logic (for future extensibility)
function getTemplateTypeConfig(templateType) {
    const configs = {
        [TEMPLATE_TYPES.CHARACTER_SHEET]: {
            defaultWidth: 148.0,
            defaultHeight: 210.0,
            hasBackSide: true,
            description: 'Character Sheet Template'
        },
        [TEMPLATE_TYPES.CHARACTER_ID]: {
            defaultWidth: 85.6,
            defaultHeight: 53.98,
            hasBackSide: false,
            description: 'Character ID Template'
        },
        [TEMPLATE_TYPES.ITEM_CARD]: {
            defaultWidth: 85.6,
            defaultHeight: 53.98,
            hasBackSide: true,
            description: 'Item Card Template'
        },
        [TEMPLATE_TYPES.MEDICAMENT_CARD]: {
            defaultWidth: 63.5,
            defaultHeight: 88.9,
            hasBackSide: true,
            description: 'Medicament Card Template'
        },
        [TEMPLATE_TYPES.CONDITION_CARD]: {
            defaultWidth: 63.5,
            defaultHeight: 88.9,
            hasBackSide: true,
            description: 'Condition Card Template'
        },
        [TEMPLATE_TYPES.EXOTIC_SUBSTANCE_LABEL]: {
            defaultWidth: 25.0,
            defaultHeight: 10.0,
            hasBackSide: false,
            description: 'Exotic Substance Label Template'
        }
    };
    
    return configs[templateType] || configs[TEMPLATE_TYPES.CHARACTER_SHEET];
}

// Attach tab event listeners immediately so UI works even if Monaco is not ready
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('#monacoTabs button[data-tab]').forEach(btn => {
        btn.addEventListener('click', function() {
            const tab = this.getAttribute('data-tab');
            
            // Save current content if Monaco is ready
            if (monacoEditor) {
                monacoContents[currentMonacoTab] = monacoEditor.getValue();
            } else {
                // Save content from fallback editor if available
                const fallbackEditor = document.getElementById('fallback-editor');
                if (fallbackEditor) {
                    monacoContents[currentMonacoTab] = fallbackEditor.value;
                }
            }
            
            // Update active tab
            document.querySelectorAll('#monacoTabs .nav-link').forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            
            currentMonacoTab = tab;
            
            // If Monaco is ready, update editor content/language
            if (monacoEditor) {
                if (tab === 'front') {
                    monacoEditor.setValue(monacoContents.front);
                    monaco.editor.setModelLanguage(monacoEditor.getModel(), 'html');
                } else if (tab === 'back') {
                    monacoEditor.setValue(monacoContents.back);
                    monaco.editor.setModelLanguage(monacoEditor.getModel(), 'html');
                } else if (tab === 'css') {
                    monacoEditor.setValue(monacoContents.css);
                    monaco.editor.setModelLanguage(monacoEditor.getModel(), 'css');
                }
            } else {
                // Update fallback editor if available
                const fallbackEditor = document.getElementById('fallback-editor');
                if (fallbackEditor) {
                    fallbackEditor.value = monacoContents[tab] || '';
                }
            }
        });
    });
});

function initializeMonacoEditor() {
    // Try to load Monaco Editor with local files first, then CDN fallback
    const monacoPaths = {
        'vs': [
            '/static/external/monaco-editor/vs', // Local files first
            'https://cdn.jsdelivr.net/npm/monaco-editor@0.45.0/min/vs' // CDN fallback
        ]
    };
    
    // Try local files first, fallback to CDN if needed
    require.config({ 
        paths: { 'vs': monacoPaths.vs[0] },
        catchError: true,
        onError: function(err) {
            console.warn('Monaco Editor local files failed, trying CDN fallback...', err);
            // Try CDN fallback
            require.config({ 
                paths: { 'vs': monacoPaths.vs[1] },
                catchError: true,
                onError: function(cdnErr) {
                    console.error('Monaco Editor failed to load from both local and CDN:', cdnErr);
                    showMonacoFallback();
                }
            });
            tryInitMonaco();
        }
    });

    // Initialize content variables
    monacoContents.front = document.getElementById('front_html')?.value || '';
    monacoContents.back = document.getElementById('back_html')?.value || '';
    monacoContents.css = document.getElementById('css_styles')?.value || '';

    require(['vs/editor/editor.main'], function() {
        monacoEditor = monaco.editor.create(document.getElementById('monaco-editor-container'), {
            value: monacoContents[currentMonacoTab],
            language: currentMonacoTab === 'css' ? 'css' : 'html',
            theme: 'vs-dark',
            automaticLayout: true,
            minimap: { enabled: false },
            scrollBeyondLastLine: false,
            fontSize: 14,
            lineNumbers: 'on',
            roundedSelection: false,
            scrollbar: {
                vertical: 'visible',
                horizontal: 'visible'
            }
        });

        // Live preview on change
        monacoEditor.onDidChangeModelContent(() => {
            monacoContents[currentMonacoTab] = monacoEditor.getValue();
            debouncedUpdatePreview();
        });
        
        // Load Jinja completions
        const completions = loadJinjaCompletionsFromField();
        if (completions) {
            monaco.languages.registerCompletionItemProvider('html', {
                provideCompletionItems: function(model, position) {
                    const textUntilPosition = model.getValueInRange({
                        startLineNumber: position.lineNumber,
                        startColumn: 1,
                        endLineNumber: position.lineNumber,
                        endColumn: position.column
                    });
                    const suggestions = [];
                    // Variable completion (e.g., "character.")
                    const variableMatch = textUntilPosition.match(/(\w+)\.$/);
                    if (variableMatch) {
                        const variable = variableMatch[1];
                        const variableCompletions = completions[variable];
                        if (variableCompletions) {
                            Object.keys(variableCompletions).forEach(key => {
                                suggestions.push({
                                    label: key,
                                    kind: monaco.languages.CompletionItemKind.Field,
                                    insertText: key,
                                    detail: variableCompletions[key]
                                });
                            });
                        }
                    }
                    // Jinja tag completion (e.g., "{% ")
                    const jinjaTagMatch = textUntilPosition.match(/\{\%\s*$/);
                    if (jinjaTagMatch && completions.jinja) {
                        Object.keys(completions.jinja).forEach(key => {
                            suggestions.push({
                                label: key,
                                kind: monaco.languages.CompletionItemKind.Keyword,
                                insertText: completions.jinja[key],
                                detail: `Jinja ${key}`
                            });
                        });
                    }
                    // Jinja expression completion (e.g., "{{ ")
                    const jinjaExprMatch = textUntilPosition.match(/\{\{\s*$/);
                    if (jinjaExprMatch) {
                        Object.keys(completions).forEach(modelKey => {
                            if (modelKey !== 'jinja') {
                                suggestions.push({
                                    label: modelKey,
                                    kind: monaco.languages.CompletionItemKind.Variable,
                                    insertText: `{{ ${modelKey} }}`,
                                    detail: `${modelKey} object`
                                });
                            }
                        });
                    }
                    return { suggestions: suggestions };
                }
            });
        }
    });
}

function getEditorContent(editorId) {
    if (editorId === 'frontHtml') return monacoContents.front;
    if (editorId === 'backHtml') return monacoContents.back;
    if (editorId === 'cssStyles') return monacoContents.css;
}

function updateHiddenFields() {
    // Ensure we have the latest content from the Monaco editor
    if (monacoEditor) {
        monacoContents[currentMonacoTab] = monacoEditor.getValue();
    } else {
        // Get content from fallback editor if available
        const fallbackEditor = document.getElementById('fallback-editor');
        if (fallbackEditor) {
            monacoContents[currentMonacoTab] = fallbackEditor.value;
        }
    }
    
    // Update hidden form fields
    document.getElementById('front_html').value = monacoContents.front;
    if (document.getElementById('back_html')) document.getElementById('back_html').value = monacoContents.back;
    document.getElementById('css_styles').value = monacoContents.css;
}

// Template preview functionality
function previewTemplate() {
    // TODO: Implement template preview functionality when model is created
    alert('Template preview functionality will be implemented when the model is created.');
}

// Live preview functionality
function updatePreview() {
    const frontHtml = getEditorContent('frontHtml') || '';
    const backHtml = getEditorContent('backHtml') || '';
    const cssStyles = getEditorContent('cssStyles') || '';
    const frontPreview = document.getElementById('frontPreview');
    const backPreview = document.getElementById('backPreview');
    
    if (!frontPreview) return;
    
    // Get template dimensions from the page (set by the template data)
    const templateWidth = frontPreview.dataset.widthMm;
    const templateHeight = frontPreview.dataset.heightMm;
    const templateType = getCurrentTemplateType();
    
    // Set dimensions on the template content
    if (templateWidth && templateHeight) {
        frontPreview.style.width = templateWidth + 'mm';
        frontPreview.style.height = templateHeight + 'mm';
        if (backPreview) {
            backPreview.style.width = templateWidth + 'mm';
            backPreview.style.height = templateHeight + 'mm';
        }
    }
    
    // Show loading state on both previews
    if (frontPreview) {
        frontPreview.innerHTML = '<div class="preview-loading"><i class="fas fa-spinner fa-spin"></i> Updating front preview...</div>';
    }
    if (backPreview) {
        backPreview.innerHTML = '<div class="preview-loading"><i class="fas fa-spinner fa-spin"></i> Updating back preview...</div>';
    }
    
    // Get template ID from the page
    const templateId = getTemplateId();
    if (!templateId) {
        showAutoUpdateIndicator('Template ID not found', 'error');
        return;
    }
    
    // Call the API to render the template
    fetch(`/templates/api/${templateId}/render`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            front_html: frontHtml,
            back_html: backHtml,
            css_styles: cssStyles
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Update front preview
            if (frontPreview && data.front_html) {
                frontPreview.innerHTML = data.front_html;
            } else if (frontPreview) {
                frontPreview.innerHTML = '';
            }
            // Update back preview
            if (backPreview && data.back_html) {
                backPreview.innerHTML = data.back_html;
            } else if (backPreview) {
                backPreview.innerHTML = '';
            }
            // Inject base64 CSS into both previews
            const injectCss = (el) => {
                if (!el) return;
                // Remove any previous style tag
                const prevStyle = el.querySelector('style[data-preview-css]');
                if (prevStyle) prevStyle.remove();
                if (data.css_b64) {
                    const css = atob(data.css_b64);
                    const style = document.createElement('style');
                    style.textContent = css;
                    style.setAttribute('data-preview-css', '1');
                    el.insertBefore(style, el.firstChild);
                    el.setAttribute('data-css-b64', data.css_b64);
                } else {
                    el.removeAttribute('data-css-b64');
                }
            };
            injectCss(frontPreview);
            injectCss(backPreview);
            // Store valid content
            lastValidHtml = frontHtml;
            lastValidCss = cssStyles;
            // Show success indicator
            showAutoUpdateIndicator('Preview updated successfully');
        } else {
            // Show error message
            const errorMessage = data.error || 'Unknown error occurred';
            showAutoUpdateIndicator('Preview error: ' + errorMessage, 'error');
            
            // Show error in previews
            if (frontPreview) {
                frontPreview.innerHTML = '<div class="preview-error"><i class="fas fa-exclamation-triangle"></i> <strong>Preview Error:</strong><br>' + errorMessage + '</div>';
            }
            if (backPreview) {
                backPreview.innerHTML = '<div class="preview-error"><i class="fas fa-exclamation-triangle"></i> <strong>Preview Error:</strong><br>' + errorMessage + '</div>';
            }
        }
    })
    .catch(error => {
        console.error('Preview update error:', error);
        showAutoUpdateIndicator('Network error: ' + error.message, 'error');
        
        // Show error in previews
        const errorMessage = 'Network error occurred while updating preview';
        if (frontPreview) {
            frontPreview.innerHTML = '<div class="preview-error"><i class="fas fa-exclamation-triangle"></i> <strong>Network Error:</strong><br>' + errorMessage + '</div>';
        }
        if (backPreview) {
            backPreview.innerHTML = '<div class="preview-error"><i class="fas fa-exclamation-triangle"></i> <strong>Network Error:</strong><br>' + errorMessage + '</div>';
        }
    });
}

// Get template ID from the page
function getTemplateId() {
    // Try to get from form data attribute first
    const form = document.getElementById('templateForm');
    if (form && form.dataset.templateId) {
        return form.dataset.templateId;
    }
    
    // Try to get from URL as fallback
    const urlMatch = window.location.pathname.match(/\/templates\/(\d+)\/edit/);
    if (urlMatch) {
        return urlMatch[1];
    }
    
    return null;
}

// Debounced preview update
function debouncedUpdatePreview() {
    const autoPreview = document.getElementById('autoPreview');
    if (!autoPreview || !autoPreview.checked) return;
    
    if (previewTimeout) {
        clearTimeout(previewTimeout);
    }
    
    previewTimeout = setTimeout(() => {
        updatePreview();
    }, 500); // 500ms delay
}

// Show auto-update indicator
function showAutoUpdateIndicator(message, type = 'success') {
    let indicator = document.getElementById('auto-update-indicator');
    if (!indicator) {
        indicator = document.createElement('div');
        indicator.id = 'auto-update-indicator';
        indicator.className = 'auto-update-indicator';
        document.body.appendChild(indicator);
    }
    
    indicator.textContent = message;
    indicator.className = `auto-update-indicator ${type === 'warning' ? 'bg-warning' : 'bg-success'}`;
    indicator.classList.add('show');
    
    setTimeout(() => {
        indicator.classList.remove('show');
    }, 2000);
}

// Handle tab key in textareas
function handleTabKey(event) {
    if (event.key === 'Tab') {
        event.preventDefault();
        
        const textarea = event.target;
        const start = textarea.selectionStart;
        const end = textarea.selectionEnd;
        
        // Insert tab character at cursor position
        const newValue = textarea.value.substring(0, start) + '\t' + textarea.value.substring(end);
        textarea.value = newValue;
        
        // Set cursor position after the tab
        textarea.selectionStart = textarea.selectionEnd = start + 1;
        
        // Trigger input event for live preview
        textarea.dispatchEvent(new Event('input'));
    }
}

function processUserCss(css) {
    // Remove @import, @font-face, html selectors, and anything before body
    // Only allow body and below
    let processed = '';
    // Remove @import and @font-face
    css = css.replace(/@import[^;]+;/g, '');
    css = css.replace(/@font-face\s*{[^}]*}/g, '');
    // Remove html selectors
    css = css.replace(/html\s*{[^}]*}/g, '');
    // Find all body rules and rewrite them
    processed = css.replace(/body(\s*{[^}]*})/g, '.template-content$1');
    // Remove anything before the first .template-content rule (if user put global stuff above body)
    const firstTemplateContent = processed.indexOf('.template-content');
    if (firstTemplateContent > 0) {
        processed = processed.slice(firstTemplateContent);
    }
    // Optionally, scope all selectors to .template-content (for extra safety)
    // processed = processed.replace(/(^|\}|\s)([a-zA-Z0-9.#:\[>\-]+)\s*{/g, (m, p1, selector) => {
    //     if (selector.startsWith('.template-content')) return m;
    //     return `${p1}.template-content ${selector} {`;
    // });
    return processed;
}

// Load Jinja completions from hidden field
function loadJinjaCompletionsFromField() {
    const field = document.getElementById('jinja_completions');
    if (!field) return null;
    try {
        return JSON.parse(field.value);
    } catch (e) {
        return null;
    }
}

function showMonacoFallback() {
    const container = document.getElementById('monaco-editor-container');
    if (container) {
        container.innerHTML = `
            <div class="alert alert-danger">
                <h5><i class="bi bi-exclamation-triangle"></i> Monaco Editor Unavailable</h5>
                <p>Monaco Editor could not be loaded from local files or CDN. Using fallback textarea editor.</p>
                <p><small>This should not happen with the local Monaco Editor files. Please check the file paths and server configuration.</small></p>
            </div>
            <div class="form-group">
                <label for="fallback-editor">Template Content:</label>
                <textarea id="fallback-editor" class="form-control" rows="15" style="font-family: 'Fira Code', 'Monaco', 'Menlo', monospace; font-size: 14px;"></textarea>
            </div>
        `;
        
        // Initialize fallback editor
        const fallbackEditor = document.getElementById('fallback-editor');
        if (fallbackEditor) {
            fallbackEditor.value = monacoContents[currentMonacoTab] || '';
            fallbackEditor.addEventListener('input', function() {
                monacoContents[currentMonacoTab] = this.value;
            });
        }
    }
}

document.addEventListener('DOMContentLoaded', function() {
    // Monaco Editor
    let monacoLoaded = false;
    let monacoTimeout = setTimeout(() => {
        if (!monacoLoaded) {
            const container = document.getElementById('monaco-editor-container');
            if (container) {
                container.innerHTML = '<div class="alert alert-danger">Monaco Editor failed to load. Please check your internet connection or try again later.</div>';
            }
        }
    }, 8000); // 8 seconds fallback

    function tryInitMonaco() {
        if (window.require) {
            clearTimeout(monacoTimeout);
            monacoLoaded = true;
            initializeMonacoEditor();
        } else {
            setTimeout(tryInitMonaco, 100);
        }
    }
    tryInitMonaco();

    // Set template dimensions
    const frontPreview = document.getElementById('frontPreview');
    const backPreview = document.getElementById('backPreview');
    if (frontPreview) {
        const templateWidth = frontPreview.dataset.widthMm;
        const templateHeight = frontPreview.dataset.heightMm;
        if (templateWidth && templateHeight) {
            frontPreview.style.width = templateWidth + 'mm';
            frontPreview.style.height = templateHeight + 'mm';
            if (backPreview) {
                backPreview.style.width = templateWidth + 'mm';
                backPreview.style.height = templateHeight + 'mm';
            }
        }
    }

    setTimeout(() => { updatePreview(); }, 100);

    const refreshBtn = document.getElementById('refreshPreview');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', function() {
            clearTimeout(previewTimeout);
            updatePreview();
            showAutoUpdateIndicator('Preview refreshed manually');
        });
    }

    const form = document.getElementById('templateForm');
    if (form) {
        form.addEventListener('submit', function(e) {
            // Ensure we sync the current editor content before submitting
            updateHiddenFields();
        });
    }
});

// Printing functionality
function openPdfInNewWindow(pdfBase64, filename) {
    // Create blob from base64
    const byteCharacters = atob(pdfBase64);
    const byteNumbers = new Array(byteCharacters.length);
    for (let i = 0; i < byteCharacters.length; i++) {
        byteNumbers[i] = byteCharacters.charCodeAt(i);
    }
    const byteArray = new Uint8Array(byteNumbers);
    const blob = new Blob([byteArray], { type: 'application/pdf' });
    
    // Create object URL
    const pdfUrl = URL.createObjectURL(blob);
    
    // Open in new window
    const newWindow = window.open(pdfUrl, '_blank');
    
    // Clean up the URL object after the window loads
    newWindow.addEventListener('load', () => {
        setTimeout(() => {
            URL.revokeObjectURL(pdfUrl);
        }, 1000);
    });
}

function printTemplates(items, templateType) {
    // Show loading indicator
    const loadingToast = showAutoUpdateIndicator('Preparing print layout...', 'info');
    
    // Send request to generate print layout
    fetch(`/print/${templateType}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            items: items,
            template_type: templateType
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showAutoUpdateIndicator(data.error, 'error');
            return;
        }
        
        if (data.double_sided) {
            // Open front and back PDFs in new windows
            openPdfInNewWindow(data.front_pdf, 'front.pdf');
            if (data.back_pdf) {
                setTimeout(() => {
                    openPdfInNewWindow(data.back_pdf, 'back.pdf');
                }, 500);
            }
        } else {
            // Open single PDF in new window
            openPdfInNewWindow(data.pdf, 'document.pdf');
        }
        
        showAutoUpdateIndicator('PDFs generated successfully', 'success');
    })
    .catch(error => {
        console.error('Error:', error);
        showAutoUpdateIndicator('Error preparing print layout', 'error');
    });
}

// Event character sheet printing
function printEventCharacterSheets(eventId) {
    showAutoUpdateIndicator('Generating character sheet PDFs...', 'info');
    
    fetch(`/events/${eventId}/print_character_sheets`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                showAutoUpdateIndicator(data.error, 'error');
                return;
            }
            
            // Open PDFs in new windows
            openPdfInNewWindow(data.front_pdf, 'character_sheets_front.pdf');
            if (data.back_pdf) {
                setTimeout(() => {
                    openPdfInNewWindow(data.back_pdf, 'character_sheets_back.pdf');
                }, 500);
            }
            
            showAutoUpdateIndicator('Character sheets generated successfully', 'success');
        })
        .catch(error => {
            console.error('Error:', error);
            showAutoUpdateIndicator('Error generating character sheets', 'error');
        });
}

// Event items printing
function printEventItems(eventId) {
    showAutoUpdateIndicator('Generating item card PDFs...', 'info');
    
    fetch(`/events/${eventId}/print_items`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                showAutoUpdateIndicator(data.error, 'error');
                return;
            }
            
            // Open PDFs in new windows
            openPdfInNewWindow(data.front_pdf, 'item_cards_front.pdf');
            if (data.back_pdf) {
                setTimeout(() => {
                    openPdfInNewWindow(data.back_pdf, 'item_cards_back.pdf');
                }, 500);
            }
            
            showAutoUpdateIndicator('Item cards generated successfully', 'success');
        })
        .catch(error => {
            console.error('Error:', error);
            showAutoUpdateIndicator('Error generating item cards', 'error');
        });
}

// Single character sheet printing
function printCharacterSheet(characterId) {
    showAutoUpdateIndicator('Generating character sheet PDF...', 'info');
    
    fetch(`/characters/${characterId}/print`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                showAutoUpdateIndicator(data.error, 'error');
                return;
            }
            
            // Open PDFs in new windows
            openPdfInNewWindow(data.front_pdf, 'character_sheet_front.pdf');
            if (data.back_pdf) {
                setTimeout(() => {
                    openPdfInNewWindow(data.back_pdf, 'character_sheet_back.pdf');
                }, 500);
            }
            
            showAutoUpdateIndicator('Character sheet generated successfully', 'success');
        })
        .catch(error => {
            console.error('Error:', error);
            showAutoUpdateIndicator('Error generating character sheet', 'error');
        });
}

// Sample sticker printing
function printSampleStickers(sampleId) {
    showAutoUpdateIndicator('Generating sample sticker PDF...', 'info');
    
    fetch(`/samples/${sampleId}/print`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                showAutoUpdateIndicator(data.error, 'error');
                return;
            }
            
            // Open PDF in new window
            openPdfInNewWindow(data.pdf, 'sample_stickers.pdf');
            showAutoUpdateIndicator('Sample stickers generated successfully', 'success');
        })
        .catch(error => {
            console.error('Error:', error);
            showAutoUpdateIndicator('Error generating sample stickers', 'error');
        });
}

// Add print button click handlers
document.addEventListener('DOMContentLoaded', function() {
    // Event character sheets print button
    const eventCharactersPrintBtn = document.querySelector('.print-character-sheets-btn');
    if (eventCharactersPrintBtn) {
        const eventId = eventCharactersPrintBtn.dataset.eventId;
        eventCharactersPrintBtn.addEventListener('click', () => printEventCharacterSheets(eventId));
    }
    
    // Event items print button
    const eventItemsPrintBtn = document.querySelector('.print-items-btn');
    if (eventItemsPrintBtn) {
        const eventId = eventItemsPrintBtn.dataset.eventId;
        eventItemsPrintBtn.addEventListener('click', () => printEventItems(eventId));
    }
    
    // Character sheet print button
    const characterPrintBtn = document.querySelector('.print-character-btn');
    if (characterPrintBtn) {
        const characterId = characterPrintBtn.dataset.characterId;
        characterPrintBtn.addEventListener('click', () => printCharacterSheet(characterId));
    }
    
    // Sample stickers print buttons
    document.querySelectorAll('.print-sample-btn').forEach(button => {
        const sampleId = button.dataset.sampleId;
        button.addEventListener('click', () => printSampleStickers(sampleId));
    });
});

function printTemplatePreview() {
    // Get the template ID
    const templateId = getTemplateId();
    if (!templateId) {
        console.error('No template ID found');
        return;
    }

    // Get current content from Monaco editor
    const currentContent = monacoEditor.getValue();
    monacoContents[currentMonacoTab] = currentContent;

    // Prepare request data
    const data = {
        front_html: monacoContents.front,
        back_html: monacoContents.back,
        css_styles: monacoContents.css
    };

    // Call the print preview endpoint
    fetch(`/templates/api/${templateId}/print_preview`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            throw new Error(data.error);
        }

        // Open PDF in new tab
        openPdfInNewWindow(data.pdf, 'template_preview.pdf');
    })
    .catch(error => {
        console.error('Error generating print preview:', error);
        showAutoUpdateIndicator('Error generating print preview: ' + error.message, 'error');
    });
} 