/** @format */

import React, { useState, useEffect } from "react";
import { HelpCircle, AlertTriangle } from "lucide-react";
import { LeftPanel } from "./components/LeftPanel";
import { RightPanel } from "./components/RightPanel";
import { UpgradeModal } from "./components/UpgradeModal";
import {
  Voice,
  ProcessingConfig,
  Language,
  FileData,
  AppState,
  HistoryItem,
  VoiceLibraryQuery,
} from "./types";
import {
  API_BASE_URL,
  VOICE_LIBRARY_BASE_URL,
  VOICE_CHANGER_BASE_URL,
  CapabilitiesResponse,
  VoiceChangerPayload,
  getOutputUrl,
  voiceChange,
  getCapabilities,
  listVoices,
  VoiceInfo,
  voiceLibraryFavorites,
  voiceLibraryExplore,
  voiceLibraryCreateMyVoice,
  voiceLibraryMyVoices,
  voiceLibraryRecentUsed,
  voiceLibraryTopFixed,
  VoiceLibraryVoice,
  voiceLibraryUpdateFavorites,
} from "./backend";

const DEFAULT_VOICES: Voice[] = [
  {
    id: "anime_uncle",
    name: "Anime Uncle",
    role: "Overconfident Narrator",
    description: "Lower + punchy + dramatic (funny “uncle” vibe)",
    nationality: "🔥",
    isVerified: true,
    category: "public",
    previewUrl: "",
    imageUrl: "",
  },
  {
    id: "uwu_anime",
    name: "UwU Anime",
    role: "Cute & Sparkly",
    description: "Higher pitch + brighter tone (classic anime “uwu”)",
    nationality: "✨",
    isVerified: true,
    category: "public",
    previewUrl: "",
    imageUrl: "",
  },
  {
    id: "gender_swap",
    name: "Gender Swap",
    role: "Pitch Shift",
    description: "A noticeable pitch shift (for quick voice flips)",
    nationality: "🌀",
    isVerified: true,
    category: "public",
    previewUrl: "",
    imageUrl: "",
  },
  {
    id: "mamba",
    name: "Mamba",
    role: "Hype / Energy",
    description: "Boosted presence + compression-like punch",
    nationality: "🏀",
    isVerified: true,
    category: "public",
    previewUrl: "",
    imageUrl: "",
  },
  {
    id: "nerd_bro",
    name: "Nerd Bro",
    role: "Nasally / Snappy",
    description: "Slightly nasal + tight (meme “nerd bro” tone)",
    nationality: "🤓",
    isVerified: true,
    category: "public",
    previewUrl: "",
    imageUrl: "",
  },
];

type Toast = { kind: "error" | "warn"; message: string };

function formatSec(sec: number): string {
  const s = Math.max(0, Math.floor(sec));
  const m = Math.floor(s / 60);
  const r = s % 60;
  return `${m.toString().padStart(2, "0")}:${r.toString().padStart(2, "0")}`;
}

const App: React.FC = () => {
  // State
  const [file, setFile] = useState<FileData | null>(null);
  const [resultAudio, setResultAudio] = useState<string | null>(null);
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [appState, setAppState] = useState<AppState>("idle");
  const [voices, setVoices] = useState<Voice[]>(DEFAULT_VOICES);
  const [voicesLoading, setVoicesLoading] = useState(false);
  const [recentUsedVoices, setRecentUsedVoices] = useState<Voice[]>([]);
  const [voiceQuery, setVoiceQuery] = useState<VoiceLibraryQuery>({
    tab: "featured",
    keyword: "",
    filters: { language: "en", age: "", gender: "", scene: [], emotion: [] },
  });
  const [durationLimits, setDurationLimits] = useState<{
    min: number;
    max: number;
  }>({ min: 5, max: 300 });
  const [capabilities, setCapabilities] = useState<CapabilitiesResponse | null>(
    null,
  );
  const [limitModalOpen, setLimitModalOpen] = useState(false);
  const [toast, setToast] = useState<Toast | null>(null);
  const [showSilenceWarning, setShowSilenceWarning] = useState(false);

  const previewAudioRef = React.useRef<HTMLAudioElement | null>(null);

  const [config, setConfig] = useState<ProcessingConfig>({
    voiceId: DEFAULT_VOICES[0]?.id ?? null,
    similarity: 5,
    stability: 5,
    language: Language.SAME,
    removeNoise: false,
  });

  function mapLocalVoiceInfo(x: VoiceInfo): Voice {
    return {
      id: x.id,
      name: x.name,
      role: x.role ?? "",
      description: x.description ?? "",
      nationality: "",
      isVerified: x.is_verified ?? true,
      category: (x.category as any) ?? "public",
      previewUrl: "",
      imageUrl: "",
    } as Voice;
  }

  function mapVoiceLibraryVoice(v: VoiceLibraryVoice): Voice {
    const rawPreview = (v.url || v.fallbackurl || "") as any;
    const baseForRelativePreview = VOICE_LIBRARY_BASE_URL || API_BASE_URL;
    const previewUrl = rawPreview
      ? /^https?:\/\//i.test(String(rawPreview))
        ? String(rawPreview)
        : baseForRelativePreview
          ? `${baseForRelativePreview}${String(rawPreview)}`
          : String(rawPreview)
      : "";
    const lang = String(v.language || "").toLowerCase();
    const nationality =
      lang === "zh" ? "🇨🇳" : lang === "ja" ? "🇯🇵" : lang === "en" ? "🇺🇸" : "";
    const category: any =
      v.voice_type === "user" ? (v.is_public ? "public" : "private") : "public";
    return {
      id: v.voice_id,
      name: v.display_name,
      role: "",
      description: (v.voice_description as any) ?? "",
      nationality,
      isVerified: true,
      isFavorited: Boolean((v as any).is_favorited),
      category,
      previewUrl,
      imageUrl: "",
    } as Voice;
  }

  const handlePreviewVoice = (voice: Voice) => {
    const url = String((voice as any)?.previewUrl || "").trim();
    if (!url) {
      setToast({ kind: "warn", message: "该音色没有可用的预览音频" });
      return;
    }
    try {
      if (previewAudioRef.current) {
        previewAudioRef.current.pause();
        previewAudioRef.current = null;
      }
      const a = new Audio(url);
      a.volume = 0.9;
      previewAudioRef.current = a;
      a.play().catch((e) => {
        setToast({
          kind: "error",
          message: `预览播放失败：${String((e as any)?.message || e)}`,
        });
      });
    } catch (e: any) {
      setToast({
        kind: "error",
        message: `预览播放失败：${e?.message || "unknown error"}`,
      });
    }
  };

  async function refreshRecentUsed() {
    try {
      const data = await voiceLibraryRecentUsed(5);
      const mapped = (data.voices || []).map(mapVoiceLibraryVoice);
      console.log("Recent used voices:", mapped);

      setRecentUsedVoices(mapped);
    } catch {
      // ignore
    }
  }

  // Load voices + constraints from backend (if available). Fallback to defaults.
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const caps = await getCapabilities();
        if (cancelled) return;
        setCapabilities(caps);
        const v = (caps.voices || []).map((x) => ({
          id: x.id,
          name: x.name,
          role: x.role ?? "",
          description: x.description ?? "",
          nationality: "",
          isVerified: x.is_verified ?? true,
          category: (x.category as any) ?? "public",
          previewUrl: "",
          imageUrl: "",
        })) as Voice[];

        if (v.length > 0) setVoices(v);
        if (
          typeof caps.upload_min_duration_sec === "number" &&
          typeof caps.upload_max_duration_sec === "number"
        ) {
          setDurationLimits({
            min: caps.upload_min_duration_sec,
            max: caps.upload_max_duration_sec,
          });
        }
      } catch {
        try {
          const v = await listVoices();
          if (cancelled) return;
          const mapped = (v || []).map((x) => ({
            id: x.id,
            name: x.name,
            role: x.role ?? "",
            description: x.description ?? "",
            nationality: "",
            isVerified: x.is_verified ?? true,
            category: (x.category as any) ?? "public",
            previewUrl: "",
            imageUrl: "",
          })) as Voice[];
          if (mapped.length > 0) setVoices(mapped);
        } catch {
          // keep defaults
        }
      }
    })();

    return () => {
      cancelled = true;
    };
  }, []);

  // Load recent-used (best effort; requires X-User-Id header from frontend).
  useEffect(() => {
    refreshRecentUsed();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Load voice-library list based on UI query (filters/search/tab).
  // Keeps previous list if voice-library APIs are unavailable.
  useEffect(() => {
    let cancelled = false;

    setVoicesLoading(true);

    (async () => {
      try {
        const tab = voiceQuery.tab;
        const keyword = (voiceQuery.keyword || "").trim();
        const f = voiceQuery.filters || {};

        // Local tab: show backend-supported voices (so generation matches selection).
        if (tab === "local") {
          try {
            const local = (capabilities?.voices || []).map(mapLocalVoiceInfo);
            if (local.length > 0) {
              if (!cancelled) setVoices(local);
              return;
            }
          } catch {
            // ignore
          }
          const v = await listVoices();
          if (cancelled) return;
          const mapped = (v || []).map(mapLocalVoiceInfo);
          if (mapped.length > 0) setVoices(mapped);
          return;
        }

        const hasFilters = Boolean(
          keyword ||
          f.age ||
          f.gender ||
          (f.scene && f.scene.length > 0) ||
          (f.emotion && f.emotion.length > 0),
        );

        // Featured: top-fixed by language when no keyword/extra filters.
        if (tab === "featured" && !hasFilters) {
          const lang = (f.language || "en") as any;
          const data = await voiceLibraryTopFixed(lang);
          if (cancelled) return;
          const mapped = (data.voices || []).map(mapVoiceLibraryVoice);
          setVoices(mapped);
          return;
        }

        const sceneCsv = (f.scene || []).join(",");
        const emotionCsv = (f.emotion || []).join(",");

        if (tab === "saved") {
          const data = await voiceLibraryFavorites({
            keyword: keyword || undefined,
            language_type: f.language || undefined,
            age: f.age || undefined,
            gender: f.gender || undefined,
            scene: sceneCsv || undefined,
            emotion: emotionCsv || undefined,
            sort: "latest",
            skip: 0,
            limit: 50,
          });
          if (cancelled) return;
          setVoices((data.voices || []).map(mapVoiceLibraryVoice));
          return;
        }

        if (tab === "my_voices") {
          const data = await voiceLibraryMyVoices({
            keyword: keyword || undefined,
            language_type: f.language || undefined,
            age: f.age || undefined,
            gender: f.gender || undefined,
            scene: sceneCsv || undefined,
            emotion: emotionCsv || undefined,
            sort: "latest",
            skip: 0,
            limit: 50,
          });
          if (cancelled) return;
          setVoices((data.voices || []).map(mapVoiceLibraryVoice));
          return;
        }

        const data = await voiceLibraryExplore({
          keyword: keyword || undefined,
          language_type: f.language || undefined,
          age: f.age || undefined,
          gender: f.gender || undefined,
          scene: sceneCsv || undefined,
          emotion: emotionCsv || undefined,
          sort: "mostUsers",
          skip: 0,
          limit: 50,
        });
        if (cancelled) return;
        const mapped = (data.voices || []).map(mapVoiceLibraryVoice);
        // On successful response, reflect empty results instead of silently keeping defaults.
        setVoices(mapped);
      } catch (e: any) {
        // Keep previous list, but surface the error so it's clear the API isn't wired/reachable.
        const msg = String(e?.message || "").trim();
        if (msg) setToast({ kind: "error", message: `音色库请求失败：${msg}` });
      } finally {
        if (!cancelled) setVoicesLoading(false);
      }
    })();

    return () => {
      cancelled = true;
      setVoicesLoading(false);
    };
  }, [voiceQuery]);

  // Ensure selected voice remains valid when voices list changes.
  useEffect(() => {
    if (!voices || voices.length === 0) return;
    if (!config.voiceId || !voices.some((v) => v.id === config.voiceId)) {
      setConfig((prev) => ({ ...prev, voiceId: voices[0].id }));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [voices]);

  const handleToggleFavorite = async (
    voiceId: string,
    nextIsFavorite: boolean,
  ) => {
    try {
      await voiceLibraryUpdateFavorites([voiceId], nextIsFavorite);
      setVoices((prev) =>
        prev.map((v) =>
          v.id === voiceId ? { ...v, isFavorited: nextIsFavorite } : v,
        ),
      );
      // Force a refresh for tabs backed by favorites.
      setVoiceQuery((prev) => ({ ...prev }));
    } catch (e: any) {
      setToast({ kind: "error", message: e?.message || "更新收藏失败" });
    }
  };

  const handleCreateMyVoice = async (displayName: string) => {
    const name = (displayName || "").trim();
    if (!name) return;
    try {
      const selectedBase =
        config.voiceId && !String(config.voiceId).startsWith("user_")
          ? String(config.voiceId)
          : "anime_uncle";
      await voiceLibraryCreateMyVoice({
        display_name: name,
        base_voice_id: selectedBase,
        language_type: voiceQuery.filters.language || undefined,
        age: voiceQuery.filters.age || undefined,
        gender: voiceQuery.filters.gender || undefined,
        scene: voiceQuery.filters.scene || undefined,
        emotion: voiceQuery.filters.emotion || undefined,
        is_public: false,
      });
      // Refresh current list
      setVoiceQuery((prev) => ({ ...prev }));
      setToast({ kind: "warn", message: `已创建（基于：${selectedBase}）` });
    } catch (e: any) {
      setToast({ kind: "error", message: e?.message || "创建失败" });
    }
  };

  // Cleanup object URL when file changes
  useEffect(() => {
    return () => {
      if (file?.url) URL.revokeObjectURL(file.url);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [file?.url]);

  useEffect(() => {
    if (!toast) return;
    const t = setTimeout(() => setToast(null), 4500);
    return () => clearTimeout(t);
  }, [toast]);

  // Handle Generation
  const handleGenerate = async () => {
    if (!file || !config.voiceId) return;

    const isVideoInput = Boolean(
      file.file?.type?.startsWith("video/") ||
      String(file.name || "")
        .toLowerCase()
        .endsWith(".mp4"),
    );
    const mediaLabel = isVideoInput ? "Media (video)" : "Audio";

    // When the UI is connected to the main-site voice library, many voice_ids are not
    // supported by this local backend's /voice-changer pipeline. Block early to avoid
    // "success but wrong voice" (passthrough/fallback) confusion.
    const rawVoiceLibBase = (import.meta as any).env
      ?.VITE_VOICE_LIBRARY_BASE_URL as string | undefined;
    const hasRemoteVoiceLibrary = Boolean((rawVoiceLibBase || "").trim());
    const rawVoiceChangerBase = (import.meta as any).env
      ?.VITE_VOICE_CHANGER_BASE_URL as string | undefined;
    // Only treat it as "remote generation available" when a separate voice-changer base is configured.
    // VOICE_CHANGER_BASE_URL may be empty in dev because we proxy through Vite.
    const hasRemoteVoiceChanger = Boolean((rawVoiceChangerBase || "").trim());

    const demoAllowUnsupported = ["1", "true", "yes", "on"].includes(
      String(
        (import.meta as any).env?.VITE_DEMO_ALLOW_UNSUPPORTED_VOICE_ID || "",
      ).toLowerCase(),
    );

    if (
      hasRemoteVoiceLibrary &&
      !hasRemoteVoiceChanger &&
      !demoAllowUnsupported
    ) {
      const id = String(config.voiceId);
      const localSupported = new Set<string>([
        ...(capabilities?.voices || []).map((v) => String(v.id)),
        ...DEFAULT_VOICES.map((v) => String(v.id)),
      ]);

      const supported = localSupported.has(id) || id.startsWith("user_");

      if (!supported) {
        setToast({
          kind: "error",
          message:
            "当前后端不支持该音色ID。请切换到 Local 标签选择可生成的音色，或在后端接入该 voice_id 的真实转换能力。",
        });
        return;
      }
    }

    if (!API_BASE_URL && (import.meta as any).env?.PROD) {
      setToast({
        kind: "error",
        message:
          "Missing VITE_API_BASE_URL. Set it to your backend domain (e.g. Render URL).",
      });
      return;
    }

    // Client-side duration guard to match backend: >min and <max.
    const d = file.durationSec;
    if (typeof d === "number") {
      if (d <= durationLimits.min) {
        setToast({
          kind: "warn",
          message: `${mediaLabel} too short (${formatSec(d)}). Must be > ${formatSec(durationLimits.min)}.`,
        });
        return;
      }
      if (d >= durationLimits.max) {
        setToast({
          kind: "warn",
          message: `${mediaLabel} too long (${formatSec(d)}). Must be < ${formatSec(durationLimits.max)}.`,
        });
        return;
      }
    }

    setAppState("uploading");
    setResultAudio(null);
    setShowSilenceWarning(false);

    try {
      const wantsVideo = isVideoInput;

      const payload: VoiceChangerPayload = {
        voice_id: String(config.voiceId),
        stability: config.stability,
        similarity: config.similarity,
        output_format: wantsVideo ? "mp4" : "mp3",
        preset_id: null,
        webhook_url: null,
        options: {
          remove_noise: config.removeNoise,
          language: config.language,
        },
      };

      setAppState("processing");
      const res = await voiceChange(file.file, payload);
      if (!res || (res as any).status !== "success") {
        throw new Error(
          `Conversion failed: ${String((res as any)?.status || "unknown")}`,
        );
      }
      if (!(res as any).output_url) {
        throw new Error("Conversion failed: missing output_url");
      }

      const demo = (res as any)?.meta?.debug?.demo;
      const demoNote = demo?.note || (res as any)?.meta?.debug?.provider?.note;
      const providerStatus = String(
        (res as any)?.meta?.debug?.provider?.status || "",
      );
      const resolvedName = String(demo?.resolved_voice_name || "").trim();
      const resolvedId = String(demo?.resolved_voice_id || "").trim();
      if (
        demoNote ||
        providerStatus.includes("disabled_no_api_key") ||
        providerStatus.includes("demo_force_passthrough")
      ) {
        const mapped =
          resolvedName || resolvedId
            ? `（已映射为本地音色：${resolvedName || resolvedId}）`
            : "";
        setToast({
          kind: "warn",
          message: `Demo 模式：主站音色无法在本地真实复刻，本次使用本地效果进行演示${mapped}。`,
        });
      }

      const outputUrl = getOutputUrl(res.output_url);
      setResultAudio(outputUrl);
      setAppState("complete");

      refreshRecentUsed();

      const selectedVoice = voices.find((v) => v.id === config.voiceId);
      const newItem: HistoryItem = {
        id: res.task_id || Date.now().toString(),
        name: `Converted: ${selectedVoice?.name || config.voiceId}`,
        url: outputUrl,
        duration: typeof d === "number" ? formatSec(d) : "--:--",
        date: new Date().toLocaleString(),
      };
      setHistory((prev) => [newItem, ...prev]);
    } catch (e: any) {
      setAppState("idle");
      setToast({ kind: "error", message: e?.message || "Conversion failed" });
    }
  };

  const handleDeleteHistory = (id: string) => {
    setHistory((prev) => prev.filter((item) => item.id !== id));
  };

  const handlePlayHistory = (url: string) => {
    setResultAudio(url);
  };

  return (
    <div className="min-h-screen flex flex-col bg-white overflow-hidden font-sans text-brand-black pt-[55px] px-[60px] pb-[38px]">
      {/* Header Bar */}
      <header className="flex items-center bg-white shrink-0 mb-[50px]">
        <div className="flex items-center gap-2">
          <h1 className="text-[20px] font-semibold text-[#0D062D] leading-normal capitalize font-['Inter']">
            Voice Changer
          </h1>
          <div className="flex items-center gap-2 px-2.5 py-1.5 border border-[#e1e1e1] rounded-full bg-white">
            <span className="text-[13px] text-[#36353a] font-medium leading-tight">
              5/5 Slots Remaining
            </span>
            <button
              onClick={() => setLimitModalOpen(true)}
              className="bg-[#feecea] text-[#fe655d] px-3 py-1 rounded-full text-[12px] font-bold hover:opacity-80 transition-opacity"
            >
              Upgrade
            </button>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 flex overflow-hidden bg-white relative">
        <div className="flex-1 bg-white overflow-hidden flex flex-col lg:flex-row relative">
          {/* Toast */}
          {toast && (
            <div
              className={`absolute top-4 left-1/2 -translate-x-1/2 px-4 py-3 rounded-lg shadow-lg border flex items-center gap-2 z-50 animate-fade-in-up ${toast.kind === "error" ? "bg-red-50 text-red-600 border-red-100" : "bg-orange-50 text-orange-700 border-orange-100"}`}
            >
              <AlertTriangle size={18} />
              <span className="text-sm font-medium">{toast.message}</span>
            </div>
          )}

          {/* Toast Notification */}
          {showSilenceWarning && (
            <div className="absolute top-4 left-1/2 -translate-x-1/2 bg-red-50 text-red-600 px-4 py-3 rounded-lg shadow-lg border border-red-100 flex items-center gap-2 z-50 animate-bounce">
              <AlertTriangle size={18} />
              <span className="text-sm font-medium">
                [!] No valid voice detected. Try recording again.
              </span>
            </div>
          )}

          {/* Left Panel: Input & Canvas */}
          <div className="w-full lg:w-[418px] h-full overflow-hidden relative">
            <LeftPanel
              file={file}
              setFile={setFile}
              removeNoise={config.removeNoise}
              setRemoveNoise={(val) =>
                setConfig({ ...config, removeNoise: val })
              }
              resultAudio={resultAudio}
              onGenerate={handleGenerate}
              isProcessing={
                appState === "uploading" || appState === "processing"
              }
              history={history}
              onDeleteHistory={handleDeleteHistory}
              onPlayHistory={handlePlayHistory}
            />
          </div>

          {/* Right Panel: Console */}
          <div className="flex-1 h-full overflow-hidden relative z-10">
            <RightPanel
              voices={voices}
              voicesLoading={voicesLoading}
              config={config}
              setConfig={setConfig}
              appState={appState}
              voiceQuery={voiceQuery}
              setVoiceQuery={setVoiceQuery}
              apiBaseUrl={API_BASE_URL}
              capabilities={capabilities}
              recentUsedVoices={recentUsedVoices}
              onToggleFavorite={handleToggleFavorite}
              onCreateMyVoice={handleCreateMyVoice}
              onPreviewVoice={handlePreviewVoice}
              isDisabled={!file}
              onGenerate={handleGenerate}
            />
          </div>
        </div>
      </main>

      <UpgradeModal
        isOpen={limitModalOpen}
        onClose={() => setLimitModalOpen(false)}
      />
    </div>
  );
};

export default App;
