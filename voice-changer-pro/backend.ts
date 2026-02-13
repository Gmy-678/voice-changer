export type VoiceChangerPayload = {
  voice_id: string;
  stability: number;
  similarity: number;
  output_format: 'mp3' | 'wav' | 'mp4';
  preset_id?: string | null;
  webhook_url?: string | null;
  options?: Record<string, unknown>;
};

export type VoiceChangerResponse = {
  task_id: string;
  status: 'success' | string;
  output_url: string;
  meta?: unknown;
};

export type VoiceInfo = {
  id: string;
  name: string;
  role?: string;
  description?: string;
  category?: string;
  is_verified?: boolean;
  provider?: string | null;
};

export type CapabilitiesResponse = {
  voices: VoiceInfo[];
  output_formats: Array<'mp3' | 'wav' | 'mp4'>;
  upload_max_bytes: number;
  allowed_content_types: string[];
  upload_min_duration_sec: number;
  upload_max_duration_sec: number;
  async_mode: boolean;
};

export type VoiceLibraryVoice = {
  id: number;
  voice_id: string;
  display_name: string;
  voice_type?: 'built-in' | 'user' | string;
  labels?: string[];
  meta?: Record<string, unknown>;
  is_public?: boolean;
  url?: string | null;
  fallbackurl?: string | null;
  is_favorited?: boolean;
  language?: string | null;
  age?: string | null;
  gender?: string | null;
  scene?: string[];
  emotion?: string[];
  voice_description?: string | null;
  creation_mode?: string;
  can_delete?: boolean;
  create_time: number;
};

export type VoicesListData = {
  total_count: number;
  voices: VoiceLibraryVoice[];
};

export type FavoritesUpdateData = {
  success_count: number;
  failed_count: number;
  failed_voice_ids?: string[] | null;
};

type APIEnvelope<T> = {
  code: number;
  message: string;
  data: T;
};

const rawBase = (import.meta as any).env?.VITE_API_BASE_URL as string | undefined;
export const API_BASE_URL = (rawBase ?? '').replace(/\/$/, '');

// Optional: route voice-changer endpoints (generation/capabilities/voices) to a different backend.
// This is useful when voice-library data comes from the main site, and generation should follow it.
const rawVoiceChangerBase = (import.meta as any).env?.VITE_VOICE_CHANGER_BASE_URL as string | undefined;
const voiceChangerBaseNormalized = (rawVoiceChangerBase ?? '').replace(/\/$/, '');

const rawVoiceLibBase = (import.meta as any).env?.VITE_VOICE_LIBRARY_BASE_URL as string | undefined;
const voiceLibBaseNormalized = (rawVoiceLibBase ?? '').replace(/\/$/, '');

// In dev, prefer proxying through the Vite dev server to avoid browser CORS.
const isDev = Boolean((import.meta as any).env?.DEV);
export const VOICE_LIBRARY_BASE_URL = (isDev && voiceLibBaseNormalized) ? '' : (voiceLibBaseNormalized || API_BASE_URL);

export const VOICE_CHANGER_BASE_URL = (isDev && voiceChangerBaseNormalized) ? '' : (voiceChangerBaseNormalized || API_BASE_URL);

const rawVoiceChangerCreds = (import.meta as any).env?.VITE_VOICE_CHANGER_CREDENTIALS as string | undefined;
const VOICE_CHANGER_CREDENTIALS: RequestCredentials | undefined =
  rawVoiceChangerCreds === 'include' || rawVoiceChangerCreds === 'omit' || rawVoiceChangerCreds === 'same-origin'
    ? (rawVoiceChangerCreds as RequestCredentials)
    : undefined;

const rawVoiceChangerBearer = (import.meta as any).env?.VITE_VOICE_CHANGER_AUTH_BEARER as string | undefined;
const VOICE_CHANGER_AUTH_BEARER = (rawVoiceChangerBearer || '').trim() || null;

const rawVoiceLibCreds = (import.meta as any).env?.VITE_VOICE_LIBRARY_CREDENTIALS as string | undefined;
const VOICE_LIBRARY_CREDENTIALS: RequestCredentials | undefined =
  rawVoiceLibCreds === 'include' || rawVoiceLibCreds === 'omit' || rawVoiceLibCreds === 'same-origin'
    ? (rawVoiceLibCreds as RequestCredentials)
    : undefined;

const rawSendUserId = (import.meta as any).env?.VITE_VOICE_LIBRARY_SEND_USER_ID as string | undefined;
const VOICE_LIBRARY_SEND_USER_ID: boolean =
  rawSendUserId !== undefined
    ? ['1', 'true', 'yes', 'on'].includes(String(rawSendUserId).toLowerCase())
    : !Boolean(rawVoiceLibBase);

let inMemoryUserId: string | null = null;

function generateRequestId(): string {
  try {
    const uuid =
      (typeof crypto !== 'undefined' && typeof (crypto as any).randomUUID === 'function')
        ? String((crypto as any).randomUUID())
        : `${Math.random().toString(16).slice(2)}${Date.now().toString(16)}`;
    return `${Date.now()}--${uuid}`;
  } catch {
    return `${Date.now()}--${Math.random().toString(16).slice(2)}`;
  }
}

function safeGetOrCreateUserId(): string | null {
  try {
    if (typeof window === 'undefined') return null;
    const key = 'voice_library_user_id';
    const existing = window.localStorage.getItem(key);
    if (existing && existing.trim()) return existing.trim();
    const id =
      (typeof crypto !== 'undefined' && typeof (crypto as any).randomUUID === 'function')
        ? (crypto as any).randomUUID()
        : `u_${Math.random().toString(16).slice(2)}_${Date.now()}`;
    // Persist best-effort; if storage is blocked, fall back to in-memory id.
    try {
      window.localStorage.setItem(key, id);
    } catch {
      // ignore
    }
    inMemoryUserId = id;
    return id;
  } catch {
    // If localStorage access throws (privacy mode), still provide a stable-ish id per tab.
    if (inMemoryUserId) return inMemoryUserId;
    inMemoryUserId = `u_${Math.random().toString(16).slice(2)}_${Date.now()}`;
    return inMemoryUserId;
  }
}

function voiceLibraryAuthHeaders(extra?: HeadersInit): HeadersInit {
  const base: Record<string, string> = {};
  if (VOICE_LIBRARY_SEND_USER_ID) {
    const userId = safeGetOrCreateUserId();
    if (userId) base['X-User-Id'] = userId;
  }
  return { ...base, ...(extra as any) };
}

function voiceLibraryFetchInit(method: string, extra?: RequestInit): RequestInit {
  const credentials = VOICE_LIBRARY_CREDENTIALS ?? (rawVoiceLibBase ? 'omit' : 'same-origin');
  return {
    method,
    credentials,
    ...(extra || {}),
    headers: voiceLibraryAuthHeaders((extra || {}).headers),
  };
}

function joinUrl(base: string, path: string): string {
  const p = path.startsWith('/') ? path : `/${path}`;
  if (!base) return p;
  return `${base}${p}`;
}

export function getOutputUrl(outputUrlOrPath: string): string {
  if (!outputUrlOrPath) return outputUrlOrPath;
  if (/^https?:\/\//i.test(outputUrlOrPath)) return outputUrlOrPath;
  // If generation is routed to a separate backend, relative output URLs should resolve against it.
  const base = voiceChangerBaseNormalized || API_BASE_URL;
  return joinUrl(base, outputUrlOrPath);
}

function voiceChangerFetchInit(method: string, extra?: RequestInit): RequestInit {
  const credentials = VOICE_CHANGER_CREDENTIALS ?? (rawVoiceChangerBase ? 'omit' : 'same-origin');
  const headers: Record<string, string> = {
    ...(extra?.headers as any),
  };
  if (VOICE_CHANGER_AUTH_BEARER) {
    headers['Authorization'] = `Bearer ${VOICE_CHANGER_AUTH_BEARER}`;
  }
  return {
    method,
    credentials,
    ...(extra || {}),
    headers,
  };
}

function errorMessageFromDetail(detail: unknown): string {
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail) && detail.length > 0) {
    const first = detail[0] as any;
    if (first?.msg) return String(first.msg);
  }
  if (detail && typeof detail === 'object') {
    const anyDetail = detail as any;
    if (anyDetail.error) return String(anyDetail.error);
  }
  return 'Request failed';
}

async function readJsonOrThrow(resp: Response): Promise<any> {
  const text = await resp.text();
  let data: any = null;
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    data = null;
  }
  if (!resp.ok) {
    const detail = data?.detail ?? text;
    throw new Error(errorMessageFromDetail(detail));
  }
  return data;
}

async function readEnvelopeOrThrow<T>(resp: Response): Promise<T> {
  const data = (await readJsonOrThrow(resp)) as APIEnvelope<T>;
  if (data && typeof data === 'object' && typeof (data as any).code === 'number') {
    if ((data as any).code !== 0) {
      throw new Error(String((data as any).message || 'Request failed'));
    }
    return (data as any).data as T;
  }
  // If backend returns raw data (non-enveloped), accept it.
  return data as unknown as T;
}

export async function getCapabilities(): Promise<CapabilitiesResponse> {
  const url = joinUrl(VOICE_CHANGER_BASE_URL, '/voice-changer/capabilities');
  const resp = await fetch(url, voiceChangerFetchInit('GET'));
  const data = await readJsonOrThrow(resp);
  return data as CapabilitiesResponse;
}

export async function listVoices(): Promise<VoiceInfo[]> {
  const url = joinUrl(VOICE_CHANGER_BASE_URL, '/voice-changer/voices');
  const resp = await fetch(url, voiceChangerFetchInit('GET'));
  const data = await readJsonOrThrow(resp);
  return (data?.voices ?? []) as VoiceInfo[];
}

export async function voiceChange(file: File, payload: VoiceChangerPayload): Promise<VoiceChangerResponse> {
  const url = joinUrl(VOICE_CHANGER_BASE_URL, '/voice-changer');

  const form = new FormData();
  form.append('file', file, file.name);
  form.append('payload', JSON.stringify(payload));

  const headers: Record<string, string> = {
    ...(voiceLibraryAuthHeaders() as any),
  };
  if (VOICE_CHANGER_AUTH_BEARER) {
    headers['Authorization'] = `Bearer ${VOICE_CHANGER_AUTH_BEARER}`;
  }

  const resp = await fetch(url, voiceChangerFetchInit('POST', { headers, body: form }));

  const data = await readJsonOrThrow(resp);
  return data as VoiceChangerResponse;
}

export async function voiceLibraryTopFixed(language: 'en' | 'zh' | 'ja' = 'en'): Promise<VoicesListData> {
  const url = joinUrl(VOICE_LIBRARY_BASE_URL, `/api/v1/voice-library/top-fixed-voices?language=${encodeURIComponent(language)}`);
  const resp = await fetch(url, voiceLibraryFetchInit('GET'));
  return await readEnvelopeOrThrow<VoicesListData>(resp);
}

export type VoiceLibraryExploreParams = {
  keyword?: string;
  voice_ids?: string;
  language?: string;
  language_type?: string;
  age?: string;
  gender?: string;
  scene?: string;
  emotion?: string;
  sort?: string;
  skip?: number;
  limit?: number;
};

export async function voiceLibraryExplore(params: VoiceLibraryExploreParams): Promise<VoicesListData> {
  const qs = new URLSearchParams();
  Object.entries(params || {}).forEach(([k, v]) => {
    if (v === undefined || v === null) return;
    const s = typeof v === 'number' ? String(v) : String(v);
    if (!s) return;
    qs.set(k, s);
  });

  const url = joinUrl(VOICE_LIBRARY_BASE_URL, `/api/v1/voice-library/explore?${qs.toString()}`);
  const resp = await fetch(url, voiceLibraryFetchInit('GET'));
  return await readEnvelopeOrThrow<VoicesListData>(resp);
}

export async function voiceLibraryMyVoices(params: VoiceLibraryExploreParams): Promise<VoicesListData> {
  const qs = new URLSearchParams();
  Object.entries(params || {}).forEach(([k, v]) => {
    if (v === undefined || v === null) return;
    const s = typeof v === 'number' ? String(v) : String(v);
    if (!s) return;
    qs.set(k, s);
  });
  const url = joinUrl(VOICE_LIBRARY_BASE_URL, `/api/v1/voice-library/my-voices?${qs.toString()}`);
  const resp = await fetch(url, voiceLibraryFetchInit('GET'));
  return await readEnvelopeOrThrow<VoicesListData>(resp);
}

export async function voiceLibraryFavorites(params: VoiceLibraryExploreParams): Promise<VoicesListData> {
  const qs = new URLSearchParams();
  Object.entries(params || {}).forEach(([k, v]) => {
    if (v === undefined || v === null) return;
    const s = typeof v === 'number' ? String(v) : String(v);
    if (!s) return;
    qs.set(k, s);
  });
  const url = joinUrl(VOICE_LIBRARY_BASE_URL, `/api/v1/voice-library/favorites?${qs.toString()}`);
  const resp = await fetch(url, voiceLibraryFetchInit('GET'));
  return await readEnvelopeOrThrow<VoicesListData>(resp);
}

export async function voiceLibraryRecentUsed(limit = 5): Promise<VoicesListData> {
  // noiz.ai commonly calls: /recent-used?request_id=...&language=en
  // Some deployments may require auth; when it fails, fall back to public explore.
  const qs = new URLSearchParams();
  qs.set('request_id', generateRequestId());
  qs.set('language', String((voiceQueryDefaultLanguage() || 'en')).toLowerCase());
  // Keep limit best-effort; if server ignores it, we can slice client-side.
  qs.set('limit', String(limit));

  const url = joinUrl(VOICE_LIBRARY_BASE_URL, `/api/v1/voice-library/recent-used?${qs.toString()}`);
  try {
    const resp = await fetch(url, voiceLibraryFetchInit('GET'));
    if (!resp.ok) {
      if (resp.status === 401 || resp.status === 403) {
        return await voiceLibraryExplore({ skip: 0, limit });
      }
      // Other errors: still fall back to keep UI functional.
      return await voiceLibraryExplore({ skip: 0, limit });
    }

    const data = await readEnvelopeOrThrow<VoicesListData>(resp);
    if (Array.isArray((data as any)?.voices) && (data as any).voices.length > limit) {
      return { ...data, voices: (data as any).voices.slice(0, limit) } as VoicesListData;
    }
    return data;
  } catch {
    return await voiceLibraryExplore({ skip: 0, limit });
  }
}

function voiceQueryDefaultLanguage(): string | null {
  // We don't have access to React state here; use an env hint if provided.
  const raw = (import.meta as any).env?.VITE_VOICE_LIBRARY_LANGUAGE as string | undefined;
  const v = (raw || '').trim();
  return v || null;
}

export async function voiceLibraryUpdateFavorites(voiceIds: string[], isFavorite: boolean): Promise<FavoritesUpdateData> {
  const url = joinUrl(VOICE_LIBRARY_BASE_URL, `/api/v1/voice-library/favorites`);
  const resp = await fetch(url, {
    ...voiceLibraryFetchInit('POST', { headers: { 'Content-Type': 'application/json' } }),
    body: JSON.stringify({ voice_ids: voiceIds, is_favorite: isFavorite }),
  });
  return await readEnvelopeOrThrow<FavoritesUpdateData>(resp);
}

export type CreateMyVoiceRequest = {
  display_name: string;
  base_voice_id?: string;
  voice_description?: string;
  language_type?: string;
  age?: string;
  gender?: string;
  scene?: string[];
  emotion?: string[];
  labels?: string[];
  meta?: Record<string, unknown>;
  is_public?: boolean;
};

export type CreateMyVoiceData = {
  voice: VoiceLibraryVoice;
};

export async function voiceLibraryCreateMyVoice(body: CreateMyVoiceRequest): Promise<CreateMyVoiceData> {
  const url = joinUrl(VOICE_LIBRARY_BASE_URL, `/api/v1/voice-library/my-voices`);
  const resp = await fetch(url, {
    ...voiceLibraryFetchInit('POST', { headers: { 'Content-Type': 'application/json' } }),
    body: JSON.stringify(body),
  });
  return await readEnvelopeOrThrow<CreateMyVoiceData>(resp);
}

export async function getMediaDurationSec(objectUrl: string): Promise<number | null> {
  return await new Promise((resolve) => {
    const audio = document.createElement('audio');
    audio.preload = 'metadata';
    audio.src = objectUrl;

    const cleanup = () => {
      audio.removeAttribute('src');
      audio.load();
    };

    audio.onloadedmetadata = () => {
      const d = Number.isFinite(audio.duration) ? audio.duration : NaN;
      cleanup();
      resolve(Number.isFinite(d) ? d : null);
    };

    audio.onerror = () => {
      cleanup();
      resolve(null);
    };
  });
}
