<template>
  <div class="audio-player" v-if="voiceStore.conversionResult">
    <div class="player-content">
      <!-- 播放控制 -->
      <div class="player-controls">
        <a-button 
          type="text" 
          shape="circle" 
          class="control-btn"
          @click="skipBackward"
        >
          <StepBackwardOutlined />
        </a-button>
        <a-button 
          type="primary" 
          shape="circle" 
          class="play-btn"
          @click="togglePlay"
        >
          <PauseOutlined v-if="isPlaying" />
          <CaretRightOutlined v-else />
        </a-button>
        <a-button 
          type="text" 
          shape="circle" 
          class="control-btn"
          @click="skipForward"
        >
          <StepForwardOutlined />
        </a-button>
      </div>
      
      <!-- 进度条 -->
      <div class="progress-section">
        <span class="time-current">{{ formatTime(currentTime) }}</span>
        <div class="progress-bar" ref="progressRef" @click="handleSeek">
          <div class="progress-track">
            <div class="progress-fill" :style="{ width: progressPercent + '%' }"></div>
          </div>
        </div>
        <span class="time-total">{{ formatTime(duration) }}</span>
      </div>
      
      <!-- 操作按钮 -->
      <div class="player-actions">
        <a-button type="text" class="action-btn" @click="handleDownload">
          <DownloadOutlined />
        </a-button>
        <a-button type="text" class="action-btn" @click="handleLike">
          <LikeOutlined :class="{ liked: isLiked }" />
        </a-button>
        <a-button type="text" class="action-btn" @click="handleDislike">
          <DislikeOutlined :class="{ disliked: isDisliked }" />
        </a-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onUnmounted } from 'vue'
import { 
  StepBackwardOutlined, 
  StepForwardOutlined, 
  CaretRightOutlined, 
  PauseOutlined,
  DownloadOutlined,
  LikeOutlined,
  DislikeOutlined
} from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import { useVoiceStore } from '@/stores/voice'

const voiceStore = useVoiceStore()
const progressRef = ref<HTMLDivElement | null>(null)

const isPlaying = ref(false)
const currentTime = ref(0)
const duration = ref(0)
const isLiked = ref(false)
const isDisliked = ref(false)

let audio: HTMLAudioElement | null = null

const progressPercent = computed(() => {
  if (duration.value === 0) return 0
  return (currentTime.value / duration.value) * 100
})

const formatTime = (seconds: number): string => {
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
}

const initAudio = () => {
  if (!voiceStore.conversionResult?.outputUrl) return
  
  if (audio) {
    audio.pause()
    audio = null
  }
  
  audio = new Audio(voiceStore.conversionResult.outputUrl)
  
  audio.onloadedmetadata = () => {
    duration.value = audio?.duration || 0
  }
  
  audio.ontimeupdate = () => {
    currentTime.value = audio?.currentTime || 0
  }
  
  audio.onplay = () => {
    isPlaying.value = true
  }
  
  audio.onpause = () => {
    isPlaying.value = false
  }
  
  audio.onended = () => {
    isPlaying.value = false
    currentTime.value = 0
  }
}

const togglePlay = () => {
  if (!audio) return
  
  if (isPlaying.value) {
    audio.pause()
  } else {
    audio.play()
  }
}

const skipBackward = () => {
  if (!audio) return
  audio.currentTime = Math.max(0, audio.currentTime - 10)
}

const skipForward = () => {
  if (!audio) return
  audio.currentTime = Math.min(duration.value, audio.currentTime + 10)
}

const handleSeek = (event: MouseEvent) => {
  if (!audio || !progressRef.value) return
  
  const rect = progressRef.value.getBoundingClientRect()
  const percent = (event.clientX - rect.left) / rect.width
  audio.currentTime = percent * duration.value
}

const handleDownload = async () => {
  if (!voiceStore.conversionResult?.outputUrl) return
  
  try {
    const response = await fetch(voiceStore.conversionResult.outputUrl)
    const blob = await response.blob()
    const url = URL.createObjectURL(blob)
    
    const link = document.createElement('a')
    link.href = url
    link.download = `converted_${voiceStore.conversionResult.voiceName}_${Date.now()}.mp3`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    
    URL.revokeObjectURL(url)
    message.success('Download started')
  } catch (error) {
    message.error('Download failed')
  }
}

const handleLike = () => {
  isLiked.value = !isLiked.value
  if (isLiked.value) {
    isDisliked.value = false
    message.success('Thanks for your feedback!')
  }
}

const handleDislike = () => {
  isDisliked.value = !isDisliked.value
  if (isDisliked.value) {
    isLiked.value = false
    message.info('We\'ll work on improving!')
  }
}

watch(() => voiceStore.conversionResult?.outputUrl, (newUrl) => {
  if (newUrl) {
    initAudio()
  }
}, { immediate: true })

onUnmounted(() => {
  if (audio) {
    audio.pause()
    audio = null
  }
})
</script>

<style scoped>
.audio-player {
  position: fixed;
  bottom: 0;
  left: 72px;
  right: 0;
  background: linear-gradient(180deg, #ffffff 0%, #f8f8fa 100%);
  border-top: 1px solid #e8e8ed;
  padding: 16px 24px;
  z-index: 100;
  box-shadow: 0 -4px 12px rgba(0, 0, 0, 0.05);
}

.player-content {
  display: flex;
  align-items: center;
  gap: 24px;
  max-width: 1200px;
  margin: 0 auto;
}

/* 播放控制 */
.player-controls {
  display: flex;
  align-items: center;
  gap: 8px;
}

.control-btn {
  width: 36px;
  height: 36px;
  color: #6b6b80;
  font-size: 16px;
}

.control-btn:hover {
  color: #1a1a2e;
}

.play-btn {
  width: 44px;
  height: 44px;
  background: linear-gradient(135deg, #fe655d 0%, #ff8a84 100%);
  border: none;
  font-size: 18px;
}

.play-btn:hover {
  background: linear-gradient(135deg, #ff8a84 0%, #fe655d 100%);
}

/* 进度条 */
.progress-section {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 12px;
}

.time-current,
.time-total {
  font-size: 12px;
  color: #9d9db5;
  font-family: monospace;
  min-width: 45px;
}

.time-current {
  text-align: right;
}

.progress-bar {
  flex: 1;
  cursor: pointer;
  padding: 8px 0;
}

.progress-track {
  height: 4px;
  background: #e8e8ed;
  border-radius: 2px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #fe655d 0%, #ff8a84 100%);
  border-radius: 2px;
  transition: width 0.1s linear;
}

/* 操作按钮 */
.player-actions {
  display: flex;
  align-items: center;
  gap: 4px;
}

.action-btn {
  width: 36px;
  height: 36px;
  color: #9d9db5;
  font-size: 16px;
}

.action-btn:hover {
  color: #6b6b80;
}

.action-btn .liked {
  color: #fe655d;
}

.action-btn .disliked {
  color: #ff4d4f;
}
</style>
