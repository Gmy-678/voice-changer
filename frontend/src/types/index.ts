export interface Voice {
  id: string
  name: string
  description: string
  gender: 'male' | 'female'
  avatar: string
  isFeatured: boolean
}

export interface AudioFile {
  file: File
  name: string
  url: string
  duration: number
}

export interface ConversionResult {
  taskId: string
  status: string
  outputUrl: string
  voiceName: string
  voiceAvatar?: string
}

export interface VoiceChangePayload {
  voice_id: string
  stability: number
  similarity: number
  output_format: string
}

export interface ApiResponse {
  task_id: string
  status: string
  output_url: string
  meta: Record<string, any>
}
