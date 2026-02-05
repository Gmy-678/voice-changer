import axios from 'axios'
import type { ApiResponse, VoiceChangePayload } from '@/types'

const api = axios.create({
  baseURL: '/api',
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
  
  const response = await api.post<ApiResponse>('/voice-changer', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
  
  return response.data
}

export function getOutputUrl(outputPath: string): string {
  // outputPath 格式: /outputs/xxx.mp3
  return outputPath
}

export default api
