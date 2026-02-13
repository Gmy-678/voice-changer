import React from 'react';
import { Play, CheckCircle2, Bookmark, MoreHorizontal } from 'lucide-react';
import { Voice } from '../types';

interface VoiceCardProps {
  voice: Voice;
  isSelected: boolean;
  onSelect: () => void;
  onToggleFavorite?: (voiceId: string, nextIsFavorite: boolean) => void;
  onPreview?: (voice: Voice) => void;
}

export const VoiceCard: React.FC<VoiceCardProps> = ({ voice, isSelected, onSelect, onToggleFavorite, onPreview }) => {
  return (
    <div 
      onClick={onSelect}
      className={`
        relative flex items-center gap-3 py-2.5 px-4 cursor-pointer transition-all duration-200 border-b border-gray-100 group
        ${isSelected 
          ? 'bg-brand-orangeLight/10' 
          : 'bg-white hover:bg-gray-50'
        }
      `}
    >
      {/* Left: Play Button */}
      <div className="flex-shrink-0">
          <button 
            className="w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center text-brand-black hover:bg-brand-black hover:text-white transition-colors"
            onClick={(e) => {
              e.stopPropagation();
              onPreview?.(voice);
            }}
          >
            <Play size={14} fill="currentColor" className="ml-0.5" />
          </button>
      </div>

      {/* Middle: Info */}
      <div className="flex-1 min-w-0 flex flex-col justify-center">
        <div className="flex items-center gap-1.5 mb-0.5">
           <span className="text-base leading-none">{voice.nationality}</span>
           <h4 className={`font-bold text-sm text-brand-black ${isSelected ? 'text-brand-orange' : ''}`}>{voice.name}</h4>
           <span className="text-gray-400 text-xs font-normal truncate">- {voice.role}</span>
           {voice.isVerified && (
             <CheckCircle2 size={14} className="text-brand-black fill-white" />
           )}
        </div>
        <p className="text-[11px] text-gray-500 line-clamp-1 leading-tight">{voice.description}</p>
      </div>

      {/* Right: Actions */}
      <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
        <button
          type="button"
          className={`p-1.5 rounded-md transition-colors ${voice.isFavorited ? 'text-brand-orange' : 'text-gray-400 hover:text-brand-black'}`}
          onClick={(e) => {
            e.stopPropagation();
            if (!onToggleFavorite) return;
            onToggleFavorite(voice.id, !Boolean(voice.isFavorited));
          }}
          aria-label={voice.isFavorited ? 'Unfavorite voice' : 'Favorite voice'}
          title={voice.isFavorited ? 'Saved' : 'Save'}
        >
          <Bookmark size={16} fill={voice.isFavorited ? 'currentColor' : 'none'} />
         </button>
         <button className="p-1.5 text-gray-400 hover:text-brand-black rounded-md transition-colors">
            <MoreHorizontal size={16} />
         </button>
      </div>
    </div>
  );
};