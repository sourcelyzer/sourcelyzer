import vue from 'vue';
import Vuex from 'vuex';

vue.use(Vuex);

const store = new Vuex.Store({
  state: {
    checking_session: true,
    logged_in: false
  },
  mutations: {
    logout(state) {
      state.logged_in = false;
    },
    login(state) {
      state.logged_in = true;
    },
    session_checked(state) {
      state.checking_session = false;
    }
  }
});

export default store;
