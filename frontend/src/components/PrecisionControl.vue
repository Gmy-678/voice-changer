<template>
  <a-popover 
    v-model:open="isOpen"
    trigger="click"
    placement="top"
    overlayClassName="precision-popover"
  >
    <template #content>
      <div class="precision-panel">
        <h4 class="panel-title">Precision Control</h4>
        
        <div class="slider-group">
          <div class="slider-header">
            <span class="slider-label">Stability</span>
            <span class="slider-value">{{ voiceStore.stability }}</span>
          </div>
          <a-slider 
            v-model:value="voiceStore.stability"
            :min="0"
            :max="10"
            :step="1"
            :tooltip="{ open: false }"
          />
          <div class="slider-hints">
            <span>More Variable</span>
            <span>More Stable</span>
          </div>
        </div>
        
        <div class="slider-group">
          <div class="slider-header">
            <span class="slider-label">Similarity</span>
            <span class="slider-value">{{ voiceStore.similarity }}</span>
          </div>
          <a-slider 
            v-model:value="voiceStore.similarity"
            :min="0"
            :max="10"
            :step="1"
            :tooltip="{ open: false }"
          />
          <div class="slider-hints">
            <span>Low</span>
            <span>High</span>
          </div>
        </div>
      </div>
    </template>
    
    <a-button shape="circle" class="control-btn">
      <SettingOutlined />
    </a-button>
  </a-popover>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { SettingOutlined } from '@ant-design/icons-vue'
import { useVoiceStore } from '@/stores/voice'

const voiceStore = useVoiceStore()
const isOpen = ref(false)
</script>

<style scoped>
.control-btn {
  width: 48px;
  height: 48px;
  background: #ffffff;
  border: 1px solid #e8e8ed;
  color: #6b6b80;
  font-size: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.control-btn:hover {
  background: #ffd1ce;
  border-color: #fe655d;
  color: #fe655d;
}

.precision-panel {
  width: 280px;
  padding: 8px;
}

.panel-title {
  font-size: 14px;
  font-weight: 600;
  color: #1a1a2e;
  margin-bottom: 20px;
}

.slider-group {
  margin-bottom: 20px;
}

.slider-group:last-child {
  margin-bottom: 0;
}

.slider-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.slider-label {
  font-size: 13px;
  color: #6b6b80;
}

.slider-value {
  font-size: 13px;
  font-weight: 600;
  color: #fe655d;
}

.slider-hints {
  display: flex;
  justify-content: space-between;
  margin-top: 4px;
  font-size: 11px;
  color: #9d9db5;
}
</style>

<style>
.precision-popover .ant-popover-inner {
  background: #ffffff !important;
  border: 1px solid #e8e8ed;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.precision-popover .ant-popover-arrow::before {
  background: #ffffff !important;
}

.precision-popover .ant-slider-track {
  background: linear-gradient(90deg, #fe655d 0%, #ff8a84 100%) !important;
}

.precision-popover .ant-slider-handle::after {
  background: #fe655d !important;
  box-shadow: 0 0 0 2px #fe655d !important;
}

.precision-popover .ant-slider-rail {
  background: #e8e8ed !important;
}
</style>
