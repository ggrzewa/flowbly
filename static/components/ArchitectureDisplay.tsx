import React, { useState, useMemo, useCallback } from 'react';
import { 
  Copy, 
  Download, 
  ChevronDown, 
  ChevronUp, 
  ExternalLink,
  Zap,
  Target,
  TrendingUp,
  Clock,
  FileText,
  Link2,
  Navigation,
  Settings
} from 'lucide-react';

// ========================================
// TYPESCRIPT INTERFACES
// ========================================

interface ArchitectureData {
  // Główne dane architektury
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
  
  // Strony
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
  
  // Linki wewnętrzne  
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
  
  // Notatki implementacyjne
  implementation_notes: Array<{
    id: string;
    category: string;
    recommendations: string[];
    difficulty_level: string;
    estimated_hours: string;
  }>;
  
  // Struktury nawigacyjne
  navigation: Array<{
    id: string;
    nav_type: 'main_menu' | 'breadcrumb_templates' | 'sidebar_nav' | 'mobile_menu';
    structure: any;
    max_depth: number;
    mobile_friendly: boolean;
  }>;
}

interface ArchitectureDisplayProps {
  data: ArchitectureData;
  onExport?: (format: 'json' | 'csv' | 'guide', section?: string) => void;
  onCopy?: (data: string) => void;
  className?: string;
}

// ========================================
// UTILITY HOOKS
// ========================================

const useTheme = (type: 'silo' | 'clusters') => {
  return useMemo(() => {
    if (type === 'silo') {
      return {
        primary: 'blue',
        gradient: 'from-blue-500 to-blue-700',
        bgGradient: 'from-blue-50 to-blue-100',
        accent: 'blue-600',
        text: 'Structure & Organization',
        icon: '🏗️',
        description: 'Rygorystyczna hierarchia bez cross-linking'
      };
    } else {
      return {
        primary: 'purple',
        gradient: 'from-purple-500 to-pink-600',
        bgGradient: 'from-purple-50 to-pink-100',
        accent: 'purple-600',
        text: 'Strategic Connections',
        icon: '🌉',
        description: 'Elastyczna architektura z AI-driven bridges'
      };
    }
  }, [type]);
};

// ========================================
// HEADER COMPONENT
// ========================================

const ArchitectureHeader: React.FC<{
  data: ArchitectureData;
  theme: any;
  onExport?: (format: string) => void;
}> = ({ data, theme, onExport }) => {
  const { architecture } = data;
  
  return (
    <div className={`bg-gradient-to-r ${theme.gradient} text-white p-6 rounded-t-lg`}>
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        {/* Left: Type & Title */}
        <div className="flex items-center gap-3">
          <span className="text-3xl">{theme.icon}</span>
          <div>
            <div className="flex items-center gap-2">
              <span className="bg-white/20 px-3 py-1 rounded-full text-sm font-medium">
                {architecture.architecture_type.toUpperCase()}
              </span>
              <span className="text-white/80">•</span>
              <span className="text-white/80">{architecture.total_pages} stron</span>
              {architecture.architecture_type === 'clusters' && (
                <>
                  <span className="text-white/80">•</span>
                  <span className="text-white/80">{architecture.cross_links_count} bridges</span>
                </>
              )}
            </div>
            <h1 className="text-2xl font-bold mt-1">{theme.text}</h1>
            <p className="text-white/80 text-sm">{theme.description}</p>
          </div>
        </div>

        {/* Right: Metrics & Actions */}
        <div className="flex flex-col md:flex-row items-start md:items-center gap-4">
          {/* Key Metrics */}
          <div className="flex gap-4 text-center">
            {architecture.seo_score && (
              <div className="bg-white/10 px-3 py-2 rounded-lg">
                <div className="text-lg font-bold">{architecture.seo_score}/100</div>
                <div className="text-xs text-white/80">SEO Score</div>
              </div>
            )}
            {architecture.processing_time && (
              <div className="bg-white/10 px-3 py-2 rounded-lg">
                <div className="text-lg font-bold">{architecture.processing_time.toFixed(1)}s</div>
                <div className="text-xs text-white/80">Processing</div>
              </div>
            )}
            <div className="bg-white/10 px-3 py-2 rounded-lg">
              <div className="text-lg font-bold">2</div>
              <div className="text-xs text-white/80">Max Depth</div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex gap-2">
            <button 
              onClick={() => onExport?.('json')}
              className="bg-white/20 hover:bg-white/30 px-3 py-2 rounded-lg flex items-center gap-2 text-sm transition-colors"
            >
              <Download size={16} />
              Export JSON
            </button>
            <button 
              onClick={() => onExport?.('csv')}
              className="bg-white/20 hover:bg-white/30 px-3 py-2 rounded-lg flex items-center gap-2 text-sm transition-colors"
            >
              <FileText size={16} />
              Export CSV
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

// ========================================
// STRATEGIC BRIDGES COMPONENT (CLUSTERS ONLY)
// ========================================

const StrategyBridges: React.FC<{
  bridges: ArchitectureData['internal_links'];
  theme: any;
}> = ({ bridges, theme }) => {
  const [showAll, setShowAll] = useState(false);
  const [selectedBridge, setSelectedBridge] = useState<string | null>(null);

  const strategicBridges = bridges.filter(link => link.link_type === 'strategic_bridge');
  const displayBridges = showAll ? strategicBridges : strategicBridges.slice(0, 5);

  const getBridgeType = (similarity: string | null) => {
    const score = parseFloat(similarity || '0');
    if (score > 0.9) return { type: 'very_high', color: 'green' };
    if (score > 0.8) return { type: 'high', color: 'blue' };
    if (score > 0.7) return { type: 'medium', color: 'yellow' };
    return { type: 'low', color: 'gray' };
  };

  return (
    <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Zap className={`text-${theme.accent}`} size={24} />
          <h2 className="text-xl font-bold">Strategic Cross-Linking</h2>
          <span className="bg-purple-100 text-purple-700 px-2 py-1 rounded-full text-sm">
            {strategicBridges.length} mostów
          </span>
        </div>
      </div>

      <div className="grid gap-4">
        {displayBridges.map((bridge, index) => {
          const bridgeInfo = getBridgeType(bridge.similarity_score);
          const isExpanded = selectedBridge === bridge.id;
          
          return (
            <div key={bridge.id} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
              {/* Bridge Header */}
              <div 
                className="flex items-center justify-between cursor-pointer"
                onClick={() => setSelectedBridge(isExpanded ? null : bridge.id)}
              >
                <div className="flex items-center gap-3">
                  <div className={`w-3 h-3 rounded-full bg-${bridgeInfo.color}-400`}></div>
                  <div className="flex items-center gap-2 text-sm">
                    <span className="font-medium">Similarity: {(parseFloat(bridge.similarity_score || '0') * 100).toFixed(1)}%</span>
                    <span className="text-gray-400">|</span>
                    <span className="text-gray-600">Type: {bridgeInfo.type}</span>
                  </div>
                </div>
                {isExpanded ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
              </div>

              {/* Bridge Connection Visual */}
              <div className="mt-3 flex items-center gap-3">
                <div className="flex-1 bg-gray-100 rounded-lg p-3 text-center">
                  <div className="font-medium text-sm text-gray-700">From</div>
                  <div className="text-purple-600 font-medium">{bridge.from_page_id}</div>
                </div>
                <div className="flex items-center gap-1">
                  <div className="w-4 h-0.5 bg-gray-300"></div>
                  <Link2 size={16} className="text-gray-400" />
                  <div className="w-4 h-0.5 bg-gray-300"></div>
                </div>
                <div className="flex-1 bg-gray-100 rounded-lg p-3 text-center">
                  <div className="font-medium text-sm text-gray-700">To</div>
                  <div className="text-purple-600 font-medium">{bridge.to_page_id}</div>
                </div>
              </div>

              {/* Expanded Details */}
              {isExpanded && (
                <div className="mt-4 pt-4 border-t border-gray-100 space-y-3">
                  <div>
                    <span className="text-sm font-medium text-gray-700">Anchor Text:</span>
                    <span className="ml-2 text-sm text-gray-900 font-mono bg-gray-100 px-2 py-1 rounded">
                      "{bridge.anchor_text}"
                    </span>
                  </div>
                  
                  <div>
                    <span className="text-sm font-medium text-gray-700">Placement:</span>
                    <div className="ml-2 flex gap-1 mt-1">
                      {bridge.placement.map((place, i) => (
                        <span key={i} className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded">
                          {place}
                        </span>
                      ))}
                    </div>
                  </div>

                  {bridge.bridge_rationale && (
                    <div>
                      <span className="text-sm font-medium text-gray-700">Business Logic:</span>
                      <p className="ml-2 text-sm text-gray-600 mt-1">{bridge.bridge_rationale}</p>
                    </div>
                  )}

                  <div className="flex gap-2 pt-2">
                    <button className="text-xs bg-purple-100 text-purple-700 px-3 py-1 rounded hover:bg-purple-200 transition-colors">
                      Copy Bridge Data
                    </button>
                    <button className="text-xs bg-green-100 text-green-700 px-3 py-1 rounded hover:bg-green-200 transition-colors">
                      Implementation Guide
                    </button>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Show More/Less */}
      {strategicBridges.length > 5 && (
        <div className="mt-4 text-center">
          <button 
            onClick={() => setShowAll(!showAll)}
            className="text-purple-600 hover:text-purple-700 font-medium text-sm flex items-center gap-1 mx-auto"
          >
            {showAll ? 'Show Less' : `Show ${strategicBridges.length - 5} More Bridges`}
            {showAll ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
          </button>
        </div>
      )}
    </div>
  );
};

// ========================================
// URL STRUCTURE COMPONENT
// ========================================

const URLStructure: React.FC<{
  pages: ArchitectureData['pages'];
  type: 'silo' | 'clusters';
  theme: any;
}> = ({ pages, type, theme }) => {
  const [expandedLevels, setExpandedLevels] = useState<Set<number>>(new Set([0, 1]));

  const pagesByLevel = useMemo(() => {
    const grouped = pages.reduce((acc, page) => {
      if (!acc[page.depth_level]) acc[page.depth_level] = [];
      acc[page.depth_level].push(page);
      return acc;
    }, {} as Record<number, typeof pages>);
    
    return grouped;
  }, [pages]);

  const toggleLevel = (level: number) => {
    const newExpanded = new Set(expandedLevels);
    if (newExpanded.has(level)) {
      newExpanded.delete(level);
    } else {
      newExpanded.add(level);
    }
    setExpandedLevels(newExpanded);
  };

  const getPageIcon = (pageType: string) => {
    switch (pageType) {
      case 'pillar': return '🏛️';
      case 'category': return '📁';
      case 'subcategory': return '📄';
      case 'cluster_page': return '📃';
      default: return '📄';
    }
  };

  const getPageLabel = (pageType: string) => {
    switch (pageType) {
      case 'pillar': return 'PILLAR';
      case 'category': return 'KATEGORIA';
      case 'subcategory': return 'SUB';
      case 'cluster_page': return 'PAGE';
      default: return 'PAGE';
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
      <div className="flex items-center gap-2 mb-4">
        <Navigation className={`text-${theme.accent}`} size={24} />
        <h2 className="text-xl font-bold">Struktura URL</h2>
        {type === 'silo' && (
          <span className="bg-blue-100 text-blue-700 px-2 py-1 rounded-full text-sm">
            Hierarchical Structure
          </span>
        )}
      </div>

      <div className="space-y-2">
        {Object.entries(pagesByLevel)
          .sort(([a], [b]) => parseInt(a) - parseInt(b))
          .map(([level, levelPages]) => (
            <div key={level}>
              {/* Level Header */}
              <button
                onClick={() => toggleLevel(parseInt(level))}
                className="w-full flex items-center gap-2 py-2 px-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
              >
                {expandedLevels.has(parseInt(level)) ? <ChevronDown size={16} /> : <ChevronUp size={16} />}
                <span className="font-medium">
                  Level {level} ({levelPages.length} page{levelPages.length !== 1 ? 's' : ''})
                </span>
              </button>

              {/* Level Pages */}
              {expandedLevels.has(parseInt(level)) && (
                <div className="ml-4 mt-2 space-y-2">
                  {levelPages.map((page, pageIndex) => (
                    <div key={page.id} className="flex items-center gap-3 p-3 border border-gray-200 rounded-lg">
                      <span className="text-lg">{getPageIcon(page.page_type)}</span>
                      
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <span className={`text-xs bg-${theme.primary}-100 text-${theme.accent} px-2 py-1 rounded`}>
                            {getPageLabel(page.page_type)} {pageIndex + 1}.{parseInt(level) + 1}
                          </span>
                          <span className="font-medium">{page.name}</span>
                        </div>
                        <div className="text-sm text-gray-600 font-mono mt-1">{page.url_path}</div>
                        
                        {/* Page Details */}
                        <div className="flex gap-4 mt-2 text-xs text-gray-500">
                          <span>Keywords: {page.target_keywords.length}</span>
                          <span>Content: ~{page.estimated_content_length} words</span>
                          {page.cluster_phrase_count > 0 && (
                            <span>Phrases: {page.cluster_phrase_count}</span>
                          )}
                        </div>
                      </div>

                      <button className="p-2 hover:bg-gray-100 rounded transition-colors">
                        <Copy size={14} className="text-gray-400" />
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
      </div>
    </div>
  );
};

// ========================================
// IMPLEMENTATION GUIDE COMPONENT
// ========================================

const ImplementationGuide: React.FC<{
  notes: ArchitectureData['implementation_notes'];
  type: 'silo' | 'clusters';
}> = ({ notes, type }) => {
  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(new Set());

  const toggleCategory = (category: string) => {
    const newExpanded = new Set(expandedCategories);
    if (newExpanded.has(category)) {
      newExpanded.delete(category);
    } else {
      newExpanded.add(category);
    }
    setExpandedCategories(newExpanded);
  };

  const getCategoryIcon = (category: string) => {
    if (category.includes('wordpress')) return '⚙️';
    if (category.includes('technical')) return '🔧';
    if (category.includes('content')) return '📝';
    if (category.includes('seo')) return '📈';
    return '💡';
  };

  const getCategoryColor = (category: string) => {
    if (category.includes('wordpress')) return 'blue';
    if (category.includes('technical')) return 'green';
    if (category.includes('content')) return 'purple';
    if (category.includes('seo')) return 'orange';
    return 'gray';
  };

  return (
    <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
      <div className="flex items-center gap-2 mb-4">
        <Settings size={24} className="text-gray-600" />
        <h2 className="text-xl font-bold">Implementation Guide</h2>
        <span className="bg-gray-100 text-gray-700 px-2 py-1 rounded-full text-sm">
          {type === 'silo' ? 'Structure-focused' : 'Connection-focused'}
        </span>
      </div>

      <div className="space-y-3">
        {notes.map((note) => {
          const isExpanded = expandedCategories.has(note.category);
          const color = getCategoryColor(note.category);
          
          return (
            <div key={note.id} className="border border-gray-200 rounded-lg">
              <button
                onClick={() => toggleCategory(note.category)}
                className="w-full flex items-center justify-between p-4 hover:bg-gray-50 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <span className="text-lg">{getCategoryIcon(note.category)}</span>
                  <div className="text-left">
                    <div className="font-medium capitalize">{note.category.replace('_', ' ')}</div>
                    <div className="text-sm text-gray-500">
                      {note.recommendations.length} recommendations • {note.estimated_hours}h estimated
                    </div>
                  </div>
                </div>
                {isExpanded ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
              </button>

              {isExpanded && (
                <div className="px-4 pb-4 border-t border-gray-100">
                  <div className="space-y-2 mt-3">
                    {note.recommendations.map((rec, index) => (
                      <div key={index} className="flex items-start gap-2">
                        <span className={`w-1.5 h-1.5 bg-${color}-400 rounded-full mt-2 flex-shrink-0`}></span>
                        <span className="text-sm text-gray-700">{rec}</span>
                      </div>
                    ))}
                  </div>
                  
                  <div className="flex gap-2 mt-3 pt-3 border-t border-gray-100">
                    <span className={`text-xs bg-${color}-100 text-${color}-700 px-2 py-1 rounded`}>
                      {note.difficulty_level}
                    </span>
                    <span className="text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded">
                      {note.estimated_hours}h
                    </span>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};

// ========================================
// MAIN COMPONENT
// ========================================

const ArchitectureResultsDisplay: React.FC<ArchitectureDisplayProps> = ({
  data,
  onExport,
  onCopy,
  className = ''
}) => {
  const theme = useTheme(data.architecture.architecture_type);

  const handleCopy = useCallback((text: string) => {
    navigator.clipboard.writeText(text);
    onCopy?.(text);
  }, [onCopy]);

  const handleExport = useCallback((format: 'json' | 'csv' | 'guide', section?: string) => {
    onExport?.(format, section);
  }, [onExport]);

  return (
    <div className={`max-w-7xl mx-auto ${className}`}>
      {/* Header */}
      <ArchitectureHeader 
        data={data} 
        theme={theme} 
        onExport={handleExport}
      />

      {/* Main Content */}
      <div className="bg-gray-50 p-6 space-y-6">
        
        {/* Strategic Bridges - CLUSTERS ONLY */}
        {data.architecture.architecture_type === 'clusters' && (
          <StrategyBridges 
            bridges={data.internal_links} 
            theme={theme}
          />
        )}

        {/* URL Structure - Enhanced for SILO */}
        <URLStructure 
          pages={data.pages} 
          type={data.architecture.architecture_type}
          theme={theme}
        />

        {/* Implementation Guide */}
        <ImplementationGuide 
          notes={data.implementation_notes}
          type={data.architecture.architecture_type}
        />

        {/* Navigation Structures */}
        {data.navigation.length > 0 && (
          <div className="bg-white rounded-lg shadow-lg p-6">
            <div className="flex items-center gap-2 mb-4">
              <Navigation size={24} className="text-gray-600" />
              <h2 className="text-xl font-bold">Navigation Structures</h2>
              <span className="bg-gray-100 text-gray-700 px-2 py-1 rounded-full text-sm">
                {data.navigation.length} structures
              </span>
            </div>
            
            <div className="grid md:grid-cols-2 gap-4">
              {data.navigation.map((nav) => (
                <div key={nav.id} className="border border-gray-200 rounded-lg p-4">
                  <div className="font-medium mb-2 capitalize">
                    {nav.nav_type.replace('_', ' ')}
                  </div>
                  <div className="text-sm text-gray-600 mb-2">
                    Max depth: {nav.max_depth} • Mobile friendly: {nav.mobile_friendly ? 'Yes' : 'No'}
                  </div>
                  <button className="text-sm bg-gray-100 hover:bg-gray-200 px-3 py-1 rounded transition-colors">
                    View Structure
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

      </div>

      {/* Footer Actions */}
      <div className="bg-white border-t border-gray-200 p-4 rounded-b-lg">
        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          <button 
            onClick={() => handleExport('json')}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <Download size={16} />
            Export JSON
          </button>
          <button 
            onClick={() => handleExport('csv')}
            className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
          >
            <FileText size={16} />
            Export CSV
          </button>
          <button 
            onClick={() => handleExport('guide')}
            className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
          >
            <Target size={16} />
            Implementation Guide
          </button>
        </div>
      </div>
    </div>
  );
};

export default ArchitectureResultsDisplay;
export type { ArchitectureData }; 