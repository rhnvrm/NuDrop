<template>
  <div class="section">
    <h1 class="title">Encrypt File</h1>
    <!-- <b-field label="File Name">
      <b-input placeholder="My File"></b-input>
    </b-field> -->
    <!-- <b-field message="ipfs uri where the file will be stored">
      <p class="control">
        <span class="button is-static">ipfs://</span>
      </p>
      <b-input expanded></b-input>
    </b-field> -->
    <b-field>
      <b-input
        placeholder="Policy Key..."
        type="text"
        icon="key"
        v-model="policy_key"
      >
      </b-input>
    </b-field>
    <b-field label="File">
      <Editor @editor-data="editorDataUpdate"></Editor>
    </b-field>
    <div class="buttons">
      <b-button @click="encryptData" type="is-primary" expanded
        >Encrypt</b-button
      >
    </div>
    <b-field label="Ciphertext">
      <b-input v-model="ciphertext" type="textarea"></b-input>
    </b-field>
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
      policy_key: "",
      ciphertext: "", 
    };
  },

  methods: {
    editorDataUpdate: function (data) {
      this.editorData = data;
    },
    encryptData: function () {
      const payload = {
        policy_pub_key: this.policy_key,
        plaintext: JSON.stringify(this.editorData.json)
      }
      axios.post(
        "/api/v1/enrico/encrypt",
        querystring.stringify(payload)
      ).then((response) => {
        console.log(response)
        this.ciphertext = response.data.ciphertext
      })
    },
  },
};
</script>