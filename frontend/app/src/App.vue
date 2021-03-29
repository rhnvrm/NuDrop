<template>
  <div id="app" class="container">
    <Navbar/>
    <section>
      <div class="container">
      <router-view></router-view>
      </div>
    </section>
    <Footer/>
  </div>
</template>

<script>
import Navbar from './components/Navbar.vue'
import Footer from './components/Footer.vue'
import './styles/theme.scss'
import './styles/app.scss'

export default {
  name: 'App',
  components: {
    Navbar,
    Footer
  }
}
</script>

