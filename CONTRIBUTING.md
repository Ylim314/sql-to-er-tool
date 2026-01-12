# 贡献指南

感谢你对这个项目的兴趣！本文档将指导你如何参与项目开发。

## 贡献方式

- 📝 改进文档
- 🐛 报告和修复 Bug
- ✨ 提交新功能
- 🤝 代码审查
- 💡 提供建议和反馈

## 开发流程

### 1. Fork 和克隆

```bash
git clone https://github.com/YOUR_USERNAME/sql-to-er-tool.git
cd sql-to-er-tool
```

### 2. 创建开发分支

```bash
git checkout -b feature/your-feature-name
# 或用于修复 Bug：
git checkout -b fix/issue-description
```

### 3. 开发环境设置

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 4. 提交更改

遵循以下提交信息格式：
- `feat: 新增功能说明`
- `fix: Bug 修复说明`
- `refactor: 重构说明`
- `docs: 文档更新`
- `style: 代码风格调整`

### 5. 推送和创建 PR

```bash
git push origin feature/your-feature-name
```
然后在 GitHub 上创建 Pull Request。

## 代码规范

### 风格指南

- 遵循 PEP 8 规范
- 4 空格缩进
- 使用类型提示
- 添加必要的注释和文档字符串

### 命名规范

| 对象 | 规范 | 示例 |
|------|------|------|
| 函数/变量 | `snake_case` | `parse_sql_statement()` |
| 类 | `PascalCase` | `EntityRelationship` |
| 常量 | `UPPER_SNAKE_CASE` | `MAX_SQL_LENGTH` |

### 类型提示

```python
from typing import Dict, List, Optional

def extract_tables(sql: str) -> List[str]:
    """提取 SQL 中的所有表名。"""
    pass
```

## 项目结构

```
app.py              # 主应用，包含 SQL 解析、ER 生成、Streamlit UI
requirements.txt    # Python 依赖
tests/             # 测试目录（待添加）
docs/              # 文档目录（待添加）
```

## 测试

暂无自动化测试。如添加测试，请遵循：

- 使用 `pytest` 框架
- 测试文件放在 `tests/` 目录
- 文件命名：`test_*.py`
- 函数命名：`test_*`

```bash
pytest              # 运行所有测试
pytest -v          # 详细输出
pytest tests/test_parser.py  # 运行特定测试
```

## 提交 PR 时需要包含

- ✅ 清晰的功能描述
- ✅ 修复或新增功能的说明
- ✅ 相关的截图（如修改了 UI）
- ✅ 测试场景说明
- ✅ 相关 Issue 链接（如有）

## 常见问题

### 如何获得开发帮助？

在 [GitHub Discussions](https://github.com/Ylim314/sql-to-er-tool/discussions) 发起讨论，或创建 Issue 寻求帮助。

### 代码被拒了怎么办？

不要沮丧！维护者会提供具体的反馈意见。根据建议修改后重新推送即可。

## 行为准则

请遵守以下原则：

- 尊重他人
- 建设性反馈
- 开放包容
- 专注技术讨论

## 许可证

你的贡献将在 MIT License 下发布。

---

感谢你的贡献！❤️
