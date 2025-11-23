<script setup lang="ts">
</script>

<template>
  <router-view></router-view>
</template>

<style>
/* 注意：这里不要加 scoped，我们需要修改全局 body 样式 */
body {
  margin: 0;
  padding: 0;
  width: 100%;
  height: 100%;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
}

#app {
  width: 100%;
  height: 100%;
}
</style>