/*用户以后访问后端需要认证的API时,都要传输Token,而axios可以通过创建request interceptor 自动添加token 到请求头Authoriazation中*/



/*为了jwt的安全,jwt的有效期会设置的短一些,当他过期后,用户再通过它访问后端api时,会返回401 UNAUTHORIZED错误, 我们希望axios自动处理这个错误,如果用户当前访问的不是/login(正常登陆时),会自动跳到登陆页面,要求用户重新认证*/

import Vue from 'vue'
import axios from 'axios'
import router from './router'
import store from './store'

// 基础配置
axios.defaults.timeout = 5000  // 超时时间
axios.defaults.baseURL = 'http://localhost:5000/api'

// Add a request interceptor
axios.interceptors.request.use(function (config) {
  // Do something before request is sent
  const token = window.localStorage.getItem('madblog-token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
}, function (error) {
  // Do something with request error
  return Promise.reject(error)
})

// Add a response interceptor
axios.interceptors.response.use(function (response) {
  // Do something with response data
  return response
}, function (error) {
  // Do something with response error
  switch  (error.response.status) {
    case 401:
      // 清除 Token 及 已认证 等状态
      store.logoutAction()
      // 跳转到登录页
      if (router.currentRoute.path !== '/login') {
        Vue.toasted.error('401: 认证已失效，请先登录', { icon: 'fingerprint' })
        router.replace({
          path: '/login',
          query: { redirect: router.currentRoute.path },
        })
      }
      break

    case 404:
      Vue.toasted.error('404: NOT FOUND', { icon: 'fingerprint' })
      router.back()
      break
  }
  return Promise.reject(error)
})

export default axios
