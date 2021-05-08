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
    <b-field class="file">
      <b-upload @input="updatePolicyFile()" v-model="policyFile" expanded>
        <a class="button is-fullwidth">
          <b-icon icon="upload"></b-icon>
          <span>{{ policyFile.name || "Click to upload policy.json"}}</span>
        </a>
      </b-upload>
    </b-field>
    <b-field label="File">
      <Editor @editor-data="editorDataUpdate"></Editor>
    </b-field>
    <div class="buttons">
      <b-button @click="encryptData" type="is-primary" expanded
        >Encrypt</b-button
      >
    </div>
    <div v-if="ciphertext !== ''">
      <b-field label="Ciphertext">
        <b-input v-model="ciphertext" type="textarea"></b-input>
      </b-field>
      <b-button size="is-small"
          icon-left="download"
          @click="download()">
          Download
      </b-button>
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
      policy_key: "",
      ciphertext: "", 
      policyFile: {},
    };
  },

  methods: {
    editorDataUpdate: function (data) {
      this.editorData = data;
    },
    updatePolicyFile: function () {
      var reader = new FileReader();
      reader.readAsText(this.policyFile, 'UTF-8');
      reader.onload = (evt) => {
        var data = JSON.parse(evt.target.result)
        this.policy_key = data.policy_public_key
      }
    },
    encryptData: function () {
      if (this.policy_key == "") {
       this.$buefy.toast.open({
            duration: 5000,
            message: `Policy key was empty`,
            position: 'is-bottom',
            type: 'is-danger'
        }) 
        return
      }
      
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
      }).catch((err) => {
       this.$buefy.toast.open({
            duration: 5000,
            message: err,
            position: 'is-bottom',
            type: 'is-danger'
        }) 
      })
    },
    download: function() {
      var filename = "encrypted.json"
      var text = JSON.stringify({
        "ciphertext": this.ciphertext,
        "policy_key": this.policy_key,
      })
      var element = document.createElement('a');
      element.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(text));
      element.setAttribute('download', filename);

      element.style.display = 'none';
      document.body.appendChild(element);

      element.click();

      document.body.removeChild(element);
    }
  },
};
</script>