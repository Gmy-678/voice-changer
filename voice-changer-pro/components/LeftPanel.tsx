import React, { useState, useRef } from 'react';
import { Mic, FileAudio, File, ArrowUp, Plus, Play, Download } from 'lucide-react';
import { Toggle } from './ui/Toggle';
import { AudioPlayer } from './AudioPlayer';
import { FileData, HistoryItem } from '../types';
import { getMediaDurationSec } from '../backend';

interface LeftPanelProps {
  file: FileData | null;
  setFile: React.Dispatch<React.SetStateAction<FileData | null>>;
  removeNoise: boolean;
  setRemoveNoise: (val: boolean) => void;
  resultAudio: string | null;
  onGenerate: () => void;
  isProcessing: boolean;
  history: HistoryItem[];
  onDeleteHistory: (id: string) => void;
  onPlayHistory: (url: string) => void;
}

export const LeftPanel: React.FC<LeftPanelProps> = ({ 
  file, setFile, removeNoise, setRemoveNoise, resultAudio, onGenerate, isProcessing, history, onDeleteHistory, onPlayHistory
}) => {
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const droppedFiles = e.dataTransfer.files;
    if (droppedFiles.length > 0) {
      handleFileSelection(droppedFiles[0]);
    }
  };

  const handleFileSelection = async (selected: File) => {
    const url = URL.createObjectURL(selected);
    setFile({
      file: selected,
      name: selected.name,
      size: selected.size,
      type: selected.type,
      url,
    });

    const durationSec = await getMediaDurationSec(url);
    setFile((prev) => {
      if (!prev || prev.url !== url) return prev;
      return { ...prev, durationSec: durationSec ?? undefined };
    });
  };

  return (
    <div className="h-full flex flex-col p-6 lg:p-12 overflow-y-auto no-scrollbar">
      {/* Hidden Input */}
      <input 
          type="file" 
          ref={fileInputRef} 
          className="hidden" 
          accept="audio/*,video/*"
          onChange={(e) => e.target.files?.[0] && handleFileSelection(e.target.files[0])} 
      />

      {/* Step Header */}
      <div className="mb-8">
        <h2 className="text-4xl font-bold text-brand-black mb-2 flex items-baseline gap-3">
          <span className="text-gray-200 font-bold tracking-tighter text-5xl select-none">01</span>
          Source Input
        </h2>
        <p className="text-gray-500">Upload or record your voice to get started.</p>
      </div>

      <div className="flex-1 flex flex-col gap-6 max-w-6xl mx-auto w-full">
        {/* Upload & Record Area */}
        {!file ? (
          <div className="flex flex-col flex-1 justify-start animate-fade-in-up">
            <div className="flex flex-col md:flex-row items-stretch justify-center w-full gap-8 h-auto">
                
                {/* Upload Section - Reduced Size */}
                <div 
                    className={`flex-1 flex flex-col items-center justify-center border-2 rounded-[2rem] p-8 cursor-pointer transition-all duration-300 group hover:-translate-y-1 hover:shadow-lg bg-white min-h-[320px] max-w-md ${isDragging ? 'border-brand-orange bg-brand-orangeLight/10 border-dashed' : 'border-gray-100 hover:border-brand-orange/30'}`} 
                    onClick={() => fileInputRef.current?.click()}
                    onDragOver={handleDragOver}
                    onDragLeave={handleDragLeave}
                    onDrop={handleDrop}
                >
                    {/* Icons Area */}
                    <div className="relative flex items-center justify-center gap-4 mb-6 transform group-hover:scale-105 transition-transform duration-300">
                         {/* File Icon */}
                         <File size={56} strokeWidth={1.5} className="text-gray-400" />
                         {/* File Audio Icon */}
                         <FileAudio size={56} strokeWidth={1.5} className="text-gray-600" />
                         
                         {/* Badge (Red Arrow) */}
                         <div className="absolute -bottom-2 left-1/2 translate-x-3 bg-[#FF6B6B] rounded-full p-1.5 border-[3px] border-white shadow-sm">
                            <ArrowUp size={16} color="white" strokeWidth={3} />
                         </div>
                    </div>

                    {/* Text */}
                    <h3 className="text-lg font-medium text-brand-black mb-4 text-center leading-snug">Click to Upload or drag to drop</h3>
                    
                    {/* Badges */}
                    <div className="flex flex-wrap justify-center gap-2 opacity-60">
                        {['.MP3', '.MP4', '.WAV', '.MOV'].map(fmt => (
                            <span key={fmt} className="px-2.5 py-1 bg-gray-50 border border-gray-200 rounded-lg text-xs text-gray-500 font-medium tracking-wide">
                                {fmt}
                            </span>
                        ))}
                        <span className="text-xs text-gray-400 self-center ml-1 font-medium">&lt;10MB</span>
                    </div>
                </div>

                {/* Vertical Divider */}
                <div className="hidden md:flex flex-col items-center justify-center gap-3 px-2">
                    <div className="h-16 border-l-2 border-dashed border-gray-200"></div>
                    <span className="text-gray-300 text-sm font-bold tracking-widest uppercase bg-white py-1">OR</span>
                    <div className="h-16 border-l-2 border-dashed border-gray-200"></div>
                </div>
                {/* Horizontal Divider for mobile */}
                <div className="md:hidden w-full flex items-center justify-center gap-4 my-4 opacity-50">
                     <div className="h-px bg-gray-200 w-16 border-t-2 border-dashed border-gray-300"></div>
                     <span className="text-gray-400 text-sm font-medium uppercase">or</span>
                     <div className="h-px bg-gray-200 w-16 border-t-2 border-dashed border-gray-300"></div>
                </div>

                {/* Record Section - Reduced Size */}
                <div className="flex-1 flex flex-col items-center justify-center border-2 border-gray-100 rounded-[2rem] p-8 cursor-not-allowed opacity-70 bg-white min-h-[320px] max-w-md">
                    {/* Icon Area */}
                    <div className="relative mb-6 transform group-hover:scale-105 transition-transform duration-300">
                        <Mic size={72} strokeWidth={1.5} className="text-gray-600" />
                        <div className="absolute top-0 -right-1 bg-[#4ADE80] rounded-full p-1.5 border-[3px] border-white shadow-sm">
                            <Plus size={14} color="white" strokeWidth={4} />
                        </div>
                    </div>
                    {/* Text */}
                    <h3 className="text-lg font-medium text-brand-black mb-2 text-center">Record Audio</h3>
                  <p className="text-xs text-gray-500 text-center max-w-xs">Recording UI is not wired yet — upload a file for now.</p>
                </div>
            </div>
          </div>
        ) : (
          <div className="flex flex-col gap-6 animate-fade-in-up mt-8">
             {/* Audio Player for Input File */}
             <div className="relative group">
                <AudioPlayer 
                    src={file.url} 
                    label={file.name} 
                    isResult={false} 
                mediaType={file.type?.startsWith('video/') ? 'video' : 'audio'}
                    onReplace={() => {
                        if (fileInputRef.current) {
                            fileInputRef.current.value = ''; 
                            fileInputRef.current.click();
                        }
                    }}
                />
             </div>

             <div className="flex justify-between items-center px-4 py-2 bg-gray-50 rounded-2xl border border-gray-100">
                <span className="text-sm font-medium text-gray-500">Processing Options</span>
                <Toggle 
                  checked={removeNoise} 
                  onChange={setRemoveNoise} 
                  label="Remove Background Noise" 
                />
             </div>
          </div>
        )}

        {/* Dynamic Processing Animation */}
        {isProcessing && (
           <div className="mt-8 pt-12 border-t border-gray-50 animate-fade-in-up">
                <div className="flex flex-col items-center justify-center py-8 text-center">
                    <div className="flex items-center gap-2 h-20 mb-8">
                        <div className="w-2 bg-brand-black/20 rounded-full animate-music-bar" style={{animationDelay: '0s'}}></div>
                        <div className="w-2 bg-brand-black/40 rounded-full animate-music-bar" style={{animationDelay: '0.1s'}}></div>
                        <div className="w-2 bg-brand-orange rounded-full animate-music-bar" style={{animationDelay: '0.2s'}}></div>
                        <div className="w-2 bg-brand-black/40 rounded-full animate-music-bar" style={{animationDelay: '0.3s'}}></div>
                        <div className="w-2 bg-brand-black/20 rounded-full animate-music-bar" style={{animationDelay: '0.4s'}}></div>
                    </div>
                    <h3 className="text-2xl font-bold text-gray-900 mb-2">Generating Speech...</h3>
                    <p className="text-gray-500 max-w-xs mx-auto">AI is magically transforming your voice.</p>
                </div>
           </div>
        )}

        {/* Result Area */}
        {!isProcessing && resultAudio && (
          <div className="mt-12 pt-8 border-t border-gray-50 animate-fade-in-up">
            <h3 className="text-2xl font-bold mb-6 flex items-center gap-3 text-brand-black">
                <div className="w-1.5 h-8 bg-brand-orange rounded-full"></div>
                Generated Result
            </h3>
            
            <div className="bg-white rounded-[2rem] p-1.5 shadow-[0_8px_30px_rgb(0,0,0,0.04)] border border-gray-100 hover:border-brand-orange/20 transition-all duration-500 hover:shadow-lg">
                <AudioPlayer 
                    src={resultAudio} 
                    isResult={true} 
                    mediaType={String(resultAudio || '').toLowerCase().includes('.mp4') ? 'video' : 'audio'}
                    onRegenerate={onGenerate} 
                />
            </div>
          </div>
        )}

        {/* History Section */}
        {history.length > 0 && !isProcessing && (
            <div className="mt-12 animate-fade-in-up">
                <h3 className="text-xl font-bold text-gray-900 mb-4">History</h3>
                <div className="flex flex-col gap-2">
                    {history.map((item) => (
                        <div key={item.id} className="group flex items-center justify-between p-3 rounded-xl hover:bg-gray-50 transition-colors border border-transparent hover:border-gray-100">
                            <div className="flex items-center gap-4 overflow-hidden">
                                <button 
                                    onClick={() => onPlayHistory(item.url)}
                                    className="w-10 h-10 rounded-full bg-gray-100 text-gray-600 flex items-center justify-center flex-shrink-0 group-hover:bg-brand-black group-hover:text-white transition-colors"
                                >
                                    <Play size={16} fill="currentColor" className="ml-0.5" />
                                </button>
                                <div className="min-w-0">
                                    <h4 className="font-medium text-gray-900 truncate text-sm">{item.name}</h4>
                                    <div className="flex items-center gap-3 text-xs text-gray-400 mt-0.5">
                                        <span>{item.duration}</span>
                                        <span>{item.date}</span>
                                    </div>
                                </div>
                            </div>
                            <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                <button className="p-2 text-gray-400 hover:text-brand-black hover:bg-white rounded-lg transition-colors">
                                    <Download size={16} />
                                </button>
                                <button 
                                    onClick={() => onDeleteHistory(item.id)}
                                    className="px-3 py-1.5 text-xs font-medium text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                                >
                                    Delete
                                </button>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        )}
      </div>
    </div>
  );
};