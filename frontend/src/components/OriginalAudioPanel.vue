<template>
  <div class="original-audio-panel">
    <div class="audio-info">
      <div class="file-icon">
        <FileOutlined />
      </div>
      <div class="file-details">
        <div class="file-name">{{ voiceStore.originalAudio?.name }}</div>
        <div class="file-meta">{{ formatDuration(voiceStore.originalAudio?.duration || 0) }}</div>
      </div>
      <a-button type="text" class="replace-btn" @click="handleReplace">
        <SwapOutlined /> Replace
      </a-button>
    </div>
    
    <!-- 波形显示 -->
    <div class="waveform-container" ref="waveformRef"></div>
    
    <!-- 播放控制 -->
    <div class="playback-controls">
      <a-button 
        type="text" 
        shape="circle" 
        class="play-btn"
        @click="togglePlay"
      >
        <PauseCircleOutlined v-if="isPlaying" />
        <PlayCircleOutlined v-else />
      </a-button>
      <span class="time-display">
        {{ formatTime(currentTime) }} / {{ formatTime(duration) }}
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { FileOutlined, SwapOutlined, PlayCircleOutlined, PauseCircleOutlined } from '@ant-design/icons-vue'
import { useVoiceStore } from '@/stores/voice'
import WaveSurfer from 'wavesurfer.js'

const voiceStore = useVoiceStore()
const waveformRef = ref<HTMLDivElement | null>(null)
const isPlaying = ref(false)
const currentTime = ref(0)
const duration = ref(0)

let wavesurfer: WaveSurfer | null = null

const formatDuration = (seconds: number): string => {
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

const formatTime = (seconds: number): string => {
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
}

const initWaveSurfer = () => {
  if (!waveformRef.value || !voiceStore.originalAudio?.url) return
  
  // 销毁已存在的实例
  if (wavesurfer) {
    wavesurfer.destroy()
  }
  
  wavesurfer = WaveSurfer.create({
    container: waveformRef.value,
    waveColor: '#c5c5d0',
    progressColor: '#fe655d',
    cursorColor: '#fe655d',
    barWidth: 2,
    barGap: 2,
    barRadius: 2,
    height: 60,
    normalize: true,
  })
  
  wavesurfer.load(voiceStore.originalAudio.url)
  
  wavesurfer.on('ready', () => {
    duration.value = wavesurfer?.getDuration() || 0
  })
  
  wavesurfer.on('audioprocess', () => {
    currentTime.value = wavesurfer?.getCurrentTime() || 0
  })
  
  wavesurfer.on('play', () => {
    isPlaying.value = true
  })
  
  wavesurfer.on('pause', () => {
    isPlaying.value = false
  })
  
  wavesurfer.on('finish', () => {
    isPlaying.value = false
    currentTime.value = 0
  })
}

const togglePlay = () => {
  if (wavesurfer) {
    wavesurfer.playPause()
  }
}

const handleReplace = () => {
  voiceStore.setOriginalAudio(null)
}

watch(() => voiceStore.originalAudio?.url, () => {
  if (voiceStore.originalAudio?.url) {
    // 延迟初始化，确保DOM已渲染
    setTimeout(initWaveSurfer, 100)
  }
}, { immediate: true })

onMounted(() => {
  if (voiceStore.originalAudio?.url) {
    initWaveSurfer()
  }
})

onUnmounted(() => {
  if (wavesurfer) {
    wavesurfer.destroy()
    wavesurfer = null
  }
})
</script>

<style scoped>
.original-audio-panel {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.audio-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.file-icon {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #ffd1ce;
  border-radius: 10px;
  color: #fe655d;
  font-size: 18px;
}

.file-details {
  flex: 1;
}

.file-name {
  font-size: 14px;
  font-weight: 500;
  color: #1a1a2e;
  margin-bottom: 2px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-meta {
  font-size: 12px;
  color: #9d9db5;
}

.replace-btn {
  color: #6b6b80;
}

.replace-btn:hover {
  color: #fe655d;
}

.waveform-container {
  background: #f8f8fa;
  border-radius: 8px;
  padding: 12px;
}

.playback-controls {
  display: flex;
  align-items: center;
  gap: 12px;
}

.play-btn {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fe655d;
  font-size: 24px;
}

.time-display {
  font-size: 13px;
  color: #6b6b80;
  font-family: monospace;
}
</style>
