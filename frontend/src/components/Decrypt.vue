<template>
  <div class="section">
    <h1 class="title">Decrypt File</h1>
    <b-field label="Codename">
      <b-input v-model="codename" placeholder=""></b-input>
    </b-field>
    <!-- <b-field message="ipfs uri where the file will be stored">
      <p class="control">
        <span class="button is-static">ipfs://</span>
      </p>
      <b-input expanded></b-input>
    </b-field> -->
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

    <b-field label="Nucypher Passphrase">
      <b-input 
        v-model="nuPassphrase" 
        placeholder="passphrase"></b-input>
    </b-field>

    <b-field label="Nucypher Treasuremap">
      <b-input 
        v-model="nuTreasuremap" 
        placeholder="treasuremap"></b-input>
    </b-field>

    <b-field label="Ciphertext">
      <b-input v-model="ciphertext" type="textarea"></b-input>
    </b-field>

    <div class="buttons">
      <b-button @click="decryptData" type="is-primary" expanded
        >Decrypt</b-button
      >
    </div>

    <b-field label="Decrypted File">
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
        });
    },
  },
};
</script>