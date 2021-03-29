import '@mdi/font/css/materialdesignicons.css'
import 'inter-ui/inter.css'
import Buefy from 'buefy'
import Vue from 'vue'
import VueRouter from 'vue-router'
import App from './App.vue'
import Encrypt from './components/Encrypt.vue'
import Home from './components/Home.vue'

Vue.config.productionTip = false
Vue.use(Buefy)
Vue.use(VueRouter)

const routes = [
  { path: '/', component: Home },
  { path: '/encrypt', component: Encrypt },
]

const router = new VueRouter({
  routes // short for `routes: routes`
})

new Vue({
  render: h => h(App),
  router: router,
}).$mount('#app')
