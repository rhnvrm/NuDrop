<template>
    <div class="section">
        <h1 class="title">My Wallet</h1>
        <b-field label="Private Key">
          <b-input v-model="privateKey" placeholder="My Private Key"></b-input>
        </b-field>
    </div>
</template>

<script>
export default ({
    data: function() {
        return {

        }
    },
    methods: {

    },
    computed: {
        privateKey: {
            get() {
                return this.$store.state.private_key
            },
            set(value) {
                this.$store.commit('set_private_key', value)
            }
        }
    }
})
</script>
