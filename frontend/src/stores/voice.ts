import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Voice, AudioFile, ConversionResult } from '@/types'

export const useVoiceStore = defineStore('voice', () => {
  // 声音列表 - 5个美国热搜榜音色
  const voices = ref<Voice[]>([
    { 
      id: 'anime_uncle', 
      name: 'Anime Uncle', 
      description: '🎭 Exaggerated deep anime voice, NANI?!', 
      gender: 'male', 
      avatar: '🎭', 
      isFeatured: true 
    },
    { 
      id: 'uwu_anime', 
      name: 'UwU Anime', 
      description: '✨ Kawaii desu~ 二次元萌音', 
      gender: 'female', 
      avatar: '✨', 
      isFeatured: true 
    },
    { 
      id: 'gender_swap', 
      name: 'Gender Swap', 
      description: '🦋 Male to Female transformation~', 
      gender: 'female', 
      avatar: '🦋', 
      isFeatured: true 
    },
    { 
      id: 'mamba', 
      name: 'Mamba Mode', 
      description: '🏀 Kobe! Mamba mentality voice', 
      gender: 'male', 
      avatar: '🏀', 
      isFeatured: true 
    },
    { 
      id: 'nerd_bro', 
      name: 'Nerd Bro', 
      description: '🤓 Actually... *pushes glasses* tech bro vibes', 
      gender: 'male', 
      avatar: '🤓', 
      isFeatured: true 
    },
  ])
  
  // 当前选中的声音
  const selectedVoice = ref<Voice | null>(voices.value[0] ?? null)
  
  // 收藏的声音ID列表
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
  const activeTab = ref<'featured' | 'all' | 'favorites'>('featured')
  
  // 搜索关键词
  const searchKeyword = ref('')
  
  // 过滤后的声音列表
  const filteredVoices = computed(() => {
    let result = voices.value
    
    // 按标签页过滤
    if (activeTab.value === 'featured') {
      result = result.filter(v => v.isFeatured)
    } else if (activeTab.value === 'favorites') {
      result = result.filter(v => favoriteVoiceIds.value.includes(v.id))
    }
    
    // 按关键词过滤
    if (searchKeyword.value) {
      const keyword = searchKeyword.value.toLowerCase()
      result = result.filter(v => 
        v.name.toLowerCase().includes(keyword) || 
        v.description.toLowerCase().includes(keyword)
      )
    }
    
    return result
  })
  
  // 选择声音
  function selectVoice(voice: Voice) {
    selectedVoice.value = voice
  }
  
  // 切换收藏
  function toggleFavorite(voiceId: string) {
    const index = favoriteVoiceIds.value.indexOf(voiceId)
    if (index > -1) {
      favoriteVoiceIds.value.splice(index, 1)
    } else {
      favoriteVoiceIds.value.push(voiceId)
    }
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
    filteredVoices,
    selectVoice,
    toggleFavorite,
    setOriginalAudio,
    setConversionResult,
    reset
  }
})
