/**
 * SEKCJA 4: COMPLETE DEMOGRAPHICS
 * Wyświetla kompletną analizę demograficzną zgodnie ze schematem
 */

// ========================================
// SEKCJA 4: COMPLETE DEMOGRAPHICS - PEŁNA IMPLEMENTACJA
// ========================================

function displayDemographicsAnalysis(data) {
    console.log('👥 SEKCJA 4: Renderowanie Complete Demographics - NASA Mission Control');
    
    const demographicsContainer = document.getElementById('demographicsAnalysis');
    if (!demographicsContainer) {
        console.error('❌ Kontener #demographicsAnalysis nie znaleziony');
        return;
    }
    
    console.log('👥 SEKCJA 4 DEBUG - demographicsAnalysis data:', data);
    console.log('  gender_female:', data.gender_female);
    console.log('  gender_male:', data.gender_male);
    console.log('  age_18_24:', data.age_18_24);
    console.log('  age_25_34:', data.age_25_34);
    console.log('  age_35_44:', data.age_35_44);
    console.log('  age_45_54:', data.age_45_54);
    console.log('  age_55_64:', data.age_55_64);
    
    // Sprawdź czy mamy jakiekolwiek dane demograficzne
    const hasGenderData = (data.gender_female !== null && data.gender_female !== undefined) || 
                        (data.gender_male !== null && data.gender_male !== undefined);
    
    const hasAgeData = [data.age_18_24, data.age_25_34, data.age_35_44, data.age_45_54, data.age_55_64]
                      .some(age => age !== null && age !== undefined);
    
    if (!hasGenderData && !hasAgeData) {
        demographicsContainer.innerHTML = `
            <div class="section-4-nasa nasa-mission-control">
                <div class="control-room">
                    <section class="card">
                        <div style="padding: 40px; text-align: center; color: #6c757d;">
                            <h3>👥 No demographic data</h3>
                            <p>Demographic data is not available for this keyword.</p>
                        </div>
                    </section>
                </div>
            </div>
        `;
        return;
    }
    
    // Przygotuj dane dla NASA layout
    const genderInfo = getGenderInfo(data);
    const ageInfo = getAgeInfo(data);
    
    let html = `
        <div class="section-4-nasa nasa-mission-control">
            <div class="control-room">
                
                <!-- Gender & Age Overview -->
                <section class="card">
                    <div class="demographics-grid">
    `;
    
    // GENDER DISTRIBUTION Panel
    if (hasGenderData) {
        html += `
            <article class="panel panel-large" tabindex="0" aria-label="Gender Distribution Analysis">
                <div class="label">♂♀ Gender Split</div>
                
                <div class="gender-container">
                    <div class="pie-chart" style="background: ${genderInfo.conicGradient}" aria-label="Gender Distribution Chart"></div>
                    
                    <div class="gender-stats">
                        <div class="gender-stat">
                            <span class="stat-icon">♀</span>
                            <div class="stat-value">${genderInfo.femaleIndex}</div>
                            <div class="stat-percentage">${genderInfo.femalePercent.toFixed(1)}%</div>
                        </div>
                        <div class="gender-stat">
                            <span class="stat-icon">♂</span>
                            <div class="stat-value">${genderInfo.maleIndex}</div>
                            <div class="stat-percentage">${genderInfo.malePercent.toFixed(1)}%</div>
                        </div>
                    </div>
                    
                    <div class="gender-legend">
                        <div class="legend-item">
                            <div class="legend-color female-color"></div>
                            <span>Female: ${genderInfo.femaleIndex}</span>
                        </div>
                        <div class="legend-item">
                            <div class="legend-color male-color"></div>
                            <span>Male: ${genderInfo.maleIndex}</span>
                        </div>
                    </div>
                </div>
                
                <div class="info-panel">
                    <div class="info-title">Understanding Gender Distribution</div>
                    <div class="info-text">Values show popularity index (0-100), where 100 represents peak interest within each gender. Use this to understand which gender shows more interest in this topic and tailor your content strategy accordingly.</div>
                </div>
            </article>
        `;
    }
    
    // AGE DISTRIBUTION Panel
    if (hasAgeData) {
        html += `
            <article class="panel panel-large" tabindex="0" aria-label="Age Distribution Analysis">
                <div class="label">👥 Age Breakdown</div>
                
                <div style="margin-top:16px">
        `;
        
        // Wygeneruj paski wieku
        ageInfo.ageGroups.forEach(group => {
            const ageClass = getAgeIntensityClass(group.value);
            html += `
                <div class="age-item">
                    <div class="age-label">Age ${group.label}</div>
                    <div class="age-bar-container">
                        <div class="age-bar">
                            <div class="age-fill ${ageClass}" style="width:${group.percentage}%"></div>
                        </div>
                    </div>
                    <div class="age-value">${group.value}</div>
                </div>
            `;
        });
        
        html += `
                </div>
                
                <div class="info-panel">
                    <div class="info-title">Understanding Age Distribution</div>
                    <div class="info-text">Horizontal bars show interest levels across age groups (0-100). Darker/longer bars indicate higher interest. Use this to identify your core audience age range and adjust your content tone and marketing channels to match.</div>
                </div>
            </article>
        `;
    }
    
    html += `
                    </div>
                </section>

            </div>
        </div>
    `;
    
    demographicsContainer.innerHTML = html;
    
    // Initialize bar animations
    initializeAgeBarAnimations();
}

// ========================================
// HELPER FUNCTIONS
// ========================================

function getGenderInfo(data) {
    const femaleIndex = data.gender_female || 0;
    const maleIndex = data.gender_male || 0;
    const totalGender = femaleIndex + maleIndex;
    
    const femalePercent = totalGender > 0 ? (femaleIndex / totalGender * 100) : 0;
    const malePercent = totalGender > 0 ? (maleIndex / totalGender * 100) : 0;
    
    // Kąt dla conic-gradient (360 stopni = 100%)
    const femaleAngle = (femalePercent / 100) * 360;
    
    const conicGradient = `conic-gradient(var(--pink) 0deg ${femaleAngle}deg, var(--blue) ${femaleAngle}deg 360deg)`;
    
    return {
        femaleIndex,
        maleIndex,
        femalePercent,
        malePercent,
        conicGradient
    };
}

function getAgeInfo(data) {
    const ageGroups = [
        { label: '18-24', value: data.age_18_24 || 0, field: 'age_18_24' },
        { label: '25-34', value: data.age_25_34 || 0, field: 'age_25_34' },
        { label: '35-44', value: data.age_35_44 || 0, field: 'age_35_44' },
        { label: '45-54', value: data.age_45_54 || 0, field: 'age_45_54' },
        { label: '55-64', value: data.age_55_64 || 0, field: 'age_55_64' }
    ];
    
    // Znajdź maksymalną wartość dla skalowania pasków
    const maxAge = Math.max(...ageGroups.map(group => group.value));
    
    // Dodaj procenty dla wizualizacji
    const ageGroupsWithPercentages = ageGroups.map(group => ({
        ...group,
        percentage: maxAge > 0 ? (group.value / maxAge * 100) : 0
    }));
    
    return {
        ageGroups: ageGroupsWithPercentages,
        maxAge
    };
}

function getAgeIntensityClass(value) {
    // Mapowanie wartości na klasy intensywności
    if (value === 0) return 'age-0';
    if (value <= 25) return 'age-67'; // Niska intensywność
    if (value <= 50) return 'age-79'; // Średnia intensywność  
    if (value <= 75) return 'age-85'; // Wysoka intensywność
    return 'age-100'; // Maksymalna intensywność
}

function initializeAgeBarAnimations() {
    // Enhanced bar animations - similar to original template
    setTimeout(() => {
        const fills = document.querySelectorAll('.section-4-nasa .age-fill');
        fills.forEach((fill, index) => {
            const width = fill.style.width;
            fill.style.width = '0%';
            setTimeout(() => {
                fill.style.width = width;
            }, 200 + index * 100);
        });
    }, 100);
}

// ========================================
// EXPORT FUNCTIONS TO GLOBAL SCOPE
// ========================================
window.displayDemographicsAnalysis = displayDemographicsAnalysis;
window.getGenderInfo = getGenderInfo;
window.getAgeInfo = getAgeInfo;
window.getAgeIntensityClass = getAgeIntensityClass;
window.initializeAgeBarAnimations = initializeAgeBarAnimations;

console.log('✅ SEKCJA 4: Complete Demographics - Pełna implementacja załadowana zgodnie ze schematem'); 