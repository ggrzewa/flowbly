/**
 * SEKCJA 6: COMPLETE GEOGRAPHIC DATA - NASA MISSION CONTROL
 * Wyświetla kompletne dane geograficzne w stylu NASA Mission Control
 */

// ========================================
// SEKCJA 6: COMPLETE GEOGRAPHIC DATA - NASA MISSION CONTROL IMPLEMENTACJA
// ========================================

function displayGeographicAnalysis(data) {
    console.log('🌍 SEKCJA 6: Renderowanie Complete Geographic Data - NASA Mission Control');
    
    const geographicContainer = document.getElementById('geographicAnalysis');
    if (!geographicContainer) {
        console.error('❌ Kontener #geographicAnalysis nie znaleziony');
        return;
    }
    
    console.log('🌍 SEKCJA 6 DEBUG - geographicAnalysis data:', data);
    console.log('  location_code:', data.location_code);
    console.log('  language_code:', data.language_code);
    console.log('  subregion_interests:', data.subregion_interests);
    console.log('  trends_map:', data.trends_map);
    
    // Przygotuj dane dla NASA layout
    const locationInfo = getLocationInfo(data);
    const languageInfo = getLanguageInfo(data);
    const subregionInfo = getSubregionInfo(data);
    const trendsMapInfo = getTrendsMapInfo(data);
    const statisticsInfo = getStatisticsInfo(subregionInfo, trendsMapInfo);
    
    let html = `
        <div class="section-6-nasa nasa-mission-control">
            <div class="control-room">
                
                <!-- Explanatory text -->
                <section class="card">
                    <div style="padding:12px 16px;color:#0b3d91;font-size:11px;line-height:1.5">
                        See which regions show the highest interest in this keyword. Higher values indicate stronger search demand in that area. Use this to identify target markets and prioritize local SEO efforts.
                    </div>
                    <div class="regions-grid">
    `;
    
    // Google Trends Map Panel (only)
    html += `
        <article class="panel panel-large" tabindex="0" aria-label="Google Trends Map Data">
            <div class="label">Interest by Region</div>
            <div style="font-size:11px;font-weight:700;color:var(--teal);margin-bottom:12px">
                ${trendsMapInfo.hasData ? 'Showing regions ranked by search interest' : 'No Google Trends data'}
            </div>
            
            <div class="region-list">
                ${generateTrendsMapList(trendsMapInfo)}
            </div>
        </article>
    `;
    
    html += `
                    </div>
                </section>
    `;
    
    // Statistics Section removed per simplification
    
    html += `
            </div>
        </div>
    `;
    
    geographicContainer.innerHTML = html;
    
    // Initialize animations
    initializeGeographicAnimations();
}

// ========================================
// HELPER FUNCTIONS
// ========================================

function getLocationInfo(data) {
    const locationCode = data.location_code || 'N/A';
    
    // Mapowanie kodów lokalizacji na nazwy i flagi
    const locationMap = {
        '2616': { name: 'Poland', flag: '🇵🇱' },
        '2840': { name: 'United States', flag: '🇺🇸' },
        '2276': { name: 'Germany', flag: '🇩🇪' },
        '2826': { name: 'United Kingdom', flag: '🇬🇧' },
        '2250': { name: 'France', flag: '🇫🇷' },
        '2380': { name: 'Italy', flag: '🇮🇹' },
        '2724': { name: 'Spain', flag: '🇪🇸' },
        '2528': { name: 'Netherlands', flag: '🇳🇱' },
        '2056': { name: 'Belgium', flag: '🇧🇪' },
        '2040': { name: 'Austria', flag: '🇦🇹' }
    };
    
    const locationInfo = locationMap[locationCode] || { name: 'Unknown Location', flag: '🌍' };
    
    return {
        code: locationCode,
        name: locationInfo.name,
        flag: locationInfo.flag
    };
}

function getLanguageInfo(data) {
    const languageCode = data.language_code || 'N/A';
    
    // Mapowanie kodów języków na nazwy i flagi
    const languageMap = {
        'pl': { name: 'Polish', flag: '🇵🇱' },
        'en': { name: 'English', flag: '🇺🇸' },
        'de': { name: 'German', flag: '🇩🇪' },
        'fr': { name: 'French', flag: '🇫🇷' },
        'es': { name: 'Spanish', flag: '🇪🇸' },
        'it': { name: 'Italian', flag: '🇮🇹' },
        'nl': { name: 'Dutch', flag: '🇳🇱' },
        'pt': { name: 'Portuguese', flag: '🇵🇹' },
        'ru': { name: 'Russian', flag: '🇷🇺' },
        'ja': { name: 'Japanese', flag: '🇯🇵' }
    };
    
    const languageInfo = languageMap[languageCode.toLowerCase()] || { name: 'Unknown Language', flag: '🌐' };
    
    return {
        code: languageCode.toUpperCase(),
        name: languageInfo.name,
        flag: languageInfo.flag
    };
}

function getSubregionInfo(data) {
    let subregionData = [];
    let hasData = false;
    
    if (data.subregion_interests) {
        try {
            subregionData = typeof data.subregion_interests === 'string' 
                ? JSON.parse(data.subregion_interests) 
                : data.subregion_interests;
            hasData = Array.isArray(subregionData) && subregionData.length > 0;
        } catch (e) {
            console.error('Błąd parsowania subregion_interests:', e);
        }
    }
    
    // Sortuj po wartości (malejąco)
    if (hasData) {
        subregionData.sort((a, b) => (b.value || 0) - (a.value || 0));
    }
    
    return {
        data: subregionData,
        hasData,
        count: subregionData.length
    };
}

function getTrendsMapInfo(data) {
    let trendsMapData = [];
    let hasData = false;
    
    if (data.trends_map) {
        try {
            trendsMapData = typeof data.trends_map === 'string' 
                ? JSON.parse(data.trends_map) 
                : data.trends_map;
            hasData = Array.isArray(trendsMapData) && trendsMapData.length > 0;
        } catch (e) {
            console.error('Błąd parsowania trends_map:', e);
        }
    }
    
    // Sortuj po pierwszej wartości z values[] (malejąco)
    if (hasData) {
        trendsMapData.sort((a, b) => {
            const aValue = (a.values && a.values[0]) || 0;
            const bValue = (b.values && b.values[0]) || 0;
            return bValue - aValue;
        });
    }
    
    return {
        data: trendsMapData,
        hasData,
        count: trendsMapData.length
    };
}

function getStatisticsInfo(subregionInfo, trendsMapInfo) {
    // Używamy danych z trends_map do statystyk (bardziej precyzyjne)
    if (!trendsMapInfo.hasData) {
        return { hasData: false };
    }
    
    const values = trendsMapInfo.data.map(item => (item.values && item.values[0]) || 0);
    const maxValue = Math.max(...values);
    const minValue = Math.min(...values);
    const avgValue = values.length > 0 ? (values.reduce((a, b) => a + b, 0) / values.length).toFixed(1) : 0;
    
    return {
        hasData: true,
        regionsCount: trendsMapInfo.count,
        maxValue,
        minValue,
        avgValue
    };
}

function generateSubregionList(subregionInfo) {
    if (!subregionInfo.hasData) {
        return '<div style="text-align: center; color: #6c757d; padding: 20px;">Brak danych subregion_interests</div>';
    }
    
    const maxValue = Math.max(...subregionInfo.data.map(item => item.value || 0));
    let listHtml = '';
    
    subregionInfo.data.forEach((region, index) => {
        const value = region.value || 0;
        const percentage = maxValue > 0 ? Math.round((value / maxValue) * 100) : 0;
        const heatClass = getHeatClass(percentage);
        const rankClass = getRankClass(index + 1);
        const rankIcon = getRankIcon(index + 1);
        
        listHtml += `
            <div class="region-item">
                <span class="ranking-indicator ${rankClass}">${rankIcon}</span>
                <span class="region-name">${region.geo_name || 'Unknown Region'}</span>
                <div class="region-bar"><div class="heat-fill ${heatClass}" style="width:${percentage}%"></div></div>
                <span class="region-value">${value}</span>
            </div>
        `;
    });
    
    return listHtml;
}

function generateTrendsMapList(trendsMapInfo) {
    if (!trendsMapInfo.hasData) {
        return '<div style="text-align: center; color: #6c757d; padding: 20px;">Brak danych trends_map</div>';
    }
    
    const maxValue = Math.max(...trendsMapInfo.data.map(item => (item.values && item.values[0]) || 0));
    let listHtml = '';
    
    trendsMapInfo.data.forEach((region, index) => {
        const value = (region.values && region.values[0]) || 0;
        const percentage = maxValue > 0 ? Math.round((value / maxValue) * 100) : 0;
        const heatClass = getHeatClass(percentage);
        const rankClass = getRankClass(index + 1);
        const rankIcon = getRankIcon(index + 1);
        const valuesCount = region.values ? region.values.length : 0;
        
        listHtml += `
            <div class="region-item">
                <span class="ranking-indicator ${rankClass}">${rankIcon}</span>
                <span class="region-name">${region.geo_name || 'Unknown Region'} ${region.geo_id ? `(ID: ${region.geo_id})` : ''}</span>
                <div class="region-bar"><div class="heat-fill ${heatClass}" style="width:${percentage}%"></div></div>
                <span class="region-value">${value}<span style="font-size:8px"> (${valuesCount})</span></span>
            </div>
        `;
    });
    
    return listHtml;
}

function getHeatClass(percentage) {
    if (percentage >= 100) return 'heat-100';
    if (percentage >= 90) return 'heat-90';
    if (percentage >= 80) return 'heat-80';
    if (percentage >= 70) return 'heat-70';
    if (percentage >= 60) return 'heat-60';
    if (percentage >= 50) return 'heat-50';
    return 'heat-40';
}

function getRankClass(rank) {
    if (rank === 1) return 'rank-1';
    if (rank === 2) return 'rank-2';
    if (rank === 3) return 'rank-3';
    return 'rank-other';
}

function getRankIcon(rank) {
    if (rank === 1) return '🥇';
    if (rank === 2) return '🥈';
    if (rank === 3) return '🥉';
    return rank.toString();
}

function initializeGeographicAnimations() {
    // Enhanced heat map animations
    setTimeout(() => {
        const fills = document.querySelectorAll('.section-6-nasa .heat-fill');
        fills.forEach((fill, index) => {
            const width = fill.style.width;
            fill.style.width = '0%';
            setTimeout(() => {
                fill.style.width = width;
            }, 200 + index * 50);
        });
    }, 100);
}

function formatNumber(num) {
    if (num === null || num === undefined) return 'N/A';
    return num.toLocaleString('pl-PL');
}

// ========================================
// EXPORT FUNCTIONS TO GLOBAL SCOPE
// ========================================
window.displayGeographicAnalysis = displayGeographicAnalysis;
window.getLocationInfo = getLocationInfo;
window.getLanguageInfo = getLanguageInfo;
window.getSubregionInfo = getSubregionInfo;
window.getTrendsMapInfo = getTrendsMapInfo;
window.getStatisticsInfo = getStatisticsInfo;
window.generateSubregionList = generateSubregionList;
window.generateTrendsMapList = generateTrendsMapList;
window.getHeatClass = getHeatClass;
window.getRankClass = getRankClass;
window.getRankIcon = getRankIcon;
window.initializeGeographicAnimations = initializeGeographicAnimations;

console.log('✅ SEKCJA 6: Complete Geographic Data - NASA Mission Control implementacja załadowana');