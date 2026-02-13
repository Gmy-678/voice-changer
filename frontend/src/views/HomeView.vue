<template>
  <div class="home-view">
    <!-- Top bar -->
    <header class="header">
      <div class="header-left">
        <h1 class="title">Voice Changer</h1>
        <span class="slots-pill">
          <span class="slots-text">5/5 Slots remaining</span>
          <span class="slots-upgrade">Upgrade</span>
        </span>
      </div>
      <div class="header-right">
        <a-button
          type="text"
          class="start-over-btn"
          @click="handleStartOver"
          v-if="voiceStore.originalAudio"
        >
          <RedoOutlined /> Start Over
        </a-button>
      </div>
    </header>
    
    <!-- Main layout -->
    <div class="content-wrapper">
      <div class="main-area">
        <!-- Empty state: upload / record -->
        <template v-if="!voiceStore.originalAudio">
          <div class="panel">
            <div class="panel-title">Upload Your Audio</div>
            <div class="audio-source-card">
              <AudioUpload variant="panel" />
              <div class="or-divider"><span>or</span></div>
              <AudioRecord variant="panel" />
            </div>
          </div>
        </template>
        
        <!-- 已上传状态：显示音频和转换 -->
        <template v-else>
          <div class="audio-section">
            <!-- 原始音频 -->
            <div class="audio-block original">
              <div class="block-header">
                <span class="block-label">ORIGINAL AUDIO</span>
              </div>
              <OriginalAudioPanel />
            </div>
            
            <!-- 生成按钮区域 -->
            <div class="generate-section">
              <PrecisionControl />
              <a-button 
                type="primary" 
                class="generate-btn"
                :loading="voiceStore.isConverting"
                @click="handleGenerate"
              >
                <ThunderboltOutlined v-if="!voiceStore.isConverting" />
                Generate Voice
              </a-button>
            </div>
            
            <!-- 转换后的音频 -->
            <div class="audio-block converted">
              <div class="block-header">
                <span class="block-label">CONVERTED AUDIO</span>
              </div>
              <ConvertedAudioPanel />
            </div>
          </div>
        </template>
      </div>
      
      <!-- 右侧声音选择面板 -->
      <aside class="voice-panel">
        <VoiceSelector />
      </aside>
    </div>
    
    <!-- 底部音频播放器 -->
    <AudioPlayer v-if="voiceStore.conversionResult" />
  </div>
</template>

<script setup lang="ts">
import { RedoOutlined, ThunderboltOutlined } from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import { useVoiceStore } from '@/stores/voice'
import { API_BASE_URL, convertVoice, getOutputUrl } from '@/api'
import AudioUpload from '@/components/AudioUpload.vue'
import AudioRecord from '@/components/AudioRecord.vue'
import VoiceSelector from '@/components/VoiceSelector.vue'
import OriginalAudioPanel from '@/components/OriginalAudioPanel.vue'
import ConvertedAudioPanel from '@/components/ConvertedAudioPanel.vue'
import PrecisionControl from '@/components/PrecisionControl.vue'
import AudioPlayer from '@/components/AudioPlayer.vue'

const voiceStore = useVoiceStore()

const handleStartOver = () => {
  voiceStore.reset()
}

const handleGenerate = async () => {
  if (!voiceStore.originalAudio) {
    message.warning('Please upload an audio file first')
    return
  }
  
  if (!voiceStore.selectedVoice) {
    message.warning('Please select a voice')
    return
  }
  
  voiceStore.isConverting = true
  
  try {
    // 直接使用 0-10 的值，后端要求 1-10，所以至少为1
    const stabilityInt = Math.max(1, voiceStore.stability)
    const similarityInt = Math.max(1, voiceStore.similarity)
    
    const response = await convertVoice(voiceStore.originalAudio.file, {
      voice_id: voiceStore.selectedVoice.id,
      stability: stabilityInt,
      similarity: similarityInt,
      output_format: 'mp3'
    })
    
    voiceStore.setConversionResult({
      taskId: response.task_id,
      status: response.status,
      outputUrl: getOutputUrl(response.output_url),
      voiceName: voiceStore.selectedVoice.name
    })
    
    message.success('Voice conversion completed!')
  } catch (error: any) {
    console.error('Conversion failed:', error)
    const status = error?.response?.status
    const detail = error?.response?.data?.detail

    const detailText = (() => {
      if (typeof detail === 'string') return detail
      if (Array.isArray(detail) && detail.length > 0) {
        const first = detail[0]
        if (first?.msg) return String(first.msg)
      }
      return undefined
    })()

    if (!status) {
      message.error(
        API_BASE_URL
          ? `Network error: cannot reach API (${API_BASE_URL}). Check Render service is live and CORS allows this Vercel domain.`
          : 'Backend not configured: set VITE_API_BASE_URL in Vercel to your Render URL, then redeploy.'
      )
    } else if (status === 404) {
      message.error(
        API_BASE_URL
          ? `API not found on server (${API_BASE_URL}). Check Render is serving the backend.`
          : 'Backend not configured (404 on /api). Set VITE_API_BASE_URL in Vercel and redeploy.'
      )
    } else {
      message.error(detailText || `Voice conversion failed (HTTP ${status})`)
    }
  } finally {
    voiceStore.isConverting = false
  }
}
</script>

<style scoped>
.home-view {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

/* Top bar */
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 18px 24px 14px;
  margin-bottom: 0px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.title {
  font-size: 20px;
  font-weight: 600;
  line-height: 24px;
  text-transform: capitalize;
  color: #0d062d;
  letter-spacing: 0;
}

.slots-pill {
  display: inline-flex;
  align-items: center;
  gap: 0;
  width: 204px;
  height: 36px;
  border: 1px solid #e1e1e1;
  border-radius: 12px;
  overflow: hidden;
}

.slots-text {
  flex: 1;
  padding: 0 10px;
  font-size: 12px;
  font-weight: 500;
  line-height: 15px;
  text-transform: capitalize;
  color: #36353a;
}

.slots-upgrade {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 5px 10px;
  height: 24px;
  background: #fed7d5;
  border-radius: 8px;
  margin-right: 6px;
  font-size: 10px;
  font-weight: 500;
  line-height: 12px;
  color: #fe655d;
}

.start-over-btn {
  color: #6b6b80;
}

.start-over-btn:hover {
  color: #fe655d;
}

/* Layout - Figma: left 418px, right fills remaining (~582px at 1440) */
.content-wrapper {
  display: grid;
  grid-template-columns: 418px 1fr;
  gap: 24px;
  flex: 1;
  overflow: hidden;
  min-height: 0;
  padding: 0 24px 16px;
}

.main-area {
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow: auto;
}

.panel {
  display: flex;
  flex-direction: column;
  flex: 1;
}

.panel-title {
  font-size: 18px;
  font-weight: 500;
  line-height: 120%;
  color: #36353a;
  margin: 4px 0 14px;
  flex-shrink: 0;
}

.audio-source-card {
  width: 100%;
  flex: 1;
  background: #fafafa;
  border: 1px solid #e1e1e1;
  border-radius: 24px;
  padding: 20px;
  display: flex;
  flex-direction: column;
}

.or-divider {
  position: relative;
  display: flex;
  justify-content: center;
  margin: 10px 0 12px;
}

.or-divider::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 0;
  right: 0;
  height: 1px;
  background: transparent;
}

.or-divider span {
  position: relative;
  z-index: 1;
  font-size: 16px;
  font-weight: 400;
  line-height: 140%;
  color: #b3b3b3;
  background: transparent;
  padding: 0;
  text-transform: none;
  letter-spacing: -0.01em;
}

/* 音频区域 */
.audio-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.audio-block {
  background: #ffffff;
  border-radius: 16px;
  padding: 20px;
  border: 1px solid #e8e8ed;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.block-header {
  margin-bottom: 16px;
}

.block-label {
  font-size: 12px;
  font-weight: 600;
  color: #9d9db5;
  letter-spacing: 1px;
}

/* 生成按钮区域 */
.generate-section {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  padding: 16px 0;
}

.generate-btn {
  height: 48px;
  padding: 0 32px;
  font-size: 16px;
  font-weight: 600;
  background: linear-gradient(135deg, #fe655d 0%, #ff8a84 100%);
  border: none;
  border-radius: 24px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.generate-btn:hover {
  background: linear-gradient(135deg, #ff8a84 0%, #fe655d 100%);
}

/* 右侧面板 */
.voice-panel {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  padding-top: 4px;
}
</style>
