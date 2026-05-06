<template>
  <router-view />
</template>

<script setup>
// 这里不需要写逻辑，逻辑都在各个 views 页面里
</script>

<style>
/* 全局样式：去除默认的 margin，让页面占满屏幕 */
html, body, #app {
  margin: 0;
  padding: 0;
  height: 100%;
  width: 100%;
}
</style>
