/** @format */

import React, { useState, useRef } from "react";
import { Mic, ArrowUp, Plus, Play, Download } from "lucide-react";
import { Toggle } from "./ui/Toggle";
import { AudioPlayer } from "./AudioPlayer";
import { FileData, HistoryItem } from "../types";
import { getMediaDurationSec } from "../backend";

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
  file,
  setFile,
  removeNoise,
  setRemoveNoise,
  resultAudio,
  onGenerate,
  isProcessing,
  history,
  onDeleteHistory,
  onPlayHistory,
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
    <div className="h-full flex flex-col overflow-y-auto no-scrollbar">
      {/* Hidden Input */}
      <input
        type="file"
        ref={fileInputRef}
        className="hidden"
        accept="audio/*,video/*"
        onChange={(e) =>
          e.target.files?.[0] && handleFileSelection(e.target.files[0])
        }
      />

      {/* Step Header */}
      <div className="mb-6">
        <p className="text-[18px] text-[#36353A] font-medium leading-[1.2] font-['Inter'] text-center">
          Upload Your Audio
        </p>
      </div>

      <div className="flex-1 flex flex-col gap-6 max-w-6xl mx-auto w-full rounded-[24px] border border-[#e1e1e1] bg-[#fafafa] p-5">
        {/* Upload & Record Area */}
        {!file ? (
          <div className="flex flex-col flex-1 justify-start animate-fade-in-up">
            <div className="flex flex-col items-stretch justify-center w-full gap-[10px] h-auto">
              {/* Upload Section */}
              <div
                className={`flex-1 flex flex-col items-center justify-center border rounded-[24px] p-8 cursor-pointer transition-all duration-300 group hover:-translate-y-1 bg-white min-h-[320px] max-w-md shadow-[0_0_16px_0_rgba(0,0,0,0.08)] ${
                  isDragging
                    ? "border-[#fe655d] bg-[#fe655d]/5 border-dashed"
                    : "border-[#EBEBEB] hover:border-[#fe655d]/30"
                }`}
                onClick={() => fileInputRef.current?.click()}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
              >
                {/* Icons Area */}
                <div className="relative flex items-center justify-center gap-[10px] mb-6 transform group-hover:scale-105 transition-transform duration-300">
                  <div className="flex w-[63.202px] h-[62.634px] rotate-[-3.037deg] p-[16.56px] items-center justify-center gap-[10px] rounded-[14.72px] border-[1px] border-[#e1e1e1] bg-white">
                    <svg
                      width="20"
                      height="24"
                      viewBox="0 0 24 28"
                      fill="none"
                      xmlns="http://www.w3.org/2000/svg"
                      className="text-[#36353a]"
                    >
                      <path
                        d="M1.91396 13.8998L1.39406 4.10033C1.35959 3.45059 1.58466 2.81409 2.01975 2.33086C2.45485 1.84763 3.06433 1.55726 3.71412 1.52362L13.5143 1.01627M13.5143 1.01627C13.9024 0.995221 14.291 1.05124 14.6576 1.1811C15.0241 1.31097 15.3615 1.51209 15.6501 1.77288L20.2786 5.94041C20.5681 6.20016 20.8034 6.5146 20.9709 6.86559C21.1384 7.21658 21.2347 7.59716 21.2543 7.98538M13.5143 1.01627L13.8392 7.14095C13.8565 7.46582 14.0021 7.77071 14.244 7.98854C14.4859 8.20636 14.8043 8.31929 15.1292 8.30247L21.2543 7.98538M21.2543 7.98538L22.0342 22.6846C22.0687 23.3344 21.8436 23.9709 21.4085 24.4541C20.9734 24.9373 20.3639 25.2277 19.7141 25.2614M9.6438 20.6765L13.2452 18.3344C13.3614 18.2569 13.4961 18.2119 13.6356 18.2038C13.775 18.1958 13.9141 18.2251 14.0386 18.2888C14.163 18.3524 14.2682 18.4481 14.3434 18.5659C14.4186 18.6838 14.461 18.8195 14.4662 18.9591L14.7719 24.7212C14.7777 24.8593 14.7474 24.9965 14.6841 25.1193C14.6208 25.2421 14.5266 25.3463 14.4108 25.4216C14.295 25.497 14.1616 25.541 14.0236 25.5492C13.8856 25.5574 13.7478 25.5296 13.6237 25.4685L9.79418 23.5111M2.17391 18.7996L8.29901 18.4825C8.97557 18.4475 9.55313 18.9675 9.58902 19.644L9.84897 24.5438C9.88486 25.2203 9.3655 25.7971 8.68894 25.8321L2.56384 26.1492C1.88728 26.1842 1.30972 25.6642 1.27383 24.9877L1.01388 20.0879C0.977986 19.4114 1.49735 18.8346 2.17391 18.7996Z"
                        stroke="#36353A"
                        strokeWidth="2.02399"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      />
                    </svg>
                  </div>
                  <div className="flex w-[63.202px] h-[62.634px] rotate-[3.037deg] p-[16.56px] items-center justify-center gap-[10px] rounded-[14.72px] border-[1px] border-[#e1e1e1] bg-white">
                    <svg
                      width="22"
                      height="28"
                      viewBox="0 0 22 28"
                      fill="none"
                      xmlns="http://www.w3.org/2000/svg"
                    >
                      <path
                        d="M1.01233 13.1372L1.53059 3.3376C1.56495 2.68785 1.85603 2.07811 2.3398 1.64253C2.82357 1.20695 3.46039 0.981197 4.11018 1.01494L13.9103 1.5239M13.9103 1.5239C14.2985 1.54311 14.679 1.63901 15.0299 1.80607C15.3807 1.97313 15.6949 2.20804 15.9544 2.49725L20.1173 7.12063C20.3778 7.4089 20.5786 7.74595 20.708 8.11233C20.8375 8.47872 20.8931 8.86718 20.8716 9.25531M13.9103 1.5239L13.5863 7.64863C13.5692 7.97351 13.6817 8.29178 13.8993 8.53343C14.1169 8.77509 14.4217 8.92033 14.7466 8.9372L20.8716 9.25531M20.8716 9.25531L20.0942 23.9547C20.0599 24.6044 19.7688 25.2142 19.285 25.6498C18.8012 26.0853 18.1644 26.3111 17.5146 26.2773"
                        stroke="#36353A"
                        strokeWidth="2.02399"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      />
                      <path
                        d="M2.02365 17.2147L1.90489 19.4604M5.12204 14.373L4.68655 22.6074M8.18083 12.28L7.46822 25.7544M10.9229 16.1756L10.6458 21.4156M13.9817 14.0825L13.467 23.8141M16.7238 17.9781L16.605 20.2238"
                        stroke="#36353A"
                        strokeWidth="2.02399"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      />
                    </svg>
                  </div>

                  {/* Badge (Red Arrow) */}
                  <div className="absolute -bottom-4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[22px] h-[22px] bg-[#fe655d] rounded-full flex items-center justify-center shadow-sm">
                    <ArrowUp size={12} color="white" strokeWidth={4} />
                  </div>
                </div>

                {/* Text */}
                <h3 className="text-[16px] font-medium text-[#36353A] mb-4 text-center leading-normal font-['Inter']">
                  Click to Upload or drag to drop
                </h3>
              </div>

              {/* Vertical Divider */}
              <div className="flex flex-col items-center justify-center gap-[10px] px-2">
                <span className="text-[#B3B3B3] text-[16px] font-normal tracking-[-0.16px] leading-[1.4] text-center font-['Inter'] py-1">
                  or
                </span>
              </div>

              {/* Record Section */}
              <div className="flex-1 flex flex-col items-center justify-center border border-[#EBEBEB] rounded-[24px] p-8 cursor-not-allowed bg-white min-h-[320px] max-w-md shadow-[0_0_16px_0_rgba(0,0,0,0.08)] group">
                {/* Icon Area */}
                <div className="relative mb-6 transform group-hover:scale-105 transition-transform duration-300">
                  <div className="flex w-[63.202px] h-[62.634px] p-[10px] items-center justify-center gap-[10px] rounded-[14.72px] border-[1px] border-[#e1e1e1] bg-white">
                    <svg
                      width="36"
                      height="36"
                      viewBox="0 0 36 36"
                      fill="none"
                      xmlns="http://www.w3.org/2000/svg"
                    >
                      <path
                        d="M8.27535 32.476H21.0778C21.3737 32.476 21.6267 32.3748 21.8367 32.1725C22.0467 31.9702 22.1518 31.7265 22.1518 31.4413C22.1518 31.147 22.0467 30.8986 21.8367 30.6963C21.6267 30.4939 21.3737 30.3927 21.0778 30.3927H15.7649V27.1782C16.7673 27.1047 17.7315 26.9069 18.6576 26.585C18.4189 26.3367 18.1898 26.0722 17.9702 25.7918C17.7506 25.5112 17.5549 25.2192 17.3831 24.9157C16.5716 25.1549 15.6694 25.2744 14.6765 25.2744C13.044 25.2744 11.6215 24.9502 10.4091 24.3018C9.19663 23.6533 8.25864 22.7405 7.59513 21.5632C6.93163 20.3859 6.59987 19.0155 6.59987 17.452V14.7341C6.59987 14.449 6.49486 14.2052 6.28483 14.0029C6.07479 13.8006 5.81702 13.6994 5.51153 13.6994C5.21557 13.6994 4.96258 13.8006 4.75255 14.0029C4.54252 14.2052 4.4375 14.449 4.4375 14.7341V17.5348C4.4375 19.3374 4.82176 20.9378 5.59029 22.3358C6.35882 23.7338 7.43046 24.8536 8.80521 25.6951C10.18 26.5367 11.7791 27.0311 13.6025 27.1782V30.3927H8.27535C7.97939 30.3927 7.7264 30.4939 7.51637 30.6963C7.30635 30.8986 7.20133 31.147 7.20133 31.4413C7.20133 31.7265 7.30635 31.9702 7.51637 32.1725C7.7264 32.3748 7.97939 32.476 8.27535 32.476ZM14.6765 22.4461C14.9534 22.4461 15.2231 22.4278 15.4856 22.391C15.7482 22.3542 16.0036 22.2944 16.2518 22.2116C16.1754 21.853 16.1253 21.4897 16.1014 21.1217C16.0775 20.7538 16.0752 20.386 16.0943 20.0181C15.9033 20.1376 15.6861 20.2296 15.4427 20.294C15.1992 20.3584 14.9439 20.3906 14.6765 20.3906C13.76 20.3906 13.0225 20.0871 12.464 19.48C11.9055 18.873 11.6263 18.059 11.6263 17.0381V8.36025C11.6263 7.33934 11.9055 6.52536 12.464 5.91833C13.0225 5.3113 13.76 5.00778 14.6765 5.00778C15.593 5.00778 16.3305 5.3113 16.889 5.91833C17.4475 6.52536 17.7268 7.33934 17.7268 8.36025V15.5343C18.0132 15.0836 18.3354 14.6628 18.6934 14.2719C19.0514 13.881 19.45 13.5292 19.8891 13.2165V8.36025C19.8891 7.30255 19.6696 6.36671 19.2304 5.55273C18.7913 4.73876 18.1802 4.10183 17.3974 3.64196C16.6146 3.18208 15.7076 2.95215 14.6765 2.95215C13.6455 2.95215 12.7409 3.18208 11.9628 3.64196C11.1848 4.10183 10.5738 4.73876 10.1298 5.55273C9.6859 6.36671 9.46393 7.30255 9.46393 8.36025V17.0381C9.46393 18.0958 9.6859 19.0317 10.1298 19.8456C10.5738 20.6596 11.1848 21.2965 11.9628 21.7563C12.7409 22.2162 13.6455 22.4461 14.6765 22.4461Z"
                        fill="#36353A"
                      />
                      <path
                        fillRule="evenodd"
                        clipRule="evenodd"
                        d="M28.6801 28.9219C27.6892 29.3526 26.6393 29.568 25.5302 29.568C24.4102 29.568 23.3548 29.3554 22.364 28.93C21.3733 28.5046 20.5011 27.915 19.7472 27.1611C18.9934 26.4073 18.4011 25.535 17.9704 24.5443C17.5396 23.5536 17.3242 22.4929 17.3242 21.3622C17.3242 20.2314 17.5396 19.1734 17.9704 18.188C18.4011 17.2026 18.9934 16.3304 19.7472 15.5712C20.5011 14.812 21.3733 14.2197 22.364 13.7943C23.3548 13.3689 24.4102 13.1562 25.5302 13.1562C26.6609 13.1562 27.7216 13.3689 28.7123 13.7943C29.703 14.2197 30.5753 14.8093 31.3291 15.5631C32.0829 16.3169 32.6726 17.1892 33.098 18.18C33.5233 19.1707 33.736 20.2314 33.736 21.3622C33.736 22.4821 33.5206 23.5374 33.0899 24.5281C32.6592 25.5189 32.0642 26.3913 31.3049 27.1451C30.5457 27.8989 29.6708 28.4912 28.6801 28.9219ZM24.7951 26.2242C24.9728 26.4074 25.2125 26.499 25.5139 26.499C25.8155 26.499 26.0552 26.4074 26.2328 26.2242C26.4105 26.0412 26.4993 25.8043 26.4993 25.5135V22.3475H29.6654C29.9562 22.3475 30.1931 22.2587 30.3762 22.0811C30.5592 21.9033 30.6508 21.6637 30.6508 21.3622C30.6508 21.0606 30.5592 20.821 30.3762 20.6433C30.1931 20.4657 29.9562 20.3768 29.6654 20.3768H26.4993V17.2108C26.4993 16.92 26.4105 16.6831 26.2328 16.5C26.0552 16.3169 25.8155 16.2254 25.5139 16.2254C25.2125 16.2254 24.9728 16.3169 24.7951 16.5C24.6174 16.6831 24.5286 16.92 24.5286 17.2108V20.3768H21.3626C21.0719 20.3768 20.8349 20.4657 20.6519 20.6433C20.4687 20.821 20.3771 21.0606 20.3771 21.3622C20.3771 21.6637 20.4687 21.9033 20.6519 22.0811C20.8349 22.2587 21.0719 22.3475 21.3626 22.3475H24.5286V25.5135C24.5286 25.8043 24.6174 26.0412 24.7951 26.2242Z"
                        fill="#34C759"
                      />
                    </svg>
                  </div>
                </div>
                {/* Text */}
                <h3 className="text-[16px] font-medium text-[#36353A] mb-4 text-center leading-normal font-['Inter']">
                  Record Audio
                </h3>
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
                mediaType={file.type?.startsWith("video/") ? "video" : "audio"}
                onReplace={() => {
                  if (fileInputRef.current) {
                    fileInputRef.current.value = "";
                    fileInputRef.current.click();
                  }
                }}
              />
            </div>

            <div className="flex justify-between items-center px-4 py-2 bg-gray-50 rounded-2xl border border-[#e1e1e1]">
              <span className="text-sm font-medium text-[#b3b3b3]">
                Processing Options
              </span>
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
          <div className="mt-8 pt-12 border-t border-[#f2f4f7] animate-fade-in-up">
            <div className="flex flex-col items-center justify-center py-8 text-center">
              <div className="flex items-center gap-2 h-20 mb-8">
                <div
                  className="w-2 bg-[#36353a]/20 rounded-full animate-music-bar"
                  style={{ animationDelay: "0s" }}
                ></div>
                <div
                  className="w-2 bg-[#36353a]/40 rounded-full animate-music-bar"
                  style={{ animationDelay: "0.1s" }}
                ></div>
                <div
                  className="w-2 bg-[#fe655d] rounded-full animate-music-bar"
                  style={{ animationDelay: "0.2s" }}
                ></div>
                <div
                  className="w-2 bg-[#36353a]/40 rounded-full animate-music-bar"
                  style={{ animationDelay: "0.3s" }}
                ></div>
                <div
                  className="w-2 bg-[#36353a]/20 rounded-full animate-music-bar"
                  style={{ animationDelay: "0.4s" }}
                ></div>
              </div>
              <h3 className="text-2xl font-bold text-[#36353a] mb-2">
                Generating Speech...
              </h3>
              <p className="text-[#b3b3b3] max-w-xs mx-auto">
                AI is magically transforming your voice.
              </p>
            </div>
          </div>
        )}

        {/* Result Area */}
        {!isProcessing && resultAudio && (
          <div className="mt-12 pt-8 border-t border-[#f2f4f7] animate-fade-in-up">
            <h3 className="text-2xl font-bold mb-6 flex items-center gap-3 text-[#36353a]">
              <div className="w-1.5 h-8 bg-[#fe655d] rounded-full"></div>
              Generated Result
            </h3>

            <div className="bg-white rounded-[24px] p-1.5 shadow-[0_8px_30px_rgb(0,0,0,0.04)] border border-[#e1e1e1] hover:border-[#fe655d]/20 transition-all duration-500 hover:shadow-lg">
              <AudioPlayer
                src={resultAudio}
                isResult={true}
                mediaType={
                  String(resultAudio || "")
                    .toLowerCase()
                    .includes(".mp4")
                    ? "video"
                    : "audio"
                }
                onRegenerate={onGenerate}
              />
            </div>
          </div>
        )}

        {/* History Section */}
        {history.length > 0 && !isProcessing && (
          <div className="mt-12 animate-fade-in-up">
            <h3 className="text-xl font-bold text-[#36353a] mb-4">History</h3>
            <div className="flex flex-col gap-2">
              {history.map((item) => (
                <div
                  key={item.id}
                  className="group flex items-center justify-between p-3 rounded-xl hover:bg-gray-50 transition-colors border border-transparent hover:border-[#e1e1e1]"
                >
                  <div className="flex items-center gap-4 overflow-hidden">
                    <button
                      onClick={() => onPlayHistory(item.url)}
                      className="w-10 h-10 rounded-full bg-gray-100 text-[#b3b3b3] flex items-center justify-center flex-shrink-0 group-hover:bg-[#36353a] group-hover:text-white transition-colors"
                    >
                      <Play size={16} fill="currentColor" className="ml-0.5" />
                    </button>
                    <div className="min-w-0">
                      <h4 className="font-medium text-[#36353a] truncate text-sm">
                        {item.name}
                      </h4>
                      <div className="flex items-center gap-3 text-xs text-[#b3b3b3] mt-0.5">
                        <span>{item.duration}</span>
                        <span>{item.date}</span>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button className="p-2 text-[#b3b3b3] hover:text-[#36353a] hover:bg-white rounded-lg transition-colors">
                      <Download size={16} />
                    </button>
                    <button
                      onClick={() => onDeleteHistory(item.id)}
                      className="px-3 py-1.5 text-xs font-medium text-[#b3b3b3] hover:text-[#fe655d] hover:bg-[#fe655d]/10 rounded-lg transition-colors"
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
