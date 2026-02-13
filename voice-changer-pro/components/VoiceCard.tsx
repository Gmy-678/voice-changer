import React from 'react';
import { Play, CheckCircle2, Bookmark, ArrowRight } from 'lucide-react';
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
        relative flex items-center gap-4 py-3 px-4 cursor-pointer transition-all duration-300 rounded-[16px] mb-2 group
        bg-white hover:bg-gray-50
      `}
    >
      {/* Left: Avatar with Play Overlay */}
      <div className="flex-shrink-0 relative group/avatar">
          <div className="w-12 h-12 rounded-full overflow-hidden bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white text-lg font-bold shadow-sm">
             {voice.imageUrl ? (
                <img src={voice.imageUrl} alt={voice.name} className="w-full h-full object-cover" />
             ) : (
                <span>{voice.name.charAt(0)}</span>
             )}
          </div>
          
          {/* Play Overlay */}
          <button 
            className="absolute inset-0 bg-black/40 rounded-full flex items-center justify-center opacity-0 group-hover/avatar:opacity-100 transition-opacity"
            onClick={(e) => {
              e.stopPropagation();
              onPreview?.(voice);
            }}
          >
            <Play size={20} fill="white" className="text-white ml-0.5" />
          </button>
      </div>

      {/* Middle: Info */}
      <div className="flex-1 min-w-0 flex flex-col justify-center gap-1.5">
        <div className="flex items-center gap-2">
           <h4 className="font-bold text-base text-[#36353a] truncate leading-tight">{voice.name}</h4>
           {voice.isVerified && (
             <CheckCircle2 size={14} className="text-blue-500 fill-white flex-shrink-0" />
           )}
        </div>
        
        {/* Tags */}
        <div className="flex items-center gap-2 overflow-hidden flex-wrap h-5">
            {voice.role && (
                <span className="px-2 py-0.5 bg-[#f2f4f7] text-[#5d5d5d] text-[11px] rounded-[4px] font-medium truncate">
                    {voice.role}
                </span>
            )}
            {voice.nationality && (
                 <span className="px-2 py-0.5 bg-[#f2f4f7] text-[#5d5d5d] text-[11px] rounded-[4px] font-medium truncate">
                    {voice.nationality}
                </span>
            )}
             <span className="px-2 py-0.5 bg-[#f2f4f7] text-[#5d5d5d] text-[11px] rounded-[4px] font-medium truncate">
                Label
            </span>
        </div>
      </div>

      {/* Right: Actions */}
      <div className="flex items-center gap-2">
         <button
          type="button"
          className={`p-2 rounded-full transition-colors ${voice.isFavorited ? 'text-[#fe655d]' : 'text-gray-300 hover:text-[#36353a]'}`}
          onClick={(e) => {
            e.stopPropagation();
            if (!onToggleFavorite) return;
            onToggleFavorite(voice.id, !Boolean(voice.isFavorited));
          }}
        >
          <Bookmark size={18} fill={voice.isFavorited ? 'currentColor' : 'none'} />
         </button>
         
         {/* Arrow Icon for selection indication or detail view */}
         <div className="w-8 h-8 rounded-full border border-[#e1e1e1] flex items-center justify-center text-[#b3b3b3] group-hover:bg-[#36353a] group-hover:text-white group-hover:border-[#36353a] transition-all">
             <ArrowRight size={14} />
         </div>
      </div>
    </div>
  );
};