/**
 * SECTIONS LOADER - Modularny system ładowania sekcji
 * Dynamicznie ładuje CSS i JavaScript dla każdej sekcji SEO Analysis
 */

class SectionsLoader {
    constructor() {
        this.loadedSections = new Set();
        this.loadedStylesheets = new Set();
        this.sectionDefinitions = {
            1: { name: 'header', title: 'Extended Header' },
            2: { name: 'metrics', title: 'Extended Core SEO Metrics' },
            3: { name: 'intent', title: 'Complete Intent Analysis' },
            4: { name: 'demographics', title: 'Complete Demographics' },
            5: { name: 'trends', title: 'Extended Trends & Seasonality' },
            6: { name: 'geographic', title: 'Complete Geographic Data' },
            7: { name: 'competition', title: 'Enhanced Competition Analysis' },
            8: { name: 'related', title: 'Enhanced Related Keywords' },
            9: { name: 'serp', title: 'Enhanced SERP Analysis' },
            10: { name: 'autocomplete', title: 'Enhanced Autocomplete Analysis' }
        };
    }

    /**
     * Ładuje CSS dla konkretnej sekcji
     */
    async loadSectionCSS(sectionNumber) {
        const cssPath = `/static/sections/section${sectionNumber}/section${sectionNumber}.css`;
        
        if (this.loadedStylesheets.has(cssPath)) {
            console.log(`📄 CSS dla sekcji ${sectionNumber} już załadowany`);
            return;
        }

        try {
            const link = document.createElement('link');
            link.rel = 'stylesheet';
            link.type = 'text/css';
            link.href = cssPath;
            link.id = `section${sectionNumber}-css`;
            
            document.head.appendChild(link);
            this.loadedStylesheets.add(cssPath);
            
            console.log(`✅ Załadowano CSS dla sekcji ${sectionNumber}`);
        } catch (error) {
            console.warn(`⚠️ Nie można załadować CSS dla sekcji ${sectionNumber}:`, error);
        }
    }

    /**
     * Ładuje JavaScript dla konkretnej sekcji
     */
    async loadSectionJS(sectionNumber) {
        const jsPath = `/static/sections/section${sectionNumber}/section${sectionNumber}.js`;
        
        if (this.loadedSections.has(sectionNumber)) {
            console.log(`📜 JavaScript dla sekcji ${sectionNumber} już załadowany`);
            return;
        }

        try {
            const script = document.createElement('script');
            script.src = jsPath;
            script.type = 'text/javascript';
            script.id = `section${sectionNumber}-js`;
            
            return new Promise((resolve, reject) => {
                script.onload = () => {
                    this.loadedSections.add(sectionNumber);
                    console.log(`✅ Załadowano JavaScript dla sekcji ${sectionNumber}`);
                    resolve();
                };
                
                script.onerror = () => {
                    console.warn(`⚠️ Nie można załadować JavaScript dla sekcji ${sectionNumber}`);
                    reject(new Error(`Failed to load section ${sectionNumber} JS`));
                };
                
                document.head.appendChild(script);
            });
        } catch (error) {
            console.warn(`⚠️ Błąd ładowania JavaScript dla sekcji ${sectionNumber}:`, error);
            throw error;
        }
    }

    /**
     * Ładuje konkretną sekcję (CSS + JS)
     */
    async loadSection(sectionNumber) {
        console.log(`🔄 Ładowanie sekcji ${sectionNumber}: ${this.getSectionTitle(sectionNumber)}`);
        
        try {
            // Ładuj CSS i JS równolegle
            await Promise.all([
                this.loadSectionCSS(sectionNumber),
                this.loadSectionJS(sectionNumber)
            ]);
            
            console.log(`✅ Sekcja ${sectionNumber} załadowana pomyślnie`);
            return true;
        } catch (error) {
            console.error(`❌ Błąd ładowania sekcji ${sectionNumber}:`, error);
            return false;
        }
    }

    /**
     * Ładuje wszystkie sekcje
     */
    async loadAllSections() {
        console.log('🚀 Rozpoczynam ładowanie wszystkich sekcji modułów...');
        
        const sectionNumbers = Object.keys(this.sectionDefinitions).map(Number);
        const loadPromises = sectionNumbers.map(num => this.loadSection(num));
        
        try {
            const results = await Promise.allSettled(loadPromises);
            
            const successful = results.filter(r => r.status === 'fulfilled').length;
            const failed = results.filter(r => r.status === 'rejected').length;
            
            console.log(`📊 Ładowanie sekcji zakończone: ${successful} ✅ | ${failed} ❌`);
            
            if (failed > 0) {
                console.warn('⚠️ Niektóre sekcje nie zostały załadowane - używając fallback funkcji');
            }
            
            return { successful, failed };
        } catch (error) {
            console.error('❌ Krytyczny błąd ładowania sekcji:', error);
            throw error;
        }
    }

    /**
     * Ładuje tylko konkretne sekcje
     */
    async loadSpecificSections(sectionNumbers) {
        console.log(`🎯 Ładowanie konkretnych sekcji: ${sectionNumbers.join(', ')}`);
        
        const loadPromises = sectionNumbers.map(num => this.loadSection(num));
        
        try {
            await Promise.all(loadPromises);
            console.log(`✅ Wszystkie konkretne sekcje załadowane`);
        } catch (error) {
            console.error('❌ Błąd ładowania konkretnych sekcji:', error);
            throw error;
        }
    }

    /**
     * Sprawdza czy sekcja jest załadowana
     */
    isSectionLoaded(sectionNumber) {
        return this.loadedSections.has(sectionNumber);
    }

    /**
     * Pobiera tytuł sekcji
     */
    getSectionTitle(sectionNumber) {
        return this.sectionDefinitions[sectionNumber]?.title || `Sekcja ${sectionNumber}`;
    }

    /**
     * Pobiera nazwę sekcji
     */
    getSectionName(sectionNumber) {
        return this.sectionDefinitions[sectionNumber]?.name || `section${sectionNumber}`;
    }

    /**
     * Sprawdza dostępność plików sekcji
     */
    async checkSectionAvailability(sectionNumber) {
        const cssPath = `/static/sections/section${sectionNumber}/section${sectionNumber}.css`;
        const jsPath = `/static/sections/section${sectionNumber}/section${sectionNumber}.js`;
        
        try {
            const [cssResponse, jsResponse] = await Promise.all([
                fetch(cssPath, { method: 'HEAD' }),
                fetch(jsPath, { method: 'HEAD' })
            ]);
            
            return {
                css: cssResponse.ok,
                js: jsResponse.ok,
                available: cssResponse.ok && jsResponse.ok
            };
        } catch (error) {
            return {
                css: false,
                js: false,
                available: false,
                error: error.message
            };
        }
    }

    /**
     * Usuwa sekcję z pamięci (dla testów)
     */
    unloadSection(sectionNumber) {
        // Usuń CSS
        const cssElement = document.getElementById(`section${sectionNumber}-css`);
        if (cssElement) {
            cssElement.remove();
            this.loadedStylesheets.delete(`/static/sections/section${sectionNumber}/section${sectionNumber}.css`);
        }

        // Usuń JS
        const jsElement = document.getElementById(`section${sectionNumber}-js`);
        if (jsElement) {
            jsElement.remove();
            this.loadedSections.delete(sectionNumber);
        }

        console.log(`🗑️ Usunięto sekcję ${sectionNumber} z pamięci`);
    }

    /**
     * Status wszystkich sekcji
     */
    getLoadingStatus() {
        const status = {};
        Object.keys(this.sectionDefinitions).forEach(num => {
            const sectionNum = parseInt(num);
            status[sectionNum] = {
                loaded: this.isSectionLoaded(sectionNum),
                title: this.getSectionTitle(sectionNum),
                name: this.getSectionName(sectionNum)
            };
        });
        return status;
    }
}

// ========================================
// FALLBACK FUNCTIONS
// ========================================

/**
 * Fallback function dla sekcji 10 jeśli moduł nie załaduje się
 */
function displayAutocompleteAnalysisFallback(data) {
    console.log('🔄 Używam fallback funkcji dla SEKCJI 10');
    
    const container = document.getElementById('autocompleteAnalysis');
    if (!container) return;

    if (!data.autocomplete_results || !data.autocomplete_suggestions) {
        container.innerHTML = `
            <div style="margin: 30px 0; padding: 25px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 15px; color: white;">
                <h2 style="margin: 0 0 25px 0; text-align: center;">🔮 SEKCJA 10: ENHANCED AUTOCOMPLETE ANALYSIS</h2>
                <div style="text-align: center; padding: 40px;">
                    <div style="font-size: 48px; margin-bottom: 15px;">🔍</div>
                    <div style="font-size: 18px; margin-bottom: 10px;">Brak Danych Autocomplete</div>
                    <div style="font-size: 14px; opacity: 0.8;">Dane autocomplete nie są dostępne dla tego słowa kluczowego</div>
                </div>
            </div>
        `;
        return;
    }

    const suggestions = data.autocomplete_suggestions || [];
    const basicTable = suggestions.slice(0, 10).map((suggestion, index) => `
        <tr style="border-bottom: 1px solid rgba(255,255,255,0.1);">
            <td style="padding: 8px;">${index + 1}</td>
            <td style="padding: 8px;"><strong>${suggestion.suggestion || 'N/A'}</strong></td>
            <td style="padding: 8px;">${suggestion.word_count || 0}</td>
        </tr>
    `).join('');

    container.innerHTML = `
        <div style="margin: 30px 0; padding: 25px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 15px; color: white;">
            <h2 style="margin: 0 0 25px 0; text-align: center;">🔮 SEKCJA 10: ENHANCED AUTOCOMPLETE ANALYSIS</h2>
            <div style="background: rgba(255,255,255,0.1); border-radius: 12px; padding: 20px;">
                <h3 style="margin: 0 0 15px 0;">📋 Podstawowe Sugestie Autocomplete (${suggestions.length})</h3>
                <div style="overflow-x: auto;">
                    <table style="width: 100%; border-collapse: collapse;">
                        <thead>
                            <tr style="background: rgba(0,0,0,0.3);">
                                <th style="padding: 12px 8px; text-align: left; font-weight: 600;">Rank</th>
                                <th style="padding: 12px 8px; text-align: left; font-weight: 600;">Suggestion</th>
                                <th style="padding: 12px 8px; text-align: left; font-weight: 600;">Words</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${basicTable}
                        </tbody>
                    </table>
                </div>
                <div style="margin-top: 15px; padding: 10px; background: rgba(255,255,255,0.1); border-radius: 8px; font-size: 14px;">
                    ⚠️ To jest uproszczona wersja. Pełna analiza wymaga załadowania modułu sekcji.
                </div>
            </div>
        </div>
    `;
}

// ========================================
// GLOBALNE INSTANCJE
// ========================================

// Utwórz globalną instancję loadera
window.sectionsLoader = new SectionsLoader();

// Eksportuj do globalnego zakresu
window.SectionsLoader = SectionsLoader;

console.log('📦 Sections Loader załadowany i gotowy do użycia'); 