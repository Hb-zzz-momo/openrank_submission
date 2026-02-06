# 安全改进文档 (Security Improvements Documentation)

## 概述 (Overview)

本文档记录了在项目中发现和修复的安全漏洞。所有修复已经过验证，并通过 CodeQL 安全扫描。

## 已修复的安全漏洞 (Fixed Vulnerabilities)

### 1. SSL 证书验证被禁用 (Critical) ✅

**问题描述:**
- 多个文件中使用 `verify=False` 参数禁用 SSL 证书验证
- 这允许中间人攻击（MITM），攻击者可以截获和篡改 HTTPS 通信

**影响的文件:**
- `backend/api/opendigger.py`
- `backend/data_fetcher.py`
- `backend/check_repos.py`

**修复方案:**
- 移除所有 `verify=False` 参数
- 启用默认的 SSL 证书验证

**代码变更:**
```python
# 修复前:
resp = requests.get(api_url, timeout=30, verify=False)

# 修复后:
resp = requests.get(api_url, timeout=30)
```

### 2. 安全警告被抑制 (High) ✅

**问题描述:**
- 使用 `warnings.filterwarnings('ignore', message='Unverified HTTPS request')` 隐藏安全警告
- 这掩盖了潜在的安全问题

**影响的文件:**
- `backend/api/opendigger.py`
- `backend/data_fetcher.py`

**修复方案:**
- 完全移除警告过滤代码
- 让安全警告正常显示（如果有）

### 3. 密码强度验证缺失 (Medium) ✅

**问题描述:**
- 注册接口未验证密码强度
- 允许创建弱密码账户

**影响的文件:**
- `backend/api/auth.py`

**修复方案:**
- 添加密码长度验证（最少 8 个字符）
- 添加邮箱格式验证（正则表达式）
- 添加用户名格式验证（3-32 个字符，仅字母、数字、下划线）

**代码变更:**
```python
# 2. 密码强度验证
if len(password) < 8:
    raise ApiException(400, "密码长度至少为8个字符")

# 3. 邮箱格式验证
import re
email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
if not re.match(email_pattern, email):
    raise ApiException(400, "邮箱格式不正确")

# 4. 用户名格式验证（仅允许字母、数字、下划线，3-32字符）
username_pattern = r'^[a-zA-Z0-9_]{3,32}$'
if not re.match(username_pattern, username):
    raise ApiException(400, "用户名格式不正确（3-32个字符，仅允许字母、数字、下划线）")
```

### 4. CORS 配置改进 (Medium) ✅

**问题描述:**
- CORS 使用正则表达式模式，可能匹配非预期的域名
- 缺少生产环境的域名白名单机制

**影响的文件:**
- `backend/main.py`

**修复方案:**
- 开发环境：使用显式的域名列表（localhost:5173, 127.0.0.1:5173）
- 生产环境：从环境变量读取允许的域名白名单
- 添加 `ALLOWED_ORIGINS` 环境变量配置

**代码变更:**
```python
# ✅ CORS 配置：生产环境使用严格的域名白名单
allowed_origins = os.getenv("ALLOWED_ORIGINS", "")
if allowed_origins:
    # 生产环境：从环境变量读取允许的域名列表（逗号分隔）
    origins = [origin.strip() for origin in allowed_origins.split(",")]
    CORS(app, resources={r"/api/*": {"origins": origins}}, supports_credentials=True)
else:
    # 开发环境：仅允许本地访问
    CORS(
        app,
        resources={r"/api/*": {"origins": ["http://localhost:5173", "http://127.0.0.1:5173"]}},
        supports_credentials=True
    )
```

### 5. XSS 防护 - Markdown 渲染 (Low) ✅

**问题描述:**
- Markdown 解析器配置了 `html: true`，允许任意 HTML 标签
- 虽然内容来自后端 AI，但从防御深度角度应该禁用

**影响的文件:**
- `frontend/src/views/HomeView.vue`

**修复方案:**
- 将 `html` 选项改为 `false`
- 只允许纯 Markdown 语法，不允许 HTML 标签

**代码变更:**
```javascript
// 修复前:
const md = new MarkdownIt({
  html: true,      // 允许HTML标签
  breaks: true,
  linkify: true
})

// 修复后:
const md = new MarkdownIt({
  html: false,     // ✅ 禁止HTML标签以防止XSS
  breaks: true,
  linkify: true
})
```

### 6. 硬编码的 API URL (Low) ✅

**问题描述:**
- 前端 API 基础 URL 硬编码为 `http://127.0.0.1:8000`
- 无法灵活配置生产环境的 API 地址

**影响的文件:**
- `frontend/src/api/api.js`

**修复方案:**
- 使用 Vite 环境变量 `VITE_API_BASE_URL`
- 提供 `.env.example` 文件作为配置模板

**代码变更:**
```javascript
// 修复前:
const http = axios.create({
  baseURL: 'http://127.0.0.1:8000',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 修复后:
const http = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})
```

### 7. .gitignore 改进 (Low) ✅

**问题描述:**
- `.gitignore` 未覆盖所有可能的敏感文件位置

**修复方案:**
- 添加 `backend/.env`, `backend/.env.local`
- 添加 `frontend/.env`, `frontend/.env.local`
- 添加 `backend/*.db`（数据库文件）

## 安全最佳实践 (Security Best Practices)

### 环境配置

1. **后端配置** (`backend/.env`)
   ```bash
   # 必须配置（生产环境）
   FLASK_ENV=production
   SECRET_KEY=<使用 secrets.token_hex(32) 生成>
   JWT_SECRET_KEY=<使用 secrets.token_hex(32) 生成>
   ALLOWED_ORIGINS=https://your-domain.com
   
   # 可选配置
   OPENAI_API_KEY=sk-xxx
   ```

2. **前端配置** (`frontend/.env`)
   ```bash
   VITE_API_BASE_URL=https://your-api-domain.com
   ```

### 密码策略

- 最小长度：8 个字符
- 建议：包含大小写字母、数字和特殊字符
- 用户名：3-32 个字符，仅允许字母、数字、下划线

### API 安全

- 所有 API 请求使用 HTTPS（生产环境）
- JWT Token 有效期：7 天
- 速率限制已启用（见 `rate_limiter.py`）

### 数据保护

- 密码使用 `werkzeug.security` 的 `generate_password_hash` 加密存储
- JWT Token 存储在 `localStorage`（前端）
- 敏感数据不记录到日志

## CodeQL 扫描结果

✅ **扫描时间:** 2026-02-06

✅ **结果:** 0 个安全警报

✅ **语言:** Python

## 依赖项安全

### 后端依赖

所有依赖项都来自 PyPI 官方源，使用时应定期更新：

```bash
pip install --upgrade Flask Flask-Cors flask_sqlalchemy flask-jwt-extended requests openai pandas python-dotenv
```

### 前端依赖

定期运行安全审计：

```bash
npm audit
npm audit fix
```

## 未来改进建议

1. **依赖版本固定**: 在 `requirements.txt` 中固定版本号
2. **双因素认证**: 为管理员账户添加 2FA
3. **API 密钥轮换**: 实现 OpenAI API 密钥的定期轮换机制
4. **安全头部**: 添加 CSP、X-Frame-Options 等安全响应头
5. **审计日志**: 记录所有认证和授权相关的操作
6. **速率限制升级**: 生产环境使用 Redis 实现分布式速率限制

## 联系方式

如发现新的安全问题，请通过 GitHub Issues 报告，并标记为 `security` 标签。

---

**最后更新:** 2026-02-06  
**维护者:** Hb-zzz-momo / OpenRank Submission Project Team
