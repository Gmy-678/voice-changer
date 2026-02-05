<template>
  <div class="converted-audio-panel">
    <template v-if="voiceStore.conversionResult">
      <!-- 转换完成状态 -->
      <div class="result-info">
        <div class="voice-avatar">
          <UserOutlined />
        </div>
        <div class="voice-details">
          <div class="voice-name">{{ voiceStore.conversionResult.voiceName }}</div>
          <div class="voice-status">Conversion completed</div>
        </div>
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
    </template>
    
    <template v-else>
      <!-- 空状态 -->
      <div class="empty-state">
        <div class="empty-icon">
          <SoundOutlined />
        </div>
        <p class="empty-text">Result will appear here</p>
        <p class="empty-hint">Select a voice and click Generate</p>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onUnmounted } from 'vue'
import { UserOutlined, PlayCircleOutlined, PauseCircleOutlined, SoundOutlined } from '@ant-design/icons-vue'
import { useVoiceStore } from '@/stores/voice'
import WaveSurfer from 'wavesurfer.js'

const voiceStore = useVoiceStore()
const waveformRef = ref<HTMLDivElement | null>(null)
const isPlaying = ref(false)
const currentTime = ref(0)
const duration = ref(0)

let wavesurfer: WaveSurfer | null = null

const formatTime = (seconds: number): string => {
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
}

const initWaveSurfer = () => {
  if (!waveformRef.value || !voiceStore.conversionResult?.outputUrl) return
  
  if (wavesurfer) {
    wavesurfer.destroy()
  }
  
  wavesurfer = WaveSurfer.create({
    container: waveformRef.value,
    waveColor: '#c5c5d0',
    progressColor: '#52c41a',
    cursorColor: '#52c41a',
    barWidth: 2,
    barGap: 2,
    barRadius: 2,
    height: 60,
    normalize: true,
  })
  
  wavesurfer.load(voiceStore.conversionResult.outputUrl)
  
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

watch(() => voiceStore.conversionResult?.outputUrl, (newUrl) => {
  if (newUrl) {
    setTimeout(initWaveSurfer, 100)
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
.converted-audio-panel {
  min-height: 150px;
  display: flex;
  flex-direction: column;
}

.result-info {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.voice-avatar {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #52c41a 0%, #73d13d 100%);
  border-radius: 10px;
  color: #ffffff;
  font-size: 18px;
}

.voice-details {
  flex: 1;
}

.voice-name {
  font-size: 14px;
  font-weight: 500;
  color: #1a1a2e;
  margin-bottom: 2px;
}

.voice-status {
  font-size: 12px;
  color: #52c41a;
}

.waveform-container {
  background: #f8f8fa;
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 16px;
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
  color: #52c41a;
  font-size: 24px;
}

.time-display {
  font-size: 13px;
  color: #6b6b80;
  font-family: monospace;
}

/* 空状态 */
.empty-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
}

.empty-icon {
  width: 64px;
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f5f7;
  border-radius: 16px;
  font-size: 28px;
  color: #c5c5d0;
  margin-bottom: 16px;
}

.empty-text {
  font-size: 14px;
  color: #9d9db5;
  margin-bottom: 4px;
}

.empty-hint {
  font-size: 12px;
  color: #c5c5d0;
}
</style>
