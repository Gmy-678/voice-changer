import React, { useState } from 'react';
import { Info } from 'lucide-react';

interface SliderProps {
  label: string;
  value: number;
  onChange: (val: number) => void;
  min: number;
  max: number;
  leftLabel: string;
  rightLabel: string;
  tooltipText: string;
  recommendedText?: string;
}

export const Slider: React.FC<SliderProps> = ({ 
  label, value, onChange, min, max, leftLabel, rightLabel, tooltipText, recommendedText 
}) => {
  const [showTooltip, setShowTooltip] = useState(false);

  return (
    <div className="mb-4 group">
      <div className="flex justify-between items-center mb-1.5">
        <div className="flex items-center gap-1.5">
          <label className="text-xs font-semibold text-gray-700">{label}</label>
          <div 
            className="relative"
            onMouseEnter={() => setShowTooltip(true)}
            onMouseLeave={() => setShowTooltip(false)}
          >
            <Info className="w-3 h-3 text-gray-300 hover:text-gray-500 cursor-help transition-colors" />
            {showTooltip && (
              <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-56 bg-brand-black text-white text-[10px] p-2 rounded shadow-xl z-50 pointer-events-none leading-relaxed">
                {tooltipText}
                <div className="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-brand-black"></div>
              </div>
            )}
          </div>
        </div>
        <span className="text-[10px] font-bold text-gray-500 bg-gray-100 px-1.5 rounded">{value}</span>
      </div>
      
      <div className="relative h-3 flex items-center">
        {/* Track Background */}
        <div className="absolute w-full h-1 bg-gray-100 rounded-full overflow-hidden">
           <div 
             className="h-full bg-brand-black/10 group-hover:bg-brand-orange/20 transition-colors"
             style={{ width: `${((value - min) / (max - min)) * 100}%` }}
           />
        </div>
        
        <input 
          type="range" 
          min={min} 
          max={max} 
          value={value} 
          onChange={(e) => onChange(Number(e.target.value))}
          className="absolute w-full h-full opacity-0 cursor-pointer z-10"
        />

        {/* Custom Thumb (Visual Only) */}
        <div 
            className="pointer-events-none absolute h-3 w-3 bg-white border border-brand-black rounded-full shadow-sm group-hover:scale-110 group-hover:border-brand-orange transition-all duration-200 ease-out"
            style={{ left: `calc(${((value - min) / (max - min)) * 100}% - 6px)` }}
        />
      </div>

      <div className="flex justify-between items-start mt-0.5">
        <span className="text-[9px] text-gray-400 font-medium">{leftLabel}</span>
        <span className="text-[9px] text-gray-400 font-medium">{rightLabel}</span>
      </div>
    </div>
  );
};