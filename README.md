# Paper Writer - 学术论文写作辅助系统

基于多AI Agent协作的学术论文写作工具，支持从Word文档中提取研究内容、AI自动分析图表、选择文献库、配置各章节模型，生成完整论文初稿。

## ✨ 功能特点

| 功能 | 描述 |
|------|------|
| 📄 **Word文档解析** | 上传包含研究背景、试验设计、数据表格、图表的Word文档，自动提取内容 |
| 📊 **图表AI分析** | 自动识别并分析文档中的表格和图片，生成描述用于论文撰写 |
| 📚 **文献库管理** | 支持多文献库选择，合并引用 |
| 🤖 **模型灵活配置** | 为每个章节（引言、方法、结果、讨论、摘要、结论）单独选择AI模型 |
| 📝 **一键写作** | 自动完成从内容解析到论文撰写的完整流程 |

## 🚀 快速开始

### 1. 运行Web界面

```bash
cd paper_writer
streamlit run app.py
```

访问 `http://localhost:8501` 打开网页界面。

### 2. 配置API

系统需要配置两个API服务：

#### 主要模型API（模型中转站）
- **推荐服务**: ModelGate (https://modelgate.cn)
- **API URL**: `https://modelgate.cn/v1` 或其他模型中转站地址
- **API Key**: 从ModelGate获取的API密钥
- **用途**: 用于论文写作的主要AI模型调用

#### DeepSeek API（可选，用于风格分析增强）
- **API URL**: `https://api.deepseek.com/v1`
- **API Key**: 从DeepSeek官网获取的API密钥
- **用途**: 用于增强的期刊风格分析功能

在侧边栏分别配置这两个API的地址和密钥。

### 3. 开始写作

1. **Tab 1**: 上传目标期刊范文（可选，用于分析期刊风格）
2. **Tab 2**: 导入文献库（可选，用于自动引用）
3. **Tab 3**: 
   - 下载研究内容模板 (research_content_template.md)
   - 按模板整理研究内容到一个Word文档
   - 上传Word文档并解析
   - 选择文献库
   - 配置各章节使用的模型
   - 点击「开始全自动写作」

## 📖 Tab功能说明

### Tab 1: 范文风格分析
上传目标期刊的论文范文，系统自动分析其写作风格、结构和表达偏好，生成风格指南供后续写作参考。

### Tab 2: 文献数据库管理
从Web of Science等数据库导出文献，建立文献库。

**导出要求**：
- **格式**: 必须导出为Plain Text File（纯文本文件）格式
- **内容**: 包含完整的文献信息（标题、作者、摘要等）

系统会自动解析导入的文献文件，支持多库选择，写作时自动引用相关文献。

### Tab 3: 一键写作（核心功能）

```
工作流程：
1. 上传研究文档（Word格式）
   ├── 解析文档提取文字、表格、图片
   └── AI自动分析图表内容

2. 确认研究数据
   ├── 查看提取的文本内容
   ├── 确认表格分析结果
   └── 确认图表描述

3. 选择文献库（多选）
   └── 合并多个文献库的引用

4. 配置模型
   ├── 引言 → GPT-4o（结构化写作）
   ├── 方法 → GPT-4o（精确描述）
   ├── 结果 → GPT-4o（数据呈现）
   ├── 讨论 → Claude-Sonnet-4.5（批判性分析）
   ├── 摘要 → GPT-4o（简洁总结）
   └── 结论 → Claude-Sonnet-4.5（深度思考）

5. 开始写作
   └── 自动生成各章节并整合
```

## 📁 项目结构

```
paper_writer/
├── app.py                          # Streamlit网页界面
├── research_content_template.md      # 研究内容整理模板
├── config/
│   └── config.yaml                 # 配置文件
├── src/
│   ├── __init__.py
│   ├── analyzer/                   # 风格分析模块
│   │   └── journal_style_analyzer.py
│   ├── coordinator/                # Agent协调模块
│   │   ├── __init__.py
│   │   └── multi_agent_coordinator.py  # 多Agent协调器
│   ├── document_processor/         # 文档处理模块
│   │   ├── __init__.py
│   │   ├── simple_parser.py        # 简单文档解析
│   │   └── word_analyzer.py        # Word文档分析（含图表）
│   ├── integrator/                 # 草稿整合模块
│   │   └── draft_integrator.py
│   ├── literature/                 # 文献数据库模块
│   │   └── db_manager.py
│   └── model_router/               # 模型路由模块
├── input/                          # 输入文件目录
│   ├── sample_papers/              # 范文样本
│   └── background.md               # 研究背景
├── sample_papers/                  # 风格分析范文
├── literature_exports/             # Web of Science文献导出
├── output/                         # 输出文件目录
│   ├── style/                      # 风格分析结果
│   ├── sections/                   # 各章节草稿
│   │   ├── abstract.md
│   │   ├── introduction.md
│   │   ├── methods.md
│   │   ├── results.md
│   │   ├── discussion.md
│   │   └── conclusion.md
│   └── final/                      # 最终论文
│       └── final_draft.md
└── requirements.txt                # 依赖列表
```

## 🛠️ 安装依赖

```bash
pip install -r requirements.txt

# 可选：spacy模型（用于NLP处理）
python -m spacy download en_core_web_sm
```

## ⚙️ 配置说明

编辑 `config/config.yaml`：

```yaml
api:
  base_url: "http://127.0.0.1:13148/v1"  # API代理地址
  api_key: ""                             # API密钥

models:
  # 各章节默认模型配置
  introduction: "GPT-4o"
  methods: "GPT-4o"
  results: "GPT-4o"
  discussion: "Claude-Sonnet-4.5"
  abstract: "GPT-4o"
  conclusion: "Claude-Sonnet-4.5"

document_processing:
  max_image_size: "2048x2048"
  table_analysis_limit: 100
```

## 💡 使用建议

1. **研究内容整理**: 下载「research_content_template.md」，按模板结构整理所有研究内容到一个Word文档
2. **图表处理**: 将数据表格和图表直接粘贴到Word文档中，系统会自动提取分析
3. **模型选择**:
   - 结构化内容（引言、方法、结果、摘要）→ GPT-4o
   - 深度分析（讨论、结论）→ Claude-Sonnet-4.5
4. **文献引用**: 建立文献库可自动引用相关论文，提高学术性

## 📝 依赖列表

- Python 3.9+
- streamlit >= 1.28.0
- pandas >= 1.5.0
- python-docx >= 0.8.11
- openpyxl >= 3.0.0
- requests >= 2.31.0
- anthropic-sdk >= 0.2.0  # 可选

## 📄 许可证

MIT License
