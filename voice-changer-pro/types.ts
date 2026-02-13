
export enum Language {
  SAME = "Same as input",
  CHINESE = "Chinese",
  ENGLISH = "English",
  JAPANESE = "Japanese"
}

export interface Voice {
  id: string;
  name: string;
  role: string;
  description: string;
  nationality: string; // Emoji flag
  isVerified: boolean;
  isFavorited?: boolean;
  category: 'public' | 'private' | 'generated' | 'saved'; // Expanded categories
  previewUrl: string; // Placeholder for preview audio
  imageUrl: string;
}

export interface ProcessingConfig {
  voiceId: string | null;
  similarity: number;
  stability: number;
  language: Language;
  removeNoise: boolean;
}

export interface FileData {
  file: File;
  name: string;
  size: number;
  type: string;
  url: string;
  durationSec?: number;
}

export interface HistoryItem {
  id: string;
  name: string;
  url: string;
  duration: string;
  date: string;
}

export type AppState = 'idle' | 'uploading' | 'processing' | 'complete';

export type VoiceLibraryTab = 'local' | 'featured' | 'all_voices' | 'my_voices' | 'saved';

export type VoiceLibraryFilters = {
  language?: 'en' | 'zh' | 'ja' | '';
  age?: 'young' | 'middle_age' | 'old' | '';
  gender?: 'male' | 'female' | '';
  scene?: string[];
  emotion?: string[];
};

export type VoiceLibraryQuery = {
  tab: VoiceLibraryTab;
  keyword: string;
  filters: VoiceLibraryFilters;
};
