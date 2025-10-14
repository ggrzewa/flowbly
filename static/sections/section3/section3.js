/**
 * SEKCJA 3: COMPLETE INTENT ANALYSIS
 * Wyświetla kompletną analizę intencji wyszukiwania
 */

// ========================================
// SEKCJA 3: COMPLETE INTENT ANALYSIS - PEŁNA IMPLEMENTACJA
// ========================================

function displayIntentAnalysis(data) {
    console.log('🔍 SEKCJA 3: Renderowanie Complete Intent Analysis - NASA Mission Control');
    
    const intentContainer = document.getElementById('intentAnalysis');
    if (!intentContainer) {
        console.error('❌ Kontener #intentAnalysis nie znaleziony');
        return;
    }
    
    // DEBUG: Loguj wszystkie dane intent
    console.log('🔍 SEKCJA 3 DEBUG - displayIntentAnalysis data:', data);
    console.log('  main_intent:', data.main_intent);
    console.log('  intent_probability:', data.intent_probability);
    console.log('  secondary_intents:', data.secondary_intents);
    console.log('  autocomplete_intent_analysis type:', typeof data.autocomplete_intent_analysis);
    console.log('  autocomplete_intent_analysis:', data.autocomplete_intent_analysis);
    
    let html = `
        <div class="section-3-nasa nasa-mission-control">
            <div class="control-room">
                <section class="card">
                    <div class="single-intent">
    `;
    
    // GŁÓWNA INTENCJA Z TABELI KEYWORDS - Panel
    const mainIntentInfo = getMainIntentInfo(data.main_intent, data.intent_probability);
    html += `
        <article class="panel panel-large" tabindex="0" aria-label="Primary Intent Analysis">
            <div class="label">Primary Search Intent</div>
            <div class="intent-primary">${mainIntentInfo.intent}</div>
            <div class="confidence">${mainIntentInfo.confidence}%</div>
            
            <div class="signal-strength" aria-label="Intent Confidence">
                <div class="signal-fill ${mainIntentInfo.fillClass}" style="width:${mainIntentInfo.confidence}%"></div>
            </div>
            <div class="probability">
                <span>Confidence: ${mainIntentInfo.confidence}%</span>
            </div>
        </article>
    `;
    html += `
                    </div>
                </section>
            </div>
        </div>
    `;
    
    intentContainer.innerHTML = html;
    
    // Initialize signal animations
    initializeSignalAnimations();
}

// ========================================
// HELPER FUNCTIONS
// ========================================

function getIntentClass(intent) {
    const intentLower = intent.toLowerCase();
    
    if (intentLower.includes('informational') || intentLower.includes('info')) {
        return 'intent-informational';
    } else if (intentLower.includes('transactional') || intentLower.includes('commercial') || intentLower.includes('buy')) {
        return 'intent-transactional';
    } else if (intentLower.includes('navigational') || intentLower.includes('nav')) {
        return 'intent-navigational';
    } else if (intentLower.includes('local')) {
        return 'intent-local';
    } else if (intentLower.includes('commercial')) {
        return 'intent-commercial';
    } else {
        return 'intent-unknown';
    }
}

function getMainIntentInfo(mainIntent, intentProbability) {
    if (!mainIntent) {
        return {
            intent: 'BRAK DANYCH',
            confidence: 0,
            status: 'analyzing',
            fillClass: 'fill-strong'
        };
    }
    
    const confidence = intentProbability ? Math.round(intentProbability * 100) : 0;
    const intentUpper = mainIntent.toUpperCase();
    
    let status, fillClass;
    
    if (intentUpper.includes('NAVIGATIONAL')) {
        status = 'active';
        fillClass = 'fill-navigational';
    } else if (intentUpper.includes('INFORMATIONAL')) {
        status = 'analyzing';
        fillClass = 'fill-informational';
    } else {
        status = 'detected';
        fillClass = 'fill-strong';
    }
    
    return {
        intent: intentUpper,
        confidence,
        status,
        fillClass
    };
}

function getAutocompleteInfo(autocompleteData) {
    if (!autocompleteData) {
        return {
            primaryIntent: 'BRAK DANYCH',
            status: 'analyzing'
        };
    }
    
    try {
        const data = typeof autocompleteData === 'string' 
            ? JSON.parse(autocompleteData) 
            : autocompleteData;
        
        const primaryIntent = data.primary_intent || 'UNKNOWN';
        
        return {
            primaryIntent: primaryIntent.toUpperCase(),
            status: 'detected'
        };
    } catch (error) {
        return {
            primaryIntent: 'ERROR',
            status: 'analyzing'
        };
    }
}

function getIntentDistributionInfo(autocompleteData) {
    if (!autocompleteData) {
        return {
            totalCount: 0,
            dominantIntent: 'brak danych',
            percentage: 0
        };
    }
    
    try {
        const data = typeof autocompleteData === 'string' 
            ? JSON.parse(autocompleteData) 
            : autocompleteData;
        
        if (!data.intent_distribution || Object.keys(data.intent_distribution).length === 0) {
            return {
                totalCount: 0,
                dominantIntent: 'brak danych',
                percentage: 0
            };
        }
        
        const distribution = data.intent_distribution;
        const totalCount = Object.values(distribution).reduce((sum, count) => sum + count, 0);
        
        // Znajdź dominującą intencję
        let dominantIntent = 'unknown';
        let maxCount = 0;
        
        Object.entries(distribution).forEach(([intent, count]) => {
            if (count > maxCount) {
                maxCount = count;
                dominantIntent = intent;
            }
        });
        
        const percentage = totalCount > 0 ? Math.round((maxCount / totalCount) * 100) : 0;
        
        return {
            totalCount,
            dominantIntent,
            percentage
        };
    } catch (error) {
        return {
            totalCount: 0,
            dominantIntent: 'error',
            percentage: 0
        };
    }
}

function getCategorizedSuggestionsInfo(autocompleteData) {
    if (!autocompleteData) {
        return {
            categories: [{
                name: 'BRAK DANYCH',
                count: 0,
                suggestions: [],
                type: 'N/A'
            }]
        };
    }
    
    try {
        const data = typeof autocompleteData === 'string' 
            ? JSON.parse(autocompleteData) 
            : autocompleteData;
        
        if (!data.categorized_suggestions || Object.keys(data.categorized_suggestions).length === 0) {
            return {
                categories: [{
                    name: 'BRAK KATEGORII',
                    count: 0,
                    suggestions: [],
                    type: 'N/A'
                }]
            };
        }
        
        const categories = [];
        
        Object.entries(data.categorized_suggestions).forEach(([category, suggestions]) => {
            if (suggestions && suggestions.length > 0) {
                categories.push({
                    name: category.toUpperCase(),
                    count: suggestions.length,
                    suggestions: suggestions,
                    type: getIntentTypeShort(category)
                });
            }
        });
        
        if (categories.length === 0) {
            return {
                categories: [{
                    name: 'PUSTE KATEGORIE',
                    count: 0,
                    suggestions: [],
                    type: 'EMPTY'
                }]
            };
        }
        
        return { categories };
    } catch (error) {
        return {
            categories: [{
                name: 'ERROR',
                count: 0,
                suggestions: [],
                type: 'ERR'
            }]
        };
    }
}

function getIntentTypeShort(intent) {
    const intentLower = intent.toLowerCase();
    
    if (intentLower.includes('informational') || intentLower.includes('info')) {
        return 'INFO';
    } else if (intentLower.includes('transactional') || intentLower.includes('commercial')) {
        return 'TRANS';
    } else if (intentLower.includes('navigational') || intentLower.includes('nav')) {
        return 'NAV';
    } else if (intentLower.includes('local')) {
        return 'LOCAL';
    } else {
        return 'UNK';
    }
}

function initializeSignalAnimations() {
    // Enhanced signal animations - similar to original template
    setTimeout(() => {
        const fills = document.querySelectorAll('.section-3-nasa .signal-fill');
        fills.forEach(fill => {
            const width = fill.style.width;
            fill.style.width = '0%';
            setTimeout(() => {
                fill.style.width = width;
            }, 300);
        });
    }, 100);
}

// ========================================
// EXPORT FUNCTIONS TO GLOBAL SCOPE
// ========================================
window.displayIntentAnalysis = displayIntentAnalysis;
window.getIntentClass = getIntentClass;
window.getMainIntentInfo = getMainIntentInfo;
window.getIntentTypeShort = getIntentTypeShort;
window.initializeSignalAnimations = initializeSignalAnimations;

console.log('✅ SEKCJA 3: Complete Intent Analysis - Pełna implementacja załadowana'); 