# OpenRank API 看板（API Dashboard）

> **目的**：用一份“可执行的接口总表”统一前后端联调口径、测试验收。
> **后端路由基准**：`/api/*`（Flask Blueprint 风格），典型接口包括：`/api/platforms`、`/api/entities/github`、`/api/data/github/<owner>/<repo>/openrank`、`/api/llm/summary`、`/api/llm/report`。
> **维护原则**：以代码为准；接口变更必须同步更新此文档（单一事实源）。

---

## 0. 文档信息

* 仓库：`openrank2`
* 建议文件位置：`docs/API_DASHBOARD.md`
* 维护人：`（填写）`
* 最近更新：`YYYY-MM-DD`
* 后端框架：`Flask`
* Base URL（本地）：`http://127.0.0.1:5000`
* API 前缀：`/api`

---

## 1. 统一约定

### 1.1 请求头

* `Content-Type: application/json`
* `Authorization: Bearer <JWT_TOKEN>`（仅需要登录鉴权的接口）

### 1.2 响应结构（强烈建议统一，便于前端三态处理）

```json
{
  "code": 0,
  "msg": "ok",
  "data": {}
}
```

### 1.3 前端三态（所有接口都要能落到这三种 UI）

* Loading：请求中
* Empty：请求成功但数据为空
* Error：请求失败（网络/鉴权/限流/服务器错误）

---

## 2. 接口总览（看板核心表）

> 状态标记：✅ 可用｜🧪 已实现待测试/补文档｜🚧 规划中
> 缓存建议：数据类接口建议 TTL；用户个性化接口建议短 TTL 或不缓存

| 模块       | 状态 | Method | Path                                       | 描述                  | 鉴权  | 缓存建议       | 关键参数                          | 前端使用点  | 备注/测试点     |
| -------- | -: | ------ | ------------------------------------------ | ------------------- | --- | ---------- | ----------------------------- | ------ | ---------- |
| Meta     | 🧪 | GET    | `/api/health`                              | 健康检查（建议新增）          | No  | No         | -                             | 启动自检   | 返回版本/时间戳   |
| Meta     |  ✅ | GET    | `/api/platforms`                           | 平台列表（github 等）      | No  | TTL=3600s  | -                             | 平台选择   | 必须稳定返回     |
| Search   |  ✅ | GET    | `/api/entities/github`                     | GitHub 实体检索（组织/仓库等） | No  | TTL=600s   | `q,page,page_size`            | 搜索联想   | 兜底：无结果     |
| Data     |  ✅ | GET    | `/api/data/github/<owner>/<repo>/openrank` | OpenRank 指标序列       | No  | TTL=3600s  | `from,to,granularity`         | 趋势图/概览 | 空数据不崩      |
| Data     | 🧪 | GET    | `/api/data/github/<owner>/<repo>/<metric>` | 其他指标序列（如活跃度等）       | No  | TTL=3600s  | `metric,from,to`              | 多指标看板  | metric 白名单 |
| LLM      | 🧪 | POST   | `/api/llm/summary`                         | 生成摘要（洞察+解释）         | 视实现 | TTL=86400s | `platform,owner,repo,from,to` | 一键总结   | 建议限流       |
| LLM      | 🧪 | POST   | `/api/llm/report`                          | 生成报告（markdown/结构化）  | 视实现 | No         | `platform,owner,repo,from,to` | 导出报告   | 可下载/可复制    |
| Auth     | 🧪 | POST   | `/api/auth/register`                       | 注册（如启用）             | No  | No         | `username,password`           | 注册页    | 用户名重复      |
| Auth     | 🧪 | POST   | `/api/auth/login`                          | 登录获取 JWT（如启用）       | No  | No         | `username,password`           | 登录页    | 错误码清晰      |
| User     | 🧪 | GET    | `/api/user/profile`                        | 当前用户信息（如启用）         | Yes | TTL=60s    | -                             | 个人中心   | token 过期处理 |
| Favorite | 🧪 | GET    | `/api/favorites`                           | 收藏列表（如启用）           | Yes | TTL=30s    | `page,page_size`              | 我的收藏   | 分页/排序      |
| Favorite | 🧪 | POST   | `/api/favorites`                           | 新增收藏（如启用）           | Yes | No         | `platform,owner,repo`         | 收藏按钮   | 幂等/防重复     |
| Favorite | 🧪 | DELETE | `/api/favorites/<id>`                      | 删除收藏（如启用）           | Yes | No         | `id`                          | 收藏管理   | 只能删自己的     |


## 3. 关键接口详情与可复制测试

### 3.1 平台列表

* **GET** `/api/platforms`

```bash
curl "http://127.0.0.1:5000/api/platforms"
```

* **期望**：返回平台数组（至少包含 `github`）

---

### 3.2 GitHub 实体检索

* **GET** `/api/entities/github`
* **Query**

  * `q`：关键词（如 `pytorch`）
  * `page`：页码（可选）
  * `page_size`：每页数量（可选）

```bash
curl "http://127.0.0.1:5000/api/entities/github?q=pytorch&page=1&page_size=10"
```

* **期望**：返回可用于后续数据接口的 `owner/repo` 信息
* **兜底**：无结果返回空列表 + 可读 msg

---

### 3.3 OpenRank 指标序列

* **GET** `/api/data/github/<owner>/<repo>/openrank`
* **Query（建议统一支持）**

  * `from=YYYY-MM-DD`
  * `to=YYYY-MM-DD`
  * `granularity=day|week|month`

```bash
curl "http://127.0.0.1:5000/api/data/github/pytorch/pytorch/openrank?from=2024-01-01&to=2024-12-31&granularity=week"
```

* **期望**：返回时间序列（日期 + 数值）
* **兜底**：数据缺失/空数据必须不崩溃

---

### 3.4 LLM 摘要（summary）

* **POST** `/api/llm/summary`
* **Body（建议）**

```json
{
  "platform": "github",
  "owner": "pytorch",
  "repo": "pytorch",
  "from": "2024-01-01",
  "to": "2024-12-31"
}
```

```bash
curl -X POST "http://127.0.0.1:5000/api/llm/summary" \
  -H "Content-Type: application/json" \
  -d "{\"platform\":\"github\",\"owner\":\"pytorch\",\"repo\":\"pytorch\",\"from\":\"2024-01-01\",\"to\":\"2024-12-31\"}"
```

* **建议输出**：结论要包含时间范围、数据来源、关键变化点（便于答辩讲）

---

### 3.5 LLM 报告（report）

* **POST** `/api/llm/report`

```bash
curl -X POST "http://127.0.0.1:5000/api/llm/report" \
  -H "Content-Type: application/json" \
  -d "{\"platform\":\"github\",\"owner\":\"pytorch\",\"repo\":\"pytorch\",\"from\":\"2024-01-01\",\"to\":\"2024-12-31\"}"
```

* **建议输出**：markdown（前端可直接渲染），或返回结构化 JSON + `markdown` 字段

---

## 4. 参数规范（建议统一，利于联调）

### 4.1 时间范围（数据类接口统一支持）

* `from`: `YYYY-MM-DD`
* `to`: `YYYY-MM-DD`
* `granularity`: `day/week/month`

### 4.2 分页（列表接口统一支持）

* `page`：从 1 开始
* `page_size`：默认 20
* 返回建议：

```json
{
  "items": [],
  "page": 1,
  "page_size": 20,
  "total": 123
}
```

---

## 5. 错误码与稳定性兜底（强烈建议）

| HTTP/Code    | 含义     | 常见原因                | 前端处理建议       |
| ------------ | ------ | ------------------- | ------------ |
| 200 + code=0 | 成功     | -                   | 正常渲染         |
| 400          | 参数错误   | 缺字段/格式错误            | 表单提示/高亮字段    |
| 401          | 未登录/过期 | token 缺失/过期         | 跳转登录/清 token |
| 403          | 无权限    | 非本人资源/非管理员          | Toast + 禁用按钮 |
| 404          | 不存在    | repo 不存在/ID 错误      | Empty 状态页    |
| 429          | 限流     | GitHub API/LLM 调用频繁 | 冷却提示 + 重试    |
| 500          | 服务错误   | 未捕获异常               | 统一错误页 + 上报   |

---

## 6. 验收自检清单（提交前 10 分钟过一遍）

* [ ] `/api/platforms` 可稳定返回（无异常）
* [ ] `/api/entities/github` 关键词可返回结果（空结果也正常）
* [ ] `/api/data/.../openrank` 对热门项目可返回序列
* [ ] 空数据/网络失败：前端显示 Empty/Error，不崩溃
* [ ] `summary/report` 输出可读、可复制（含时间范围与来源）
* [ ] 关键接口响应时间可接受（建议记录到 README 或答辩材料）

---

## 7. 变更记录（每次接口变化补一条）

* `YYYY-MM-DD`：新增 `/api/health` 健康检查
* `YYYY-MM-DD`：统一时间参数 `from/to/granularity`
* `YYYY-MM-DD`：为 `/api/entities/github` 增加分页参数

---

## 8. 新增接口模板（复制粘贴）

| 模块  | 状态 | Method   | Path       | 描述  | 鉴权     | 缓存建议  | 关键参数 | 前端使用点 | 备注/测试点 |
| --- | -: | -------- | ---------- | --- | ------ | ----- | ---- | ----- | ------ |
| XXX | 🚧 | GET/POST | `/api/xxx` | ... | Yes/No | TTL=? | ...  | ...   | ...    |

---


