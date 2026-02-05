<template>
  <div class="voice-selector">
    <div class="selector-header">
      <h3 class="selector-title">Select Voice</h3>
      <a-input-search
        v-model:value="voiceStore.searchKeyword"
        placeholder="Search voices..."
        class="search-input"
        allow-clear
      />
    </div>
    
    <!-- 标签切换 -->
    <div class="tabs">
      <button 
        v-for="tab in tabs" 
        :key="tab.key"
        class="tab-btn"
        :class="{ active: voiceStore.activeTab === tab.key }"
        @click="voiceStore.activeTab = tab.key"
      >
        {{ tab.label }}
      </button>
    </div>
    
    <!-- 声音列表 -->
    <div class="voice-list">
      <div
        v-for="voice in voiceStore.filteredVoices"
        :key="voice.id"
        class="voice-item"
        :class="{ selected: voiceStore.selectedVoice?.id === voice.id }"
        @click="voiceStore.selectVoice(voice)"
      >
        <div class="voice-avatar">
          <span v-if="voice.avatar" class="avatar-emoji">{{ voice.avatar }}</span>
          <a-button 
            v-else
            type="text" 
            shape="circle" 
            class="play-btn"
            @click.stop="playVoicePreview(voice.id)"
          >
            <PlayCircleOutlined />
          </a-button>
        </div>
        <div class="voice-info">
          <div class="voice-name">{{ voice.name }}</div>
          <div class="voice-desc">{{ voice.description }}</div>
        </div>
        <div class="voice-meta">
          <a-tag :color="voice.gender === 'male' ? 'blue' : 'pink'" size="small">
            {{ voice.gender === 'male' ? 'Male' : 'Female' }}
          </a-tag>
          <a-button 
            type="text" 
            size="small"
            class="favorite-btn"
            @click.stop="voiceStore.toggleFavorite(voice.id)"
          >
            <HeartFilled v-if="voiceStore.favoriteVoiceIds.includes(voice.id)" style="color: #ff4d4f;" />
            <HeartOutlined v-else />
          </a-button>
        </div>
      </div>
      
      <!-- 空状态 -->
      <div v-if="voiceStore.filteredVoices.length === 0" class="empty-state">
        <InboxOutlined />
        <p>No voices found</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { PlayCircleOutlined, HeartOutlined, HeartFilled, InboxOutlined } from '@ant-design/icons-vue'
import { useVoiceStore } from '@/stores/voice'

const voiceStore = useVoiceStore()

const tabs = [
  { key: 'featured' as const, label: 'Featured' },
  { key: 'all' as const, label: 'All Voices' },
  { key: 'favorites' as const, label: 'Favorites' }
]

const playVoicePreview = (voiceId: string) => {
  // TODO: 播放声音预览
  console.log('Preview voice:', voiceId)
}
</script>

<style scoped>
.voice-selector {
  background: #ffffff;
  border-radius: 16px;
  padding: 20px;
  height: 100%;
  display: flex;
  flex-direction: column;
  border: 1px solid #e8e8ed;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.selector-header {
  margin-bottom: 16px;
}

.selector-title {
  font-size: 16px;
  font-weight: 600;
  color: #1a1a2e;
  margin-bottom: 12px;
}

.search-input {
  width: 100%;
}

.search-input :deep(.ant-input) {
  background: #f8f8fa;
  border-color: #e8e8ed;
  color: #1a1a2e;
}

.search-input :deep(.ant-input::placeholder) {
  color: #9d9db5;
}

.search-input :deep(.ant-input-search-button) {
  background: #f8f8fa;
  border-color: #e8e8ed;
}

/* 标签切换 */
.tabs {
  display: flex;
  gap: 4px;
  margin-bottom: 16px;
  background: #f5f5f7;
  padding: 4px;
  border-radius: 8px;
}

.tab-btn {
  flex: 1;
  padding: 8px 12px;
  border: none;
  background: transparent;
  color: #6b6b80;
  font-size: 13px;
  font-weight: 500;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.tab-btn:hover {
  color: #fe655d;
  background: #ffd1ce;
}

.tab-btn.active {
  background: #fe655d;
  color: #ffffff;
}

/* 声音列表 */
.voice-list {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.voice-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: #f8f8fa;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
  border: 2px solid transparent;
}

.voice-item:hover {
  background: #f0f0f5;
}

.voice-item.selected {
  border-color: #fe655d;
  background: rgba(254, 101, 93, 0.08);
}

.voice-avatar {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #ffd1ce;
  border-radius: 10px;
}

.avatar-emoji {
  font-size: 24px;
  line-height: 1;
}

.play-btn {
  color: #fe655d;
  font-size: 20px;
}

.voice-info {
  flex: 1;
  min-width: 0;
}

.voice-name {
  font-size: 14px;
  font-weight: 600;
  color: #1a1a2e;
  margin-bottom: 2px;
}

.voice-desc {
  font-size: 12px;
  color: #9d9db5;
}

.voice-meta {
  display: flex;
  align-items: center;
  gap: 4px;
}

.favorite-btn {
  color: #9d9db5;
}

.favorite-btn:hover {
  color: #ff4d4f;
}

/* 空状态 */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  color: #9d9db5;
  font-size: 32px;
}

.empty-state p {
  margin-top: 12px;
  font-size: 14px;
}
</style>
