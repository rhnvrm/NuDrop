<template>
  <div class="section">
    <h1 class="title">Encrypt File</h1>
    <b-field label="File Name">
      <b-input placeholder="My File"></b-input>
    </b-field>
    <b-field message="ipfs uri where the file will be stored">
      <p class="control">
        <span class="button is-static">ipfs://</span>
      </p>
      <b-input expanded></b-input>
    </b-field>
    <b-field>
      <b-input
        placeholder="Policy Key..."
        type="text"
        icon="key"
      >
      </b-input>
    </b-field>
    <b-field label="File">
      <Editor @editor-data="editorDataUpdate"></Editor>
    </b-field>
    <div class="buttons">
      <b-button type="is-primary" expanded>Save</b-button>
    </div>
  </div>
</template>

<script>
// Import the editor
import Editor from "./Editor.vue";

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
    };
  },

  methods: {
    editorDataUpdate: function (data) {
      this.editorData = data;
    },
  },
};
</script>