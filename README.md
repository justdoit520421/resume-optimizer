# 简历智能优化工具

一款基于大语言模型的简历智能优化工具。用户上传简历后，系统自动完成**解析 → 岗位匹配 → 智能评分 → 内容优化 → 导出**的全流程，帮助求职者快速提升简历质量。

---

## 一、核心功能

| # | 功能 | 说明 |
|---|------|------|
| 1 | **简历解析** | 支持 PDF / Word，提取正文并结构化为「基本信息 / 教育背景 / 工作经历 / 项目经历 / 技能」等字段 |
| 2 | **岗位匹配** | 粘贴目标岗位 JD，输出匹配度评分（0-100）、已匹配能力点、缺失能力点与改进建议 |
| 3 | **智能评分** | 六维度打分并给出理由，前端以雷达图展示：完整性 15 / 量化程度 25 / 关键词匹配 25 / 逻辑结构 15 / 表达质量 10 / 岗位契合度 10 |
| 4 | **一键优化** | 按岗位类型（技术 / 产品 / 运营 / 设计）生成逐条优化建议，用户可**逐条接受或拒绝**，支持优化前后对比 |
| 5 | **导出简历** | 将应用建议后的最终简历导出为 Word / PDF，宋体正文 + 黑体标题，章节标题带分隔线，排版紧凑 |

### 使用流程

```
上传简历 → 解析预览 → 岗位匹配 → 评分报告(雷达图) → 优化对比(逐条接受) → 最终简历预览与导出
```

---

## 二、技术栈

**前端**
- React 18 + TypeScript + Vite 5
- Ant Design 5（UI 组件）
- Zustand（全局状态）
- axios（HTTP 请求，统一拦截器解包与错误提示）
- @ant-design/plots（雷达图）、react-diff-viewer（对比视图）

**后端**
- Python 3.11 + FastAPI + Uvicorn
- SQLAlchemy 2.x（ORM）+ Pydantic 2.x（校验）
- MySQL 9.x（pymysql 驱动，utf8mb4，JSON 字段）
- pdfplumber（PDF 解析）、python-docx（Word 读写）
- reportlab（PDF 生成）、openai SDK（LLM 调用）

**大模型**
- 通过 OpenAI 兼容协议统一封装，支持 7 家厂商：
  `openai` / `deepseek` / `qwen`(通义) / `glm`(智谱) / `kimi`(月之暗面) / `doubao`(豆包) / `ernie`(文心)
- 另有 `mock` 模式，无需 API Key 即可本地演示（返回预设数据）
- 强制 `response_format={"type": "json_object"}` 输出 JSON，并带多级容错解析与自动重试

---

## 三、目录结构

```
resume-optimizer/
├── README.md                    # 本文档（功能、技术栈、接口、目录）
├── 产品PRD.md                    # 产品需求文档（背景、流程、功能需求、验收口径）
├── 本地启动指南.md               # 从零启动的详细步骤
├── 一键启动.bat                  # 一键启动全部服务（推荐）
├── 1-MySQL.bat                  # 单独启动数据库
├── 2-Backend.bat                # 单独启动后端
├── 3-Frontend.bat               # 单独启动前端
├── docker-compose.yml           # Docker 编排（可选，本机未使用）
├── .env.example                 # 环境变量模板
│
├── backend/                     # 后端（FastAPI）
│   ├── .env                     # 实际生效的配置（数据库、LLM Key）
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── app/
│   │   ├── main.py              # 应用入口：路由注册、CORS、全局异常处理
│   │   ├── config.py            # 配置（环境变量 / .env）
│   │   ├── database.py          # 引擎、会话、Base、init_db(自动建表)
│   │   ├── models.py            # ORM 模型（4 张表）
│   │   ├── schemas.py           # 请求/响应模型
│   │   ├── response.py          # 统一响应体与业务码
│   │   ├── exceptions.py        # BizException
│   │   ├── api/
│   │   │   └── resume.py        # 全部 8 个接口
│   │   ├── prompts/
│   │   │   └── prompts.py       # 4 个核心 Prompt 模板
│   │   └── services/
│   │       ├── extract_service.py   # 文件文本提取 + 文本清洗
│   │       ├── parse_service.py     # 简历结构化解析
│   │       ├── score_service.py     # 智能评分
│   │       ├── optimize_service.py  # 一键优化
│   │       ├── match_service.py     # 岗位匹配
│   │       ├── export_service.py    # Word / PDF 导出
│   │       └── llm_service.py       # LLM 适配层（多厂商 + JSON 容错）
│   ├── tests/
│   │   ├── test_llm_e2e.py          # 4 个 Prompt 的端到端测试
│   │   └── test_api_integration.py  # 全链路接口集成测试
│   ├── uploads/                     # 上传的简历文件存储目录
│   └── mysql_data/                  # MySQL 数据目录（已初始化，root/123456）
│
└── frontend/                    # 前端（React + Vite）
    ├── index.html
    ├── package.json
    ├── tsconfig.json
    ├── vite.config.ts           # 开发服务器 + /api 代理到 8000
    └── src/
        ├── main.tsx
        ├── App.tsx              # 6 步流程编排
        ├── api/
        │   ├── client.ts        # axios 实例与拦截器
        │   └── resume.ts        # 8 个接口封装
        ├── store/
        │   └── resumeStore.ts   # Zustand 全局状态
        └── pages/
            ├── UploadStep.tsx    # 1. 上传
            ├── ParseStep.tsx     # 2. 解析预览
            ├── MatchStep.tsx     # 3. 岗位匹配
            ├── ScoreStep.tsx     # 4. 评分报告
            ├── OptimizeStep.tsx  # 5. 优化对比
            └── FinalStep.tsx     # 6. 最终简历与导出
```

---

## 四、快速开始

**最简单：双击 `一键启动.bat`**，会自动打开三个窗口分别启动数据库、后端、前端，并打开浏览器。

手动启动（详见 [本地启动指南.md](./本地启动指南.md)）：

```powershell
# 1) 启动 MySQL（双击 1-MySQL.bat，端口 3307，数据库 resume_optimizer 已存在，表自动创建）

# 2) 后端
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# 3) 前端
cd frontend
npm install
npm run dev

# 4) 浏览器打开 http://localhost:5173
```

> 启动顺序：**MySQL → 后端 → 前端**。后端启动时会连数据库并自动建表。

---

## 五、接口一览

统一前缀 `/api/resumes`，响应体统一为 `{ code, message, data }`（`code=0` 表示成功）。

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/health` | 健康检查 |
| POST | `/api/resumes/upload` | 上传简历（multipart），返回 `resume_id` |
| POST | `/api/resumes/{id}/parse` | 解析为结构化 JSON |
| POST | `/api/resumes/{id}/score` | 智能评分，返回各维度得分 |
| POST | `/api/resumes/{id}/optimize` | 一键优化，返回逐条建议 |
| POST | `/api/resumes/{id}/match` | 岗位匹配（传 JD 文本） |
| POST | `/api/resumes/{id}/apply-suggestions` | 应用选中的建议，生成优化后全文 |
| GET | `/api/resumes/{id}/export?format=docx\|pdf` | 导出最终简历 |
| GET | `/api/resumes/{id}/diff` | 优化前后对比数据 |

交互式接口文档：后端启动后访问 <http://localhost:8000/docs>

---

## 六、数据模型

| 表 | 说明 | 关键字段 |
|----|------|----------|
| `resumes` | 简历主表 | file_name / file_type / raw_text / parsed_content(JSON) |
| `score_records` | 评分记录 | total_score / dimensions(JSON) / summary |
| `optimization_records` | 优化记录 | job_type / suggestions(JSON) / optimized_text |
| `job_match_records` | 匹配记录 | jd_text / match_score / matched / missing / suggestions |

所有表由后端启动时的 `init_db()` 自动创建，无需手工执行建表 SQL。

---

## 七、配置说明

配置文件为 `backend/.env`：

```ini
DATABASE_URL=mysql+pymysql://root:123456@127.0.0.1:3307/resume_optimizer?charset=utf8mb4
REDIS_URL=redis://127.0.0.1:6379/0

LLM_PROVIDER=deepseek
LLM_API_KEY=sk-xxxxxxxx
LLM_BASE_URL=
LLM_MODEL=
LLM_MAX_TOKENS=8192
```

| 变量 | 说明 |
|------|------|
| `LLM_PROVIDER` | `mock` / `openai` / `deepseek` / `qwen` / `glm` / `kimi` / `doubao` / `ernie` |
| `LLM_API_KEY` | 对应厂商的 API Key（`mock` 模式可留空） |
| `LLM_BASE_URL` | 留空则使用该厂商默认地址 |
| `LLM_MODEL` | 留空则使用该厂商默认模型 |
| `LLM_MAX_TOKENS` | 单次输出上限，建议 8192，避免长简历输出被截断导致 JSON 解析失败 |
| `REDIS_URL` | 预留给后续异步任务，**当前版本代码未使用，无需安装 Redis** |

---

## 八、实现要点

- **统一响应体**：后端所有异常（含参数校验、未知异常）都返回 `code != 0` 的 JSON，前端 axios 拦截器集中处理，页面再叠加持久化的错误提示与「重试」按钮。
- **中文文本清洗**：部分 PDF 会把汉字映射到「康熙部首」码位（如 `⼤` 而非 `大`），导出时字体缺字形导致内容"消失"；`extract_service.normalize_cjk` 做码位归一化解决。
- **排版折行合并**：PDF 的视觉换行会被提取成硬换行，导致句中多出换行；`clean_resume_text` 依据「上一行语义未结束 + 当前行不是新条目」的规则把句子接回，并收敛多余空格。
- **LLM JSON 容错**：解析失败自动重试一次，并支持「直接解析 → 提取 ```json 代码块 → 截取首尾大括号片段」三级兜底；输出被 `max_tokens` 截断时给出明确提示。
- **避免重复请求**：开发模式下 React StrictMode 会让 `useEffect` 执行两次，解析/评分/优化三个自动触发步骤用 `useRef` 守卫，避免重复调用 LLM。
