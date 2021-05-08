import '@mdi/font/css/materialdesignicons.css'
import 'inter-ui/inter.css'
import Buefy from 'buefy'
import Vue from 'vue'
import VueRouter from 'vue-router'
import App from './App.vue'
import Encrypt from './components/Encrypt.vue'
import Decrypt from './components/Decrypt.vue'
import PolicyCreate from './components/PolicyCreate.vue'
import FileViewer from './components/FileViewer.vue'
import Wallet from './components/Wallet.vue'
import Home from './components/Home.vue'
import Vuex from 'vuex'
import VuexPersist from 'vuex-persist'

Vue.config.productionTip = false
Vue.use(Buefy, {
  defaultProgrammaticPromise: true
})
Vue.use(VueRouter)

const routes = [
  { path: '/', component: Home },
  { path: '/encrypt', component: Encrypt },
  { path: '/decrypt', component: Decrypt },
  { path: '/policy/create', component: PolicyCreate },
  { path: '/me/files', component: FileViewer },
  { path: '/me/wallet', component: Wallet },
]

const router = new VueRouter({
  routes // short for `routes: routes`
})

Vue.use(Vuex)

const vuexPersist = new VuexPersist({
  key: 'nudrop',
  storage: window.localStorage
})

const store = new Vuex.Store({
  state: {
    private_key: "not available",
    pseudonym: "",
  },
  mutations: {
    set_private_key(state, private_key) {
      state.private_key = private_key
    },
    set_pseudonym(state, pseudonym) {
      state.pseudonym = pseudonym
    }
  },
  plugins: [vuexPersist.plugin]
})

new Vue({
  render: h => h(App),
  router: router,
  store: store,
}).$mount('#app')
