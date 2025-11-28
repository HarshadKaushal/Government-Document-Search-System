// API base URL
const API_BASE = '/api';

// DOM elements
const searchForm = document.getElementById('searchForm');
const searchQuery = document.getElementById('searchQuery');
const searchBtn = document.getElementById('searchBtn');
const resultsDiv = document.getElementById('results');
const loadingDiv = document.getElementById('loading');
const errorDiv = document.getElementById('error');
const statsDiv = document.getElementById('stats');
const statsContent = document.getElementById('statsContent');

// Load stats on page load
window.addEventListener('DOMContentLoaded', () => {
    loadStats();
    
    // Add click handlers for summary buttons (event delegation)
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('summarize-btn')) {
            e.stopPropagation();
            const docId = e.target.dataset.docId;
            const query = document.getElementById('searchQuery').value;
            summarizeDocument(docId, query, e.target);
        }
    });
});

// Handle form submission
searchForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    await performSearch();
});

// Load system statistics
async function loadStats() {
    try {
        const response = await fetch(`${API_BASE}/stats`);
        const data = await response.json();
        
        if (response.ok) {
            displayStats(data);
        }
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

function displayStats(stats) {
    statsDiv.classList.remove('hidden');
    
    let html = '<div class="stats-content">';
    html += `<div class="stat-item"><strong>Total Documents</strong>${stats.total_documents.toLocaleString()}</div>`;
    
    if (stats.sources) {
        for (const [source, count] of Object.entries(stats.sources)) {
            html += `<div class="stat-item"><strong>${source.toUpperCase()}</strong>${count.toLocaleString()}</div>`;
        }
    }
    
    html += '</div>';
    statsContent.innerHTML = html;
}

// Perform search
async function performSearch() {
    const query = searchQuery.value.trim();
    
    if (!query) {
        showError('Please enter a search query');
        return;
    }
    
    // Show loading
    loadingDiv.classList.remove('hidden');
    errorDiv.classList.add('hidden');
    resultsDiv.innerHTML = '';
    searchBtn.disabled = true;
    
    try {
        // Get form values
        const formData = {
            query: query,
            search_type: document.getElementById('searchType').value,
            source: document.getElementById('sourceFilter').value,
            section: document.getElementById('sectionFilter').value,
            size: parseInt(document.getElementById('resultSize').value),
            deduplicate: document.getElementById('deduplicate').checked,
            include_summaries: document.getElementById('includeSummaries').checked
        };
        
        // Make API request
        const response = await fetch(`${API_BASE}/search`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Search failed');
        }
        
        // Display results
        displayResults(data);
        
    } catch (error) {
        showError(`Error: ${error.message}`);
        console.error('Search error:', error);
    } finally {
        loadingDiv.classList.add('hidden');
        searchBtn.disabled = false;
    }
}

// Display search results
function displayResults(data) {
    resultsDiv.innerHTML = '';
    
    if (data.search_type === 'both') {
        // Display both semantic and keyword results
        if (data.semantic_results && data.semantic_results.length > 0) {
            const normalizedResults = normalizeScores(data.semantic_results, 'semantic');
            const semanticSection = createResultsSection('Semantic Search Results', normalizedResults, data.total_semantic);
            resultsDiv.appendChild(semanticSection);
        }
        
        if (data.keyword_results && data.keyword_results.length > 0) {
            const normalizedResults = normalizeScores(data.keyword_results, 'keyword');
            const keywordSection = createResultsSection('Keyword Search Results', normalizedResults, data.total_keyword);
            resultsDiv.appendChild(keywordSection);
        }
    } else {
        // Display single search type results
        if (data.results && data.results.length > 0) {
            const normalizedResults = normalizeScores(data.results, data.search_type);
            const section = createResultsSection(
                `${data.search_type === 'semantic' ? 'Semantic' : 'Keyword'} Search Results`,
                normalizedResults,
                data.total
            );
            resultsDiv.appendChild(section);
        } else {
            showNoResults();
        }
    }
}

// Normalize scores for display
function normalizeScores(results, searchType) {
    if (!results || results.length === 0) return results;
    
    if (searchType === 'keyword') {
        // For BM25: normalize scores relative to max score (top result = 100%)
        const maxScore = Math.max(...results.map(r => r.score || 0));
        if (maxScore > 0) {
            return results.map(r => ({
                ...r,
                normalized_score: (r.score / maxScore) * 100,
                raw_score: r.score
            }));
        }
    } else {
        // For semantic: scores are already 0-1, just add normalized_score
        return results.map(r => ({
            ...r,
            normalized_score: (r.score || 0) * 100,
            raw_score: r.score
        }));
    }
    
    return results;
}

// Create results section
function createResultsSection(title, results, total) {
    const section = document.createElement('div');
    section.className = 'results-section';
    
    let html = `<h2>${title} (${total} result${total !== 1 ? 's' : ''})</h2>`;
    
    results.forEach((result, index) => {
        html += createResultItem(result, index + 1);
    });
    
    section.innerHTML = html;
    
    // Attach click handlers after creating section
    section.querySelectorAll('.clickable-result').forEach(item => {
        item.addEventListener('click', function(e) {
            // Allow clicking on badges/links inside
            if (e.target.tagName === 'A' || e.target.closest('a')) {
                return;
            }
            
            const docId = this.dataset.docId || '';
            let filepath = '';
            
            // Decode filepath from base64
            const encodedFilepath = this.dataset.filepathEncoded;
            if (encodedFilepath) {
                try {
                    filepath = decodeURIComponent(escape(atob(encodedFilepath)));
                } catch (e) {
                    console.error('Error decoding filepath:', e);
                }
            }
            
            const pageNum = this.dataset.page ? parseInt(this.dataset.page) : null;
            openPDF(docId, filepath, pageNum);
        });
    });
    
    return section;
}

// Create result item HTML
function createResultItem(result, index) {
    const resultSearchType = result.search_type || getSearchType();
    
    // Use normalized_score if available, otherwise calculate
    const scorePercent = result.normalized_score !== undefined 
        ? result.normalized_score.toFixed(1)
        : (resultSearchType === 'keyword' ? 0 : (result.score || 0) * 100).toFixed(1);
    
    const rawScore = result.raw_score !== undefined ? result.raw_score : result.score || 0;
    
    const sourceName = result.source ? result.source.replace('_', ' ').toUpperCase() : 'UNKNOWN';
    const sectionName = result.section || 'Document';
    const date = result.date || 'N/A';
    const page = result.page ? `Page ${result.page}` : '';
    const preview = truncateText(result.text_chunk || '', 300);
    
    // Create click handler data attributes
    const docId = result.doc_id || '';
    const filepath = result.filepath || '';
    const pageNum = result.page || null;
    
    // Base64 encode filepath for safe storage in data attribute
    const encodedFilepath = filepath ? btoa(unescape(encodeURIComponent(filepath))) : '';
    
    return `
        <div class="result-item clickable-result" 
             data-doc-id="${docId}" 
             data-filepath-encoded="${encodedFilepath}"
             data-page="${pageNum || ''}"
             title="Click to open PDF">
            <div class="result-header">
                <div class="result-title">[${index}] ${escapeHtml(result.title)}</div>
            <div class="result-meta">
                <span class="result-badge badge-score">Relevance: ${scorePercent}%${resultSearchType === 'keyword' ? ' (BM25: ' + rawScore.toFixed(2) + ')' : ''}</span>
                <button class="result-badge summarize-btn" 
                        data-doc-id="${docId}"
                        style="background: #e3f2fd; color: #1976d2; border: none; padding: 4px 10px; border-radius: 12px; cursor: pointer; margin-left: 10px; font-size: 0.85em;"
                        title="Generate AI summary">
                    📝 Summarize
                </button>
                <span class="result-badge" style="background: #fff3cd; color: #856404; margin-left: 10px; cursor: pointer;">📄 Click to open PDF</span>
            </div>
            </div>
            <div class="result-meta">
                <span class="result-badge badge-source">${sourceName}</span>
                <span class="result-badge badge-section">${sectionName}</span>
                <span>Date: ${date}</span>
                ${page ? `<span>${page}</span>` : ''}
            </div>
            <div class="result-preview">${escapeHtml(preview)}</div>
            ${result.summary ? `
            <div class="result-summary" style="margin-top: 15px; padding: 15px; background: #e3f2fd; border-radius: 6px; border-left: 4px solid #2196f3;">
                <strong style="color: #1976d2;">📝 AI Summary:</strong>
                <p style="margin-top: 8px; color: #333; line-height: 1.6;">${escapeHtml(result.summary)}</p>
            </div>
            ` : ''}
            <div class="result-footer">
                File: ${escapeHtml(result.filename || 'N/A')}
            </div>
        </div>
    `;
}

// Show error message
function showError(message) {
    errorDiv.textContent = message;
    errorDiv.classList.remove('hidden');
}

// Show no results message
function showNoResults() {
    resultsDiv.innerHTML = `
        <div class="no-results">
            <h3>No results found</h3>
            <p>Try:</p>
            <ul style="text-align: left; display: inline-block; margin-top: 10px;">
                <li>Broadening your search terms</li>
                <li>Removing filters</li>
                <li>Checking spelling</li>
                <li>Using different search type</li>
            </ul>
        </div>
    `;
}

// Utility functions
function truncateText(text, maxLength) {
    if (!text) return '';
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength).trim() + '...';
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Summarize a document
async function summarizeDocument(docId, query, buttonElement) {
    if (!docId) {
        alert('Document ID not available');
        return;
    }
    
    // Show loading state
    const originalText = buttonElement.textContent;
    buttonElement.textContent = '⏳ Summarizing...';
    buttonElement.disabled = true;
    
    // Find the result item
    const resultItem = buttonElement.closest('.result-item');
    const summaryDiv = resultItem.querySelector('.result-summary');
    
    try {
        const response = await fetch('/api/summarize', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                doc_id: docId,
                query: query || null,
                num_sentences: 3
            })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Summarization failed');
        }
        
        // Display summary
        if (summaryDiv) {
            summaryDiv.innerHTML = `
                <strong style="color: #1976d2;">📝 AI Summary:</strong>
                <p style="margin-top: 8px; color: #333; line-height: 1.6;">${escapeHtml(data.summary)}</p>
            `;
        } else {
            // Create summary div
            const previewDiv = resultItem.querySelector('.result-preview');
            const newSummaryDiv = document.createElement('div');
            newSummaryDiv.className = 'result-summary';
            newSummaryDiv.style.cssText = 'margin-top: 15px; padding: 15px; background: #e3f2fd; border-radius: 6px; border-left: 4px solid #2196f3;';
            newSummaryDiv.innerHTML = `
                <strong style="color: #1976d2;">📝 AI Summary:</strong>
                <p style="margin-top: 8px; color: #333; line-height: 1.6;">${escapeHtml(data.summary)}</p>
            `;
            previewDiv.insertAdjacentElement('afterend', newSummaryDiv);
        }
        
        // Update button
        buttonElement.textContent = '✓ Summarized';
        buttonElement.style.background = '#e8f5e9';
        buttonElement.style.color = '#2e7d32';
        buttonElement.disabled = true;
        
    } catch (error) {
        alert(`Error generating summary: ${error.message}`);
        buttonElement.textContent = originalText;
        buttonElement.disabled = false;
    }
}

// Get current search type from form
function getSearchType() {
    return document.getElementById('searchType').value;
}

// Open PDF function
function openPDF(docId, filepath, pageNum) {
    if (!docId && !filepath) {
        alert('PDF file not available');
        return;
    }
    
    // Try to open by doc_id first (more reliable as it looks up from Elasticsearch)
    let url;
    if (docId) {
        url = `/api/pdf?doc_id=${encodeURIComponent(docId)}`;
        if (pageNum) {
            url += `&page=${pageNum}`;
        }
    } else if (filepath) {
        // Fallback to filepath
        // Normalize filepath - handle Windows paths and relative paths
        let normalizedPath = filepath.replace(/\\/g, '/');
        
        // Extract path relative to downloads/
        let relativePath;
        const downloadsIndex = normalizedPath.indexOf('downloads/');
        if (downloadsIndex !== -1) {
            // Extract from downloads/ onwards
            relativePath = normalizedPath.substring(downloadsIndex);
        } else if (normalizedPath.startsWith('downloads/')) {
            relativePath = normalizedPath;
        } else {
            // Assume it's relative to downloads/
            relativePath = 'downloads/' + normalizedPath;
        }
        
        // URL encode the path segments
        relativePath = relativePath.split('/').map(segment => encodeURIComponent(segment)).join('/');
        url = `/api/pdf/${relativePath}`;
        
        if (pageNum) {
            // Add page anchor (browsers may support PDF page navigation)
            url += `#page=${pageNum}`;
        }
    }
    
    // Open PDF in new tab
    if (url) {
        window.open(url, '_blank');
    } else {
        alert('Unable to generate PDF URL');
    }
}

