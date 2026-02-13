<template>
  <a-config-provider :theme="themeConfig">
    <div class="app-shell">
      <div class="workspace">
        <!-- Left navigation (Figma-like) -->
        <aside class="sidebar">
          <div class="brand">
            <div class="brand-mark">NOIZ</div>
            <div class="brand-caret" aria-hidden="true">▾</div>
          </div>

          <div class="nav-section">
            <div class="nav-label">PROJECT</div>
            <button class="nav-link">
              <span class="nav-icon">
                <SoundOutlined />
              </span>
              <span class="nav-text">Text to Speech</span>
            </button>
            <button class="nav-link">
              <span class="nav-icon">
                <VideoCameraOutlined />
              </span>
              <span class="nav-text">Video Dubbing</span>
            </button>
          </div>

          <div class="nav-section">
            <div class="nav-label">NAVIGATION</div>
            <button class="nav-link">
              <span class="nav-icon">
                <CompassOutlined />
              </span>
              <span class="nav-text">Discover</span>
            </button>
            <button class="nav-link">
              <span class="nav-icon">
                <AudioOutlined />
              </span>
              <span class="nav-text">Voice Library</span>
            </button>
            <button class="nav-link">
              <span class="nav-icon">
                <UserSwitchOutlined />
              </span>
              <span class="nav-text">Voice Clone</span>
            </button>
            <button class="nav-link">
              <span class="nav-icon">
                <BgColorsOutlined />
              </span>
              <span class="nav-text">Voice Design</span>
            </button>
            <button class="nav-link active">
              <span class="nav-icon">
                <ThunderboltOutlined />
              </span>
              <span class="nav-text">Voice Changer</span>
            </button>
          </div>

          <div class="sidebar-spacer" />

          <div class="user-card" role="button" tabindex="0">
            <div class="user-avatar">J</div>
            <div class="user-meta">
              <div class="user-name">Viewer</div>
              <div class="user-plan">PRO</div>
            </div>
          </div>
        </aside>

        <!-- Main content -->
        <main class="main-content">
          <router-view />
        </main>
      </div>
    </div>
  </a-config-provider>
</template>

<script setup lang="ts">
import {
  AudioOutlined,
  BgColorsOutlined,
  CompassOutlined,
  SoundOutlined,
  ThunderboltOutlined,
  UserSwitchOutlined,
  VideoCameraOutlined,
} from '@ant-design/icons-vue'
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
  background-color: #f2f4f7;
  color: #1a1a2e;
  min-height: 100vh;
}

#app {
  min-height: 100vh;
}

.app-shell {
  min-height: 100vh;
  background: #f2f4f7;
}

.workspace {
  width: 100%;
  min-height: 100vh;
  display: flex;
  background: #ffffff;
}

/* Left sidebar */
.sidebar {
  width: 240px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  padding: 6px 16px 16px;
  background: #ffffff;
}

.brand {
  display: flex;
  align-items: baseline;
  gap: 8px;
  padding: 6px 0 16px;
  margin-bottom: 6px;
}

.brand-mark {
  font-weight: 900;
  letter-spacing: 0.12em;
  font-size: 14px;
  color: #fe655d;
}

.brand-caret {
  font-size: 12px;
  color: #9d9db5;
  transform: translateY(-1px);
}

.nav-section {
  width: 208px;
  margin: 0 auto;
  padding: 10px 0;
}

.nav-label {
  font-size: 12px;
  font-weight: 500;
  line-height: 15px;
  color: #b3b3b3;
  padding: 10px 10px 8px;
}

.nav-link {
  width: 100%;
  height: 40px;
  display: grid;
  grid-template-columns: 48px 1fr;
  gap: 0px;
  align-items: center;
  padding: 0px;
  border-radius: 12px;
  border: 1px solid transparent;
  background: transparent;
  color: #3a3a4a;
  cursor: pointer;
  transition: background 0.18s ease, border-color 0.18s ease, color 0.18s ease;
  text-align: left;
}

.nav-link .nav-icon {
  display: grid;
  place-items: center;
  width: 48px;
  height: 40px;
  border-radius: 12px;
  color: #36353a;
  background: transparent;
}

.nav-link .nav-text {
  font-size: 14px;
  font-weight: 500;
  line-height: 17px;
  color: #36353a;
}

.nav-link:hover {
  background: #e9ecf0;
}

.nav-link:hover .nav-icon {
  color: #36353a;
}

.nav-link.active {
  background: #e9ecf0;
  border-color: transparent;
}

.nav-link.active .nav-icon {
  background: transparent;
  color: #36353a;
}

.sidebar-spacer {
  flex: 1;
}

.user-card {
  width: 208px;
  height: 71px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 12px;
  border: 1px solid #ffffff;
  background: #ffffff;
  border-radius: 16px;
  cursor: pointer;
}

.user-avatar {
  width: 34px;
  height: 34px;
  border-radius: 12px;
  display: grid;
  place-items: center;
  font-weight: 800;
  color: #ffffff;
  background: linear-gradient(135deg, #fe655d 0%, #ff8a84 100%);
}

.user-name {
  font-size: 13px;
  font-weight: 500;
  color: #36353a;
  line-height: 24px;
}

.user-plan {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 26px;
  height: 16px;
  margin-top: -6px;
  font-size: 10px;
  font-weight: 600;
  line-height: 24px;
  color: #ffffff;
  background: #fe655d;
  border-radius: 4px;
  box-shadow: 0px 2px 4px rgba(254, 101, 93, 0.3);
  letter-spacing: 0;
}

/* Main content */
.main-content {
  flex: 1;
  padding: 0;
  overflow: hidden;
  background: #ffffff;
  border-radius: 24px 0 0 0;
  box-shadow: 0px 2px 20px rgba(0, 0, 0, 0.06);
  min-width: 0;
}
</style>
