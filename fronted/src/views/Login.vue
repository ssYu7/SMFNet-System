<template>
  <div class="login-wrapper">
    <div class="login-container">
      <div class="header">
        <h2>Audio-Vision Source Separation System</h2>
        <p>视听源分离演示系统</p>
      </div>

      <el-card class="box-card">
        <el-tabs v-model="activeTab" stretch @tab-click="handleTabClick">

          <el-tab-pane label="用户登录" name="login">
            <el-form
              ref="loginFormRef"
              :model="loginForm"
              :rules="rules"
              label-position="top"
              size="large"
            >
              <el-form-item label="用户名" prop="username">
                <el-input v-model="loginForm.username" prefix-icon="User" placeholder="请输入用户名" />
              </el-form-item>
              <el-form-item label="密码" prop="password">
                <el-input
                  v-model="loginForm.password"
                  prefix-icon="Lock"
                  type="password"
                  placeholder="请输入密码"
                  show-password
                  @keyup.enter="submitLogin"
                />
              </el-form-item>
              <el-button type="primary" class="full-btn" :loading="loading" @click="submitLogin">
                立即登录
              </el-button>
            </el-form>
          </el-tab-pane>

          <el-tab-pane label="新用户注册" name="register">
            <el-form
              ref="regFormRef"
              :model="regForm"
              :rules="rules"
              label-position="top"
              size="large"
            >
              <el-form-item label="设置用户名" prop="username">
                <el-input v-model="regForm.username" prefix-icon="User" placeholder="请输入注册用户名" />
              </el-form-item>
              <el-form-item label="设置密码" prop="password">
                <el-input
                  v-model="regForm.password"
                  prefix-icon="Lock"
                  type="password"
                  placeholder="请输入注册密码"
                  show-password
                />
              </el-form-item>
              <el-button type="success" class="full-btn" :loading="loading" @click="submitRegister">
                确认注册
              </el-button>
            </el-form>
          </el-tab-pane>

        </el-tabs>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import request from '@/api/request'
import { ElMessage } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'

const router = useRouter()
const activeTab = ref('login')
const loading = ref(false)

// 表单数据
const loginForm = reactive({ username: '', password: '' })
const regForm = reactive({ username: '', password: '' })

// 表单校验规则
const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

// 切换标签时重置表单
const handleTabClick = () => {
  loginForm.username = ''
  loginForm.password = ''
  regForm.username = ''
  regForm.password = ''
}

// --- 登录逻辑 ---
const submitLogin = async () => {
  if (!loginForm.username || !loginForm.password) {
    ElMessage.warning('请填写完整信息')
    return
  }

  loading.value = true
  try {
    // 发送登录请求
    const res = await request.post('/api/login', loginForm)

    // 登录成功处理
    ElMessage.success('登录成功')
    localStorage.setItem('token', res.data.token) // 这里的 token 就是 user_id
    localStorage.setItem('user_id', res.data.token)
    localStorage.setItem('username', res.data.username)

    // 跳转首页
    router.push('/')
  } catch (err) {
    // 错误已经在 request.js 里弹窗了，这里不用再弹
    console.error(err)
  } finally {
    loading.value = false
  }
}

// --- 注册逻辑 ---
const submitRegister = async () => {
  if (!regForm.username || !regForm.password) {
    ElMessage.warning('请填写完整信息')
    return
  }

  loading.value = true
  try {
    // 发送注册请求
    await request.post('/api/register', regForm)

    ElMessage.success('注册成功！请切换到登录页进行登录')

    // 注册成功后，自动切回登录 Tab，并帮忙填好用户名
    activeTab.value = 'login'
    loginForm.username = regForm.username
    loginForm.password = '' // 密码让用户自己再输一次，增强安全性感

  } catch (err) {
    console.error(err)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-wrapper {
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background: linear-gradient(135deg, #2d3a4b 0%, #1f2a38 100%);
  color: #fff;
}

.login-container {
  width: 400px;
}

.header {
  text-align: center;
  margin-bottom: 30px;
}
.header h2 { margin: 0; font-size: 28px; }
.header p { margin: 10px 0 0; opacity: 0.8; }

.box-card {
  border-radius: 8px;
}

.full-btn {
  width: 100%;
  margin-top: 10px;
  font-weight: bold;
}
</style>
