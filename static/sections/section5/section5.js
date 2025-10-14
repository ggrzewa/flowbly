/**
 * SEKCJA 5: EXTENDED TRENDS & SEASONALITY - NASA MISSION CONTROL
 * Wyświetla rozszerzoną analizę trendów i sezonowości w stylu NASA Mission Control
 */

// ========================================
// SEKCJA 5: EXTENDED TRENDS & SEASONALITY - NASA MISSION CONTROL IMPLEMENTACJA
// ========================================

function displayTrendsAnalysis(data) {
    console.log('📈 SEKCJA 5: Renderowanie Extended Trends & Seasonality - NASA Mission Control');
    
    const trendsContainer = document.getElementById('trendsAnalysis');
    if (!trendsContainer) {
        console.error('❌ Kontener #trendsAnalysis nie znaleziony');
        return;
    }
    
    console.log('📈 SEKCJA 5 DEBUG - trendsAnalysis data:', data);
    console.log('  monthly_searches:', data.monthly_searches);
    console.log('  search_volume_trend:', data.search_volume_trend);
    console.log('  trends_graph:', data.trends_graph);
    console.log('  historical_data length:', data.historical_data ? data.historical_data.length : 0);
    
    // Przygotuj dane dla NASA layout
    const trendsInfo = getTrendsInfo(data);
    const monthlyInfo = getMonthlySearchesInfo(data);
    const volumeTrendsInfo = getVolumeTrendsInfo(data);
    const historicalInfo = getHistoricalInfo(data);
    
    let html = `
        <div class="section-5-nasa nasa-mission-control">
            <div class="control-room">
                
                <section class="card">
                    <div class="trends-grid">
    `;
    
    // Google Trends Chart Panel
    html += `
        <article class="panel panel-large" tabindex="0" aria-label="Google Trends Analysis">
            <div class="label">📈 GOOGLE TRENDS</div>
            <div style="font-size:11px;color:#0b3d91;margin-top:4px">
                Search interest over time (scale 0-100). A value of 100 represents peak popularity, 50 means half as popular, and 0 indicates insufficient data.
            </div>
            
            ${generateTrendsChart(trendsInfo)}
            
            <div class="expandable" onclick="toggleTrends(this)">
                <div style="font-size:11px;color:var(--blue);margin-top:12px;padding:10px;background:var(--panel-2);border-radius:4px;cursor:pointer;border:1px solid var(--border);font-weight:600">
                    📊 Show all data points <span class="expand-toggle">▶</span>
                </div>
            </div>
            
            <div id="trendsData" class="expandable-content">
                ${generateTrendsTable(trendsInfo)}
        </div>
        </article>
    `;
    
    // Monthly Searches Panel
    html += `
        <article class="panel panel-large" tabindex="0" aria-label="Monthly Search Volume">
            <div class="label">📅 MONTHLY SEARCHES (12 MONTHS)</div>
            <div style="font-size:11px;color:#0b3d91;margin-top:4px">Actual search volume per month based on keyword data.</div>
            
            <div class="monthly-container">
                ${generateMonthlyBars(monthlyInfo)}
            </div>
        </article>
    `;
    
    html += `
                    </div>
                </section>

                <!-- Volume Trends -->
                <section class="card">
                    <div class="volume-grid">
    `;
    
    // Volume Trends Panels
    volumeTrendsInfo.trends.forEach((trend, index) => {
        const trendClass = getTrendClass(trend.value);
        const fillClass = getFillClass(trend.value);
        const icon = getTrendIcon(trend.value);
        const description = getTrendDescription(trend.value);
        const percentage = Math.abs(trend.value);
                    
                    html += `
            <article class="panel panel-compact" tabindex="0" aria-label="${trend.label} Trend">
                <div class="label">${trend.label}</div>
                <div class="value-small ${trendClass}">${icon}${trend.value}%</div>
                <div class="volume-telemetry">
                    <div class="volume-fill ${fillClass}" style="width:${percentage}%"></div>
                        </div>
                <div class="volume-percentage">${description}</div>
            </article>
                    `;
                });
                
    html += `
                    </div>
                </section>
    `;
    
    // Historical Data Section - removed per simplification
    
    html += `
            </div>
        </div>
    `;
    
    trendsContainer.innerHTML = html;
    
    // Initialize animations
    initializeTrendsAnimations();
}

// ========================================
// HELPER FUNCTIONS
// ========================================

function getTrendsInfo(data) {
    let trendsData = [];
    let pointsCount = 0;
    
    if (data.trends_graph) {
        try {
            trendsData = typeof data.trends_graph === 'string' ? JSON.parse(data.trends_graph) : data.trends_graph;
            pointsCount = Array.isArray(trendsData) ? trendsData.length : 0;
        } catch (e) {
            console.error('Błąd parsowania trends_graph:', e);
        }
    }
    
    return {
        data: trendsData,
        pointsCount,
        hasData: pointsCount > 0
    };
}

function getMonthlySearchesInfo(data) {
    let monthlyData = [];
    let monthsCount = 0;
    
    if (data.monthly_searches) {
        try {
            monthlyData = typeof data.monthly_searches === 'string' ? JSON.parse(data.monthly_searches) : data.monthly_searches;
            monthsCount = Array.isArray(monthlyData) ? monthlyData.length : 0;
        } catch (e) {
            console.error('Błąd parsowania monthly_searches:', e);
        }
    }
    
    return {
        data: monthlyData,
        monthsCount,
        hasData: monthsCount > 0
    };
}

function getVolumeTrendsInfo(data) {
    const trends = [];
    
    if (data.search_volume_trend) {
        try {
            const trendData = typeof data.search_volume_trend === 'string' ? JSON.parse(data.search_volume_trend) : data.search_volume_trend;
                
                if (trendData.monthly !== undefined) {
                trends.push({ label: 'Monthly', value: trendData.monthly });
            }
            if (trendData.quarterly !== undefined) {
                trends.push({ label: 'Quarterly', value: trendData.quarterly });
            }
            if (trendData.yearly !== undefined) {
                trends.push({ label: 'Yearly', value: trendData.yearly });
            }
        } catch (e) {
            console.error('Błąd parsowania search_volume_trend:', e);
        }
    }
    
    return { trends };
}

function getHistoricalInfo(data) {
    if (!data.historical_data || data.historical_data.length === 0) {
        return { hasData: false };
    }
    
    const totalRecords = data.historical_data.length;
    const latestRecord = data.historical_data[0];
    const oldestRecord = data.historical_data[data.historical_data.length - 1];
    
    const latestDate = `${latestRecord.year}-${String(latestRecord.month).padStart(2, '0')}`;
    const oldestDate = `${oldestRecord.year}-${String(oldestRecord.month).padStart(2, '0')}`;
    
    return {
        hasData: true,
        totalRecords,
        latestDate,
        oldestDate,
        data: data.historical_data
    };
}

function generateTrendsChart(trendsInfo) {
    if (!trendsInfo.hasData) {
        return `
            <div style="text-align: center; padding: 40px; color: #6c757d; background: var(--panel-2); border-radius: 4px; border: 2px dashed var(--border);">
                📈 Brak danych Google Trends
                        </div>
                    `;
                }
                
    // Generuj SVG chart (uproszczona wersja)
    return `
        <div class="trends-chart">
            <div class="chart-grid"></div>
            <svg class="chart-line" viewBox="0 0 400 140">
                <defs>
                    <linearGradient id="trendGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                        <stop offset="0%" style="stop-color:var(--blue);stop-opacity:0.3"/>
                        <stop offset="100%" style="stop-color:var(--blue);stop-opacity:0"/>
                    </linearGradient>
                </defs>
                ${generateTrendPath(trendsInfo.data)}
            </svg>
            <div id="tooltip" class="tooltip"></div>
                        </div>
                    `;
                }
                
function generateTrendPath(trendsData) {
    if (!Array.isArray(trendsData) || trendsData.length === 0) return '';
    
    const maxValue = Math.max(...trendsData.map(point => point.values && point.values[0] ? point.values[0] : 0));
    const minValue = Math.min(...trendsData.map(point => point.values && point.values[0] ? point.values[0] : 0));
    const range = maxValue - minValue || 1;
    
    let pathData = 'M';
    let areaData = 'M0,140 ';
    let points = '';
    
    trendsData.slice(0, 10).forEach((point, index) => {
        const value = point.values && point.values[0] ? point.values[0] : 0;
        const x = (index / 9) * 400;
        const y = 140 - ((value - minValue) / range) * 120;
        
        if (index === 0) {
            pathData += `${x},${y}`;
            areaData += `L0,${y}`;
            } else {
            pathData += ` L${x},${y}`;
        }
        areaData += ` L${x},${y}`;
        
        const dateFrom = new Date(point.date_from).toLocaleDateString('en-US');
        const dateTo = new Date(point.date_to).toLocaleDateString('en-US');
        points += `<circle class="trend-point" cx="${x}" cy="${y}" data-date="${dateFrom} - ${dateTo}" data-value="${value}" style="animation-delay:${0.1 + index * 0.1}s"/>`;
    });
    
    areaData += ' L400,140 Z';
    
    return `
        <path class="trend-area" d="${areaData}"/>
        <path class="trend-path" d="${pathData}"/>
        ${points}
    `;
}

function generateTrendsTable(trendsInfo) {
    if (!trendsInfo.hasData) return '<div>No data to display</div>';
    
    let tableRows = '';
    trendsInfo.data.forEach(point => {
        const dateFrom = new Date(point.date_from).toLocaleDateString('pl-PL');
        const dateTo = new Date(point.date_to).toLocaleDateString('pl-PL');
        const value = point.values && point.values[0] ? point.values[0] : 'N/A';
        
        tableRows += `
            <tr>
                <td>${dateFrom} - ${dateTo}</td>
                <td><strong>${value}</strong></td>
            </tr>
        `;
    });
    
    return `
        <div style="margin-top:8px">
            <table class="data-table" style="font-size:11px">
                <thead>
                    <tr>
                        <th style="width:60%">PERIOD</th>
                        <th style="width:40%">VALUE</th>
                    </tr>
                </thead>
                <tbody>
                    ${tableRows}
                </tbody>
            </table>
        </div>
    `;
}

function generateMonthlyBars(monthlyInfo) {
    if (!monthlyInfo.hasData) {
        return '<div style="text-align: center; color: #6c757d;">No monthly data</div>';
    }
    
    const maxVolume = Math.max(...monthlyInfo.data.map(month => month.search_volume || 0));
    let barsHtml = '';
    
    monthlyInfo.data.slice(0, 12).forEach(month => {
        const yearMonth = `${month.year}-${String(month.month).padStart(2, '0')}`;
        const volume = month.search_volume ? formatNumber(month.search_volume) : 'N/A';
        const percentage = maxVolume > 0 ? Math.round((month.search_volume / maxVolume) * 100) : 0;
        
        barsHtml += `
            <div class="month-item">
                <div class="month-label">${yearMonth}</div>
                <div class="month-bar">
                    <div class="month-fill" style="width:${percentage}%"></div>
                </div>
                <div class="month-value">${volume}</div>
            </div>
        `;
    });
    
    return barsHtml;
}

function generateHistoricalTable(historicalInfo) {
    let tableRows = '';
    
    historicalInfo.data.forEach(record => {
            const yearMonth = `${record.year}-${String(record.month).padStart(2, '0')}`;
            const volume = record.search_volume ? formatNumber(record.search_volume) : 'N/A';
            const cpc = record.cpc ? `$${record.cpc.toFixed(2)}` : 'N/A';
            const competition = record.competition ? (record.competition * 100).toFixed(1) + '%' : 'N/A';
            
            const competitionLevel = record.competition_level || 'unknown';
            const competitionClass = getCompetitionClass(competitionLevel);
            
            const lowBid = record.low_top_of_page_bid ? `$${record.low_top_of_page_bid.toFixed(2)}` : 'N/A';
            const highBid = record.high_top_of_page_bid ? `$${record.high_top_of_page_bid.toFixed(2)}` : 'N/A';
            const bidRange = `${lowBid} - ${highBid}`;
            
        const categories = record.categories && record.categories.length > 0 
            ? record.categories.join(', ') 
            : 'Brak kategorii';
        
        tableRows += `
            <tr>
                <td><strong>${yearMonth}</strong></td>
                <td>${volume}</td>
                <td>${cpc}</td>
                <td>${competition}</td>
                <td><span class="${competitionClass}">${competitionLevel.toUpperCase()}</span></td>
                <td>${bidRange}</td>
                <td>${categories}</td>
                </tr>
            `;
        });
        
    return `
        <table class="data-table">
            <thead>
                <tr>
                    <th>Year-Month</th>
                    <th>Search Volume</th>
                    <th>CPC</th>
                    <th>Competition</th>
                    <th>Level</th>
                    <th>Bid Range</th>
                    <th>Categories</th>
                </tr>
            </thead>
            <tbody>
                ${tableRows}
            </tbody>
        </table>
    `;
}

function getTrendClass(value) {
    if (value > 0) return 'trend-positive';
    if (value < 0) return 'trend-negative';
    return 'trend-neutral';
}

function getFillClass(value) {
    if (value > 0) return 'fill-positive';
    if (value < 0) return 'fill-negative';
    return 'fill-neutral';
}

function getTrendIcon(value) {
    if (value > 0) return '📈+';
    if (value < 0) return '📉';
    return '➖';
}

function getTrendDescription(value) {
    if (value > 0) return 'Rising trend';
    if (value < 0) return 'Declining trend';
    return 'No change';
}

function getCompetitionClass(level) {
    const levelLower = (level || '').toLowerCase();
    if (levelLower === 'low') return 'comp-low';
    if (levelLower === 'medium') return 'comp-medium';
    if (levelLower === 'high') return 'comp-high';
    return 'comp-low'; // fallback
}

function initializeTrendsAnimations() {
    // Enhanced bar animations
    setTimeout(() => {
        const fills = document.querySelectorAll('.section-5-nasa .month-fill');
        fills.forEach((fill, index) => {
            const width = fill.style.width;
            fill.style.width = '0%';
            setTimeout(() => {
                fill.style.width = width;
            }, 300 + index * 100);
        });

        // Volume trends animations
        const volumeFills = document.querySelectorAll('.section-5-nasa .volume-fill');
        volumeFills.forEach((fill, index) => {
            const width = fill.style.width;
            fill.style.width = '0%';
            setTimeout(() => {
                fill.style.width = width;
            }, 800 + index * 150);
        });

        // Tooltip functionality
        const tooltip = document.getElementById('tooltip');
        const points = document.querySelectorAll('.section-5-nasa .trend-point');
        
        points.forEach(point => {
            point.addEventListener('mouseenter', function(e) {
                const date = this.getAttribute('data-date');
                const value = this.getAttribute('data-value');
                tooltip.innerHTML = `📅 ${date}<br><strong>Wartość: ${value}</strong>`;
                tooltip.classList.add('show');
                
                const rect = this.getBoundingClientRect();
                const chartRect = this.closest('.trends-chart').getBoundingClientRect();
                tooltip.style.left = (rect.left - chartRect.left) + 'px';
                tooltip.style.top = (rect.top - chartRect.top - 50) + 'px';
            });
            
            point.addEventListener('mouseleave', function() {
                tooltip.classList.remove('show');
            });
        });
    }, 100);
}

function formatNumber(num) {
    if (num === null || num === undefined) return 'N/A';
    return num.toLocaleString('pl-PL');
}

// Expandable sections
function toggleTrends(element) {
    const content = document.getElementById('trendsData');
    const toggle = element.querySelector('.expand-toggle');
    
    content.classList.toggle('open');
    toggle.classList.toggle('open');
    toggle.textContent = content.classList.contains('open') ? '▼' : '▶';
}

// ========================================
// EXPORT FUNCTIONS TO GLOBAL SCOPE
// ========================================
window.displayTrendsAnalysis = displayTrendsAnalysis;
window.formatNumber = formatNumber;
window.getCompetitionClass = getCompetitionClass;
window.getTrendsInfo = getTrendsInfo;
window.getMonthlySearchesInfo = getMonthlySearchesInfo;
window.getVolumeTrendsInfo = getVolumeTrendsInfo;
window.getHistoricalInfo = getHistoricalInfo;
window.initializeTrendsAnimations = initializeTrendsAnimations;
window.toggleTrends = toggleTrends;

console.log('✅ SEKCJA 5: Extended Trends & Seasonality - NASA Mission Control implementacja załadowana');