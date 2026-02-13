import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Voice, AudioFile, ConversionResult } from '@/types'
import {
  voiceLibraryTopFixed,
  voiceLibraryExplore,
  voiceLibraryFavorites,
  voiceLibraryMyVoices,
  voiceLibraryCreateMyVoice,
  voiceLibraryUpdateFavorites,
  type VoiceLibraryVoice
} from '@/api'

export const useVoiceStore = defineStore('voice', () => {
  // 声音列表（来自后端 voice-library）
  const voices = ref<Voice[]>([])
  
  // 当前选中的声音
  const selectedVoice = ref<Voice | null>(null)
  
  // 收藏的声音ID列表（与后端 favorites 同步）
  const favoriteVoiceIds = ref<string[]>([])
  
  // 原始音频文件
  const originalAudio = ref<AudioFile | null>(null)
  
  // 转换后的结果
  const conversionResult = ref<ConversionResult | null>(null)
  
  // 转换参数 (0-10)
  const stability = ref(5)
  const similarity = ref(8)
  
  // 加载状态
  const isConverting = ref(false)
  const isUploading = ref(false)
  
  // 当前标签页
  const activeTab = ref<'featured' | 'all' | 'favorites' | 'my_voices'>('featured')
  
  // 搜索关键词
  const searchKeyword = ref('')

  const isLoadingVoices = ref(false)

  function emojiForVoice(v: VoiceLibraryVoice): string {
    const type = String(v.voice_type || '').toLowerCase()
    if (type === 'user') return '🧩'
    const vid = String(v.voice_id || '')
    if (vid.indexOf('uwu') >= 0) return '✨'
    if (vid.indexOf('anime') >= 0) return '🎭'
    if (vid.indexOf('mamba') >= 0) return '🏀'
    if (vid.indexOf('nerd') >= 0) return '🤓'
    return '🎙️'
  }

  function mapVoiceLibraryVoice(v: VoiceLibraryVoice, featured = false): Voice {
    const g = String(v.gender || '').toLowerCase()
    const gender: any = g === 'male' ? 'male' : g === 'female' ? 'female' : 'unknown'
    return {
      id: v.voice_id,
      name: v.display_name,
      description: (v.voice_description as any) || '',
      gender,
      avatar: emojiForVoice(v),
      isFeatured: featured,
      isFavorited: Boolean((v as any).is_favorited),
      voiceType: v.voice_type
    }
  }

  async function fetchVoices() {
    isLoadingVoices.value = true
    try {
      const keyword = (searchKeyword.value || '').trim()
      if (activeTab.value === 'featured' && !keyword) {
        const data = await voiceLibraryTopFixed('en')
        voices.value = (data.voices || []).map((v) => mapVoiceLibraryVoice(v, true))
      } else if (activeTab.value === 'my_voices') {
        const data = await voiceLibraryMyVoices({ keyword: keyword || undefined, sort: 'latest', skip: 0, limit: 50 })
        voices.value = (data.voices || []).map((v) => mapVoiceLibraryVoice(v, false))
      } else if (activeTab.value === 'favorites') {
        const data = await voiceLibraryFavorites({ keyword: keyword || undefined, sort: 'latest', skip: 0, limit: 50 })
        voices.value = (data.voices || []).map((v) => mapVoiceLibraryVoice(v, false))
      } else {
        const data = await voiceLibraryExplore({ keyword: keyword || undefined, sort: 'mostUsers', skip: 0, limit: 50 })
        voices.value = (data.voices || []).map((v) => mapVoiceLibraryVoice(v, false))
      }

      // Sync favorite ids from server flags
      favoriteVoiceIds.value = voices.value.filter((v: Voice) => Boolean(v.isFavorited)).map((v: Voice) => v.id)

      // Keep selection valid
      if (voices.value.length > 0) {
        if (!selectedVoice.value || !voices.value.some((x: Voice) => x.id === selectedVoice.value?.id)) {
          selectedVoice.value = voices.value[0] ?? null
        }
      }
    } finally {
      isLoadingVoices.value = false
    }
  }
  
  // 过滤后的声音列表
  const filteredVoices = computed(() => {
    // Voices are already fetched server-side based on tab/query.
    // Keep a tiny client-side fallback filter in case the server returns a superset.
    let result = voices.value
    if (searchKeyword.value) {
      const keyword = searchKeyword.value.toLowerCase()
      result = result.filter((v: Voice) => (v.name || '').toLowerCase().indexOf(keyword) >= 0 || (v.description || '').toLowerCase().indexOf(keyword) >= 0)
    }
    return result
  })
  
  // 选择声音
  function selectVoice(voice: Voice) {
    selectedVoice.value = voice
  }
  
  // 切换收藏
  async function toggleFavorite(voiceId: string) {
    const isFav = favoriteVoiceIds.value.includes(voiceId)
    const next = !isFav
    await voiceLibraryUpdateFavorites([voiceId], next)
    // Update local state immediately
    if (next) {
      if (!favoriteVoiceIds.value.includes(voiceId)) favoriteVoiceIds.value.push(voiceId)
    } else {
      favoriteVoiceIds.value = favoriteVoiceIds.value.filter((x: string) => x !== voiceId)
    }
    voices.value = voices.value.map((v: Voice) => (v.id === voiceId ? { ...v, isFavorited: next } : v))

    // If we are on the favorites tab, refresh from server.
    if (activeTab.value === 'favorites') {
      await fetchVoices()
    }
  }

  async function createMyVoice(displayName: string) {
    const name = (displayName || '').trim()
    if (!name) return
    // Select a built-in base voice for conversion; if currently selected is a user_ voice, fallback.
    const selectedId = selectedVoice.value?.id ? String(selectedVoice.value.id) : ''
    const baseVoiceId = selectedId && selectedId.indexOf('user_') !== 0 ? selectedId : 'anime_uncle'
    await voiceLibraryCreateMyVoice({
      display_name: name,
      base_voice_id: baseVoiceId,
      is_public: false
    })

    // After creating, refresh list and ensure we're on My Voices.
    activeTab.value = 'my_voices'
    await fetchVoices()
  }
  
  // 设置原始音频
  function setOriginalAudio(audio: AudioFile | null) {
    originalAudio.value = audio
    conversionResult.value = null
  }
  
  // 设置转换结果
  function setConversionResult(result: ConversionResult | null) {
    conversionResult.value = result
  }
  
  // 重置所有状态
  function reset() {
    originalAudio.value = null
    conversionResult.value = null
    isConverting.value = false
    isUploading.value = false
  }
  
  return {
    voices,
    selectedVoice,
    favoriteVoiceIds,
    originalAudio,
    conversionResult,
    stability,
    similarity,
    isConverting,
    isUploading,
    activeTab,
    searchKeyword,
    isLoadingVoices,
    filteredVoices,
    selectVoice,
    toggleFavorite,
    fetchVoices,
    createMyVoice,
    setOriginalAudio,
    setConversionResult,
    reset
  }
})
