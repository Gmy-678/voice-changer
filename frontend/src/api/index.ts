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
  const response = await api.post<ApiResponse>('/voice-changer', formData)
  
  return response.data
}

export function getOutputUrl(outputPath: string): string {
  // outputPath 格式: /outputs/xxx.mp3
  if (!API_BASE_URL) return outputPath
  return `${API_BASE_URL}${outputPath}`
}

export default api
