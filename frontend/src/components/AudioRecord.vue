<template>
  <div class="record-card" :class="variant">
    <div class="record-icon" :class="{ recording: isRecording }">
      <AudioOutlined />
    </div>
    <h3 class="record-title" v-if="variant !== 'panel'">Record Audio</h3>
    <p class="record-desc" v-if="variant !== 'panel'">Use your microphone</p>
    <p class="record-desc panel-hint" v-else>Record audio</p>
    <a-button 
      :type="isRecording ? 'primary' : 'default'"
      :danger="isRecording"
      class="record-btn"
      @click="toggleRecording"
    >
      <template v-if="isRecording">
        <PauseCircleOutlined /> Stop Recording ({{ formatTime(recordingTime) }})
      </template>
      <template v-else>
        <AudioOutlined /> Start Recording
      </template>
    </a-button>
  </div>
</template>

<script setup lang="ts">
import { ref, onUnmounted } from 'vue'
import { AudioOutlined, PauseCircleOutlined } from '@ant-design/icons-vue'
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
const isRecording = ref(false)
const recordingTime = ref(0)
let mediaRecorder: MediaRecorder | null = null
let audioChunks: Blob[] = []
let timerInterval: number | null = null

const MAX_RECORDING_TIME = 300 // 5分钟

const formatTime = (seconds: number): string => {
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

const toggleRecording = async () => {
  if (isRecording.value) {
    stopRecording()
  } else {
    await startRecording()
  }
}

const startRecording = async () => {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
    
    mediaRecorder = new MediaRecorder(stream)
    audioChunks = []
    
    mediaRecorder.ondataavailable = (event) => {
      if (event.data.size > 0) {
        audioChunks.push(event.data)
      }
    }
    
    mediaRecorder.onstop = () => {
      const audioBlob = new Blob(audioChunks, { type: 'audio/wav' })
      const file = new File([audioBlob], `recording_${Date.now()}.wav`, { type: 'audio/wav' })
      const url = URL.createObjectURL(audioBlob)
      
      voiceStore.setOriginalAudio({
        file,
        name: file.name,
        url,
        duration: recordingTime.value
      })
      
      // 停止所有音轨
      stream.getTracks().forEach(track => track.stop())
      
      message.success('Recording saved successfully')
    }
    
    mediaRecorder.start()
    isRecording.value = true
    recordingTime.value = 0
    
    // 开始计时
    timerInterval = window.setInterval(() => {
      recordingTime.value++
      if (recordingTime.value >= MAX_RECORDING_TIME) {
        stopRecording()
        message.warning('Maximum recording time reached (5 minutes)')
      }
    }, 1000)
    
  } catch (error) {
    console.error('Recording failed:', error)
    message.error('Failed to access microphone. Please check permissions.')
  }
}

const stopRecording = () => {
  if (mediaRecorder && mediaRecorder.state !== 'inactive') {
    mediaRecorder.stop()
  }
  
  isRecording.value = false
  
  if (timerInterval) {
    clearInterval(timerInterval)
    timerInterval = null
  }
}

onUnmounted(() => {
  if (isRecording.value) {
    stopRecording()
  }
})
</script>

<style scoped>
.record-card {
  background: #ffffff;
  border: 2px dashed #e8e8ed;
  border-radius: 16px;
  padding: 40px 24px;
  text-align: center;
  transition: all 0.3s ease;
}

.record-card:hover {
  border-color: #c5c5d0;
}

.record-card.panel {
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

.record-card.panel:hover {
  border-color: rgba(54, 53, 58, 0.16);
}

.record-icon {
  width: 64px;
  height: 64px;
  margin: 0 auto 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f5f7;
  border-radius: 16px;
  font-size: 28px;
  color: #9d9db5;
  transition: all 0.3s ease;
}

.record-card.panel .record-icon {
  width: 62px;
  height: 62px;
  margin-bottom: 16px;
  border-radius: 18px;
  background: #ffffff;
  border: 1px solid #e1e1e1;
  color: #36353a;
}

.record-icon.recording {
  background: rgba(255, 77, 79, 0.1);
  color: #ff4d4f;
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% {
    transform: scale(1);
    opacity: 1;
  }
  50% {
    transform: scale(1.05);
    opacity: 0.8;
  }
}

.record-title {
  font-size: 18px;
  font-weight: 600;
  color: #1a1a2e;
  margin-bottom: 8px;
}

.record-desc {
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

.record-btn {
  border-color: #e8e8ed;
  color: #6b6b80;
}

.record-btn:hover {
  border-color: #c5c5d0;
  color: #1a1a2e;
}
</style>
