# 🏗️ Architecture Display Component - Dokumentacja

## 📋 **Przegląd**

Nowy **Architecture Display Component** to zaawansowany system wyświetlania wyników z **Modułu 3: Architecture Generator**. Komponent oferuje:

- ✅ **Dynamic Theming** - SILO (blue) vs CLUSTERS (purple)
- ✅ **Progressive Disclosure** - show more/less functionality
- ✅ **Interactive Bridge Explorer** - similarity scores, business logic
- ✅ **Mobile Responsive Design** - cards stack vertically
- ✅ **Export Functionality** - JSON/CSV/Implementation Guide
- ✅ **TypeScript Support** - kompletne typowanie danych

---

## 🚀 **Quick Start**

### **1. Pliki komponentu:**

```
static/
├── components/
│   ├── ArchitectureDisplay.tsx    # Main React TypeScript component
│   └── ArchitectureDisplay.css    # Styling z dynamic theming
└── sections/section10/
    └── section10.js               # Vanilla JS integration
```

### **2. Użycie w HTML:**

```html
<!-- W <head> -->
<link rel="stylesheet" href="/static/components/ArchitectureDisplay.css">
<script src="https://cdn.tailwindcss.com"></script>

<!-- Przed </body> -->
<script src="/static/sections/section10/section10.js"></script>

<!-- Container do wyświetlania -->
<div id="architecture-results-container"></div>
```

### **3. Wywołanie JavaScript:**

```javascript
// Przykład danych z API
const architectureData = {
    architecture: {
        id: "cluster_123",
        architecture_type: "clusters", // lub "silo"
        name: "Soczewki kontaktowe - CLUSTERS",
        total_pages: 16,
        cross_links_count: 15,
        seo_score: 90,
        processing_time: 12.5
    },
    pages: [...],
    internal_links: [...],
    implementation_notes: [...],
    navigation: [...]
};

// Renderowanie komponentu
window.renderArchitectureResults(architectureData, 'architecture-results-container');
```

---

## 🎨 **Dynamic Theming**

### **SILO MODE (Blue Theme):**
- Focus: **Structure & Organization**
- Color: `blue-600` gradient
- Icon: 🏗️
- Description: "Rygorystyczna hierarchia bez cross-linking"

### **CLUSTERS MODE (Purple Theme):**
- Focus: **Strategic Connections**
- Color: `purple-600` to `pink-600` gradient
- Icon: 🌉
- Description: "Elastyczna architektura z AI-driven bridges"

---

## 📊 **Struktura Danych (TypeScript Interface)**

```typescript
interface ArchitectureData {
  architecture: {
    id: string;
    architecture_type: 'silo' | 'clusters';
    name: string;
    total_pages: number;
    cross_links_count: number;
    created_at: string;
    hierarchy: any;
    seo_score?: number;
    processing_time?: number;
  };
  
  pages: Array<{
    id: string;
    name: string;
    url_path: string;
    page_type: 'pillar' | 'category' | 'subcategory' | 'cluster_page';
    target_keywords: string[];
    estimated_content_length: number;
    cluster_name: string;
    cluster_phrase_count: number;
    depth_level: number;
  }>;
  
  internal_links: Array<{
    id: string;
    from_page_id: string;
    to_page_id: string;
    link_type: 'upward_category' | 'upward_pillar' | 'strategic_bridge';
    anchor_text: string;
    placement: string[];
    similarity_score: string | null;
    bridge_rationale: string | null;
    priority: number;
    frequency: string | null;
  }>;
  
  implementation_notes: Array<{
    id: string;
    category: string;
    recommendations: string[];
    difficulty_level: string;
    estimated_hours: string;
  }>;
  
  navigation: Array<{
    id: string;
    nav_type: 'main_menu' | 'breadcrumb_templates' | 'sidebar_nav' | 'mobile_menu';
    structure: any;
    max_depth: number;
    mobile_friendly: boolean;
  }>;
}
```

---

## 🌉 **Strategic Bridges (CLUSTERS tylko)**

### **Funkcjonalności:**
- **Similarity Scores** - 70% - 100% threshold
- **Bridge Types** - very_high, high, medium, low
- **Business Logic** - AI-generated rationale
- **Smart Anchor Text** - context-aware anchor generation
- **Placement Strategy** - intro, mid_content, conclusion

### **Przykład Bridge Card:**

```javascript
{
  "from_cluster": "Marki laptopów",
  "to_cluster": "Sklepy i platformy",
  "similarity_score": 0.89,
  "suggested_anchor": "więcej o sklepy i platformy sprzedaży",
  "bridge_rationale": "Users researching brands need to know where to buy",
  "placement": ["mid_content", "conclusion"],
  "priority": 85
}
```

---

## 📱 **Mobile Responsiveness**

### **Breakpoints:**
```css
/* Mobile: < 768px */
@media (max-width: 768px) {
  .bridge-cards { grid-template-columns: 1fr; }
  .header-metrics { flex-direction: column; }
  .action-buttons { flex-direction: column; width: 100%; }
}
```

### **Touch Optimizations:**
- Larger touch targets (44px minimum)
- Swipe gestures for card navigation
- Collapsible sections for small screens
- Optimized font sizes (14px+ on mobile)

---

## 🔧 **Funkcje Interactive**

### **Progressive Disclosure:**

```javascript
// Toggle bridge details
function toggleBridgeDetails(bridgeId) {
    const card = document.querySelector(`[data-bridge-id="${bridgeId}"]`);
    const details = card.querySelector('.bridge-details');
    
    if (details.classList.contains('hidden')) {
        details.classList.remove('hidden');
    } else {
        details.classList.add('hidden');
    }
}

// Toggle level pages
function toggleLevel(level) {
    const pages = document.querySelector(`.level-${level}`);
    // Implementation...
}
```

### **Export Functions:**

```javascript
// JSON Export
function exportArchitecture(format) {
    const data = window.currentArchitectureData;
    
    if (format === 'json') {
        const blob = new Blob([JSON.stringify(data, null, 2)], 
                            { type: 'application/json' });
        downloadFile(blob, 'architecture.json');
    }
    
    if (format === 'csv') {
        const csv = convertToCSV(data.pages);
        const blob = new Blob([csv], { type: 'text/csv' });
        downloadFile(blob, 'architecture.csv');
    }
}
```

---

## 🔄 **Integracja z Backend API**

### **Data Transformation:**

```javascript
function transformArchitectureDataForComponent(backendData, meta) {
    // Transform backend response to component interface
    return {
        architecture: {
            id: backendData.semantic_cluster_id,
            architecture_type: backendData.architecture_type,
            name: `${backendData.seed_keyword} - ${backendData.architecture_type.toUpperCase()}`,
            total_pages: backendData.stats.total_pages,
            cross_links_count: backendData.strategic_bridges?.length || 0,
            seo_score: backendData.seo_score,
            processing_time: meta.processing_time
        },
        pages: transformPages(backendData.url_structure),
        internal_links: transformBridges(backendData.strategic_bridges),
        implementation_notes: transformNotes(backendData.implementation_notes),
        navigation: transformNavigation(backendData.navigation)
    };
}
```

### **API Call Example:**

```javascript
async function generateArchitecture(clusterId, type) {
    const response = await fetch('/api/v6/architecture/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            semantic_cluster_id: clusterId,
            architecture_type: type,
            domain: 'moje-soczewki.pl'
        })
    });
    
    const result = await response.json();
    
    // Transform and display
    const transformedData = transformArchitectureDataForComponent(result.data, result.meta);
    window.renderArchitectureResults(transformedData, 'architecture-results-container');
}
```

---

## 🎯 **Customization Options**

### **Theme Variables:**

```css
/* Silo Theme */
.theme-silo {
  --primary-color: #2563eb;
  --primary-light: #dbeafe;
  --gradient-start: #3b82f6;
  --gradient-end: #1d4ed8;
}

/* Clusters Theme */
.theme-clusters {
  --primary-color: #7c3aed;
  --primary-light: #ede9fe;
  --gradient-start: #8b5cf6;
  --gradient-end: #ec4899;
}
```

### **Bridge Colors:**

```javascript
function getBridgeType(similarity) {
    if (similarity > 0.9) return { type: 'very_high', color: 'green' };
    if (similarity > 0.8) return { type: 'high', color: 'blue' };
    if (similarity > 0.7) return { type: 'medium', color: 'yellow' };
    return { type: 'low', color: 'gray' };
}
```

---

## 🚨 **Error Handling**

### **Fallback System:**

```javascript
try {
    if (typeof window.renderArchitectureResults === 'function') {
        window.renderArchitectureResults(transformedData, 'architectureResults');
    } else {
        console.warn('⚠️ New component not available, using fallback');
        displayArchitectureResultsFallback(architectureData, meta);
    }
} catch (error) {
    console.error('❌ Error rendering component:', error);
    displayArchitectureResultsFallback(architectureData, meta);
}
```

### **Loading States:**

```html
<!-- Loading skeleton -->
<div id="architecture-loading" class="text-center py-8">
    <div class="skeleton w-full h-32 rounded-lg mb-4"></div>
    <div class="skeleton w-3/4 h-4 rounded mb-2 mx-auto"></div>
</div>

<!-- Error state -->
<div id="architecture-error" class="hidden bg-red-50 border border-red-200 rounded-lg p-4">
    <div class="flex items-center gap-2 text-red-700">
        <span>❌</span>
        <span class="font-medium">Błąd generowania architektury</span>
    </div>
</div>
```

---

## 📈 **Performance Optimizations**

### **React Optimizations (dla TSX):**

```typescript
// Memoized components
const StrategyBridges = React.memo<BridgesProps>(({ bridges, theme }) => {
    // Component logic
});

// Optimized calculations
const pagesByLevel = useMemo(() => {
    return pages.reduce((acc, page) => {
        if (!acc[page.depth_level]) acc[page.depth_level] = [];
        acc[page.depth_level].push(page);
        return acc;
    }, {} as Record<number, typeof pages>);
}, [pages]);

// Callback optimization
const handleCopy = useCallback((text: string) => {
    navigator.clipboard.writeText(text);
    onCopy?.(text);
}, [onCopy]);
```

### **Vanilla JS Optimizations:**

```javascript
// Virtual scrolling for large lists
function renderVisibleBridges(bridges, startIndex, endIndex) {
    return bridges.slice(startIndex, endIndex).map(createBridgeCard);
}

// Debounced search
const debouncedSearch = debounce((query) => {
    filterBridges(query);
}, 300);
```

---

## 🧪 **Testing**

### **Unit Tests:**

```javascript
// Test data transformation
describe('transformArchitectureDataForComponent', () => {
    it('should transform backend data correctly', () => {
        const backendData = { /* mock data */ };
        const result = transformArchitectureDataForComponent(backendData, {});
        
        expect(result.architecture.architecture_type).toBe('clusters');
        expect(result.pages).toHaveLength(5);
    });
});

// Test component rendering
describe('renderArchitectureResults', () => {
    it('should render without errors', () => {
        const container = document.createElement('div');
        container.id = 'test-container';
        document.body.appendChild(container);
        
        expect(() => {
            renderArchitectureResults(mockData, 'test-container');
        }).not.toThrow();
    });
});
```

---

## 🔗 **Browser Support**

### **Supported Browsers:**
- ✅ Chrome/Edge 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Mobile browsers (iOS Safari, Chrome Mobile)

### **Feature Detection:**

```javascript
// Check for required features
function checkBrowserSupport() {
    const features = {
        fetch: typeof fetch !== 'undefined',
        promises: typeof Promise !== 'undefined',
        clipboard: navigator.clipboard !== undefined,
        css_grid: CSS.supports('display', 'grid')
    };
    
    return Object.values(features).every(Boolean);
}
```

---

## 📚 **Dodatkowe Zasoby**

### **Related Files:**
- `app/services/architecture_generator.py` - Backend generator
- `app/main.py` - API endpoints
- `static/sections/section10/section10.css` - Additional styles
- `templates/seo_analysis_modular.html` - HTML integration

### **API Endpoints:**
- `POST /api/v6/architecture/generate` - Generate architecture
- `GET /api/v6/architecture/{id}` - Get architecture details
- `GET /api/v6/architecture/test-connection` - Test module

### **Example Projects:**
- Zobacz `test_enhanced_prompt_demo.py` dla przykładów użycia
- Check out `test_ai_clustering_demo.py` dla integracji z modułem 1

---

**🎉 Komponent jest gotowy do użycia! Przetestuj z prawdziwymi danymi z Modułu 3.** 