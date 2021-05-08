<template>
  <div class="section">
    <h1 class="title">Decrypt File</h1>

    <!-- <b-field message="ipfs uri where the file will be stored">
      <p class="control">
        <span class="button is-static">ipfs://</span>
      </p>
      <b-input expanded></b-input>
    </b-field> -->
    <b-field class="file">
      <b-upload @input="updatePolicyFile()" v-model="policyFile" expanded>
        <a class="button is-fullwidth">
          <b-icon icon="upload"></b-icon>
          <span>{{ policyFile.name || "Click to upload policy.json"}}</span>
        </a>
      </b-upload>
    </b-field>
    <b-field class="file">
      <b-upload @input="updateCipherFile()" v-model="cipherFile" expanded>
        <a class="button is-fullwidth">
          <b-icon icon="upload"></b-icon>
          <span>{{ cipherFile.name || "Click to upload encrypted.json"}}</span>
        </a>
      </b-upload>
    </b-field>

    <b-field label="Codename">
      <b-input v-model="codename" placeholder=""></b-input>
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

    <b-field label="Nucypher Treasuremap">
      <b-input 
        v-model="nuTreasuremap" 
        placeholder="treasuremap"></b-input>
    </b-field>

    <b-field label="Ciphertext">
      <b-input v-model="ciphertext" type="textarea"></b-input>
    </b-field>

    <b-field label="Nucypher Passphrase">
      <b-input 
        v-model="nuPassphrase" 
        placeholder="passphrase"></b-input>
    </b-field>

    <div class="buttons">
      <b-button @click="decryptData" type="is-primary" expanded
        >Decrypt</b-button
      >
    </div>

    <b-field v-show="decrypted" label="Decrypted File">
      <Editor ref="editor" @editor-data="editorDataUpdate"></Editor>
    </b-field>
  </div>
</template>

<script>
import Editor from "./Editor.vue";
import axios from "axios";
import querystring from "querystring";
import Web3 from "web3";
import PrivateKeyProvider from "truffle-privatekey-provider";

export default {
  components: {
    Editor,
  },
  async mounted() {
    if (this.$store.state.private_key == "not available") {
      this.$router.push("/me/wallet");
    }

    var provider = new PrivateKeyProvider(
      this.$store.state.private_key,
      "https://goerli.infura.io/v3/79153147849f40cf9bc97d4ec3c6416b"
    );

    var web3 = new Web3(provider);
    this.web3 = web3;
    this.user_address = web3.eth.accounts.wallet._accounts.currentProvider.address;

    this.$refs.editor.setContent();
  },
  data: function () {
    return {
      editorData: {
        json: "",
        data: "",
      },
      editor: null,
      user_address: "not available",
      enc_key: "",
      sig_key: "",
      policy_key: "",
      alice_verifying_key: "",
      codename: "",
      api_response_data: "",
      ciphertext: "",
      nuPassphrase: "",
      nuTreasuremap: "",
      policyFile: {},
      cipherFile: {},
      decrypted: false,
    };
  },
  computed: {
    label: {
      get() {
        return "nudrop/" + this.codename;
      },
    },
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
        this.alice_verifying_key = data.verifying_key
        this.policy_key = data.policy_public_key
        this.codename = data.label.split("nudrop/").reverse()[0]
        this.nuTreasuremap = data.tmap_bytes
      }
    },
    updateCipherFile: function () {
      var reader = new FileReader();
      reader.readAsText(this.cipherFile, 'UTF-8');
      reader.onload = (evt) => {
        var data = JSON.parse(evt.target.result)
        this.ciphertext = data.ciphertext
      }
    },
    decryptData: function () {
      const payload = {
        policy_pub_key: this.policy_key,
        alice_verifying_key: this.alice_verifying_key,
        label: this.label,
        ciphertext: this.ciphertext,
        bob_address: this.user_address,
        bob_password: this.nuPassphrase,
        tmap_bytes: this.nuTreasuremap,
      };

      axios
        .post("/api/v1/bob/decrypt", querystring.stringify(payload))
        .then((response) => {
          console.log(response);
          this.api_response_data = response;
          this.$refs.editor.setContent(JSON.parse(response.data.cleartext[0]))
          this.decrypted = true
        }).catch((err) => {
        this.$buefy.toast.open({
          duration: 5000,
          message: err,
          position: 'is-bottom',
          type: 'is-danger'
        }) 
        });
    },
  },
};
</script>