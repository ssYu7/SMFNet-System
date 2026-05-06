import axios from 'axios'
import { BASE_URL } from './config'
import { ElMessage } from 'element-plus'

const service = axios.create({
  baseURL: BASE_URL,
  timeout: 600000 // 10分钟超时，模型跑得慢也不怕
})

// 响应拦截器
service.interceptors.response.use(
  res => res,
  error => {
    console.error('Request Error:', error)
    ElMessage.error(error.message || '请求失败')
    return Promise.reject(error)
  }
)

export default service
