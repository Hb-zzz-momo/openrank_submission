<template>
  <div class="auth-page">
    <div class="auth-card">
      <h1>登录 OpenDigger 可视化平台</h1>
      <p class="sub-text">使用你的用户名或邮箱登录，解锁收藏与个性化看板。</p>

      <form @submit.prevent="onSubmit">
        <label class="form-item">
          <span>用户名 / 邮箱</span>
          <input
            v-model="form.username"
            type="text"
            placeholder="zbh or zbh@example.com"
          />
        </label>

        <label class="form-item">
          <span>密码</span>
          <input
            v-model="form.password"
            type="password"
            placeholder="请输入密码"
          />
        </label>

        <p v-if="auth.error" class="error-text">
          {{ auth.error }}
        </p>

        <button type="submit" class="primary-btn" :disabled="auth.loading">
          {{ auth.loading ? '登录中...' : '登录' }}
        </button>
      </form>

      <p class="switch-text">
        还没有账号？
        <router-link to="/register">去注册</router-link>
      </p>
    </div>
  </div>
</template>

<script setup>
import { reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const auth = useAuthStore()

const form = reactive({
  username: '',
  password: ''
})

const onSubmit = async () => {
  if (!form.username || !form.password) {
    alert('请输入用户名/邮箱和密码')
    return
  }

  try {
    await auth.login({
      username: form.username,
      password: form.password
    })
    // 登录成功跳回首页（也可以跳到 favorites）
    router.push('/')
  } catch (err) {
    // 错误信息在 auth.error 里
    console.error(err)
  }
}
</script>

<style scoped>
.auth-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: radial-gradient(circle at 0 0, #1d4ed8 0, transparent 55%),
              radial-gradient(circle at 100% 100%, #22c55e 0, #020617 60%);
}

.auth-card {
  width: 360px;
  padding: 24px 28px;
  border-radius: 16px;
  background: rgba(15, 23, 42, 0.96);
  box-shadow: 0 20px 40px rgba(15, 23, 42, 0.9);
  color: #e5e7eb;
}

.auth-card h1 {
  margin: 0 0 6px;
  font-size: 20px;
}

.sub-text {
  margin: 0 0 18px;
  font-size: 13px;
  color: #94a3b8;
}

.form-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-bottom: 12px;
  font-size: 13px;
}

.form-item input {
  padding: 8px 10px;
  border-radius: 8px;
  border: 1px solid #475569;
  background: #020617;
  color: #e5e7eb;
}

.form-item input:focus {
  outline: none;
  border-color: #38bdf8;
}

.primary-btn {
  width: 100%;
  margin-top: 6px;
  padding: 8px 0;
  border: none;
  border-radius: 999px;
  background: linear-gradient(135deg, #22c55e, #38bdf8);
  color: #0b1120;
  font-weight: 600;
  cursor: pointer;
}

.primary-btn[disabled] {
  opacity: 0.6;
  cursor: not-allowed;
}

.error-text {
  margin: 4px 0;
  color: #fecaca;
  font-size: 13px;
}

.switch-text {
  margin-top: 14px;
  font-size: 13px;
  color: #9ca3af;
}

.switch-text a {
  color: #38bdf8;
}
</style>
