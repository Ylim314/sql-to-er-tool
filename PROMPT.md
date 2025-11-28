# SQL to ER Diagram Converter - Complete Specification

## System / Role
你是一位精通 Python、Streamlit 和数据可视化的全栈工程师，擅长把 SQL DDL 转换为学术风格的 E-R 图（Chen's Notation）。请严格根据下面的要求输出代码，包含必要的注释说明。

---

## Project Overview
编写一个可运行的 Streamlit Web 应用，实现 SQL DDL → Chen's Notation ER 图的自动转换和可视化。

### 文件结构
```
.
├── app.py              # 主应用文件（完整可运行）
├── requirements.txt    # Python 依赖
└── schema.json         # 运行时生成的中间数据
```

---

## Functional Requirements

### 1. SQL 解析范围（明确边界）

#### 支持的 DDL 语法子集
- **CREATE TABLE**: 表定义、列定义、数据类型
- **PRIMARY KEY**:
  - Inline: `id INT PRIMARY KEY`
  - Table-level: `PRIMARY KEY (id)` 或 `PRIMARY KEY (col1, col2)`
- **FOREIGN KEY**:
  - Inline: `user_id INT REFERENCES users(id)`
  - Table-level: `FOREIGN KEY (user_id) REFERENCES users(id)`
  - 复合外键: `FOREIGN KEY (a, b) REFERENCES table(x, y)`
- **基础约束**: NOT NULL, UNIQUE, DEFAULT
- **数据类型**: 标准 SQL 类型（INT, VARCHAR, TEXT, DATE, TIMESTAMP 等）

#### 方言支持
- MySQL: 反引号 \`table\`, AUTO_INCREMENT, ENGINE=InnoDB
- PostgreSQL: 双引号 "table", SERIAL, ::type
- SQLite: 简化语法

#### 明确不支持（遇到时跳过并记录警告）
- CREATE INDEX / CREATE VIEW / CREATE TRIGGER
- ALTER TABLE / DROP TABLE
- 复杂 CHECK 约束（如涉及子查询）
- 存储过程、函数定义
- 分区表、临时表

#### 解析策略
1. **预处理**:
   - 移除单行注释（-- 和 #）和多行注释（/* */）
   - 规范化空白字符
   - 处理字符串转义
2. **主解析器**:
   - 使用 `sqlparse` 库进行词法分析
   - 正则表达式辅助提取关键信息
3. **错误处理**:
   - 记录无法解析的语句（含行号和上下文）
   - 继续解析其他语句（Fail-safe）
   - 所有错误写入 `schema.json["errors"]`

---

### 2. Join Table 自动识别

#### 识别规则（满足任一即判定为 Join Table）
1. **规则 A**: 表仅包含 2 个列，且都是外键
2. **规则 B**: 复合主键恰好由 2 个外键组成
3. **规则 C**: 包含 2 个以 `_id` 结尾的外键列，且其他列仅为：
   - 主键（自增 ID）
   - 时间戳（created_at, updated_at）
   - 软删除标记（deleted_at, is_deleted）
   - 排序字段（sort_order, position）

#### 多元关系处理
- **三元关系**（3 个外键）: 用特殊样式菱形表示，边上标注 "3-way"
- **四元及以上**: 显示警告，建议用户检查设计合理性

#### 手动覆盖机制
- 在 Streamlit sidebar 提供 **"Manual Join Tables"** 文本框
- 用户可输入表名（逗号分隔），强制标记为 Join Table
- 示例: `enrollments, order_items, user_roles`

---

### 3. Chen's Notation 完整规范

#### 图形元素
| 元素 | 形状 | Graphviz 属性 | 说明 |
|------|------|---------------|------|
| **实体** | 矩形 | `shape=box` | 表名用粗体 |
| **弱实体** | 双线矩形 | `shape=box, peripheries=2` | 依赖其他实体存在 |
| **属性** | 椭圆 | `shape=ellipse` | 列名 |
| **主键属性** | 椭圆+下划线 | `shape=ellipse, label=<u>id</u>` | 使用 HTML-like label |
| **多值属性** | 双线椭圆 | `shape=ellipse, peripheries=2` | 如 JSON 数组字段 |
| **派生属性** | 虚线椭圆 | `shape=ellipse, style=dashed` | 如计算字段（可选） |
| **联系** | 菱形 | `shape=diamond` | 关系名称 |
| **标识性关系** | 双线菱形 | `shape=diamond, peripheries=2` | 用于弱实体 |

#### 基数标注（Cardinality）
在边的标签上显示关系基数：
- **1:1** - 两端都标 "1"
- **1:N** - 一端 "1"，另一端 "N"
- **N:M** - 两端都标 "N" 和 "M"

推断规则：
- 如果外键有 UNIQUE 约束 → 1:1
- 普通外键 → N:1
- Join Table 连接的两端 → N:M

示例：
```dot
entity1 -- "1" -- relationship -- "N" -- entity2
```

#### 参与度（Participation）
- **全参与**（Total）: 双线边 `style=bold` 或 `penwidth=2`
- **部分参与**（Partial）: 单线边（默认）

推断规则：
- 外键列有 NOT NULL 约束 → 全参与
- 外键列可为 NULL → 部分参与

---

### 4. JSON Schema 格式（schema.json）

```json
{
  "entities": [
    {
      "name": "users",
      "is_weak": false,
      "columns": [
        {
          "name": "id",
          "type": "INT",
          "nullable": false,
          "is_pk": true,
          "is_fk": false,
          "is_unique": false,
          "default": null,
          "ref": null
        },
        {
          "name": "email",
          "type": "VARCHAR(255)",
          "nullable": false,
          "is_pk": false,
          "is_fk": false,
          "is_unique": true,
          "default": null,
          "ref": null
        }
      ]
    }
  ],
  "relationships": [
    {
      "name": "enrolls",
      "type": "N-M",
      "entities": ["students", "courses"],
      "via_table": "enrollments",
      "cardinality": {
        "students": "N",
        "courses": "M"
      },
      "participation": {
        "students": "partial",
        "courses": "total"
      },
      "attributes": [
        {
          "name": "enrolled_at",
          "type": "TIMESTAMP"
        },
        {
          "name": "grade",
          "type": "DECIMAL(3,2)"
        }
      ]
    },
    {
      "name": "writes",
      "type": "1-N",
      "entities": ["authors", "books"],
      "via_table": null,
      "cardinality": {
        "authors": "1",
        "books": "N"
      },
      "participation": {
        "authors": "partial",
        "books": "total"
      },
      "attributes": []
    }
  ],
  "warnings": [
    "Table 'log_entries' has 4 foreign keys (quaternary relationship) - please verify design"
  ],
  "errors": [
    {
      "line": 42,
      "statement": "CREATE TEMPORARY TABLE...",
      "message": "Temporary tables are not supported",
      "severity": "warning"
    }
  ]
}
```

---

### 5. Graphviz 渲染规则

#### 布局引擎选择
在 Streamlit sidebar 提供下拉菜单：
```python
layout_engine = st.selectbox(
    "Graph Layout",
    ["neato", "fdp", "dot", "circo", "twopi"],
    index=0,  # 默认 neato
    help="neato/fdp 适合 ER 图；dot 适合层次结构"
)
```

#### 属性显示策略
```python
show_all_attrs = st.checkbox(
    "Show All Attributes",
    value=False,
    help="取消勾选后仅显示主键和外键"
)
```

**显示逻辑**：
- `show_all_attrs = True`: 显示所有列
- `show_all_attrs = False`: 仅显示 `is_pk=True` 或 `is_fk=True` 的列

#### 图形样式配置
```dot
graph [
    rankdir=LR,           # 可选：LR（左右）或 TB（上下）
    bgcolor=white,
    fontname="Arial",
    splines=true,         # 曲线边
    nodesep=1.0,          # 节点间距
    ranksep=1.5           # 层级间距
]

node [
    fontname="Arial",
    fontsize=12
]

edge [
    fontname="Arial",
    fontsize=10,
    labeldistance=2.0
]
```

#### 颜色方案
- 实体: `fillcolor=lightblue, style=filled`
- 弱实体: `fillcolor=lightyellow, style=filled`
- 属性: `fillcolor=white, style=filled`
- 主键属性: `fillcolor=lightgreen, style=filled`
- 联系: `fillcolor=pink, style=filled`

---

### 6. Streamlit UI 布局

```python
# 页面配置
st.set_page_config(
    page_title="SQL to ER Diagram",
    page_icon="🗂️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Sidebar 配置
with st.sidebar:
    st.header("⚙️ Configuration")

    # 布局引擎
    layout = st.selectbox(...)

    # 属性显示
    show_all = st.checkbox(...)

    # 手动 Join Table
    manual_joins = st.text_area(
        "Manual Join Tables",
        placeholder="table1, table2, table3",
        help="强制标记为关系表（逗号分隔）"
    )

    # 示例 SQL
    st.subheader("📚 Example Schemas")
    if st.button("Load University Schema"):
        # 加载预定义示例
        pass

# 主布局
col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.header("📝 SQL DDL Input")
    sql_input = st.text_area(
        "Paste your SQL here",
        height=600,
        placeholder="CREATE TABLE users (\n  id INT PRIMARY KEY,\n  ...);"
    )

    parse_btn = st.button("🔄 Parse & Generate", type="primary")

with col2:
    st.header("📊 ER Diagram")

    # 图形显示区
    if parsed_data:
        st.graphviz_chart(dot_source, use_container_width=True)

        # 下载按钮
        col_a, col_b, col_c = st.columns(3)
        col_a.download_button("⬇️ DOT", dot_source, "schema.dot")
        col_b.download_button("⬇️ SVG", svg_data, "schema.svg")
        col_c.download_button("⬇️ JSON", json_data, "schema.json")

    # 日志和错误
    with st.expander("📋 Parser Log", expanded=False):
        st.json(schema["warnings"])

    with st.expander("⚠️ Errors", expanded=True):
        if schema["errors"]:
            for err in schema["errors"]:
                st.error(f"Line {err['line']}: {err['message']}")
        else:
            st.success("No errors")
```

---

### 7. 内置示例 SQL

提供 3 个复杂度递增的示例：

#### 示例 1: Simple（单表）
```sql
CREATE TABLE users (
    id INT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 示例 2: Medium（1:N 关系）
```sql
CREATE TABLE authors (
    id INT PRIMARY KEY,
    name VARCHAR(100) NOT NULL
);

CREATE TABLE books (
    id INT PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    author_id INT NOT NULL,
    published_date DATE,
    FOREIGN KEY (author_id) REFERENCES authors(id)
);
```

#### 示例 3: Complex（N:M + 弱实体）
```sql
CREATE TABLE students (
    id INT PRIMARY KEY,
    name VARCHAR(100) NOT NULL
);

CREATE TABLE courses (
    code VARCHAR(10) PRIMARY KEY,
    title VARCHAR(200) NOT NULL
);

-- Join table with attributes
CREATE TABLE enrollments (
    student_id INT NOT NULL,
    course_code VARCHAR(10) NOT NULL,
    enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    grade DECIMAL(3,2),
    PRIMARY KEY (student_id, course_code),
    FOREIGN KEY (student_id) REFERENCES students(id),
    FOREIGN KEY (course_code) REFERENCES courses(code)
);

-- Weak entity
CREATE TABLE course_sections (
    section_number INT NOT NULL,
    course_code VARCHAR(10) NOT NULL,
    instructor VARCHAR(100),
    room VARCHAR(50),
    PRIMARY KEY (course_code, section_number),
    FOREIGN KEY (course_code) REFERENCES courses(code) ON DELETE CASCADE
);
```

---

## Technical Implementation Details

### 依赖库（requirements.txt）
```txt
streamlit>=1.28.0
graphviz>=0.20.1
sqlparse>=0.4.4
```

### 核心函数架构

```python
# 1. SQL 预处理
def preprocess_sql(sql: str) -> str:
    """移除注释、规范化空白"""
    pass

# 2. 解析器
def parse_sql_ddl(sql: str) -> dict:
    """
    返回: {
        "entities": [...],
        "raw_foreign_keys": [...],
        "errors": [...]
    }
    """
    pass

# 3. 关系推断
def infer_relationships(entities: list, manual_joins: list) -> list:
    """识别 Join Table 并构建 relationships"""
    pass

# 4. Graphviz 生成
def generate_dot(schema: dict, layout: str, show_all: bool) -> str:
    """生成 DOT 语言图定义"""
    pass

# 5. 导出功能
def export_svg(dot: str) -> bytes:
    """使用 graphviz 渲染 SVG"""
    pass
```

---

## Error Handling Requirements

### 严格要求
1. **不允许静默失败**: 所有解析错误必须记录
2. **带上下文的错误信息**:
   ```python
   {
       "line": 42,
       "statement": "CREATE TABLE...",  # 前 100 字符
       "message": "Syntax error near 'ENGIN'",
       "severity": "error" | "warning"
   }
   ```
3. **Fail-safe 原则**: 一个表解析失败不影响其他表
4. **用户友好**: 错误信息用自然语言，附带修复建议

### 警告级别
- **Warning**: 不支持的功能（INDEX、VIEW）- 跳过继续
- **Error**: 语法错误 - 跳过该语句
- **Critical**: 无法生成任何实体 - 显示帮助信息

---

## Performance Optimization

### 大规模 Schema 处理
- **表数量 > 30**:
  - 默认 `show_all_attrs = False`
  - 提示用户使用过滤功能

- **表数量 > 50**:
  - 强制使用 "dot" 布局（更快）
  - 禁用属性显示
  - 显示性能警告

### 搜索与过滤（可选功能）
```python
search_term = st.text_input("🔍 Filter Tables", "")
if search_term:
    # 仅显示名称包含 search_term 的表及其直接关联
    filtered_entities = filter_by_name(entities, search_term)
```

---

## Output Requirements

### 必须提供的文件

#### 1. app.py
- 完整可运行的 Streamlit 应用
- 包含所有函数定义
- 必要的行内注释（解释复杂逻辑）
- 模块化结构（函数职责单一）

#### 2. requirements.txt
- 精确版本号
- 仅包含必要依赖

#### 3. 代码规范
- 遵循 PEP 8
- 类型提示（Python 3.9+）
- Docstrings（Google Style）

---

## Success Criteria

生成的工具必须满足：
1. ✅ 能正确解析示例 1/2/3
2. ✅ Chen notation 元素完整（实体、属性、联系、基数）
3. ✅ 自动识别 Join Table（80% 准确率）
4. ✅ 错误处理友好（显示行号和修复建议）
5. ✅ 支持 3 种布局引擎切换
6. ✅ 导出功能正常（DOT/SVG/JSON）
7. ✅ UI 响应流畅（< 2 秒渲染 20 表 schema）

---

## Final Notes

### 代码输出要求
- **不要截断代码**: 如果超长，分段输出但保证完整性
- **不要省略关键函数**: 尤其是 `parse_sql_ddl` 和 `generate_dot`
- **测试完整性**: 提供的代码应能直接运行 `streamlit run app.py`

### 优先级
1. **P0**: 基础解析 + 简单 ER 图（实体+属性+1:N 关系）
2. **P1**: Join Table 识别 + N:M 关系 + 基数标注
3. **P2**: 弱实体 + 手动覆盖 + 多种布局
4. **P3**: 搜索过滤 + 性能优化 + 样式美化

---

现在请开始实现完整的 `app.py` 和 `requirements.txt`。
