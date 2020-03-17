<template>
  <div class="container">
    <h1>Sing In</h1>
    <div class="row">
      <div class="col-md-4">
        <form action="" @submit.prevent="onSubmit">
          <div class="form-group">
            <label for="username">Username</label>
            <input type="text" v-model="loginForm.username" class="form-control"
                   v-bind:class="{'is-invalid': loginForm.usernameError}" id="username" placeholder="">
            <div v-show="loginForm.usernameError" class="invalid-feedback">{{ loginForm.usernameError }}</div>
          </div>
          <div class="form-group">
            <label for="password">Password</label>
            <input type="password" v-model="loginForm.password" class="form-control"
                   v-bind:class="{'is-invalid': loginForm.passwordError}" id="password" placeholder="">
            <div v-show="loginForm.passwordError" class="invalid-feedback">{{ loginForm.passwordError }}</div>
          </div>
          <button type="submit" class="btn btn-primary">Sign In</button>
        </form>
      </div>
    </div>
    <br>
    <p>New User?
      <router-link to="/register">Click to Register</router-link>
    </p>
    <p>Forgot Your Password?</p>
    <a href="#">Click to Reset It</a>
  </div>
</template>

<script>

  import store from '../store.js'

  export default {
    name: "Login",
    data() {
      return {
        sharedState: store.state,
        loginForm: {
          username: '',
          password: '',
          submitted: false, //是否点击了 submit按钮
          errors: 0,   //表单是否在前端通过验证,0表示没有错误,验证通过
          usernameError: null,
          passwordError: null
        },
        methods: {
          onSubmit(e) {
            this.loginForm.submitted = true;  //先更新状态
            this.loginForm.errors = 0;

            if (!this.loginForm.username) {
              this.loginForm.errors++;
              this.loginForm.usernameError = 'Username Require.'
            } else {
              this.loginForm.usernameError = null
            }

            if (!this.loginForm.password) {
              this.loginForm.errors++
              this.loginForm.passwordError = 'Password Require.'
            } else {
              this.loginForm.passwordError = null
            }

            if (this.loginForm.errors > 0) {
              //表单验证没通过时,不继续往下执行,即不会通过axios调用后端api
              return false
            }
            const path = '/tokens'
            //axios 实现Basic auth 需要在config中设置auth这个属性即可
            this.$axios.post(path, {}, {
              auth: {
                'username': this.loginForm.username,
                'password': this.loginForm.password,
              }
            }).then((response) => {
              //handle success
              //设置token
              window.localStorage.setItem('madblog-token', response.data.token);
              store.resetNotNewAction();
              store.loginAction();

              const name = JSON.parse(atob(response.data.token.split('.')[1])).name
              this.$toasted.success(`Welcome ${name}`, {icon: 'fingerprint'})

              if (typeof this.$route.query.redirect == 'undefined') {
                this.$route.push('/')
              } else {
                this.$route.push(this.$route.query.redirect)
              }
            })
              .catch((error) => {
                //handle error
                if (error.response.status === 401) {
                  this.loginForm.usernameError = 'Invalid username or password.';
                  this.loginForm.passwordError = 'Invalid username or password.';
                } else {
                  console.log(error.response)
                }

              })
          }
        }
      }
    }
  }
</script>

<style scoped>

</style>
