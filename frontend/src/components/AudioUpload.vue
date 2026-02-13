<template>
  <div 
    class="upload-card"
    :class="[variant, { dragging: isDragging }]"
    @dragover.prevent="isDragging = true"
    @dragleave="isDragging = false"
    @drop.prevent="handleDrop"
  >
    <div class="upload-icon">
      <CloudUploadOutlined />
    </div>
    <h3 class="upload-title" v-if="variant !== 'panel'">Upload File</h3>
    <p class="upload-desc" v-if="variant !== 'panel'">MP3, WAV, M4A up to 50MB</p>
    <p class="upload-desc panel-hint" v-else>Click to upload or drag and drop</p>
    <input 
      ref="fileInput"
      type="file" 
      accept=".mp3,.wav,.m4a,audio/*"
      @change="handleFileSelect"
      hidden
    />
    <a-button type="primary" ghost class="upload-btn" @click="triggerUpload">
      <UploadOutlined /> Choose File
    </a-button>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { CloudUploadOutlined, UploadOutlined } from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import { useVoiceStore } from '@/stores/voice'

withDefaults(
  defineProps<{
    variant?: 'card' | 'panel'
  }>(),
  {
    variant: 'card'
  }
)

const voiceStore = useVoiceStore()
const fileInput = ref<HTMLInputElement | null>(null)
const isDragging = ref(false)

const MAX_FILE_SIZE = 50 * 1024 * 1024 // 50MB
const ALLOWED_TYPES = ['audio/mpeg', 'audio/wav', 'audio/x-wav', 'audio/mp4', 'audio/x-m4a', 'audio/mp3']

const triggerUpload = () => {
  fileInput.value?.click()
}

const validateFile = (file: File): boolean => {
  if (file.size > MAX_FILE_SIZE) {
    message.error('File size exceeds 50MB limit')
    return false
  }
  
  // 检查文件类型或扩展名
  const ext = file.name.toLowerCase().split('.').pop()
  const validExt = ['mp3', 'wav', 'm4a'].includes(ext || '')
  const validType = ALLOWED_TYPES.includes(file.type) || file.type.startsWith('audio/')
  
  if (!validExt && !validType) {
    message.error('Please upload MP3, WAV, or M4A file')
    return false
  }
  
  return true
}

const processFile = async (file: File) => {
  if (!validateFile(file)) return
  
  voiceStore.isUploading = true
  
  try {
    // 创建音频URL用于预览
    const url = URL.createObjectURL(file)
    
    // 获取音频时长
    const duration = await getAudioDuration(url)
    
    // 检查时长限制（5分钟）
    if (duration > 300) {
      message.error('Audio duration exceeds 5 minutes limit')
      URL.revokeObjectURL(url)
      return
    }
    
    voiceStore.setOriginalAudio({
      file,
      name: file.name,
      url,
      duration
    })
    
    message.success('File uploaded successfully')
  } catch (error) {
    console.error('Upload failed:', error)
    message.error('Failed to process audio file')
  } finally {
    voiceStore.isUploading = false
  }
}

const getAudioDuration = (url: string): Promise<number> => {
  return new Promise((resolve, reject) => {
    const audio = new Audio()
    audio.onloadedmetadata = () => {
      resolve(audio.duration)
    }
    audio.onerror = () => {
      reject(new Error('Failed to load audio'))
    }
    audio.src = url
  })
}

const handleFileSelect = (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (file) {
    processFile(file)
  }
  // 重置input以便可以重复选择同一文件
  target.value = ''
}

const handleDrop = (event: DragEvent) => {
  isDragging.value = false
  const file = event.dataTransfer?.files[0]
  if (file) {
    processFile(file)
  }
}
</script>

<style scoped>
.upload-card {
  background: #ffffff;
  border: 2px dashed #e8e8ed;
  border-radius: 16px;
  padding: 40px 24px;
  text-align: center;
  transition: all 0.3s ease;
  cursor: pointer;
}

.upload-card:hover,
.upload-card.dragging {
  border-color: #fe655d;
  background: rgba(254, 101, 93, 0.04);
}

.upload-card.panel {
  width: 100%;
  flex: 1;
  padding: 20px;
  border-radius: 24px;
  border-style: solid;
  border-width: 1px;
  border-color: #ebebeb;
  background: #ffffff;
  box-shadow: 0px 0px 16px rgba(0, 0, 0, 0.08);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.upload-card.panel:hover,
.upload-card.panel.dragging {
  border-color: rgba(54, 53, 58, 0.16);
  background: #ffffff;
}

.upload-icon {
  width: 64px;
  height: 64px;
  margin: 0 auto 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #ffd1ce;
  border-radius: 16px;
  font-size: 28px;
  color: #fe655d;
}

.upload-card.panel .upload-icon {
  width: 62px;
  height: 62px;
  border-radius: 18px;
  margin-bottom: 16px;
  background: #ffffff;
  border: 1px solid #e1e1e1;
  color: #36353a;
}

.upload-title {
  font-size: 18px;
  font-weight: 600;
  color: #1a1a2e;
  margin-bottom: 8px;
}

.upload-desc {
  font-size: 14px;
  color: #9d9db5;
  margin-bottom: 20px;
}

.panel-hint {
  margin-bottom: 14px;
  font-size: 16px;
  font-weight: 500;
  line-height: 19px;
  color: #36353a;
}

.upload-btn {
  border-color: #fe655d;
  color: #fe655d;
}

.upload-btn:hover {
  background: #ffd1ce;
  border-color: #ff8a84;
  color: #fe655d;
}
</style>
