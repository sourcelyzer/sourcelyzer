<template>
  <div>
  <h1>Welcome to Sourcelyzer</h1>
  <button v-on:click="install">Install Plugin</button>
  <div>
    <p v-for="msg in msgs"> {{msg}} </p>
  </div>
  </div>
</template>

<script>

import axios from 'axios';

export default {

  data() {
    return {
      msgs: []
    }
  },

  methods: {

    listen() {
      var ws = new WebSocket('ws://localhost:8080/ws/ws');
      ws.onopen = function() {
        ws.send('{"cmd": "bg-listen"}');
      };
      ws.onmessage = function(msg) {
        console.log(msg);
        this.msgs.push(msg.data);
      }.bind(this);
    },

    install(event) {
      event.preventDefault();

      this.listen();

      axios.get('/httpapi/v1/plugins/install?key=sourcelyzer.svn-0.1.0&repo=1')
        .then(function(response) {
          var taskid = response.data['task-id'];
        }.bind(this));
    }
  }
};
</script>

