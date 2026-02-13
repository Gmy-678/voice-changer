/** @format */

import React, { useEffect, useMemo, useRef, useState } from "react";
import {
  Play,
  Pause,
  RefreshCw,
  ThumbsUp,
  ThumbsDown,
  Download,
} from "lucide-react";

interface AudioPlayerProps {
  src: string | null;
  label?: string;
  onRegenerate?: () => void;
  isResult?: boolean;
  onReplace?: () => void;
  mediaType?: "audio" | "video";
}

function inferIsVideo(src: string, label?: string): boolean {
  const s = String(src || "").toLowerCase();
  const l = String(label || "").toLowerCase();
  return s.includes(".mp4") || l.endsWith(".mp4");
}

export const AudioPlayer: React.FC<AudioPlayerProps> = ({
  src,
  label,
  onRegenerate,
  isResult = false,
  onReplace,
  mediaType,
}) => {
  const [isPlaying, setIsPlaying] = useState(false);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [durationSec, setDurationSec] = useState<number>(0);
  const [currentSec, setCurrentSec] = useState<number>(0);
  const [liked, setLiked] = useState<boolean | null>(null);
  const [showRegeneratePrompt, setShowRegeneratePrompt] = useState(false);

  const isVideo = useMemo(() => {
    if (!src) return false;
    if (mediaType === "video") return true;
    if (mediaType === "audio") return false;
    return inferIsVideo(src, label);
  }, [src, label, mediaType]);

  useEffect(() => {
    setIsPlaying(false);
    setDurationSec(0);
    setCurrentSec(0);
    setLiked(null);
    setShowRegeneratePrompt(false);
  }, [src]);

  const progressPct = useMemo(() => {
    if (!durationSec || durationSec <= 0) return 0;
    return Math.min(100, Math.max(0, (currentSec / durationSec) * 100));
  }, [currentSec, durationSec]);

  const fmt = (sec: number): string => {
    const s = Math.max(0, Math.floor(sec));
    const m = Math.floor(s / 60);
    const r = s % 60;
    return `${m.toString().padStart(2, "0")}:${r.toString().padStart(2, "0")}`;
  };

  const handleLike = () => {
    setLiked(true);
    setShowRegeneratePrompt(false);
  };

  const handleDislike = () => {
    const newLikedState = liked === false ? null : false;
    setLiked(newLikedState);
    if (newLikedState === false) {
      setShowRegeneratePrompt(true);
    } else {
      setShowRegeneratePrompt(false);
    }
  };

  if (!src) return null;

  if (isVideo) {
    return (
      <div className="flex flex-col w-full">
        <div
          className={`${isResult ? "py-4 px-4" : "p-4 bg-white rounded-2xl border border-gray-100 shadow-sm"}`}
        >
          {label && !isResult && (
            <div
              className="mb-3 text-sm font-medium text-gray-700 truncate"
              title={label}
            >
              {label}
            </div>
          )}
          <video
            src={src}
            controls
            preload="metadata"
            className="w-full rounded-2xl border border-gray-100 bg-black/5"
          />

          <div className="mt-3 flex items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              {onReplace && (
                <button
                  onClick={onReplace}
                  className="p-2 text-gray-400 hover:text-brand-orange hover:bg-brand-orangeLight/20 rounded-lg transition-colors"
                  title="Replace file"
                >
                  <RefreshCw size={16} />
                </button>
              )}
              {onRegenerate && isResult && (
                <button
                  onClick={onRegenerate}
                  className="p-2 text-gray-400 hover:text-brand-black hover:bg-gray-50 rounded-lg transition-colors"
                  title="Regenerate"
                >
                  <RefreshCw size={16} />
                </button>
              )}
            </div>

            {isResult && (
              <div className="flex items-center gap-2">
                <a
                  className="p-2 rounded-lg text-gray-400 hover:text-brand-black hover:bg-gray-50 transition-colors"
                  title="Download result"
                  href={src}
                  target="_blank"
                  rel="noreferrer"
                  download
                >
                  <Download size={20} />
                </a>
                <div className="flex gap-1">
                  <button
                    onClick={handleLike}
                    className={`p-2 rounded-lg transition-colors ${liked === true ? "text-brand-orange bg-brand-orangeLight/20" : "text-gray-400 hover:text-gray-600 hover:bg-gray-50"}`}
                  >
                    <ThumbsUp size={20} />
                  </button>
                  <button
                    onClick={handleDislike}
                    className={`p-2 rounded-lg transition-colors ${liked === false ? "text-brand-orange bg-brand-orangeLight/20" : "text-gray-400 hover:text-gray-600 hover:bg-gray-50"}`}
                  >
                    <ThumbsDown size={20} />
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>

        {showRegeneratePrompt && isResult && (
          <div className="mt-3 bg-brand-orangeLight/30 rounded-xl p-3 flex items-center justify-between animate-fade-in-up border border-brand-orange/10 mx-1">
            <span className="text-xs font-semibold text-brand-orange uppercase tracking-wide ml-2">
              Not satisfied?
            </span>
            <button
              onClick={onRegenerate}
              className="flex items-center gap-1.5 text-xs font-bold text-white bg-brand-orange hover:bg-orange-600 px-3 py-1.5 rounded-lg transition-colors shadow-sm"
            >
              <RefreshCw size={12} />
              Regenerate
            </button>
          </div>
        )}
      </div>
    );
  }

  const togglePlay = async () => {
    const a = audioRef.current;
    if (!a) return;
    if (a.paused) {
      try {
        await a.play();
      } catch {
        // ignore autoplay restrictions
      }
    } else {
      a.pause();
    }
  };

  const seekToPct = (percentage: number) => {
    const a = audioRef.current;
    if (!a || !durationSec) return;
    const p = Math.min(100, Math.max(0, percentage));
    a.currentTime = (p / 100) * durationSec;
  };

  return (
    <div className="flex flex-col w-full">
      <audio
        ref={audioRef}
        src={src}
        preload="metadata"
        onPlay={() => setIsPlaying(true)}
        onPause={() => setIsPlaying(false)}
        onEnded={() => {
          setIsPlaying(false);
          setCurrentSec(0);
        }}
        onLoadedMetadata={(e) => {
          const a = e.currentTarget;
          const d = Number.isFinite(a.duration) ? a.duration : 0;
          setDurationSec(d);
          setCurrentSec(Number.isFinite(a.currentTime) ? a.currentTime : 0);
        }}
        onTimeUpdate={(e) => {
          const a = e.currentTarget;
          setCurrentSec(Number.isFinite(a.currentTime) ? a.currentTime : 0);
        }}
      />
      <div
        className={`w-full flex items-center gap-6 ${isResult ? "py-4 px-4" : "p-4 bg-white rounded-2xl border border-[#e1e1e1] shadow-[0px_4px_20px_0px_rgba(0,0,0,0.05)]"}`}
      >
        {/* 1. Playback Controls Cluster (Left) */}
        <div className="flex items-center gap-5 flex-shrink-0">
          <button
            onClick={togglePlay}
            className="flex items-center justify-center rounded-full bg-[#36353a] text-white hover:opacity-90 transition-transform active:scale-95 shadow-md w-12 h-12"
          >
            {isPlaying ? (
              <Pause size={20} fill="currentColor" className="stroke-none" />
            ) : (
              <Play
                size={20}
                fill="currentColor"
                className="stroke-none ml-1"
              />
            )}
          </button>
        </div>

        {/* 2. Progress Section (Center) */}
        <div className="flex items-center gap-3 flex-1">
          {/* Current Time */}
          <span className="font-medium text-gray-900 tabular-nums text-sm w-10 text-right">
            {fmt(currentSec)}
          </span>

          {/* Progress Bar */}
          <div className="flex-1 h-1.5 bg-gray-100 rounded-full overflow-hidden relative group cursor-pointer">
            <div
              className="absolute inset-0 w-full h-full bg-transparent z-10"
              onClick={(e) => {
                const rect = e.currentTarget.getBoundingClientRect();
                const x = e.clientX - rect.left;
                const percentage = (x / rect.width) * 100;
                seekToPct(percentage);
              }}
            />
            <div
              className="h-full bg-[#fe655d] rounded-full transition-all duration-75 ease-linear"
              style={{ width: `${progressPct}%` }}
            />
          </div>

          {/* Total Time */}
          <span className="font-medium text-gray-400 tabular-nums text-sm w-10">
            {durationSec ? fmt(durationSec) : "--:--"}
          </span>

          {/* Replace/Update Button */}
          {onReplace && (
            <button
              onClick={onReplace}
              className="p-1.5 text-gray-400 hover:text-brand-orange hover:bg-brand-orangeLight/20 rounded-lg transition-colors ml-1"
              title="Replace file"
            >
              <RefreshCw size={16} />
            </button>
          )}
        </div>

        {/* 3. Actions Section (Right) */}
        {isResult && (
          <div className="flex items-center gap-2 pl-4 border-l border-gray-100 ml-2">
            <a
              className="p-2 rounded-lg text-gray-400 hover:text-brand-black hover:bg-gray-50 transition-colors"
              title="Download result"
              href={src}
              target="_blank"
              rel="noreferrer"
              download
            >
              <Download size={20} />
            </a>
            <div className="flex gap-1">
              <button
                onClick={handleLike}
                className={`p-2 rounded-lg transition-colors ${liked === true ? "text-brand-orange bg-brand-orangeLight/20" : "text-gray-400 hover:text-gray-600 hover:bg-gray-50"}`}
              >
                <ThumbsUp size={20} />
              </button>
              <button
                onClick={handleDislike}
                className={`p-2 rounded-lg transition-colors ${liked === false ? "text-brand-orange bg-brand-orangeLight/20" : "text-gray-400 hover:text-gray-600 hover:bg-gray-50"}`}
              >
                <ThumbsDown size={20} />
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Regenerate Prompt Bar */}
      {showRegeneratePrompt && isResult && (
        <div className="mt-3 bg-brand-orangeLight/30 rounded-xl p-3 flex items-center justify-between animate-fade-in-up border border-brand-orange/10 mx-1">
          <span className="text-xs font-semibold text-brand-orange uppercase tracking-wide ml-2">
            Not satisfied?
          </span>
          <button
            onClick={onRegenerate}
            className="flex items-center gap-1.5 text-xs font-bold text-white bg-brand-orange hover:bg-orange-600 px-3 py-1.5 rounded-lg transition-colors shadow-sm"
          >
            <RefreshCw size={12} />
            Regenerate
          </button>
        </div>
      )}
    </div>
  );
};
