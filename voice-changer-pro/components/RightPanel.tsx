import React, { useState, useEffect } from 'react';
import { Wand2, ChevronDown, Sliders, Search, ChevronUp, Server, Filter, X } from 'lucide-react';
import { Voice, ProcessingConfig, Language, AppState, VoiceLibraryQuery, VoiceLibraryTab } from '../types';
import type { CapabilitiesResponse } from '../backend';
import { Slider } from './ui/Slider';
import { VoiceCard } from './VoiceCard';

interface RightPanelProps {
  voices: Voice[];
    voicesLoading?: boolean;
    recentUsedVoices?: Voice[];
    onToggleFavorite?: (voiceId: string, nextIsFavorite: boolean) => void;
    onCreateMyVoice?: (displayName: string) => void;
        onPreviewVoice?: (voice: Voice) => void;
  config: ProcessingConfig;
  setConfig: (config: ProcessingConfig) => void;
  appState: AppState;
  onGenerate: () => void;
  isDisabled: boolean;
    apiBaseUrl?: string;
    capabilities?: CapabilitiesResponse | null;
    voiceQuery: VoiceLibraryQuery;
    setVoiceQuery: React.Dispatch<React.SetStateAction<VoiceLibraryQuery>>;
}

export const RightPanel: React.FC<RightPanelProps> = ({ 
    voices, voicesLoading, recentUsedVoices, onToggleFavorite, onCreateMyVoice, onPreviewVoice, config, setConfig, appState, onGenerate, isDisabled, apiBaseUrl, capabilities, voiceQuery, setVoiceQuery
}) => {
    const [activeTab, setActiveTab] = useState<VoiceLibraryTab>(voiceQuery.tab);
  const [isAdvancedOpen, setIsAdvancedOpen] = useState(false);
    const [isBackendOpen, setIsBackendOpen] = useState(false);
    const [isTypesOpen, setIsTypesOpen] = useState(false);
    const [filtersOpen, setFiltersOpen] = useState(false);
    const [searchQuery, setSearchQuery] = useState(voiceQuery.keyword || '');
    const [myVoiceName, setMyVoiceName] = useState('');

    const formatBytes = (bytes?: number) => {
        if (typeof bytes !== 'number' || !Number.isFinite(bytes)) return '--';
        return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
    };

    const formatSec = (sec?: number) => {
        if (typeof sec !== 'number' || !Number.isFinite(sec)) return '--:--';
        const s = Math.max(0, Math.floor(sec));
        const m = Math.floor(s / 60);
        const r = s % 60;
        return `${m.toString().padStart(2, '0')}:${r.toString().padStart(2, '0')}`;
    };

        const dimmed = Boolean(isDisabled);

    // Sync local tab -> query
    useEffect(() => {
        setActiveTab(voiceQuery.tab);
    }, [voiceQuery.tab]);

    // Debounce keyword -> query
    useEffect(() => {
        const t = setTimeout(() => {
            const next = (searchQuery || '').trim();
            if (next === (voiceQuery.keyword || '')) return;
            setVoiceQuery((prev) => ({ ...prev, keyword: next }));
        }, 250);
        return () => clearTimeout(t);
    }, [searchQuery]);

    const filteredVoices = voices;

    const setTab = (tab: VoiceLibraryTab) => {
        setActiveTab(tab);
        setVoiceQuery((prev) => ({ ...prev, tab }));
    };

    const updateFilters = (patch: Partial<VoiceLibraryQuery['filters']>) => {
        setVoiceQuery((prev) => ({
            ...prev,
            filters: { ...prev.filters, ...patch },
        }));
    };

    const toggleListValue = (key: 'scene' | 'emotion', value: string) => {
        setVoiceQuery((prev) => {
            const cur = (prev.filters?.[key] || []) as string[];
            const next = cur.includes(value) ? cur.filter((x) => x !== value) : [...cur, value];
            return { ...prev, filters: { ...prev.filters, [key]: next } as any };
        });
    };

    const clearAllFilters = () => {
        setVoiceQuery((prev) => ({
            ...prev,
            filters: { language: prev.filters.language || 'en', age: '', gender: '', scene: [], emotion: [] },
        }));
    };

    const filterChips: Array<{ label: string; onClear: () => void }> = [];
    const f = voiceQuery.filters || {};
    if (f.language) {
        const label = f.language === 'en' ? 'English' : f.language === 'zh' ? 'Chinese' : f.language === 'ja' ? 'Japanese' : '';
        if (label) filterChips.push({ label, onClear: () => updateFilters({ language: '' }) });
    }
    if (f.age) {
        const label = f.age === 'young' ? 'Young' : f.age === 'middle_age' ? 'Middle age' : f.age === 'old' ? 'Old' : '';
        if (label) filterChips.push({ label, onClear: () => updateFilters({ age: '' }) });
    }
    if (f.gender) {
        const label = f.gender === 'male' ? 'Male' : f.gender === 'female' ? 'Female' : '';
        if (label) filterChips.push({ label, onClear: () => updateFilters({ gender: '' }) });
    }
    (f.scene || []).forEach((s) => filterChips.push({ label: s, onClear: () => toggleListValue('scene', s) }));
    (f.emotion || []).forEach((e) => filterChips.push({ label: e, onClear: () => toggleListValue('emotion', e) }));

  return (
    <div className={`
        h-full flex flex-col bg-white border-l border-gray-200 transition-all duration-700 ease-out transform
                ${dimmed ? 'opacity-60 grayscale' : 'opacity-100 grayscale-0'}
    `}>
      {/* Fixed Header Section */}
      <div className="flex-shrink-0 px-6 pt-8 pb-4 bg-white z-10">
        <h2 className="text-3xl font-bold text-brand-black mb-2 flex items-baseline gap-3">
                    <span className={`font-bold tracking-tighter text-4xl select-none transition-colors duration-500 ${dimmed ? 'text-gray-200' : 'text-gray-300'}`}>02</span>
          Voice Selection
        </h2>
        
        {/* Search Bar */}
        <div className="relative mt-6 mb-4">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
            <input 
                type="text"
                placeholder="Search"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full bg-white border border-gray-200 rounded-lg pl-10 pr-4 py-2.5 text-sm focus:outline-none focus:border-brand-orange focus:ring-1 focus:ring-brand-orange/20 transition-all"
            />
        </div>

        {activeTab === 'my_voices' && (
            <div className="mb-6 rounded-xl border border-gray-200 bg-white p-3">
                <div className="text-xs font-bold text-gray-500 uppercase tracking-wide mb-2">Create my voice</div>
                <div className="flex items-center gap-2">
                    <input
                        value={myVoiceName}
                        onChange={(e) => setMyVoiceName(e.target.value)}
                        placeholder="输入一个音色名称（例如：我的旁白）"
                        className="flex-1 bg-white border border-gray-200 text-gray-700 text-sm py-2 px-3 rounded-lg leading-tight focus:outline-none focus:border-brand-orange shadow-sm"
                    />
                    <button
                        type="button"
                        onClick={() => {
                            const name = (myVoiceName || '').trim();
                            if (!name) return;
                            onCreateMyVoice?.(name);
                            setMyVoiceName('');
                        }}
                        className="px-3 py-2 rounded-lg bg-brand-black text-white text-sm font-semibold hover:bg-gray-900 transition-colors"
                    >
                        添加
                    </button>
                </div>
                <div className="mt-2 text-xs text-gray-400">最小可用版本：先创建元数据，后续可再加上传音频训练/绑定。</div>
            </div>
        )}

        {/* Filters Row */}
                <div className="mb-6">
                    <div className="flex items-center gap-2 overflow-x-auto no-scrollbar">
                        <button
                            type="button"
                            onClick={() => setFiltersOpen((v) => !v)}
                            className="flex items-center gap-1.5 px-3 py-1.5 rounded-full border border-gray-200 text-xs font-semibold text-gray-700 hover:bg-gray-50 hover:border-gray-300 whitespace-nowrap"
                        >
                            <Filter size={12} />
                            Filter
                            <ChevronDown size={12} />
                        </button>

                        {filterChips.map((c) => (
                            <button
                                key={c.label}
                                type="button"
                                onClick={c.onClear}
                                className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-gray-50 border border-gray-200 text-xs font-medium text-gray-700 hover:bg-gray-100 whitespace-nowrap"
                            >
                                <span className="truncate max-w-[160px]">{c.label}</span>
                                <X size={12} className="text-gray-400" />
                            </button>
                        ))}

                        {filterChips.length > 0 && (
                            <button
                                type="button"
                                onClick={clearAllFilters}
                                className="px-3 py-1.5 rounded-full text-xs font-medium text-gray-500 hover:text-brand-black whitespace-nowrap"
                            >
                                Clear
                            </button>
                        )}
                    </div>

                    {filtersOpen && (
                        <div className="mt-3 rounded-xl border border-gray-200 bg-white p-3 animate-fade-in-up">
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                                {/* Language */}
                                <div>
                                    <label className="text-xs font-semibold text-gray-600 mb-1 block">Language</label>
                                    <div className="relative">
                                        <select
                                            value={voiceQuery.filters.language || ''}
                                            onChange={(e) => updateFilters({ language: (e.target.value as any) || '' })}
                                            className="w-full appearance-none bg-white border border-gray-200 text-gray-700 text-sm py-2 px-3 pr-8 rounded-lg leading-tight focus:outline-none focus:border-brand-orange shadow-sm"
                                        >
                                            <option value="">Any</option>
                                            <option value="en">English</option>
                                            <option value="zh">Chinese</option>
                                            <option value="ja">Japanese</option>
                                        </select>
                                        <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-gray-500">
                                            <ChevronDown size={14} />
                                        </div>
                                    </div>
                                </div>

                                {/* Age */}
                                <div>
                                    <label className="text-xs font-semibold text-gray-600 mb-1 block">Age</label>
                                    <div className="relative">
                                        <select
                                            value={voiceQuery.filters.age || ''}
                                            onChange={(e) => updateFilters({ age: (e.target.value as any) || '' })}
                                            className="w-full appearance-none bg-white border border-gray-200 text-gray-700 text-sm py-2 px-3 pr-8 rounded-lg leading-tight focus:outline-none focus:border-brand-orange shadow-sm"
                                        >
                                            <option value="">Any</option>
                                            <option value="young">Young</option>
                                            <option value="middle_age">Middle age</option>
                                            <option value="old">Old</option>
                                        </select>
                                        <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-gray-500">
                                            <ChevronDown size={14} />
                                        </div>
                                    </div>
                                </div>

                                {/* Gender */}
                                <div>
                                    <label className="text-xs font-semibold text-gray-600 mb-1 block">Gender</label>
                                    <div className="relative">
                                        <select
                                            value={voiceQuery.filters.gender || ''}
                                            onChange={(e) => updateFilters({ gender: (e.target.value as any) || '' })}
                                            className="w-full appearance-none bg-white border border-gray-200 text-gray-700 text-sm py-2 px-3 pr-8 rounded-lg leading-tight focus:outline-none focus:border-brand-orange shadow-sm"
                                        >
                                            <option value="">Any</option>
                                            <option value="male">Male</option>
                                            <option value="female">Female</option>
                                        </select>
                                        <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-gray-500">
                                            <ChevronDown size={14} />
                                        </div>
                                    </div>
                                </div>
                            </div>

                            {/* Scene */}
                            <div className="mt-3">
                                <label className="text-xs font-semibold text-gray-600 mb-1 block">Scene</label>
                                <div className="grid grid-cols-2 gap-2">
                                    {[
                                        'Social Video',
                                        'Podcast',
                                        'Advertising / Commercial',
                                        'eCommerce',
                                        'Education',
                                        'Gaming & Fiction',
                                        'Wellness',
                                        'Audiobook',
                                    ].map((s) => (
                                        <label key={s} className="flex items-center gap-2 text-xs text-gray-700">
                                            <input
                                                type="checkbox"
                                                checked={(voiceQuery.filters.scene || []).includes(s)}
                                                onChange={() => toggleListValue('scene', s)}
                                                className="rounded border-gray-300 text-brand-orange focus:ring-brand-orange"
                                            />
                                            <span>{s}</span>
                                        </label>
                                    ))}
                                </div>
                            </div>

                            {/* Emotion */}
                            <div className="mt-3">
                                <label className="text-xs font-semibold text-gray-600 mb-1 block">Emotion</label>
                                <div className="grid grid-cols-2 gap-2">
                                    {['joyful', 'Angry', 'Sad', 'Fearful', 'Surprise', 'Calm'].map((e) => (
                                        <label key={e} className="flex items-center gap-2 text-xs text-gray-700">
                                            <input
                                                type="checkbox"
                                                checked={(voiceQuery.filters.emotion || []).includes(e)}
                                                onChange={() => toggleListValue('emotion', e)}
                                                className="rounded border-gray-300 text-brand-orange focus:ring-brand-orange"
                                            />
                                            <span>{e}</span>
                                        </label>
                                    ))}
                                </div>
                            </div>
                        </div>
                    )}
                </div>

        {/* Tabs */}
        <div className="flex items-center gap-6 border-b border-gray-100">
            {['Local', 'Featured', 'All voices', 'My voices', 'Saved'].map((tab) => {
                const key = tab.toLowerCase().replace(' ', '_') as VoiceLibraryTab;
                const isActive = activeTab === key;
                return (
                    <button 
                        key={key}
                        onClick={() => setTab(key)}
                        className={`pb-3 text-sm font-medium transition-all relative ${isActive ? 'text-brand-black' : 'text-gray-400 hover:text-gray-600'}`}
                    >
                        {tab}
                        {isActive && <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-brand-black rounded-t-full" />}
                    </button>
                );
            })}
        </div>
      </div>

      {/* Scrollable Voice List */}
      <div className="flex-1 overflow-y-auto no-scrollbar px-6 pb-4">
          <div className="flex flex-col">
              {voicesLoading && (
                  <div className="py-4 text-center text-gray-400 text-sm">Loading voices...</div>
              )}
              {recentUsedVoices && recentUsedVoices.length > 0 && (
                  <div className="py-3">
                      <div className="text-xs font-bold text-gray-500 uppercase tracking-wide mb-2">Recently used</div>
                      <div className="flex flex-wrap gap-2">
                          {recentUsedVoices.slice(0, 6).map((v) => (
                              <button
                                  key={v.id}
                                  type="button"
                                  onClick={() => setConfig({ ...config, voiceId: v.id })}
                                  className={`px-3 py-1.5 rounded-full text-xs font-medium border transition-colors ${config.voiceId === v.id ? 'bg-brand-orangeLight/20 border-brand-orange/30 text-brand-black' : 'bg-white border-gray-200 text-gray-600 hover:bg-gray-50'}`}
                              >
                                  {v.name}
                              </button>
                          ))}
                      </div>
                  </div>
              )}
              {filteredVoices.map(voice => (
                  <VoiceCard 
                      key={voice.id}
                      voice={voice}
                      isSelected={config.voiceId === voice.id}
                      onSelect={() => setConfig({ ...config, voiceId: voice.id })}
                      onToggleFavorite={onToggleFavorite}
                      onPreview={onPreviewVoice}
                  />
              ))}
              {filteredVoices.length === 0 && (
                  <div className="py-8 text-center text-gray-400 text-sm">No voices found</div>
              )}
          </div>
      </div>

      {/* Configuration & Action Footer */}
      <div className="flex-shrink-0 border-t border-gray-200 bg-gray-50/50">
        {/* Advanced Settings Toggle */}
        <div className="px-6 py-2 border-b border-gray-200 bg-white">
             <button 
                onClick={() => setIsAdvancedOpen(!isAdvancedOpen)}
                className="flex items-center justify-between w-full text-xs font-bold text-gray-500 uppercase tracking-wide hover:text-brand-black transition-colors py-2"
            >
                <div className="flex items-center gap-2">
                    <Sliders size={14} />
                    <span>Parameters & Language</span>
                </div>
                {isAdvancedOpen ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
            </button>

            {isAdvancedOpen && (
                <div className="pt-4 pb-2 animate-fade-in-up">
                    <div className="mb-4">
                        <label className="text-xs font-semibold text-gray-700 mb-2 block">Output Language</label>
                        <div className="relative">
                            <select 
                                className="w-full appearance-none bg-white border border-gray-200 text-gray-700 text-sm py-2 px-3 pr-8 rounded-lg leading-tight focus:outline-none focus:border-brand-orange shadow-sm font-medium"
                                value={config.language}
                                onChange={(e) => setConfig({...config, language: e.target.value as Language})}
                            >
                                {Object.values(Language).map((lang) => (
                                    <option key={lang} value={lang}>{lang}</option>
                                ))}
                            </select>
                            <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-gray-500">
                                <ChevronDown size={14} />
                            </div>
                        </div>
                    </div>
                    <div className="space-y-4">
                        <Slider 
                            label="Similarity"
                            value={config.similarity}
                            onChange={(val) => setConfig({ ...config, similarity: val })}
                            min={1}
                            max={10}
                            leftLabel="Low"
                            rightLabel="High"
                            tooltipText="Higher values mimic the target speaker more closely."
                        />
                        <Slider 
                            label="Stability"
                            value={config.stability}
                            onChange={(val) => setConfig({ ...config, stability: val })}
                            min={1}
                            max={10}
                            leftLabel="Variable"
                            rightLabel="Stable"
                            tooltipText="Higher values produce more consistent tone."
                        />
                    </div>
                </div>
            )}
        </div>

                {/* Backend Info Toggle */}
                <div className="px-6 py-2 border-b border-gray-200 bg-white">
                         <button
                                onClick={() => setIsBackendOpen(!isBackendOpen)}
                                className="flex items-center justify-between w-full text-xs font-bold text-gray-500 uppercase tracking-wide hover:text-brand-black transition-colors py-2"
                        >
                                <div className="flex items-center gap-2">
                                        <Server size={14} />
                                        <span>Backend</span>
                                </div>
                                {isBackendOpen ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                        </button>

                        {isBackendOpen && (
                            <div className="pt-2 pb-3 animate-fade-in-up">
                                <div className="text-xs text-gray-600 space-y-1">
                                    <div className="flex items-center justify-between gap-4">
                                        <span className="text-gray-500">API base</span>
                                        <span className="font-mono text-[11px] text-gray-700 truncate max-w-[240px]">{apiBaseUrl || '(dev proxy)'}</span>
                                    </div>

                                    {!capabilities ? (
                                        <div className="text-gray-400 text-[11px]">Capabilities unavailable (using defaults)</div>
                                    ) : (
                                        <>
                                            <div className="flex items-center justify-between gap-4">
                                                <span className="text-gray-500">Max upload</span>
                                                <span className="text-gray-700">{formatBytes(capabilities.upload_max_bytes)}</span>
                                            </div>
                                            <div className="flex items-center justify-between gap-4">
                                                <span className="text-gray-500">Duration</span>
                                                <span className="text-gray-700">&gt; {formatSec(capabilities.upload_min_duration_sec)} and &lt; {formatSec(capabilities.upload_max_duration_sec)}</span>
                                            </div>
                                            <div className="flex items-center justify-between gap-4">
                                                <span className="text-gray-500">Content types</span>
                                                <button
                                                    type="button"
                                                    onClick={() => setIsTypesOpen((v) => !v)}
                                                    className="text-gray-700 hover:text-brand-black transition-colors inline-flex items-center gap-1"
                                                >
                                                    <span>{(capabilities.allowed_content_types || []).length}</span>
                                                    {isTypesOpen ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
                                                </button>
                                            </div>

                                            {isTypesOpen && (
                                                <div className="mt-1 rounded-lg border border-gray-200 bg-gray-50 px-2 py-2">
                                                    <div className="text-[11px] text-gray-700 font-mono whitespace-pre-wrap break-words">
                                                        {(capabilities.allowed_content_types || []).join('\n') || '--'}
                                                    </div>
                                                </div>
                                            )}

                                            <div className="flex items-center justify-between gap-4">
                                                <span className="text-gray-500">Async</span>
                                                <span className="text-gray-700">{capabilities.async_mode ? 'yes' : 'no'}</span>
                                            </div>
                                        </>
                                    )}
                                </div>
                            </div>
                        )}
                </div>

        {/* Generate Button */}
        <div className="p-6 bg-white">
             <button 
                onClick={onGenerate}
                disabled={isDisabled || !config.voiceId || appState === 'processing'}
                className={`
                    w-full h-12 rounded-xl flex items-center justify-center gap-2 font-bold text-base transition-all duration-300
                    ${isDisabled || !config.voiceId 
                        ? 'bg-gray-100 text-gray-400 cursor-not-allowed' 
                        : appState === 'processing'
                            ? 'bg-brand-black text-white opacity-90 cursor-wait scale-[0.98]'
                            : 'bg-brand-black text-white hover:bg-gray-800 shadow-lg hover:shadow-xl transform hover:-translate-y-0.5 active:scale-95'
                    }
                `}
             >
                {appState === 'processing' ? (
                    <div className="flex items-center gap-2">
                        <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                        <span>Processing...</span>
                    </div>
                ) : (
                    <>
                        <Wand2 size={18} fill="currentColor" />
                        Generate Speech
                    </>
                )}
             </button>
        </div>
      </div>
    </div>
  );
};