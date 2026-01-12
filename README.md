# SQL to ER Diagram Converter

> 一个强大的工具，将 SQL DDL 语句快速转换为标准 Chen 氏关系模型（ER 图）

[![Live Demo](https://img.shields.io/badge/Demo-https://er.ylim.me-blue?style=flat-square)](https://er.ylim.me/)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

## 🎯 项目简介

SQL to ER Diagram Converter 是一个基于 Streamlit 的可视化工具，能够自动解析 SQL 创建语句，智能识别表、列、主键、外键等数据库对象，并生成美观的 ER 图。这对数据库设计、文档编写、架构分析等场景非常有用。

### ✨ 核心功能

- **SQL 解析**：支持标准 SQL DDL 语法，准确识别表结构
- **关系自动推断**：智能检测一对一、一对多、多对多关系
- **ER 图生成**：采用 Chen 氏标准关系模型，生成专业的关系图
- **实时预览**：输入 SQL 即时生成和预览 ER 图
- **导出支持**：支持多种格式导出（SVG、PNG）

## 🚀 快速开始

### 前置要求

- Python 3.10 或更高版本
- Graphviz（用于图表渲染）

### 安装 Graphviz

**Windows:**
```bash
choco install graphviz  # 使用 Chocolatey
# 或从 https://graphviz.org/download/ 下载安装
```

**macOS:**
```bash
brew install graphviz
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install graphviz
```

### 安装依赖并运行

```bash
# 1. 克隆仓库
git clone https://github.com/Ylim314/sql-to-er-tool.git
cd sql-to-er-tool

# 2. 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 运行应用
streamlit run app.py
```

应用将在 `http://localhost:8501` 打开。

## 💡 使用示例

在应用中输入 SQL：

```sql
CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE posts (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    title VARCHAR(200) NOT NULL,
    content TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE comments (
    id INT PRIMARY KEY AUTO_INCREMENT,
    post_id INT NOT NULL,
    user_id INT NOT NULL,
    content TEXT NOT NULL,
    FOREIGN KEY (post_id) REFERENCES posts(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

点击"生成 ER 图"，系统会自动生成对应的关系图。

## 📁 项目结构

```
sql-to-er-tool/
├── app.py              # 主应用程序（SQL 解析、ER 生成、UI）
├── requirements.txt    # Python 依赖
├── README.md          # 项目文档
├── CONTRIBUTING.md    # 开发指南
└── LICENSE            # MIT 许可证
```

### 核心模块说明

- **SQL 解析**：使用 `sqlparse` 库解析 SQL，提取表、列、约束等信息
- **关系推断**：基于外键约束自动识别实体间的关系类型
- **ER 图渲染**：采用 `graphviz` 生成标准 Chen 氏关系模型的可视化图表

## 🛠️ 开发指南

### 代码规范

遵循 PEP 8 规范：
- 函数和变量：`snake_case`
- 类：`PascalCase`
- 常量：`UPPER_SNAKE_CASE`
- 使用类型提示

### 本地开发

```bash
# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # 或 .venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 可选：安装开发工具
pip install ruff mypy pytest

# 运行代码检查
ruff check app.py
mypy app.py
```

### 贡献

详见 [CONTRIBUTING.md](CONTRIBUTING.md) 了解开发工作流和提交指南。

## 📋 路线图

- [ ] 支持更多 SQL 方言（MySQL、PostgreSQL、Oracle 等）
- [ ] 添加自动化测试套件
- [ ] 支持关系图模式（1:1、1:N、N:M）的更灵活配置
- [ ] 在线编辑器增强功能
- [ ] 多语言支持

## 🐛 报告问题

发现 Bug？欢迎通过 [GitHub Issues](https://github.com/Ylim314/sql-to-er-tool/issues) 报告。

## 📝 许可证

本项目采用 [MIT License](LICENSE) 许可证 - 详见 [LICENSE](LICENSE) 文件。

## 🙏 致谢

- [Streamlit](https://streamlit.io/) - 应用框架
- [sqlparse](https://github.com/andialbrecht/sqlparse) - SQL 解析库
- [Graphviz](https://graphviz.org/) - 图表渲染引擎
- [Chen's ER Model](https://en.wikipedia.org/wiki/Entity%E2%80%93relationship_model) - 数据模型

## 📞 联系方式

- 🌐 在线体验：[https://er.ylim.me/](https://er.ylim.me/)
- 💻 GitHub：[https://github.com/Ylim314/sql-to-er-tool](https://github.com/Ylim314/sql-to-er-tool)
- 𝕏 Twitter：[https://x.com/HunterH798601](https://x.com/HunterH798601)

---

**如果这个项目对你有帮助，欢迎给个 Star ⭐**
