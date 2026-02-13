import axios from 'axios'
import type { ApiResponse, VoiceChangePayload } from '@/types'

const rawApiBaseUrl = import.meta.env.VITE_API_BASE_URL as string | undefined
export const API_BASE_URL = rawApiBaseUrl?.replace(/\/+$/, '')

const api = axios.create({
  // Local dev: uses Vite proxy (/api -> http://127.0.0.1:8000)
  // Prod (Vercel): set VITE_API_BASE_URL=https://<your-render-service>.onrender.com
  baseURL: API_BASE_URL ?? '/api',
  timeout: 120000 // 2分钟超时，因为音频处理可能较慢
})

type APIEnvelope<T> = {
  code: number
  message: string
  data: T
}

export type VoiceLibraryVoice = {
  id: number
  voice_id: string
  display_name: string
  voice_type?: 'built-in' | 'user' | string
  labels?: string[]
  meta?: Record<string, any>
  is_public?: boolean
  url?: string | null
  fallbackurl?: string | null
  is_favorited?: boolean
  language?: string | null
  age?: string | null
  gender?: string | null
  scene?: string[]
  emotion?: string[]
  voice_description?: string | null
  creation_mode?: string
  can_delete?: boolean
  create_time: number
}

export type VoicesListData = {
  total_count: number
  voices: VoiceLibraryVoice[]
}

export type FavoritesUpdateData = {
  success_count: number
  failed_count: number
  failed_voice_ids?: string[] | null
}

function safeGetOrCreateUserId(): string | null {
  try {
    const key = 'voice_library_user_id'
    const existing = window.localStorage.getItem(key)
    if (existing && existing.trim()) return existing.trim()
    const id =
      typeof crypto !== 'undefined' && typeof (crypto as any).randomUUID === 'function'
        ? (crypto as any).randomUUID()
        : `u_${Math.random().toString(16).slice(2)}_${Date.now()}`
    window.localStorage.setItem(key, id)
    return id
  } catch {
    return null
  }
}

function voiceLibraryHeaders(extra?: Record<string, string>) {
  const userId = typeof window !== 'undefined' ? safeGetOrCreateUserId() : null
  return {
    ...(userId ? { 'X-User-Id': userId } : {}),
    ...(extra || {})
  }
}

// Voice library client:
// - Dev: calls absolute /api/v1/* which Vite proxies to backend (no rewrite).
// - Prod: if API_BASE_URL is set, calls ${API_BASE_URL}/api/v1/*.
const voiceLibraryApi = axios.create({
  baseURL: API_BASE_URL ?? '',
  timeout: 120000
})

async function readEnvelope<T>(promise: Promise<{ data: APIEnvelope<T> }>): Promise<T> {
  const resp = await promise
  const env = resp.data
  if (!env || typeof env.code !== 'number') {
    // Allow non-enveloped responses (shouldn't happen, but keeps client resilient)
    return (resp as any).data as T
  }
  if (env.code !== 0) {
    throw new Error(env.message || 'Request failed')
  }
  return env.data
}

export async function healthCheck(): Promise<boolean> {
  try {
    const response = await api.get('/healthz')
    return response.data.status === 'ok'
  } catch {
    return false
  }
}

export async function convertVoice(
  file: File,
  payload: VoiceChangePayload
): Promise<ApiResponse> {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('payload', JSON.stringify(payload))
  
  // IMPORTANT: Do not manually set Content-Type for multipart.
  // The browser must include the boundary; otherwise FastAPI may return 422.
  const response = await api.post<ApiResponse>('/voice-changer', formData, {
    headers: voiceLibraryHeaders()
  })
  
  return response.data
}

export async function voiceLibraryTopFixed(language: 'en' | 'zh' | 'ja' = 'en'): Promise<VoicesListData> {
  return await readEnvelope<VoicesListData>(
    voiceLibraryApi.get('/api/v1/voice-library/top-fixed-voices', {
      params: { language },
      headers: voiceLibraryHeaders()
    }) as any
  )
}

export type VoiceLibraryExploreParams = {
  keyword?: string
  voice_ids?: string
  language?: string
  language_type?: string
  age?: string
  gender?: string
  scene?: string
  emotion?: string
  sort?: string
  skip?: number
  limit?: number
}

export async function voiceLibraryExplore(params: VoiceLibraryExploreParams): Promise<VoicesListData> {
  return await readEnvelope<VoicesListData>(
    voiceLibraryApi.get('/api/v1/voice-library/explore', {
      params,
      headers: voiceLibraryHeaders()
    }) as any
  )
}

export async function voiceLibraryFavorites(params: VoiceLibraryExploreParams): Promise<VoicesListData> {
  return await readEnvelope<VoicesListData>(
    voiceLibraryApi.get('/api/v1/voice-library/favorites', {
      params,
      headers: voiceLibraryHeaders()
    }) as any
  )
}

export async function voiceLibraryMyVoices(params: VoiceLibraryExploreParams): Promise<VoicesListData> {
  return await readEnvelope<VoicesListData>(
    voiceLibraryApi.get('/api/v1/voice-library/my-voices', {
      params,
      headers: voiceLibraryHeaders()
    }) as any
  )
}

export type CreateMyVoiceRequest = {
  display_name: string
  base_voice_id?: string
  voice_description?: string
  language_type?: string
  age?: string
  gender?: string
  scene?: string[]
  emotion?: string[]
  labels?: string[]
  meta?: Record<string, unknown>
  is_public?: boolean
}

export type CreateMyVoiceData = {
  voice: VoiceLibraryVoice
}

export async function voiceLibraryCreateMyVoice(body: CreateMyVoiceRequest): Promise<CreateMyVoiceData> {
  return await readEnvelope<CreateMyVoiceData>(
    voiceLibraryApi.post('/api/v1/voice-library/my-voices', body, {
      headers: voiceLibraryHeaders({ 'Content-Type': 'application/json' })
    }) as any
  )
}

export async function voiceLibraryUpdateFavorites(voiceIds: string[], isFavorite: boolean): Promise<FavoritesUpdateData> {
  return await readEnvelope<FavoritesUpdateData>(
    voiceLibraryApi.post(
      '/api/v1/voice-library/favorites',
      { voice_ids: voiceIds, is_favorite: isFavorite },
      { headers: voiceLibraryHeaders({ 'Content-Type': 'application/json' }) }
    ) as any
  )
}

export function getOutputUrl(outputPath: string): string {
  // outputPath 格式: /outputs/xxx.mp3
  if (!API_BASE_URL) return outputPath
  return `${API_BASE_URL}${outputPath}`
}

export default api
