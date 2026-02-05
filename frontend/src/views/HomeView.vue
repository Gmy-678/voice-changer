<template>
  <div class="home-view">
    <!-- 顶部标题栏 -->
    <header class="header">
      <div class="header-left">
        <h1 class="title">CoralVoice Studio</h1>
        <a-select v-model:value="selectedDevice" class="device-select" size="small">
          <a-select-option value="default">Device</a-select-option>
        </a-select>
      </div>
      <div class="header-right">
        <a-button type="text" class="start-over-btn" @click="handleStartOver" v-if="voiceStore.originalAudio">
          <RedoOutlined /> Start Over
        </a-button>
      </div>
    </header>
    
    <!-- 主要内容区 -->
    <div class="content-wrapper">
      <div class="main-area">
        <!-- 初始状态：上传/录制 -->
        <template v-if="!voiceStore.originalAudio">
          <div class="upload-section">
            <AudioUpload />
            <AudioRecord />
          </div>
          <div class="tip-text">
            <BulbOutlined /> Tip: Select a voice from the right panel to customize your result.
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
import { ref } from 'vue'
import { RedoOutlined, BulbOutlined, ThunderboltOutlined } from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import { useVoiceStore } from '@/stores/voice'
import { convertVoice } from '@/api'
import AudioUpload from '@/components/AudioUpload.vue'
import AudioRecord from '@/components/AudioRecord.vue'
import VoiceSelector from '@/components/VoiceSelector.vue'
import OriginalAudioPanel from '@/components/OriginalAudioPanel.vue'
import ConvertedAudioPanel from '@/components/ConvertedAudioPanel.vue'
import PrecisionControl from '@/components/PrecisionControl.vue'
import AudioPlayer from '@/components/AudioPlayer.vue'

const voiceStore = useVoiceStore()
const selectedDevice = ref('default')

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
      outputUrl: response.output_url,
      voiceName: voiceStore.selectedVoice.name
    })
    
    message.success('Voice conversion completed!')
  } catch (error: any) {
    console.error('Conversion failed:', error)
    message.error(error.response?.data?.detail || 'Voice conversion failed')
  } finally {
    voiceStore.isConverting = false
  }
}
</script>

<style scoped>
.home-view {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 48px);
}

/* 顶部标题栏 */
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.title {
  font-size: 24px;
  font-weight: 600;
  background: linear-gradient(135deg, #fe655d 0%, #ff8a84 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.device-select {
  background: #ffffff;
  border-radius: 8px;
}

.device-select :deep(.ant-select-selector) {
  background: #ffffff !important;
  border: 1px solid #e8e8ed !important;
  color: #6b6b80;
}

.start-over-btn {
  color: #6b6b80;
}

.start-over-btn:hover {
  color: #fe655d;
}

/* 内容包装器 */
.content-wrapper {
  display: flex;
  flex: 1;
  gap: 24px;
  overflow: hidden;
}

.main-area {
  flex: 1;
  display: flex;
  flex-direction: column;
}

/* 上传区域 */
.upload-section {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  margin-bottom: 24px;
}

.tip-text {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #6b6b80;
  font-size: 14px;
  padding: 12px 16px;
  background: #ffd1ce;
  border-radius: 8px;
  border: 1px solid rgba(254, 101, 93, 0.2);
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
  width: 320px;
  flex-shrink: 0;
}
</style>
