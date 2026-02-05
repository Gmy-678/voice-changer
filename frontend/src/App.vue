<template>
  <a-config-provider :theme="themeConfig">
    <div class="app-container">
      <!-- 左侧边栏 -->
      <aside class="sidebar">
        <div class="logo">
          <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
            <circle cx="16" cy="16" r="14" stroke="url(#gradient)" stroke-width="2"/>
            <path d="M12 10L22 16L12 22V10Z" fill="url(#gradient)"/>
            <defs>
              <linearGradient id="gradient" x1="0" y1="0" x2="32" y2="32">
                <stop offset="0%" stop-color="#fe655d"/>
                <stop offset="100%" stop-color="#ff8a84"/>
              </linearGradient>
            </defs>
          </svg>
        </div>
        <nav class="nav-menu">
          <a-tooltip placement="right" title="Home">
            <div class="nav-item active">
              <HomeOutlined />
            </div>
          </a-tooltip>
          <a-tooltip placement="right" title="Voice Library">
            <div class="nav-item">
              <AudioOutlined />
            </div>
          </a-tooltip>
          <a-tooltip placement="right" title="History">
            <div class="nav-item">
              <HistoryOutlined />
            </div>
          </a-tooltip>
          <a-tooltip placement="right" title="Settings">
            <div class="nav-item">
              <SettingOutlined />
            </div>
          </a-tooltip>
        </nav>
      </aside>
      
      <!-- 主内容区 -->
      <main class="main-content">
        <router-view />
      </main>
    </div>
  </a-config-provider>
</template>

<script setup lang="ts">
import { HomeOutlined, AudioOutlined, HistoryOutlined, SettingOutlined } from '@ant-design/icons-vue'
import type { ThemeConfig } from 'ant-design-vue/es/config-provider/context'

const themeConfig: ThemeConfig = {
  token: {
    colorPrimary: '#fe655d',
    colorBgContainer: '#ffffff',
    colorBgElevated: '#f8f8fa',
    colorText: '#1a1a2e',
    colorTextSecondary: '#6b6b80',
    borderRadius: 12,
  },
  algorithm: undefined
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background-color: #f5f5f7;
  color: #1a1a2e;
  min-height: 100vh;
}

#app {
  min-height: 100vh;
}

.app-container {
  display: flex;
  min-height: 100vh;
}

/* 左侧边栏 */
.sidebar {
  width: 72px;
  background: linear-gradient(180deg, #ffffff 0%, #f8f8fa 100%);
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px 0;
  border-right: 1px solid #e8e8ed;
}

.logo {
  margin-bottom: 40px;
}

.nav-menu {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.nav-item {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  cursor: pointer;
  color: #9d9db5;
  font-size: 20px;
  transition: all 0.2s ease;
}

.nav-item:hover {
  background: #ffd1ce;
  color: #fe655d;
}

.nav-item.active {
  background: linear-gradient(135deg, #fe655d 0%, #ff8a84 100%);
  color: #ffffff;
}

/* 主内容区 */
.main-content {
  flex: 1;
  padding: 24px;
  overflow-y: auto;
}
</style>
