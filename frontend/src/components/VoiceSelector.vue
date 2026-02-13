<template>
  <div class="voice-selector">
    <!-- Selected voice -->
    <div class="selected-block">
      <div class="block-title">Selected Voice</div>
      <button class="selected-card" type="button" @click="openSelectedVoice">
        <div class="selected-avatar">
          <span v-if="voiceStore.selectedVoice?.avatar">{{ voiceStore.selectedVoice.avatar }}</span>
          <span v-else class="dot" />
        </div>
        <div class="selected-info">
          <div class="selected-name">
            {{ voiceStore.selectedVoice?.name || 'Pick a voice from the list' }}
          </div>
          <div class="selected-desc">
            {{ voiceStore.selectedVoice?.description || 'Your choice will be used for conversion.' }}
          </div>
        </div>
      </button>
    </div>

    <!-- Choose a voice header -->
    <div class="choose-header">
      <div class="choose-title">Choose a Voice</div>
      <a-button type="text" class="view-library" @click="viewVoiceLibrary">
        View Voice Library →
      </a-button>
    </div>

    <!-- Tabs -->
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

    <!-- Search / filter -->
    <div class="search-row">
      <a-input
        v-model:value="voiceStore.searchKeyword"
        placeholder="Search..."
        allow-clear
        class="search-input"
      >
        <template #prefix>
          <SearchOutlined />
        </template>
      </a-input>
      <a-button class="filter-btn" @click="openFilter">
        <FilterOutlined /> Filter
      </a-button>
    </div>

    <!-- My voices: create form -->
    <div v-if="voiceStore.activeTab === 'my_voices'" class="create-my-voice">
      <div class="create-title">Create my voice</div>
      <div class="create-row">
        <a-input
          v-model:value="myVoiceName"
          placeholder="输入一个音色名称（例如：我的旁白）"
          class="create-input"
          @keyup.enter="submitCreate"
        />
        <a-button type="primary" class="create-btn" @click="submitCreate" :loading="creating">
          添加
        </a-button>
      </div>
      <div class="create-hint">最小可用版本：先创建元数据（绑定基底音色），后续可扩展训练/上传。</div>
    </div>
    
    <!-- 声音列表 -->
    <div class="voice-list">
      <div v-if="voiceStore.isLoadingVoices" class="loading-state">
        Loading voices...
      </div>
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
          <div class="voice-tags">
            <span class="voice-tag" v-for="tag in getVoiceTags(voice)" :key="tag">{{ tag }}</span>
          </div>
        </div>
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
      
      <!-- 空状态 -->
      <div v-if="voiceStore.filteredVoices.length === 0" class="empty-state">
        <InboxOutlined />
        <p>No voices found</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { PlayCircleOutlined, HeartOutlined, HeartFilled, InboxOutlined, SearchOutlined, FilterOutlined } from '@ant-design/icons-vue'
import { onMounted, watch, ref } from 'vue'
import { useVoiceStore } from '@/stores/voice'

const voiceStore = useVoiceStore()

const myVoiceName = ref('')
const creating = ref(false)

const tabs = [
  { key: 'featured' as const, label: 'Recommend' },
  { key: 'my_voices' as const, label: 'My Voices' },
  { key: 'favorites' as const, label: 'Favorite' }
]

const submitCreate = async () => {
  const name = (myVoiceName.value || '').trim()
  if (!name) return
  creating.value = true
  try {
    await voiceStore.createMyVoice(name)
    myVoiceName.value = ''
  } finally {
    creating.value = false
  }
}

const getVoiceTags = (voice: any): string[] => {
  const tags: string[] = []
  if (voice.description) {
    const parts = voice.description.split(/[,\s]+/).filter((s: string) => s.length > 0).slice(0, 5)
    tags.push(...parts)
  }
  if (tags.length === 0) {
    if (voice.gender === 'male') tags.push('Male')
    else if (voice.gender === 'female') tags.push('Female')
    tags.push('Voice')
  }
  return tags
}

const playVoicePreview = (voiceId: string) => {
  // TODO: 播放声音预览
  console.log('Preview voice:', voiceId)
}

const openSelectedVoice = () => {
  // no-op for now (keeps interaction affordance like Figma)
}

const viewVoiceLibrary = () => {
  // TODO: route to library when page exists
  console.log('View voice library')
}

const openFilter = () => {
  // TODO: add filter UI later
  console.log('Open filter')
}

onMounted(() => {
  voiceStore.fetchVoices().catch(() => {
    // best-effort
  })
})

watch(
  () => voiceStore.activeTab,
  () => {
    voiceStore.fetchVoices().catch(() => {
      // best-effort
    })
  }
)

watch(
  () => voiceStore.searchKeyword,
  () => {
    voiceStore.fetchVoices().catch(() => {
      // best-effort
    })
  }
)
</script>

<style scoped>
.voice-selector {
  width: 100%;
  background: transparent;
  border-radius: 0;
  padding: 0;
  height: 100%;
  display: flex;
  flex-direction: column;
  border: none;
  box-shadow: none;
}

.selected-block {
  margin-bottom: 14px;
}

.block-title {
  font-size: 16px;
  font-weight: 500;
  line-height: 19px;
  text-transform: capitalize;
  color: #36353a;
  letter-spacing: 0;
  margin-bottom: 12px;
}

.selected-card {
  width: 100%;
  display: flex;
  gap: 12px;
  align-items: center;
  height: 72px;
  padding: 16px;
  border-radius: 16px;
  border: none;
  position: relative;
  background: #fafafa;
  box-shadow:
    1px 4px 8px rgba(254, 101, 93, 0.16),
    3px 1px 8px rgba(151, 213, 247, 0.16);
  cursor: pointer;
  text-align: left;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}

.selected-card::before {
  content: '';
  position: absolute;
  inset: -1px;
  border-radius: 17px;
  padding: 1px;
  background: linear-gradient(135deg, #97d5f7, #d297ff, #fe655d);
  -webkit-mask:
    linear-gradient(#fff 0 0) content-box,
    linear-gradient(#fff 0 0);
  -webkit-mask-composite: xor;
  mask-composite: exclude;
  pointer-events: none;
}

.selected-card:hover {
  transform: translateY(-1px);
}

.selected-avatar {
  width: 40px;
  height: 40px;
  border-radius: 14px;
  display: grid;
  place-items: center;
  background: #d9d9d9;
  border: 1px solid #ffffff;
  color: #36353a;
  flex-shrink: 0;
  font-size: 20px;
}

.dot {
  width: 14px;
  height: 14px;
  border-radius: 999px;
  background: linear-gradient(135deg, #fe655d 0%, #ff8a84 100%);
}

.selected-info {
  min-width: 0;
}

.selected-name {
  font-size: 14px;
  font-weight: 500;
  color: #36353a;
  margin-bottom: 2px;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.selected-desc {
  font-size: 10px;
  font-weight: 400;
  line-height: 12px;
  color: #7d7d7d;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.choose-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin: 18px 0 10px;
}

.choose-title {
  font-size: 18px;
  font-weight: 500;
  line-height: 120%;
  color: #36353a;
}

.view-library {
  padding: 0 6px;
  height: auto;
  color: #36353a;
  font-weight: 600;
  font-size: 14px;
  line-height: 17px;
}

.view-library:hover {
  color: #fe655d;
}

.tabs {
  display: flex;
  gap: 16px;
  margin-bottom: 18px;
}

.tab-btn {
  flex: 0 0 auto;
  padding: 0;
  border: none;
  background: transparent;
  color: #b3b3b3;
  font-size: 16px;
  font-weight: 600;
  line-height: 19px;
  border-radius: 0;
  cursor: pointer;
  transition: color 0.15s ease;
}

.tab-btn:hover {
  color: #36353a;
}

.tab-btn.active {
  color: #36353a;
}

.search-row {
  display: flex;
  gap: 10px;
  align-items: center;
  margin-bottom: 16px;
}

.search-input {
  flex: 1;
}

.search-input :deep(.ant-input) {
  height: 36px;
  background: #ffffff;
  border-color: #e9ebf0;
  border-radius: 16px;
  color: #1a1a2e;
}

.search-input :deep(.ant-input::placeholder) {
  color: #9d9db5;
}

.filter-btn {
  width: 100px;
  height: 36px;
  border-radius: 16px;
  border-color: #e9ebf0;
  background: #ffffff;
  color: #36353a;
  font-weight: 500;
  font-size: 14px;
  line-height: 17px;
}

.filter-btn:hover {
  border-color: rgba(54, 53, 58, 0.18);
  color: #36353a;
}

/* Create */
.create-my-voice {
  margin-bottom: 12px;
  padding: 12px;
  border-radius: 14px;
  border: 1px solid #ececf3;
  background: #ffffff;
}

.create-title {
  font-size: 11px;
  font-weight: 800;
  color: #6b6b80;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  margin-bottom: 8px;
}

.create-row {
  display: flex;
  gap: 8px;
  align-items: center;
}

.create-input {
  flex: 1;
}

.create-btn {
  flex-shrink: 0;
}

.create-hint {
  margin-top: 8px;
  font-size: 12px;
  color: #9d9db5;
  line-height: 1.4;
}

/* 声音列表 */
.voice-list {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.loading-state {
  padding: 10px 12px;
  border: 1px dashed #e8e8ed;
  border-radius: 12px;
  background: #ffffff;
  color: #6b6b80;
  font-size: 13px;
}

.voice-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  background: #fafafa;
  border-radius: 12px;
  cursor: pointer;
  transition: transform 0.15s ease, box-shadow 0.15s ease, border-color 0.15s ease;
  border: none;
  width: 100%;
  min-height: 68px;
}

.voice-item:hover {
  transform: translateY(-1px);
  box-shadow: 0px 1px 10px rgba(0, 0, 0, 0.06);
}

.voice-item.selected {
  min-height: 72px;
  border-radius: 16px;
  position: relative;
  background: #fafafa;
  box-shadow:
    1px 4px 8px rgba(254, 101, 93, 0.16),
    3px 1px 8px rgba(151, 213, 247, 0.16);
}

.voice-item.selected::before {
  content: '';
  position: absolute;
  inset: -1px;
  border-radius: 17px;
  padding: 1px;
  background: linear-gradient(135deg, #97d5f7, #d297ff, #fe655d);
  -webkit-mask:
    linear-gradient(#fff 0 0) content-box,
    linear-gradient(#fff 0 0);
  -webkit-mask-composite: xor;
  mask-composite: exclude;
  pointer-events: none;
}

.voice-avatar {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(254, 101, 93, 0.1);
  border: 1px solid rgba(254, 101, 93, 0.14);
  border-radius: 14px;
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

.voice-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-top: 4px;
}

.voice-tag {
  display: inline-flex;
  align-items: center;
  height: 18px;
  padding: 0 6px;
  background: #eff0f2;
  border-radius: 4px;
  font-size: 10px;
  font-weight: 400;
  line-height: 12px;
  color: #7d7d7d;
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
