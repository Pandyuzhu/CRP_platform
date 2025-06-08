<template>
  <v-app>
    <NavBar />
    <v-main class="main-background">
      <router-view />
    </v-main>
  </v-app>
</template>

<script>
import NavBar from './components/common/NavBar.vue';

export default {
  name: 'App',
  components: {
    NavBar
  }
}
</script>

<style>
.main-background {
  background: #000;
  min-height: 100vh;
  position: relative;
}

/* Custom scrollbar */
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

::-webkit-scrollbar-track {
  background: rgba(0, 0, 0, 0.1);
}

::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.2);
  border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.3);
}
</style> 