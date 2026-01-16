# UnstructuredIO 本地部署指南

## 方法1：使用 Docker（推荐）

### 步骤1：确保Docker Desktop正在运行
在Windows开始菜单搜索并打开 **"Docker Desktop"**，等待右下角出现鲸鱼图标。

### 步骤2：下载并运行容器（需要约6GB空间）
```bash
# 这个命令会自动下载镜像（约6GB），需要5-15分钟
docker run -d --name unstructured-api -p 8000:8000 unstructuredio/unstructured:0.14.8
```

### 步骤3：验证是否运行成功
```bash
# 检查容器状态
docker ps

# 应该显示类似：
# CONTAINER ID   IMAGE                           COMMAND   CREATED   STATUS    PORTS
# abc123def456   unstructuredio/unstructured:0.14.8   "/app/start-api-server"   2 minutes ago   Up 2 minutes   0.0.0.0:8000->8000/tcp   unstructured-api

# 测试API健康
curl http://localhost:8000/healthcheck

# 预期输出: {"status":"OK"}
```

### 步骤4：如果下载太慢，可以试试
```bash
# 停止并删除失败的容器
docker rm -f unstructured-api 2>/dev/null

# 使用国内镜像加速（如果你的Docker配置了镜像加速器）
# 或者尝试分步下载：
docker pull unstructuredio/unstructured:0.14.8
```

---

## 方法2：本地pip安装（网络要求较低）

### 步骤1：安装Python依赖
```bash
cd E:\AI_projects\学术写作\paper_writer
pip install "unstructured[all-docs]" --quiet
```

### 步骤2：安装系统依赖（Windows）
1. 安装 Tesseract OCR：
   - 下载地址：https://github.com/UB-Mannheim/tesseract/wiki
   - 安装后添加到系统PATH

2. 安装 poppler（用于PDF处理）：
   - 下载地址：https://github.com/oschwartz10612/poppler-windows/releases/
   - 解压后添加到系统PATH

### 步骤3：测试安装
```bash
python -c "from unstructured.partition.auto import partition; print('OK')"
```

---

## 方法3：使用现有PDF工具（最简单）

如果你已经安装了 `pdfplumber`，可以直接使用，不需要UnstructuredIO：

```bash
# 确保已安装
pip install pdfplumber openpyxl python-docx -q

# 测试
python -c "
from src.document_processor import DocumentProcessor
p = DocumentProcessor(use_api=False)
elements = p.parse('input/sample_papers/sample_paper_1.txt')
print(f'解析成功: {len(elements)} 个元素')
"
```

---

## 配置切换

### 使用UnstructuredIO API（方法1）
编辑 `config/config.yaml`：
```yaml
document_processing:
  provider: "unstructured"
  api_url: "http://localhost:8000"
  strategy: "auto"
```

### 使用本地降级解析器（方法2或3）
```yaml
document_processing:
  provider: "local"
```

---

## 故障排除

### Docker下载超时
```bash
# 检查网络
ping registry-1.docker.io

# 使用镜像加速器（编辑Docker Desktop设置 -> Docker Engine）
{
  "registry-mirrors": [
    "https://docker.mirrors.ustc.edu.cn",
    "https://hub-mirror.c.163.com"
  ]
}
```

### 端口被占用
```bash
# 查看8000端口占用
netstat -ano | findstr :8000

# 停止占用端口的程序，或使用其他端口
docker run -d --name unstructured-api -p 8080:8000 unstructuredio/unstructured:0.14.8
```

### 容器启动失败
```bash
# 查看日志
docker logs unstructured-api

# 常见问题：内存不足（至少需要4GB）
# 解决方法：增加Docker Desktop内存限制
```

---

## 快速测试命令

安装完成后，运行以下命令验证：

```bash
cd E:\AI_projects\学术写作\paper_writer

# 测试1：文档处理器
python -c "
from document_processor import DocumentProcessor
p = DocumentProcessor()
print('[OK] 文档处理器初始化成功')

# 如果使用API模式，会显示：
# [OK] UnstructuredIO API健康检查通过
"

# 测试2：完整流程
python -m src.main analyze input/sample_papers output/style --journal "Nature Communications"
```
