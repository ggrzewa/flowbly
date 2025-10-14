// ========================================
// SEKCJA 8: ENHANCED RELATED KEYWORDS - NASA MISSION CONTROL STYLE
// ========================================

function displayRelatedKeywordsAnalysis(data) {
    console.log('🔗 SEKCJA 8: Renderowanie Enhanced Related Keywords - NASA Mission Control');
    
    const relatedContainer = document.getElementById('relatedKeywordsAnalysis');
    if (!relatedContainer) {
        console.error('❌ Kontener #relatedKeywordsAnalysis nie znaleziony');
        return;
    }
    
    console.log('🔗 SEKCJA 8 DEBUG - relatedKeywordsAnalysis data:', data);
    
    // Dodaj wrapper z klasą NASA
    let html = '<div class="section-8-nasa nasa-mission-control">';
    
    html += '<div class="control-room">';
    
    // SUBSEKCJA A: Google Trends Related Data
    html += getGoogleTrendsSection(data);
    
    // SUBSEKCJA B: Complete Related Keywords
    html += getCompleteRelatedKeywordsSection(data);
    
    html += '</div>'; // Koniec control-room
    html += '</div>'; // Koniec section-8-nasa
    
    relatedContainer.innerHTML = html;
    
    // Inicjalizuj funkcjonalności
    initializeNASAViewSwitchers();
    initializeNASAAnimations();
}

// ========================================
// HELPER FUNCTIONS - NASA MISSION CONTROL STYLE
// ========================================

function getGoogleTrendsSection(data) {
    let html = `
        <section class="card">
            <div class="label" style="padding:10px 16px;font-weight:800;color:var(--blue)">Related Topics & Queries</div>
            <div class="trends-grid">
    `;
    
    // Related Topics Panel
    html += getRelatedTopicsPanel(data);
    
    // Related Queries Panel
    html += getRelatedQueriesPanel(data);
    
    html += '</div>'; // Koniec trends-grid
    
    // Removed data source panel
    
    html += '</section>';
    
    return html;
}

function getRelatedTopicsPanel(data) {
    let html = `
        <article class="panel panel-large" tabindex="0" aria-label="Related Topics Analysis">
            <div class="label">📊 Related Topics</div>
            <div style="font-size:10px;color:var(--muted);margin-bottom:8px">Values show relative popularity (0-100). A score of 100 represents peak popularity, 50 means half as popular.</div>
    `;
    
    if (data.topics_list) {
        try {
            const topicsData = typeof data.topics_list === 'string' ? 
                JSON.parse(data.topics_list) : data.topics_list;
            
            // Top Topics
            if (topicsData.top && topicsData.top.length > 0) {
                html += `
                    <div style="font-weight:700;color:var(--purple);margin-bottom:8px;font-size:12px">
                        🔝 Top Topics:
                    </div>
                    <div class="tag-cloud">
                `;
                
                topicsData.top.slice(0, 10).forEach(topic => {
                    html += `<div class="tag-item">${topic.topic_title}<span class="tag-score">(${topic.value})</span></div>`;
                });
                
                html += '</div>';
            }
            
            // Rising Topics
            if (topicsData.rising && topicsData.rising.length > 0) {
                html += `
                    <div style="font-weight:700;color:var(--orange);margin:16px 0 8px;font-size:12px">📈 Rising Topics:</div>
                    <div style="font-size:10px;color:var(--muted);margin-bottom:6px">Values show growth rate as percentage. Higher percentages indicate rapidly growing interest.</div>
                    <div class="tag-cloud">
                `;
                
                topicsData.rising.slice(0, 8).forEach(topic => {
                    html += `<div class="tag-item rising-tag">${topic.topic_title}<span class="rising-percent">+${topic.value}%</span></div>`;
                });
                
                html += '</div>';
            }
            
        } catch (e) {
            console.error('Błąd parsowania topics_list:', e);
            html += '<div style="color:var(--red);font-style:italic">❌ Błąd parsowania topics</div>';
        }
    } else {
        html += '<div style="color:var(--muted);font-style:italic">🏷️ Brak danych topics</div>';
    }
    
    html += '</article>';
    
    return html;
}

function getRelatedQueriesPanel(data) {
    let html = `
        <article class="panel panel-large" tabindex="0" aria-label="Related Queries Analysis">
            <div class="label">🔍 Related Queries</div>
            <div style="font-size:10px;color:var(--muted);margin-bottom:8px">Values show relative popularity (0-100). A score of 100 represents peak popularity, 50 means half as popular.</div>
    `;
    
    if (data.queries_list) {
        try {
            const queriesData = typeof data.queries_list === 'string' ? 
                JSON.parse(data.queries_list) : data.queries_list;
            
            // Top Queries
            if (queriesData.top && queriesData.top.length > 0) {
                html += `
                    <div style="font-weight:700;color:var(--purple);margin-bottom:8px;font-size:12px">
                        🔝 Top Queries:
                    </div>
                    <div class="query-list">
                `;
                
                queriesData.top.slice(0, 8).forEach(query => {
                    html += `
                        <div class="query-item">
                            <span class="query-text">${query.query}</span>
                            <span class="query-score">${query.value}</span>
                        </div>
                    `;
                });
                
                html += '</div>';
            }
            
            // Rising Queries
            if (queriesData.rising && queriesData.rising.length > 0) {
                html += `
                    <div style="font-weight:700;color:var(--orange);margin:16px 0 8px;font-size:12px">
                        📈 Rising Queries:
                    </div>
                    <div class="query-list">
                `;
                
                queriesData.rising.slice(0, 6).forEach(query => {
                    html += `
                        <div class="query-item">
                            <span class="query-text">${query.query}</span>
                            <span class="query-score query-rising">+${query.value}%</span>
                        </div>
                    `;
                });
                
                html += '</div>';
            }
            
        } catch (e) {
            console.error('Błąd parsowania queries_list:', e);
            html += '<div style="color:var(--red);font-style:italic">❌ Błąd parsowania queries</div>';
        }
    } else {
        html += '<div style="color:var(--muted);font-style:italic">🔍 Brak danych queries</div>';
    }
    
    html += '</article>';
    
    return html;
}

function getCompleteRelatedKeywordsSection(data) {
    let html = `
        <section class="card">
            <div class="label" style="padding:10px 16px;font-weight:800;color:var(--blue)">Keyword Suggestions</div>
            
            <div class="view-toggle">
                <button class="toggle-btn" onclick="switchNASAView('table')">TABLE</button>
                <button class="toggle-btn active" onclick="switchNASAView('intents')">BY INTENT</button>
        </div>
    `;
    
    if (data.related_keywords && data.related_keywords.length > 0) {
        // Table View
        html += getTableView(data.related_keywords);
        
        // Intents View
        html += getIntentsView(data.related_keywords);
        
    } else {
        html += `
            <div style="text-align:center;padding:40px;color:var(--muted);font-style:italic">
                🔗 Brak danych related keywords
            </div>
        `;
    }
    
    html += '</section>';
    
    return html;
}

function getTableView(relatedKeywords) {
    let html = `
        <div id="table-view" class="view-content">
            <article class="panel" tabindex="0" aria-label="Related Keywords Table">
                <div class="keywords-container">
                    <table class="keywords-table">
                    <thead>
                        <tr>
                            <th>Related Keyword</th>
                            <th>Volume</th>
                            <th>CPC</th>
                            <th>Intent</th>
                            <th>Trend</th>
                        </tr>
                    </thead>
                    <tbody>
        `;
        
        // Sortuj według depth, potem relevance_score
    const sortedKeywords = relatedKeywords.sort((a, b) => {
            if (a.depth !== b.depth) return a.depth - b.depth;
            return (b.relevance_score || 0) - (a.relevance_score || 0);
        });
        
    sortedKeywords.forEach(relation => {
        const keywordData = relation.keywords || {};
        const keywordName = keywordData.keyword || 'Unknown';
        const volume = formatNumber(relation.search_volume || keywordData.search_volume || 0);
        const cpc = (keywordData.cpc || 0).toFixed(2);
        const intent = keywordData.main_intent || 'unknown';
        const trend = keywordData.monthly_trend_pct || 0;
        const trendIcon = trend > 0 ? '📈' : trend < 0 ? '📉' : '➖';
        
        html += `
            <tr>
                <td style="font-weight:600;color:var(--text)">${keywordName}</td>
                <td>${volume}</td>
                <td>$${cpc}</td>
                <td><span class="intent-badge intent-${intent}">${intent}</span></td>
                <td><span class="trend-neutral">${trendIcon} ${trend}%</span></td>
            </tr>
        `;
    });
            
            html += `
                        </tbody>
                    </table>
                </div>
            </article>
                </div>
            `;
    
    return html;
}

function getIntentsView(relatedKeywords) {
    // Grupuj według intencji
    const keywordsByIntent = {};
    relatedKeywords.forEach(relation => {
        const keywordData = relation.keywords || {};
        const intent = keywordData.main_intent || 'unknown';
        if (!keywordsByIntent[intent]) {
            keywordsByIntent[intent] = [];
        }
        keywordsByIntent[intent].push(relation);
    });
    
    // Definicja intencji
    const intentInfo = {
        'commercial': { icon: '💰', name: 'Commercial', desc: 'Słowa związane z zakupami i transakcjami' },
        'transactional': { icon: '🛒', name: 'Transactional', desc: 'Słowa z wyraźną intencją zakupu' },
        'navigational': { icon: '🧭', name: 'Navigational', desc: 'Słowa związane z konkretną marką/stroną' },
        'informational': { icon: '📚', name: 'Informational', desc: 'Słowa związane z wyszukiwaniem informacji' },
        'unknown': { icon: '❓', name: 'Unknown', desc: 'Nierozpoznana intencja' }
    };
    
    let html = `<div id="intents-view" class="view-content active">`;
    
    // Sortuj intencje według ważności
    const intentOrder = ['commercial', 'transactional', 'navigational', 'informational', 'unknown'];
    
    intentOrder.forEach(intentKey => {
        if (keywordsByIntent[intentKey] && keywordsByIntent[intentKey].length > 0) {
            const keywords = keywordsByIntent[intentKey];
            const info = intentInfo[intentKey];
            
            // Oblicz statystyki
            const totalVolume = keywords.reduce((sum, rel) => {
                const vol = rel.search_volume || rel.keywords?.search_volume || 0;
                return sum + vol;
            }, 0);
            const avgDifficulty = Math.round(keywords.reduce((sum, rel) => {
                const diff = rel.keyword_difficulty || rel.keywords?.keyword_difficulty || 0;
                return sum + diff;
            }, 0) / keywords.length);
            
            html += `
                <div class="intent-section">
                    <div class="intent-header">
                        <div class="intent-icon">${info.icon}</div>
                        <div class="intent-info">
                            <div class="intent-title">${info.name} (${keywords.length} keywords)</div>
                            <div class="intent-stats">📊 ${formatNumber(totalVolume)} total vol</div>
                            <div class="intent-description">${info.desc}</div>
                        </div>
                    </div>
                    <div class="intent-keywords">
            `;
            
            // Sortuj słowa według volume
            keywords.sort((a, b) => {
                const volA = a.search_volume || a.keywords?.search_volume || 0;
                const volB = b.search_volume || b.keywords?.search_volume || 0;
                return volB - volA;
            });
            
            keywords.slice(0, 6).forEach(relation => { // Pokaż tylko pierwsze 6
                const keywordData = relation.keywords || {};
                const keywordName = keywordData.keyword || 'Unknown';
                const volume = formatNumber(relation.search_volume || keywordData.search_volume || 0);
                const cpc = (keywordData.cpc || 0).toFixed(2);
                const trend = keywordData.monthly_trend_pct || 0;
                
                html += `
                    <div class="keyword-card">
                        <div class="keyword-name">${keywordName}</div>
                        <div class="keyword-metrics">
                            <div class="metric">
                                <div class="metric-label">📊 Vol</div>
                                <div class="metric-value">${volume}</div>
                            </div>
                            <div class="metric">
                                <div class="metric-label">💰 CPC</div>
                                <div class="metric-value">$${cpc}</div>
                            </div>
                            <div class="metric">
                                <div class="metric-label">📈 Trend</div>
                                <div class="metric-value trend-neutral">${trend}%</div>
                            </div>
                        </div>
                    </div>
                `;
            });
            
            html += '</div></div>'; // Koniec intent-keywords i intent-section
        }
    });
    
    html += '</div>'; // Koniec intents-view
    
    return html;
}

// ========================================
// UTILITY FUNCTIONS
// ========================================

function formatNumber(num) {
    if (num === null || num === undefined || num === 0) return '0';
    return num.toLocaleString('pl-PL');
}

// ========================================
// NASA MISSION CONTROL INTERACTIONS
// ========================================

function switchNASAView(view) {
    // Update buttons
    document.querySelectorAll('.section-8-nasa .toggle-btn').forEach(btn => btn.classList.remove('active'));
    event.target.classList.add('active');
    
    // Update content
    document.querySelectorAll('.section-8-nasa .view-content').forEach(content => content.classList.remove('active'));
    document.getElementById(view === 'table' ? 'table-view' : 'intents-view').classList.add('active');
}

function initializeNASAViewSwitchers() {
    // Dodatkowa inicjalizacja przełączników jeśli potrzebna
    console.log('🔄 NASA View Switchers initialized');
}

function initializeNASAAnimations() {
    // Tag cloud interactions
    setTimeout(() => {
        const tags = document.querySelectorAll('.section-8-nasa .tag-item, .section-8-nasa .keyword-card');
        tags.forEach(tag => {
            tag.addEventListener('click', function() {
                this.style.transform = 'scale(0.95)';
                setTimeout(() => {
                    this.style.transform = '';
                }, 150);
            });
        });
    }, 100);
}

// ========================================
// EXPORT FUNCTIONS TO GLOBAL SCOPE
// ========================================
window.displayRelatedKeywordsAnalysis = displayRelatedKeywordsAnalysis;
window.switchNASAView = switchNASAView;

console.log('✅ SEKCJA 8: Enhanced Related Keywords - NASA Mission Control Style załadowany');