// ========================================
// SEKCJA 7: ENHANCED COMPETITION ANALYSIS - PEŁNA IMPLEMENTACJA
// ========================================

function displayCompetitionAnalysis(data) {
    console.log('⚔️ SEKCJA 7: Renderowanie Enhanced Competition Analysis');
    
    const competitionContainer = document.getElementById('competitionAnalysis');
    if (!competitionContainer) {
        console.error('❌ Kontener #competitionAnalysis nie znaleziony');
        return;
    }
    
    console.log('⚔️ SEKCJA 7 DEBUG - competitionAnalysis data:', data);
    console.log('  serp_info:', data.serp_info);
    console.log('  backlinks_info:', data.backlinks_info);
    
    let html = '<div class="competition-analysis-content">';
    
    // Informacja o źródle danych
    html += `
        <div class="competition-info-box">
            <p><strong>Źródło:</strong> <span class="field-source">keywords</span> tabela (snapshot data) + dane z SERP analysis</p>
            <p><strong>Dane:</strong> SERP Snapshot Info (serp_info JSONB) + Backlinks Analysis (backlinks_info JSONB)</p>
        </div>
    `;
    
    // Grid z dwoma sekcjami: SERP Info + Backlinks Analysis
    html += '<div class="competition-grid">';
    
    // SEKCJA A: SERP Snapshot Info
    html += '<div class="competition-section">';
    html += '<h4>🔍 SERP Snapshot Info</h4>';
    html += '<p class="section-description">Pole: <span class="field-source">keywords.serp_info</span> (JSONB) - snapshot z momentu analizy</p>';
    
    if (data.serp_info) {
        try {
            const serpData = typeof data.serp_info === 'string' ? 
                JSON.parse(data.serp_info) : data.serp_info;
            
            html += '<div class="serp-info-grid">';
            
            // Results Count
            if (serpData.se_results_count) {
                html += `
                    <div class="serp-info-item">
                        <span class="serp-info-label">Results Count</span>
                        <span class="serp-info-value serp-results-count">${formatNumber(serpData.se_results_count)}</span>
                        <span class="serp-info-source">serp_info.se_results_count</span>
                    </div>
                `;
            }
            
            // SERP Item Types
            if (serpData.serp_item_types && Array.isArray(serpData.serp_item_types)) {
                html += `
                    <div class="serp-info-item serp-types-item">
                        <span class="serp-info-label">SERP Item Types</span>
                        <div class="serp-item-types">
                `;
                serpData.serp_item_types.forEach(type => {
                    const typeClass = getSerpTypeClass(type);
                    html += `<span class="serp-type-badge ${typeClass}">${type}</span>`;
                });
                html += '</div>';
                html += '<span class="serp-info-source">serp_info.serp_item_types[]</span>';
                html += '</div>';
            }
            
            // Check URL
            if (serpData.check_url) {
                html += `
                    <div class="serp-info-item serp-url-item">
                        <span class="serp-info-label">Check URL</span>
                        <div class="serp-check-url">${serpData.check_url}</div>
                        <span class="serp-info-source">serp_info.check_url</span>
                    </div>
                `;
            }
            
            // SE Type
            if (serpData.se_type) {
                html += `
                    <div class="serp-info-item">
                        <span class="serp-info-label">Search Engine</span>
                        <span class="serp-info-value">${serpData.se_type.toUpperCase()}</span>
                        <span class="serp-info-source">serp_info.se_type</span>
                    </div>
                `;
            }
            
            // Last Updated
            if (serpData.last_updated_time) {
                const lastUpdated = new Date(serpData.last_updated_time).toLocaleString('pl-PL');
                html += `
                    <div class="serp-info-item">
                        <span class="serp-info-label">Last Updated</span>
                        <span class="serp-info-value serp-timestamp">${lastUpdated}</span>
                        <span class="serp-info-source">serp_info.last_updated_time</span>
                    </div>
                `;
            }
            
            html += '</div>'; // Koniec serp-info-grid
            
        } catch (e) {
            console.error('Błąd parsowania serp_info:', e);
            html += '<div class="competition-no-data">❌ Błąd parsowania danych SERP</div>';
        }
    } else {
        html += '<div class="competition-no-data">🔍 Brak danych serp_info</div>';
    }
    
    html += '</div>'; // Koniec competition-section A
    
    // SEKCJA B: Backlinks Analysis
    html += '<div class="competition-section">';
    html += '<h4>�� Backlinks Analysis</h4>';
    html += '<p class="section-description">Pole: <span class="field-source">keywords.backlinks_info</span> (JSONB) - TOP-10 średnie metryki linkowe</p>';
    
    if (data.backlinks_info) {
        try {
            const backlinksData = typeof data.backlinks_info === 'string' ? 
                JSON.parse(data.backlinks_info) : data.backlinks_info;
            
            html += '<div class="backlinks-metrics">';
            
            // Avg Backlinks
            if (backlinksData.backlinks !== undefined) {
                const backlinksClass = getBacklinksClass(backlinksData.backlinks);
                html += `
                    <div class="backlinks-metric">
                        <span class="backlinks-label">Avg Backlinks</span>
                        <span class="backlinks-value ${backlinksClass}">${formatNumber(backlinksData.backlinks)}</span>
                        <span class="backlinks-source">backlinks_info.avg_backlinks</span>
                    </div>
                `;
            }
            
            // Avg Dofollow
            if (backlinksData.dofollow !== undefined) {
                const dofollowClass = getBacklinksClass(backlinksData.dofollow);
                html += `
                    <div class="backlinks-metric">
                        <span class="backlinks-label">Avg Dofollow</span>
                        <span class="backlinks-value ${dofollowClass}">${formatNumber(backlinksData.dofollow)}</span>
                        <span class="backlinks-source">backlinks_info.avg_dofollow</span>
                    </div>
                `;
            }
            
            // Avg Referring Domains
            if (backlinksData.referring_domains !== undefined) {
                const refDomainsClass = getBacklinksClass(backlinksData.referring_domains);
                html += `
                    <div class="backlinks-metric">
                        <span class="backlinks-label">Avg Ref Domains</span>
                        <span class="backlinks-value ${refDomainsClass}">${formatNumber(backlinksData.referring_domains)}</span>
                        <span class="backlinks-source">backlinks_info.avg_referring_domains</span>
                    </div>
                `;
            }
            
            // Avg Referring Pages
            if (backlinksData.referring_pages !== undefined) {
                const refPagesClass = getBacklinksClass(backlinksData.referring_pages);
                html += `
                    <div class="backlinks-metric">
                        <span class="backlinks-label">Avg Ref Pages</span>
                        <span class="backlinks-value ${refPagesClass}">${formatNumber(backlinksData.referring_pages)}</span>
                        <span class="backlinks-source">backlinks_info.avg_referring_pages</span>
                    </div>
                `;
            }
            
            // Domain Rank
            if (backlinksData.main_domain_rank !== undefined) {
                html += `
                    <div class="backlinks-metric">
                        <span class="backlinks-label">Main Domain Rank</span>
                        <span class="backlinks-value backlinks-medium">${backlinksData.main_domain_rank.toFixed(1)}</span>
                        <span class="backlinks-source">backlinks_info.main_domain_rank</span>
                    </div>
                `;
            }
            
            // Overall Rank
            if (backlinksData.rank !== undefined) {
                html += `
                    <div class="backlinks-metric">
                        <span class="backlinks-label">Overall Rank</span>
                        <span class="backlinks-value backlinks-medium">${backlinksData.rank.toFixed(1)}</span>
                        <span class="backlinks-source">backlinks_info.rank</span>
                    </div>
                `;
            }
            
            html += '</div>'; // Koniec backlinks-metrics
            
        } catch (e) {
            console.error('Błąd parsowania backlinks_info:', e);
            html += '<div class="competition-no-data">❌ Błąd parsowania danych backlinks</div>';
        }
    } else {
        html += '<div class="competition-no-data">🔗 Brak danych backlinks_info</div>';
    }
    
    html += '</div>'; // Koniec competition-section B
    html += '</div>'; // Koniec competition-grid
    
    // Summary
    html += `
        <div class="competition-summary">
            <h4>⚔️ Wyjaśnienie analizy konkurencji</h4>
            <p><strong>SERP snapshot</strong> zawiera podstawowe informacje o competitive landscape z momentu analizy słowa kluczowego. 
            <strong>Backlinks analysis</strong> pokazuje średnie metryki linkowe dla TOP-10 wyników organicznych, 
            co daje wgląd w poziom trudności pozycjonowania. Te dane pochodzą z tabeli keywords jako skonsolidowane snapshot, 
            a nie live SERP data.</p>
        </div>
    `;
    
    html += '</div>'; // Koniec competition-analysis-content
    
    competitionContainer.innerHTML = html;
}

// ========================================
// HELPER FUNCTIONS
// ========================================

function formatNumber(num) {
    if (num === null || num === undefined) return 'N/A';
    return num.toLocaleString('pl-PL');
}

function getSerpTypeClass(type) {
    const typeLower = type.toLowerCase();
    if (typeLower.includes('organic')) return 'serp-type-organic';
    if (typeLower.includes('paid') || typeLower.includes('ads')) return 'serp-type-paid';
    if (typeLower.includes('features') || typeLower.includes('snippet') || typeLower.includes('knowledge')) return 'serp-type-features';
    return 'serp-type-default';
}

function getBacklinksClass(value) {
    if (value >= 1000) return 'backlinks-high';
    if (value >= 100) return 'backlinks-medium';
    return 'backlinks-low';
}

// ========================================
// EXPORT FUNCTIONS TO GLOBAL SCOPE
// ========================================
window.displayCompetitionAnalysis = displayCompetitionAnalysis;
window.getSerpTypeClass = getSerpTypeClass;
window.getBacklinksClass = getBacklinksClass;

console.log('✅ SEKCJA 7: Enhanced Competition Analysis - Pełna implementacja załadowana'); 