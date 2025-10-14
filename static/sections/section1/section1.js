/**
 * SEKCJA 1: EXTENDED HEADER
 * Wyświetla rozszerzony nagłówek słowa kluczowego z metadanymi
 */

// ========================================
// SEKCJA 1: EXTENDED HEADER - PEŁNA IMPLEMENTACJA
// ========================================

function displayKeywordHeader(data) {
    console.log('🎯 SEKCJA 1: Renderowanie Extended Header');
    
    const headerContainer = document.getElementById('keywordHeader');
    if (!headerContainer) {
        console.error('❌ Kontener #keywordHeader nie znaleziony');
        return;
    }

    // Główne słowo kluczowe
    let html = `
        <div class="keyword-header">
            <div class="keyword-identity">🎯 ${escapeHtml(data.keyword_name || 'N/A')}</div>
            <div class="geo-info">📍 GEO: ${data.location_code || 'N/A'} | ${(data.language_code || 'N/A').toUpperCase()}</div>
    `;
    
    // Badges
    html += '<div class="badges-container">';
    
    // Badge Sugestia
    if (data.is_suggestion) {
        html += '<span class="badge suggestion">🏷️ SUGESTIA</span>';
    }
    
    // Badge Depth
    if (data.depth && data.depth > 0) {
        html += `<span class="badge depth">📊 DEPTH: ${data.depth}</span>`;
    }
    
    // Badge ostrzeżenie o języku
    if (data.is_another_language) {
        html += '<span class="badge language-warning">⚠️ INNY JĘZYK</span>';
    }
    
    // Badges kategorii
    if (data.categories && data.categories.length > 0) {
        data.categories.forEach(category => {
            html += `<span class="badge category">🏷️ ${escapeHtml(category)}</span>`;
        });
    }
    
    html += '</div>';
    
    // Seed keyword (jeśli różne)
    if (data.seed_keyword && data.seed_keyword !== data.keyword_name) {
        html += `<div style="margin: 10px 0; font-weight: bold;">🌱 SEED: ${escapeHtml(data.seed_keyword)}</div>`;
    }
    
    // Metadata grid
    html += '<div class="metadata-grid">';
    
    // Detected Language
    if (data.detected_language) {
        html += `
            <div class="metadata-item">
                <div class="metadata-label">🗣️ Wykryty język</div>
                <div class="metadata-value">${escapeHtml(data.detected_language.toUpperCase())}</div>
            </div>
        `;
    }
    
    // Core Keyword
    if (data.core_keyword) {
        html += `
            <div class="metadata-item">
                <div class="metadata-label">🏷️ Słowo główne</div>
                <div class="metadata-value">${escapeHtml(data.core_keyword)}</div>
            </div>
        `;
    }
    
    // Clustering Algorithm
    if (data.synonym_clustering_algorithm) {
        html += `
            <div class="metadata-item">
                <div class="metadata-label">🧠 Algorytm</div>
                <div class="metadata-value">${escapeHtml(data.synonym_clustering_algorithm)}</div>
            </div>
        `;
    }
    
    // Last Updated
    if (data.last_updated) {
        const date = formatDateTime(data.last_updated);
        html += `
            <div class="metadata-item">
                <div class="metadata-label">📅 Ostatnia aktualizacja</div>
                <div class="metadata-value">${date}</div>
            </div>
        `;
    }
    
    // Total Cost
    html += `
        <div class="metadata-item">
            <div class="metadata-label">💰 Koszt całkowity</div>
            <div class="metadata-value">$${(data.api_costs_total || 0).toFixed(4)}</div>
        </div>
    `;
    
    // Data Sources
    if (data.data_sources && data.data_sources.length > 0) {
        html += `
            <div class="metadata-item">
                <div class="metadata-label">🔗 Źródła danych</div>
                <div class="metadata-value">${data.data_sources.map(source => escapeHtml(source)).join(', ')}</div>
            </div>
        `;
    }
    
    html += '</div>'; // Koniec metadata-grid
    html += '</div>'; // Koniec keyword-header
    
    headerContainer.innerHTML = html;
}

// ========================================
// HELPER FUNCTIONS
// ========================================

function formatDateTime(datetime) {
    if (!datetime) return 'N/A';
    try {
        const date = new Date(datetime);
        return date.toLocaleString('pl-PL', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        });
    } catch (e) {
        return 'N/A';
    }
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ========================================
// EXPORT FUNCTIONS TO GLOBAL SCOPE
// ========================================
window.displayKeywordHeader = displayKeywordHeader;
window.formatDateTime = formatDateTime;
window.escapeHtml = escapeHtml;

console.log('✅ SEKCJA 1: Extended Header - Pełna implementacja załadowana'); 