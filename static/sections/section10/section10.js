/**
 * SEKCJA 10: ENHANCED AUTOCOMPLETE ANALYSIS - NASA MISSION CONTROL STYLE
 */

function displayAutocompleteAnalysis(data) {
    console.log('🔮 SEKCJA 10: Renderowanie Enhanced Autocomplete Analysis - NASA Mission Control');
    
    const container = document.getElementById('autocompleteAnalysis');
    if (!container) {
        console.error('❌ Kontener #autocompleteAnalysis nie znaleziony');
        return;
    }

    // Sprawdź czy mamy dane autocomplete
    if (!data.autocomplete_results || !data.autocomplete_suggestions) {
        container.innerHTML = `
            <div class="section-10-nasa nasa-mission-control">
                <div style="text-align:center;padding:60px;color:var(--muted)">
                    <div style="font-size:48px;margin-bottom:15px">🔍</div>
                    <div style="font-size:18px;margin-bottom:10px;font-weight:700">Brak Danych Autocomplete</div>
                    <div style="font-size:14px;opacity:0.8">Dane autocomplete nie są dostępne dla tego słowa kluczowego</div>
                </div>
            </div>
        `;
        return;
    }

    const autocompleteResults = data.autocomplete_results;
    const autocompleteSuggestions = data.autocomplete_suggestions || [];

    console.log(`📊 Dane autocomplete: ${autocompleteSuggestions.length} sugestii`);

    // Dodaj wrapper z klasą NASA
    let html = '<div class="section-10-nasa nasa-mission-control">';
    
    html += '<div class="control-room">';
    
    // Only simplified suggestions section
    html += getAutocompleteSuggestionsSection(autocompleteSuggestions);
    
    html += '</div>'; // Koniec control-room
    html += '</div>'; // Koniec section-10-nasa
    
    container.innerHTML = html;
}

// ========================================
// HELPER FUNCTIONS - NASA MISSION CONTROL STYLE
// ========================================

function getAutocompleteMetadataSection(results) {
    if (!results) return '';

    const location_flag = getCountryFlag(results.location_code);
    const language_flag = getLanguageFlag(results.language_code);
    const client_icon = getClientIcon(results.client);
    const freshness_hours = results.data_freshness_hours || 0;
    const freshness_status = getFreshnessStatus(freshness_hours);
    const query_date = results.query_date ? formatDate(results.query_date) : 'N/A';

    let html = `
        <section class="card">
            <div class="display-header">
                <div class="display-title">📊 A. Enhanced Autocomplete Metadata</div>
                <div class="mission-state"><span class="state-dot"></span> DATA CAPTURED</div>
            </div>
            
            <div class="metadata-grid">
    `;

    // Słowo Kluczowe
    html += `
        <article class="panel" tabindex="0">
            <div class="p-head">
                <span class="code">META-001</span>
                <span class="p-status analyzing"></span>
            </div>
            <div class="label">Słowo Kluczowe</div>
            <div class="value" style="font-size:12px">${escapeHtml(results.keyword || 'N/A')}</div>
        </article>
    `;

    // Lokalizacja
    html += `
        <article class="panel" tabindex="0">
            <div class="p-head">
                <span class="code">LOC-002</span>
                <span class="p-status nominal"></span>
            </div>
            <div class="label">Lokalizacja</div>
            <div class="value">${location_flag} ${results.location_code || 'N/A'}</div>
        </article>
    `;

    // Język
    html += `
        <article class="panel" tabindex="0">
            <div class="p-head">
                <span class="code">LANG-003</span>
                <span class="p-status nominal"></span>
            </div>
            <div class="label">Język</div>
            <div class="value">${language_flag} ${results.language_code || 'N/A'}</div>
        </article>
    `;

    // Domena SE
    html += `
        <article class="panel" tabindex="0">
            <div class="p-head">
                <span class="code">DOM-004</span>
                <span class="p-status processing"></span>
            </div>
            <div class="label">Domena SE</div>
            <div class="value" style="font-size:13px">${results.se_domain || 'google.com'}</div>
        </article>
    `;

    // Klient
    html += `
        <article class="panel" tabindex="0">
            <div class="p-head">
                <span class="code">CLI-005</span>
                <span class="p-status processing"></span>
            </div>
            <div class="label">Klient</div>
            <div class="value" style="font-size:11px">${client_icon} ${results.client || 'N/A'}</div>
        </article>
    `;

    // Pozycja Kursora
    html += `
        <article class="panel" tabindex="0">
            <div class="p-head">
                <span class="code">CUR-006</span>
                <span class="p-status analyzing"></span>
            </div>
            <div class="label">Pozycja Kursora</div>
            <div class="value-large">${results.cursor_position || 0}</div>
        </article>
    `;

    // Liczba Pozycji
    html += `
        <article class="panel" tabindex="0">
            <div class="p-head">
                <span class="code">POS-007</span>
                <span class="p-status analyzing"></span>
            </div>
            <div class="label">Liczba Pozycji</div>
            <div class="value-large">${results.items_count || 0}</div>
        </article>
    `;

    // Suma Sugestii
    html += `
        <article class="panel" tabindex="0">
            <div class="p-head">
                <span class="code">SUM-008</span>
                <span class="p-status analyzing"></span>
            </div>
            <div class="label">Suma Sugestii</div>
            <div class="value-large">${results.summation_count || 0}</div>
        </article>
    `;

    // Data Zapytania
    html += `
        <article class="panel" tabindex="0">
            <div class="p-head">
                <span class="code">DATE-009</span>
                <span class="p-status fresh"></span>
            </div>
            <div class="label">Data Zapytania</div>
            <div class="value" style="font-size:11px">${query_date}</div>
        </article>
    `;

    // Świeżość Danych
    html += `
        <article class="panel" tabindex="0">
            <div class="p-head">
                <span class="code">FRSH-010</span>
                <span class="p-status fresh"></span>
            </div>
            <div class="label">Świeżość Danych</div>
            <div class="value" style="font-size:14px">${freshness_status.icon} ${freshness_status.text}</div>
            <span class="badge ${freshness_status.badgeClass}" style="margin-top:4px">${freshness_status.badge}</span>
        </article>
    `;

    // Koszt API
    html += `
        <article class="panel" tabindex="0">
            <div class="p-head">
                <span class="code">COST-011</span>
                <span class="p-status nominal"></span>
            </div>
            <div class="label">Koszt API</div>
            <div class="value">$${(results.api_cost || 0).toFixed(4)}</div>
        </article>
    `;

    // Korekta Pisowni
    const hasSpellCorrection = results.spell_correction_enabled || false;
    html += `
        <article class="panel" tabindex="0">
            <div class="p-head">
                <span class="code">SPEL-012</span>
                <span class="p-status nominal"></span>
            </div>
            <div class="label">Korekta Pisowni</div>
            <div class="value">${hasSpellCorrection ? '✅ Tak' : '❌ Nie'}</div>
            <span class="badge ${hasSpellCorrection ? 'badge-high' : 'badge-no'}" style="margin-top:4px">${hasSpellCorrection ? 'Enabled' : 'No Correction'}</span>
        </article>
    `;

    html += '</div></section>';

    return html;
}

function getAutocompleteSuggestionsSection(suggestions) {
    const suggestionsCount = suggestions.length;

    let html = `
        <section class="card">
            <div style="padding:10px 16px;font-weight:800;color:var(--blue)">Suggestions</div>
            <div style="padding:0 16px 6px;color:var(--muted);font-size:10px">Showing ${suggestionsCount} suggestions</div>
            
            <article class="panel" tabindex="0">
    `;

    if (suggestions.length > 0) {
        html += `
            <div class="suggestions-container">
                <table class="suggestions-table">
                    <thead>
                        <tr>
                            <th style="width:60px">Rank</th>
                            <th>Suggestion</th>
                            <th style="width:80px">Words</th>
                        </tr>
                    </thead>
                    <tbody>
        `;

        suggestions.forEach(sugg => {
            const rank = sugg.position || 0;
            const suggestionText = sugg.suggestion || 'N/A';
            const wordCount = sugg.word_count || 0;

            html += `
                <tr>
                    <td><span class="rank-badge">${rank}</span></td>
                    <td><span class="suggestion-text">${escapeHtml(suggestionText)}</span></td>
                    <td>${wordCount}</td>
                </tr>
            `;
        });

        html += '</tbody></table></div>';

    } else {
        html += '<div style="text-align:center;padding:40px;color:var(--muted);font-style:italic">Brak sugestii autocomplete</div>';
    }

    html += '</article></section>';

    return html;
}

function getAutocompleteBusinessIntelligenceSection(results, suggestions) {
    // Oblicz statystyki
    const categoryStats = getCategoryStats(suggestions);
    const avgRelevance = suggestions.length > 0 ? 
        (suggestions.reduce((sum, s) => sum + (s.relevance || 0), 0) / suggestions.length).toFixed(1) : 0;
    const avgWords = suggestions.length > 0 ?
        Math.round(suggestions.reduce((sum, s) => sum + (s.word_count || 0), 0) / suggestions.length) : 0;
    const questionCount = suggestions.filter(s => s.is_question).length;

    let html = `
        <section class="card">
            <div class="display-header">
                <div class="display-title">🧠 C. Enhanced Autocomplete Categories & Business Intelligence</div>
                <div class="mission-state"><span class="state-dot"></span> INTELLIGENCE PROCESSED</div>
            </div>
            
            <article class="panel" tabindex="0">
                <div class="p-head">
                    <span class="code">CAT-014</span>
                    <span class="p-status analyzing"></span>
                </div>
                
                <div class="label">📂 Kategorie Sugestii</div>
    `;

    // Kategorie
    Object.keys(categoryStats).forEach(category => {
        const count = categoryStats[category];
        html += `
            <div class="category-item">
                <div class="category-header">
                    <div class="category-title">${capitalize(category)}</div>
                    <div class="category-count">${count} sugestii</div>
                </div>
            </div>
        `;
    });

    // Content Expansion
    html += `
        <div class="label" style="margin-top:16px">📈 Business Intelligence & Content Opportunities</div>
        
        <div class="info-panel">
            <div class="info-title">📝 Content Expansion</div>
            <div class="info-text">${suggestions.length} sugestii do poszerzenia tematyki treści</div>
        </div>
    `;

    // BI Grid
    html += `
        <div class="bi-grid">
            <div class="bi-stat">
                <div class="bi-label">Suma Sugestii</div>
                <div class="bi-value">${suggestions.length}</div>
            </div>
            <div class="bi-stat">
                <div class="bi-label">Średnia Relewancja</div>
                <div class="bi-value">${avgRelevance}</div>
            </div>
            <div class="bi-stat">
                <div class="bi-label">Średnia Długość</div>
                <div class="bi-value">${avgWords} słów</div>
            </div>
            <div class="bi-stat">
                <div class="bi-label">Pytania</div>
                <div class="bi-value">${questionCount}</div>
            </div>
        </div>
    `;

    html += '</article></section>';

    return html;
}

function getAutocompleteSummarySection(results, suggestions) {
    const topCategory = getTopCategory(suggestions);
    const avgRelevance = suggestions.length > 0 ? 
        (suggestions.reduce((sum, s) => sum + (s.relevance || 0), 0) / suggestions.length).toFixed(1) : 0;

    let html = `
        <section class="card">
            <div class="display-header">
                <div class="display-title">🎯 Podsumowanie Analizy</div>
                <div class="mission-state"><span class="state-dot"></span> ANALYSIS COMPLETE</div>
            </div>
            
            <div class="summary-panel">
                <div class="summary-title">
                    <span>📊</span>
                    <span>Wnioski i Rekomendacje</span>
                </div>
                <div class="summary-text">
                    Analiza autocomplete dla tego słowa kluczowego ujawniła <strong>${suggestions.length} sugestii</strong> 
                    ${topCategory ? `z dominującą kategorią <strong>"${capitalize(topCategory)}"</strong>` : ''}. 
                    Średnia relewancja wynosi <strong>${avgRelevance}</strong>. 
                    Rekomendujemy wykorzystanie tych danych do optymalizacji zawartości i strategii SEO.
                </div>
            </div>
        </section>
    `;

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

function capitalize(str) {
    if (!str) return '';
    return str.charAt(0).toUpperCase() + str.slice(1);
}

function getCountryFlag(locationCode) {
    const flags = {
        '2616': '🇵🇱',
        '2840': '🇺🇸',
        '2826': '🇬🇧',
        '2276': '🇩🇪',
        '2250': '🇫🇷'
    };
    return flags[locationCode] || '🌍';
}

function getLanguageFlag(languageCode) {
    const flags = {
        'pl': '🇵🇱',
        'en': '🇺🇸',
        'de': '🇩🇪',
        'fr': '🇫🇷',
        'es': '🇪🇸'
    };
    return flags[languageCode] || '🌐';
}

function getClientIcon(client) {
    const icons = {
        'chrome': '🌐',
        'gws-wiz-serp': '🔍',
        'firefox': '🦊',
        'safari': '🧭'
    };
    return icons[client] || '💻';
}

function getFreshnessStatus(hours) {
    if (hours < 24) {
        return { icon: '🟢', text: 'Świeże', badge: 'Fresh', badgeClass: 'badge-fresh' };
    } else if (hours < 168) {
        return { icon: '🟡', text: 'Aktualne', badge: 'Recent', badgeClass: 'badge-medium' };
    } else {
        return { icon: '🔴', text: 'Stare', badge: 'Old', badgeClass: 'badge-no' };
    }
}

function formatDate(dateString) {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleString('pl-PL', { 
        year: 'numeric', 
        month: '2-digit', 
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function getCategoryStats(suggestions) {
    const stats = {};
    suggestions.forEach(s => {
        const intent = s.intent || 'unknown';
        stats[intent] = (stats[intent] || 0) + 1;
    });
    return stats;
}

function getTopCategory(suggestions) {
    const stats = getCategoryStats(suggestions);
    let topCategory = null;
    let maxCount = 0;
    Object.keys(stats).forEach(category => {
        if (stats[category] > maxCount) {
            maxCount = stats[category];
            topCategory = category;
        }
    });
    return topCategory;
}

// ========================================
// EXPORT FUNCTIONS TO GLOBAL SCOPE
// ========================================
window.displayAutocompleteAnalysis = displayAutocompleteAnalysis;

console.log('✅ SEKCJA 10: Enhanced Autocomplete Analysis - NASA Mission Control Style załadowany');