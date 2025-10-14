/**
 * SEKCJA 2: EXTENDED CORE SEO METRICS
 * Wyświetla rozszerzone metryki SEO w formie tabeli
 */

// ========================================
// SEKCJA 2: EXTENDED CORE SEO METRICS - PEŁNA IMPLEMENTACJA
// ========================================

function displaySeoMetrics(data) {
    console.log('📊 SEKCJA 2: Renderowanie Extended Core SEO Metrics - NASA Mission Control');
    
    const metricsContainer = document.getElementById('seoMetrics');
    if (!metricsContainer) {
        console.error('❌ Kontener #seoMetrics nie znaleziony');
        return;
    }
    
    let html = `
        <div class="section-2-nasa nasa-mission-control">
            <div class="systems-grid">
    `;
    
    // Search Volume Panel
    if (data.search_volume !== null && data.search_volume !== undefined) {
        const volumePercentage = Math.min((data.search_volume / 10000) * 100, 100); // Scale for visualization
        html += `
            <article class="panel" tabindex="0" aria-label="Search Volume Monitoring">
                <div class="label">Search Volume</div>
                <div class="value value-large">${formatNumber(data.search_volume)}</div>
                <div class="telemetry" aria-label="Volume Performance">
                    <div class="fill fill-purple" style="--val:${volumePercentage}%"></div>
                </div>
                <div class="progress-label">
                    <span>📈 Monthly Searches</span>
                    <span>${Math.round(volumePercentage)}%</span>
                </div>
                <div class="status-badge ${getVolumeStatus(data.search_volume).class}">${getVolumeStatus(data.search_volume).text}</div>
            </article>
        `;
    }
    
    // Keyword Difficulty Panel
    if (data.keyword_difficulty !== null && data.keyword_difficulty !== undefined) {
        const difficultyInfo = getDifficultyInfo(data.keyword_difficulty);
        html += `
            <article class="panel" tabindex="0" aria-label="Keyword Difficulty Analysis">
                <div class="label">Keyword Difficulty</div>
                <div class="value">${data.keyword_difficulty}<span class="value-secondary">/100</span></div>
                <div class="telemetry" aria-label="Difficulty Level">
                    <div class="fill ${difficultyInfo.fillClass}" style="--val:${data.keyword_difficulty}%"></div>
                </div>
                <div class="progress-label">
                    <span>Difficulty: ${data.keyword_difficulty}%</span>
                    <span>${difficultyInfo.level}</span>
                </div>
                <div class="status-badge ${difficultyInfo.badgeClass}">${difficultyInfo.level} Difficulty</div>
            </article>
        `;
    }
    
    // CPC Panel
    if (data.cpc !== null && data.cpc !== undefined) {
        const cpcInfo = getCpcInfo(data.cpc);
        html += `
            <article class="panel" tabindex="0" aria-label="Cost Per Click Tracking">
                <div class="label">CPC</div>
                <div class="value">$${data.cpc.toFixed(2)}</div>
                <div class="telemetry" aria-label="Cost Efficiency">
                    <div class="fill ${cpcInfo.fillClass}" style="--val:${cpcInfo.percentage}%"></div>
                </div>
                <div class="progress-label">
                    <span>💰 Cost Per Click</span>
                    <span>${cpcInfo.level}</span>
                </div>
                <div class="status-badge ${cpcInfo.badgeClass}">${cpcInfo.description}</div>
            </article>
        `;
    }
    
    // Competition Score Panel
    if (data.competition !== null && data.competition !== undefined) {
        const competitionPct = (data.competition * 100).toFixed(1);
        const competitionInfo = getCompetitionInfo(parseFloat(competitionPct));
        html += `
            <article class="panel" tabindex="0" aria-label="Competition Analysis">
                <div class="label">Competition Score</div>
                <div class="value">${competitionPct}%</div>
                <div class="telemetry" aria-label="Competition Level">
                    <div class="fill ${competitionInfo.fillClass}" style="--val:${competitionPct}%"></div>
                </div>
                <div class="progress-label">
                    <span>🎯 Ad Competition</span>
                    <span>${competitionInfo.level}</span>
                </div>
                <div class="status-badge ${competitionInfo.badgeClass}">${competitionInfo.description}</div>
            </article>
        `;
    }
    
    // Competition Level Panel
    if (data.competition_level) {
        const levelInfo = getCompetitionLevelInfo(data.competition_level);
        html += `
            <article class="panel" tabindex="0" aria-label="Overall Competition Level">
                <div class="label">Competition Level</div>
                <div class="value">${data.competition_level}</div>
                <div class="telemetry" aria-label="Market Saturation">
                    <div class="fill ${levelInfo.fillClass}" style="--val:${levelInfo.percentage}%"></div>
                </div>
                <div class="progress-label">
                    <span>📊 Competition Level</span>
                    <span>${levelInfo.description}</span>
                </div>
                <div class="status-badge ${levelInfo.badgeClass}">${data.competition_level} Competition</div>
            </article>
        `;
    }
    
    // Bid Range Panel
    if (data.low_top_of_page_bid !== null && data.high_top_of_page_bid !== null) {
        const bidInfo = getBidRangeInfo(data.low_top_of_page_bid, data.high_top_of_page_bid);
        html += `
            <article class="panel" tabindex="0" aria-label="Bid Range Intelligence">
                <div class="label">Top Page Bid Range</div>
                <div class="value value-range">
                    $${data.low_top_of_page_bid?.toFixed(2) || '0.00'}<span class="range-sep">–</span>$${data.high_top_of_page_bid?.toFixed(2) || '0.00'}
                </div>
                <div class="telemetry" aria-label="Bid Spread Analysis">
                    <div class="fill ${bidInfo.fillClass}" style="--val:${bidInfo.percentage}%"></div>
                </div>
                <div class="progress-label">
                    <span>💸 PPC Bid Range</span>
                    <span>${bidInfo.description}</span>
                </div>
                <div class="status-badge ${bidInfo.badgeClass}">${bidInfo.level}</div>
            </article>
        `;
    }
    
    html += `
            </div>
        </div>
    `;
    
    metricsContainer.innerHTML = html;
    
    // Initialize telemetry animations
    initializeTelemetryAnimations();
}

// ========================================
// HELPER FUNCTIONS
// ========================================

function formatNumber(num) {
    if (num === null || num === undefined) return 'N/A';
    return num.toLocaleString('pl-PL');
}

function getDifficultyLevel(difficulty) {
    if (difficulty <= 30) return 'easy';
    if (difficulty <= 70) return 'medium';
    return 'hard';
}

function getDifficultyInfo(difficulty) {
    if (difficulty <= 30) {
        return {
            status: 'nominal',
            level: 'EASY',
            fillClass: 'fill-green',
            badgeClass: 'badge-green'
        };
    } else if (difficulty <= 70) {
        return {
            status: 'caution',
            level: 'MODERATE',
            fillClass: 'fill-orange',
            badgeClass: 'badge-orange'
        };
    } else {
        return {
            status: 'warning',
            level: 'HARD',
            fillClass: 'fill-red',
            badgeClass: 'badge-red'
        };
    }
}

function getVolumeStatus(volume) {
    if (volume >= 5000) {
        return { class: 'badge-blue', text: 'High Volume' };
    } else if (volume >= 1000) {
        return { class: 'badge-orange', text: 'Medium Volume' };
    } else {
        return { class: 'badge-green', text: 'Low Volume' };
    }
}

function getCpcInfo(cpc) {
    let percentage, level, status, fillClass, badgeClass, description;
    
    if (cpc <= 0.5) {
        percentage = Math.min((cpc / 0.5) * 100, 100);
        level = 'LOW';
        status = 'optimal';
        fillClass = 'fill-green';
        badgeClass = 'badge-green';
        description = 'Budget Friendly';
    } else if (cpc <= 2.0) {
        percentage = Math.min(((cpc - 0.5) / 1.5) * 100 + 25, 75);
        level = 'MODERATE';
        status = 'caution';
        fillClass = 'fill-orange';
        badgeClass = 'badge-orange';
        description = 'Moderate Cost';
    } else {
        percentage = Math.min(((cpc - 2.0) / 3.0) * 100 + 75, 100);
        level = 'HIGH';
        status = 'warning';
        fillClass = 'fill-red';
        badgeClass = 'badge-red';
        description = 'Expensive';
    }
    
    return { percentage, level, status, fillClass, badgeClass, description };
}

function getCompetitionInfo(competitionPct) {
    let level, status, fillClass, badgeClass, description;
    
    if (competitionPct <= 33) {
        level = 'LOW';
        status = 'nominal';
        fillClass = 'fill-green';
        badgeClass = 'badge-green';
        description = 'Low Competition';
    } else if (competitionPct <= 66) {
        level = 'MODERATE';
        status = 'caution';
        fillClass = 'fill-orange';
        badgeClass = 'badge-orange';
        description = 'Manageable';
    } else {
        level = 'HIGH';
        status = 'warning';
        fillClass = 'fill-red';
        badgeClass = 'badge-red';
        description = 'High Competition';
    }
    
    return { level, status, fillClass, badgeClass, description };
}

function getCompetitionLevelInfo(level) {
    const levelUpper = level.toUpperCase();
    let percentage, status, fillClass, badgeClass, description;
    
    switch (levelUpper) {
        case 'LOW':
            percentage = 20;
            status = 'nominal';
            fillClass = 'fill-green';
            badgeClass = 'badge-green';
            description = 'OPTIMAL';
            break;
        case 'MEDIUM':
            percentage = 50;
            status = 'caution';
            fillClass = 'fill-orange';
            badgeClass = 'badge-orange';
            description = 'MODERATE';
            break;
        case 'HIGH':
            percentage = 80;
            status = 'warning';
            fillClass = 'fill-red';
            badgeClass = 'badge-red';
            description = 'CHALLENGING';
            break;
        default:
            percentage = 30;
            status = 'nominal';
            fillClass = 'fill-blue';
            badgeClass = 'badge-blue';
            description = 'UNKNOWN';
    }
    
    return { percentage, status, fillClass, badgeClass, description };
}

function getBidRangeInfo(lowBid, highBid) {
    const spread = highBid - lowBid;
    let percentage, status, fillClass, badgeClass, level, description;
    
    if (spread <= 1.0) {
        percentage = 25;
        status = 'optimal';
        fillClass = 'fill-green';
        badgeClass = 'badge-green';
        level = 'Narrow Range';
        description = 'TIGHT';
    } else if (spread <= 5.0) {
        percentage = 45;
        status = 'nominal';
        fillClass = 'fill-blue';
        badgeClass = 'badge-blue';
        level = 'Good Range';
        description = 'WIDE';
    } else {
        percentage = 75;
        status = 'caution';
        fillClass = 'fill-orange';
        badgeClass = 'badge-orange';
        level = 'Wide Range';
        description = 'VERY WIDE';
    }
    
    return { percentage, status, fillClass, badgeClass, level, description };
}

function initializeTelemetryAnimations() {
    // Enhanced telemetry animation - similar to original template
    setTimeout(() => {
        const fills = document.querySelectorAll('.section-2-nasa .fill');
        fills.forEach(fill => {
            const width = fill.style.getPropertyValue('--val');
            fill.style.width = '0%';
            setTimeout(() => {
                fill.style.width = width;
            }, 200);
        });
    }, 100);
}

function getTrendInfo(trendPct) {
    if (trendPct > 0) {
        return { arrow: '↗', class: 'trend-positive' };
    } else if (trendPct < 0) {
        return { arrow: '↘', class: 'trend-negative' };
    } else {
        return { arrow: '→', class: 'trend-neutral' };
    }
}

// ========================================
// EXPORT FUNCTIONS TO GLOBAL SCOPE
// ========================================
window.displaySeoMetrics = displaySeoMetrics;
window.formatNumber = formatNumber;
window.getDifficultyLevel = getDifficultyLevel;
window.getDifficultyInfo = getDifficultyInfo;
window.getVolumeStatus = getVolumeStatus;
window.getCpcInfo = getCpcInfo;
window.getCompetitionInfo = getCompetitionInfo;
window.getCompetitionLevelInfo = getCompetitionLevelInfo;
window.getBidRangeInfo = getBidRangeInfo;
window.initializeTelemetryAnimations = initializeTelemetryAnimations;
window.getTrendInfo = getTrendInfo;

console.log('✅ SEKCJA 2: Extended Core SEO Metrics - Pełna implementacja załadowana'); 