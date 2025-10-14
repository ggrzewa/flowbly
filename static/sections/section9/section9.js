/**
 * SEKCJA 9: ENHANCED SERP ANALYSIS - NASA MISSION CONTROL STYLE
 */

function displaySerpAnalysis(data) {
    console.log('🔍 SEKCJA 9: Renderowanie Enhanced SERP Analysis - NASA Mission Control');
    
    const serpContainer = document.getElementById('serpAnalysis');
    if (!serpContainer) {
        console.error('❌ Kontener #serpAnalysis nie znaleziony');
        return;
    }
    
    console.log('🔍 SEKCJA 9 DEBUG - serpAnalysis data:', data);
    
    // Dodaj wrapper z klasą NASA
    let html = '<div class="section-9-nasa nasa-mission-control">';
    
    html += '<div class="control-room">';
    
    // SERP Overview
    html += getSerpOverviewSection(data);
    
    // AI Overview (jeśli istnieje)
    const aiOverviewFromItems = data.serp_items ? data.serp_items.find(item => item.type === 'ai_overview') : null;
    const aiReferences = data.serp_ai_references || [];
    if (aiOverviewFromItems || aiReferences.length > 0) {
        html += getAiOverviewSection(data, aiOverviewFromItems, aiReferences);
    }
    
    // SERP Items Table
    html += getSerpItemsSection(data);
    
    // People Also Ask
    if (data.serp_people_also_ask && data.serp_people_also_ask.length > 0) {
        html += getPeopleAlsoAskSection(data);
    }
    
    // Related Searches
    if (data.serp_related_searches && data.serp_related_searches.length > 0) {
        html += getRelatedSearchesSection(data);
    }
    
    html += '</div>'; // Koniec control-room
    html += '</div>'; // Koniec section-9-nasa
    
    serpContainer.innerHTML = html;
    // expose items for Load More
    if (data.serp_items && Array.isArray(data.serp_items)) {
        window.__SERP_ITEMS__ = data.serp_items;
    }
    
    // Inicjalizuj funkcjonalności
    initializeNASASerpInteractions();
}

// ========================================
// HELPER FUNCTIONS - NASA MISSION CONTROL STYLE
// ========================================

function getSerpOverviewSection(data) {
    const totalItems = data.serp_items ? data.serp_items.length : 0;
    const locationCode = data.serp_results?.location_code || 'N/A';
    const seType = data.serp_results?.se_type || 'N/A';
    const checkUrl = data.serp_results?.check_url || '';
    
    let html = `
        <section class="card">
            <div class="overview-grid">
    `;
    
    // Total Results simplified
    html += `
        <article class="panel panel-compact" tabindex="0" aria-label="Total Results">
            <div class="label">Total Results</div>
            <div class="value">${totalItems}</div>
        </article>
    `;
    
    // Location Panel removed
    
    // SE Type Panel removed
    
    html += '</div>'; // Koniec overview-grid
    
    // Check URL Info Panel (kept)
    if (checkUrl) {
        html += `
            <div class="info-panel">
                <div class="info-title">Check URL</div>
                <div class="url-display">${escapeHtml(checkUrl)}</div>
            </div>
        `;
    }
    
    html += '</section>';
    
    return html;
}

function getAiOverviewSection(data, aiOverviewFromItems, aiReferences) {
    let html = `
        <section class="card">
            <div class="display-header">
                <div class="display-title">🤖 AI Overview</div>
                <div class="mission-state"><span class="state-dot"></span> AI GENERATED</div>
            </div>
            
            <article class="panel" tabindex="0" aria-label="AI Overview Analysis">
                <div class="p-head">
                    <span class="code">AI-004</span>
                    <span class="p-status analyzing"></span>
                </div>
    `;
    
    // AI Overview Content
    if (aiOverviewFromItems) {
        const aiText = aiOverviewFromItems.description || 'Brak treści AI Overview';
        html += `
            <div class="ai-overview-panel">
                <div class="ai-header">
                    <div class="ai-icon">🤖</div>
                    <div class="ai-title">Google AI Overview</div>
                </div>
                <div class="ai-content">${escapeHtml(aiText)}</div>
            </div>
        `;
    }
    
    // AI References
    if (aiReferences.length > 0) {
        html += `
            <div style="margin-top:16px">
                <div class="label">📚 AI References (${aiReferences.length} sources)</div>
                <div style="margin-top:8px;display:grid;gap:8px">
        `;
        
        aiReferences.forEach((ref, index) => {
            html += `
                <div style="background:#ffffff;border:1px solid var(--border);border-radius:6px;padding:10px">
                    <div style="display:flex;gap:8px;align-items:start">
                        <div style="background:var(--blue);color:white;font-weight:800;font-size:10px;
                                  width:24px;height:24px;border-radius:50%;display:flex;align-items:center;
                                  justify-content:center;flex-shrink:0">${index + 1}</div>
                        <div style="flex:1">
                            <div style="font-weight:700;font-size:11px;color:var(--text);margin-bottom:4px">
                                ${ref.url ? `<a href="${escapeHtml(ref.url)}" target="_blank" style="color:var(--blue);text-decoration:none">${escapeHtml(ref.title || 'Bez tytułu')}</a>` : escapeHtml(ref.title || 'Bez tytułu')}
                            </div>
                            ${ref.domain ? `<div style="font-size:9px;color:var(--cyan);margin-bottom:4px">🌐 ${escapeHtml(ref.domain)}</div>` : ''}
                            ${ref.text_fragment ? `<div style="font-size:10px;color:var(--muted);line-height:1.4">${escapeHtml(ref.text_fragment)}</div>` : ''}
                            ${ref.date ? `<div style="font-size:9px;color:var(--muted);margin-top:4px">📅 ${escapeHtml(ref.date)}</div>` : ''}
                        </div>
                    </div>
                </div>
            `;
        });
        
        html += '</div></div>';
    }
    
    html += '</article></section>';
    
    return html;
}

function getSerpItemsSection(data) {
    const displayedItems = data.serp_items ? Math.min(data.serp_items.length, 15) : 0;
    const totalItems = data.serp_items ? data.serp_items.length : 0;
    
    let html = `
        <section class="card">
            <div style="padding:10px 16px;font-weight:800;color:var(--blue)">SERP Results</div>
            <div style="padding:0 16px 6px;color:var(--muted);font-size:10px">Showing 1-15 of ${totalItems} results</div>
            
            <article class="panel" tabindex="0" aria-label="SERP Items Table">
    `;
    
    if (data.serp_items && data.serp_items.length > 0) {
        html += `
            <div class="serp-container">
                <table class="serp-table">
                <thead>
                    <tr>
                            <th style="width:50px">Rank</th>
                            <th style="width:120px">Type</th>
                            <th style="width:250px">Title</th>
                            <th style="width:250px">URL</th>
                        <th>Description</th>
                    </tr>
                </thead>
                <tbody>
        `;
        
        data.serp_items.slice(0, 15).forEach(item => {
            const rank = item.rank_absolute || 'N/A';
            const type = item.type || 'unknown';
            const title = item.title || 'No title';
            const url = item.url || 'No URL';
            const description = item.description || 'No description';
            
            // Mapowanie typów na klasy CSS
            let typeClass = 'type-organic';
            if (type.includes('paa') || type.includes('people')) typeClass = 'type-paa';
            else if (type.includes('related')) typeClass = 'type-related';
            else if (type.includes('review')) typeClass = 'type-reviews';
            else if (type.includes('ai')) typeClass = 'type-ai';
            else if (type.includes('featured')) typeClass = 'type-featured';
            
            html += `
                <tr>
                    <td><span class="rank-badge">${rank}</span></td>
                    <td><span class="serp-type ${typeClass}">${type}</span></td>
                    <td><div class="serp-title">${escapeHtml(title)}</div></td>
                    <td><div class="serp-url">${escapeHtml(url)}</div></td>
                    <td><div class="serp-desc">${escapeHtml(description.substring(0, 100))}${description.length > 100 ? '...' : ''}</div></td>
                </tr>
            `;
        });
        
        html += '</tbody></table></div>';
        
        if (totalItems > 15) {
            html += `<div style="text-align:center;margin-top:12px">
                        <button id="loadMoreSerp" class="load-more">Load More Results</button>
                     </div>`;
        }
        
    } else {
        html += '<div style="text-align:center;padding:40px;color:var(--muted);font-style:italic">📋 Brak danych SERP items</div>';
    }
    
    html += '</article></section>';
    
    return html;
}

function getPeopleAlsoAskSection(data) {
    let html = `
        <section class="card">
            <div style="padding:10px 16px;font-weight:800;color:var(--blue)">People Also Ask</div>
            <div style="padding:0 16px 6px;color:var(--muted);font-size:10px">${data.serp_people_also_ask.length} questions</div>
            <div style="padding:0 16px 6px;color:#0b3d91;font-size:11px">Questions people ask about this keyword. Use these to create FAQ content and answer user questions.</div>
            
            <article class="panel" tabindex="0" aria-label="People Also Ask Section">
                <div class="paa-list">
    `;
    
    data.serp_people_also_ask.slice(0, 8).forEach((paa, index) => {
        const question = paa.question || 'No question';
        const domain = paa.expanded_domain || '';
        const description = paa.expanded_description || '';
        
        html += `
            <div class="paa-item">
                <div class="paa-question" onclick="window.toggleNASAPAA(this)">
                    <span>${escapeHtml(question)}</span>
                    <span class="paa-toggle">▶</span>
                </div>
                <div class="paa-answer">
                    <div class="paa-content">
                        ${domain ? `<div class="paa-source">${escapeHtml(domain)}</div>` : ''}
                        ${description ? `<div class="paa-text">${escapeHtml(description.substring(0, 200))}${description.length > 200 ? '...' : ''}</div>` : ''}
                    </div>
                </div>
            </div>
        `;
    });
    
    html += '</div></article></section>';
    
    return html;
}

function getRelatedSearchesSection(data) {
    let html = `
        <section class="card">
            <div style="padding:10px 16px;font-weight:800;color:var(--blue)">Related Searches</div>
            <div style="padding:0 16px 6px;color:var(--muted);font-size:10px">${data.serp_related_searches.length} queries</div>
            <div style="padding:0 16px 6px;color:#0b3d91;font-size:11px">Related queries from Google. Explore these for additional keyword opportunities and content ideas.</div>
            
            <article class="panel" tabindex="0" aria-label="Related Searches">
                <div class="related-grid">
    `;
    
        data.serp_related_searches.slice(0, 10).forEach(search => {
        const keyword = search.keyword || 'No keyword';
        html += `<div class="related-item">${escapeHtml(keyword)}</div>`;
        });
    
    html += '</div></article></section>';
    
    return html;
}

// ========================================
// UTILITY FUNCTIONS
// ========================================

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ========================================
// NASA MISSION CONTROL INTERACTIONS
// ========================================

function toggleNASAPAA(element) {
    const item = element.closest('.paa-item');
    const answer = item.querySelector('.paa-answer');
    const toggle = element.querySelector('.paa-toggle');
    
    answer.classList.toggle('open');
    toggle.classList.toggle('open');
    toggle.textContent = answer.classList.contains('open') ? '▼' : '▶';
}

function initializeNASASerpInteractions() {
    // Related search click animation
    setTimeout(() => {
        const items = document.querySelectorAll('.section-9-nasa .related-item');
        items.forEach(item => {
            item.addEventListener('click', function() {
                this.style.transform = 'scale(0.95)';
                setTimeout(() => {
                    this.style.transform = '';
                }, 150);
            });
        });

        // Load more results
        const btn = document.getElementById('loadMoreSerp');
        if (btn) {
            btn.addEventListener('click', () => {
                const tableBody = document.querySelector('.section-9-nasa .serp-table tbody');
                if (!tableBody) return;
                const existingRows = tableBody.querySelectorAll('tr').length;
                const allItems = (window.__SERP_ITEMS__ || []);
                const nextItems = allItems.slice(existingRows, existingRows + 15);
                nextItems.forEach(item => {
                    const rank = item.rank_absolute || 'N/A';
                    const type = item.type || 'unknown';
                    const title = item.title || 'No title';
                    const url = item.url || 'No URL';
                    const description = item.description || 'No description';
                    let typeClass = 'type-organic';
                    if (type.includes('paa') || type.includes('people')) typeClass = 'type-paa';
                    else if (type.includes('related')) typeClass = 'type-related';
                    else if (type.includes('review')) typeClass = 'type-reviews';
                    else if (type.includes('ai')) typeClass = 'type-ai';
                    else if (type.includes('featured')) typeClass = 'type-featured';
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td><span class="rank-badge">${rank}</span></td>
                        <td><span class="serp-type ${typeClass}">${type}</span></td>
                        <td><div class="serp-title">${escapeHtml(title)}</div></td>
                        <td><div class="serp-url">${escapeHtml(url)}</div></td>
                        <td><div class="serp-desc">${escapeHtml(description.substring(0, 100))}${description.length > 100 ? '...' : ''}</div></td>
                    `;
                    tableBody.appendChild(row);
                });
        if (allItems.length <= existingRows + 15) {
                    btn.disabled = true;
                    btn.textContent = 'No more results';
                }
            });
        }
    }, 100);
}

// ========================================
// EXPORT FUNCTIONS TO GLOBAL SCOPE
// ========================================
window.displaySerpAnalysis = displaySerpAnalysis;
window.escapeHtml = escapeHtml;
window.toggleNASAPAA = toggleNASAPAA;

console.log('✅ SEKCJA 9: Enhanced SERP Analysis - NASA Mission Control Style załadowany');