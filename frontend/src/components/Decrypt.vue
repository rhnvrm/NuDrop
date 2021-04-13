<template>
  <div class="section">

    <div>{{ api_response_data }}</div>

    <h1 class="title">Decrypt File</h1>
    <b-field label="Codename">
      <b-input v-model="codename" placeholder=""></b-input>
    </b-field>
    <b-field message="ipfs uri where the file will be stored">
      <p class="control">
        <span class="button is-static">ipfs://</span>
      </p>
      <b-input expanded></b-input>
    </b-field>
    <b-field>
      <b-input
        placeholder="Policy Encrypting Key"
        type="text"
        icon="key"
        v-model="policy_key"
      >
      </b-input>
    </b-field>
    <b-field>
      <b-input
        placeholder="Sender Verifying Key"
        type="text"
        icon="key"
        v-model="alice_verifying_key"
      >
      </b-input>
    </b-field>
    <b-field>
      <b-input
        placeholder="Your Umbral Encrypting Key"
        type="text"
        icon="key"
        v-model="enc_key"
      >
      </b-input>
    </b-field>
    <b-field>
      <b-input
        placeholder="Your Umbral Signing Key"
        type="text"
        icon="key"
        v-model="sig_key"
      >
      </b-input>
    </b-field>


    <b-field label="File">
      <Editor @editor-data="editorDataUpdate"></Editor>
    </b-field>
    <div class="buttons">
      <b-button @click="decryptData" type="is-primary" expanded
        >Encrypt</b-button
      >
    </div>
  </div>
</template>

<script>
import Editor from "./Editor.vue";
import axios from "axios";
import querystring from "querystring"

export default {
  components: {
    Editor,
  },

  data: function () {
    return {
      editorData: {
        json: "",
        data: "",
      },
      enc_key: "",
      sig_key: "",
      policy_key: "",
      alice_verifying_key: "",
      codename: "",
      api_response_data: "",
    };
  },
  computed: {
      ciphertext: {
          get(){
              return this.editorData.data 
          }
      },
      label: {
          get() {
              return "nudrop/"+this.label
          }
      }
  },

  methods: {
    editorDataUpdate: function (data) {
      this.editorData = data;
    },
    decryptData: function () {
      const payload = {
        enc_key: this.enc_key,
        sig_key: this.sig_key,
        policy_pub_key: this.policy_key,
        alice_verifying_key: this.alice_verifying_key,
        label: this.label,
        ciphertext: this.ciphertext,
      }

      axios.post(
        "/api/v1/bob/decrypt",
        querystring.stringify(payload)
      ).then((response) => {
        console.log(response)
        this.api_response_data = response
      })
    },
  },
};
</script>