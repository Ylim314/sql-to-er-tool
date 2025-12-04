"""
SQL to ER Diagram Converter
A Streamlit application that converts SQL DDL to Chen's Notation ER diagrams.
"""

import re
import json
import os
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field, asdict
import streamlit as st
import sqlparse
from sqlparse.sql import Statement, Token, TokenList, Identifier, IdentifierList, Function, Parenthesis
from sqlparse.tokens import Keyword, Name, Punctuation, String, Number, Whitespace
import graphviz

# Set Graphviz executable path
os.environ["PATH"] += os.pathsep + r"D:\soft\graphviz\bin"


# ==================== Data Classes ====================

@dataclass
class Column:
    """Represents a database column."""
    name: str
    type: str
    nullable: bool = True
    is_pk: bool = False
    is_fk: bool = False
    is_unique: bool = False
    default: Optional[str] = None
    ref: Optional[Dict[str, str]] = None  # {"table": "users", "column": "id"}


@dataclass
class Entity:
    """Represents a database table/entity."""
    name: str
    is_weak: bool = False
    columns: List[Column] = field(default_factory=list)


@dataclass
class Relationship:
    """Represents a relationship between entities."""
    name: str
    type: str  # "1-1", "1-N", "N-M"
    entities: List[str]
    via_table: Optional[str] = None
    cardinality: Dict[str, str] = field(default_factory=dict)
    participation: Dict[str, str] = field(default_factory=dict)
    attributes: List[Dict[str, str]] = field(default_factory=list)


@dataclass
class ParseError:
    """Represents a parsing error."""
    line: int
    statement: str
    message: str
    severity: str = "error"  # "error" or "warning"


# ==================== SQL Preprocessing ====================

def preprocess_sql(sql: str) -> str:
    """
    Remove comments and normalize whitespace.

    Args:
        sql: Raw SQL string

    Returns:
        Cleaned SQL string
    """
    # Remove single-line comments (-- and #)
    sql = re.sub(r'--[^\n]*', '', sql)
    sql = re.sub(r'#[^\n]*', '', sql)

    # Remove multi-line comments (/* */)
    sql = re.sub(r'/\*.*?\*/', '', sql, flags=re.DOTALL)

    # Normalize whitespace
    sql = re.sub(r'\s+', ' ', sql)
    sql = sql.strip()

    return sql


# ==================== SQL Parser ====================

def extract_column_info(column_def: str, table_level_constraints: dict) -> Optional[Column]:
    """
    Extract column information from column definition.

    Args:
        column_def: Column definition string
        table_level_constraints: Dict with table-level PK and FK info

    Returns:
        Column object or None if parsing fails
    """
    try:
        # Clean up the definition
        column_def = column_def.strip().strip(',')
        if not column_def:
            return None

        # Extract column name and type
        parts = column_def.split(None, 2)
        if len(parts) < 2:
            return None

        col_name = parts[0].strip('`"[]')
        col_type = parts[1].upper()

        # Handle types with parentheses like VARCHAR(255)
        if '(' in column_def and ')' in column_def:
            type_match = re.search(r'(\w+\([^)]+\))', column_def, re.IGNORECASE)
            if type_match:
                col_type = type_match.group(1).upper()

        # Initialize column
        col = Column(name=col_name, type=col_type)

        # Check constraints (case-insensitive)
        def_upper = column_def.upper()

        # NOT NULL
        col.nullable = 'NOT NULL' not in def_upper

        # PRIMARY KEY
        col.is_pk = 'PRIMARY KEY' in def_upper or col_name in table_level_constraints.get('primary_keys', [])

        # UNIQUE
        col.is_unique = 'UNIQUE' in def_upper

        # DEFAULT value
        default_match = re.search(r'DEFAULT\s+([^\s,)]+)', column_def, re.IGNORECASE)
        if default_match:
            col.default = default_match.group(1)

        # FOREIGN KEY (inline)
        fk_match = re.search(r'REFERENCES\s+([`"]?\w+[`"]?)\s*\(([`"]?\w+[`"]?)\)', column_def, re.IGNORECASE)
        if fk_match:
            col.is_fk = True
            ref_table = fk_match.group(1).strip('`"[]')
            ref_column = fk_match.group(2).strip('`"[]')
            col.ref = {"table": ref_table, "column": ref_column}

        return col

    except Exception as e:
        return None


def parse_create_table(statement: str) -> Tuple[Optional[Entity], List[dict], List[ParseError]]:
    """
    Parse a CREATE TABLE statement.

    Args:
        statement: CREATE TABLE SQL statement

    Returns:
        Tuple of (Entity object, foreign key list, error list)
    """
    errors = []
    foreign_keys = []

    try:
        # Extract table name
        table_match = re.search(r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?([`"]?\w+[`"]?)', statement, re.IGNORECASE)
        if not table_match:
            errors.append(ParseError(
                line=0,
                statement=statement[:100],
                message="Could not extract table name",
                severity="error"
            ))
            return None, foreign_keys, errors

        table_name = table_match.group(1).strip('`"[]')

        # Extract column definitions (everything between first and last parenthesis)
        paren_match = re.search(r'\((.*)\)', statement, re.DOTALL | re.IGNORECASE)
        if not paren_match:
            errors.append(ParseError(
                line=0,
                statement=statement[:100],
                message="Could not extract column definitions",
                severity="error"
            ))
            return None, foreign_keys, errors

        definitions = paren_match.group(1)

        # Parse table-level constraints first
        table_constraints = {'primary_keys': [], 'foreign_keys': []}

        # Extract PRIMARY KEY constraint
        pk_matches = re.findall(r'PRIMARY\s+KEY\s*\(([^)]+)\)', definitions, re.IGNORECASE)
        for pk_match in pk_matches:
            pk_cols = [col.strip().strip('`"[]') for col in pk_match.split(',')]
            table_constraints['primary_keys'].extend(pk_cols)

        # Extract FOREIGN KEY constraints
        fk_pattern = r'FOREIGN\s+KEY\s*\(([^)]+)\)\s*REFERENCES\s+([`"]?\w+[`"]?)\s*\(([^)]+)\)'
        fk_matches = re.findall(fk_pattern, definitions, re.IGNORECASE)
        for fk_match in fk_matches:
            fk_cols = [col.strip().strip('`"[]') for col in fk_match[0].split(',')]
            ref_table = fk_match[1].strip('`"[]')
            ref_cols = [col.strip().strip('`"[]') for col in fk_match[2].split(',')]

            for fk_col, ref_col in zip(fk_cols, ref_cols):
                table_constraints['foreign_keys'].append({
                    'column': fk_col,
                    'ref_table': ref_table,
                    'ref_column': ref_col
                })
                foreign_keys.append({
                    'table': table_name,
                    'column': fk_col,
                    'ref_table': ref_table,
                    'ref_column': ref_col
                })

        # Remove constraint definitions to isolate column definitions
        clean_defs = re.sub(r'PRIMARY\s+KEY\s*\([^)]+\)', '', definitions, flags=re.IGNORECASE)
        clean_defs = re.sub(r'FOREIGN\s+KEY\s*\([^)]+\)\s*REFERENCES\s+\w+\s*\([^)]+\)(?:\s+ON\s+\w+\s+\w+)*', '', clean_defs, flags=re.IGNORECASE)
        clean_defs = re.sub(r'CONSTRAINT\s+\w+\s+[^,]+', '', clean_defs, flags=re.IGNORECASE)
        clean_defs = re.sub(r'UNIQUE\s*\([^)]+\)', '', clean_defs, flags=re.IGNORECASE)
        clean_defs = re.sub(r'CHECK\s*\([^)]+\)', '', clean_defs, flags=re.IGNORECASE)
        clean_defs = re.sub(r'INDEX\s+\w+\s*\([^)]+\)', '', clean_defs, flags=re.IGNORECASE)
        clean_defs = re.sub(r'KEY\s+\w+\s*\([^)]+\)', '', clean_defs, flags=re.IGNORECASE)

        # Split into column definitions
        # Smart split that respects parentheses
        column_defs = []
        current_def = ""
        paren_depth = 0

        for char in clean_defs:
            if char == '(':
                paren_depth += 1
            elif char == ')':
                paren_depth -= 1
            elif char == ',' and paren_depth == 0:
                if current_def.strip():
                    column_defs.append(current_def.strip())
                current_def = ""
                continue
            current_def += char

        if current_def.strip():
            column_defs.append(current_def.strip())

        # Parse columns
        entity = Entity(name=table_name)

        for col_def in column_defs:
            col = extract_column_info(col_def, table_constraints)
            if col:
                # Check if this column is a foreign key from table-level constraints
                for fk in table_constraints['foreign_keys']:
                    if fk['column'] == col.name:
                        col.is_fk = True
                        col.ref = {"table": fk['ref_table'], "column": fk['ref_column']}

                entity.columns.append(col)

        # Determine if entity is weak
        # A weak entity has a composite primary key where all parts are foreign keys
        pk_cols = [col for col in entity.columns if col.is_pk]
        if len(pk_cols) > 1 and all(col.is_fk for col in pk_cols):
            entity.is_weak = True

        return entity, foreign_keys, errors

    except Exception as e:
        errors.append(ParseError(
            line=0,
            statement=statement[:100],
            message=f"Unexpected error: {str(e)}",
            severity="error"
        ))
        return None, foreign_keys, errors


def parse_sql_ddl(sql: str) -> Dict:
    """
    Parse SQL DDL and extract entities and relationships.

    Args:
        sql: SQL DDL string

    Returns:
        Dictionary with entities, relationships, warnings, and errors
    """
    result = {
        "entities": [],
        "raw_foreign_keys": [],
        "warnings": [],
        "errors": []
    }

    # Preprocess SQL
    sql = preprocess_sql(sql)

    # Split into statements
    statements = sqlparse.split(sql)

    for idx, statement in enumerate(statements):
        statement = statement.strip()
        if not statement:
            continue

        # Check for unsupported statements
        if any(keyword in statement.upper() for keyword in [
            'CREATE INDEX', 'CREATE VIEW', 'CREATE TRIGGER',
            'ALTER TABLE', 'DROP TABLE', 'CREATE PROCEDURE',
            'CREATE FUNCTION', 'CREATE TEMPORARY'
        ]):
            result['warnings'].append(f"Skipping unsupported statement: {statement[:50]}...")
            continue

        # Parse CREATE TABLE statements
        if statement.upper().startswith('CREATE TABLE'):
            entity, fks, errors = parse_create_table(statement)

            if entity:
                result['entities'].append(entity)
                result['raw_foreign_keys'].extend(fks)

            result['errors'].extend(errors)

    return result


# ==================== Relationship Inference ====================

def is_join_table(entity: Entity, manual_joins: List[str]) -> bool:
    """
    Determine if an entity is a join table.

    Args:
        entity: Entity to check
        manual_joins: List of manually specified join table names

    Returns:
        True if entity is a join table
    """
    # Manual override
    if entity.name in manual_joins:
        return True

    fk_cols = [col for col in entity.columns if col.is_fk]
    pk_cols = [col for col in entity.columns if col.is_pk]

    # Rule A: Table has exactly 2 columns and both are foreign keys
    if len(entity.columns) == 2 and len(fk_cols) == 2:
        return True

    # Rule B: Composite primary key consisting of exactly 2 foreign keys
    if len(pk_cols) == 2 and all(col.is_fk for col in pk_cols):
        return True

    # Rule C: Has 2 foreign keys ending with _id, other columns are metadata
    id_fks = [col for col in fk_cols if col.name.endswith('_id')]
    if len(id_fks) == 2:
        # Check if other columns are just metadata
        metadata_names = ['created_at', 'updated_at', 'deleted_at', 'is_deleted', 'sort_order', 'position']
        other_cols = [col for col in entity.columns if not col.is_fk and not col.is_pk]

        if all(col.name in metadata_names for col in other_cols):
            return True

    return False


def infer_cardinality_and_participation(entity_name: str, fk_column: Column) -> Tuple[str, str]:
    """
    Infer cardinality and participation for a relationship.

    Args:
        entity_name: Name of the entity
        fk_column: Foreign key column

    Returns:
        Tuple of (cardinality, participation)
    """
    # Cardinality
    if fk_column.is_unique:
        cardinality = "1"
    else:
        cardinality = "N"

    # Participation
    participation = "total" if not fk_column.nullable else "partial"

    return cardinality, participation


def infer_relationships(entities: List[Entity], manual_joins: List[str]) -> Tuple[List[Relationship], List[str]]:
    """
    Infer relationships from entities.

    Args:
        entities: List of entities
        manual_joins: List of manually specified join table names

    Returns:
        Tuple of (relationships list, warnings list)
    """
    relationships = []
    warnings = []
    entity_dict = {e.name: e for e in entities}

    # Separate join tables and regular entities
    join_tables = []
    regular_entities = []

    for entity in entities:
        if is_join_table(entity, manual_joins):
            join_tables.append(entity)
        else:
            regular_entities.append(entity)

    # Process join tables (N:M relationships)
    for join_table in join_tables:
        fk_cols = [col for col in join_table.columns if col.is_fk]

        if len(fk_cols) == 2:
            # Binary relationship (N:M)
            entity1_name = fk_cols[0].ref['table']
            entity2_name = fk_cols[1].ref['table']

            # Get relationship attributes (non-FK, non-PK columns)
            rel_attrs = []
            for col in join_table.columns:
                if not col.is_fk and not col.is_pk:
                    rel_attrs.append({"name": col.name, "type": col.type})

            # Infer participation
            participation1 = "total" if not fk_cols[0].nullable else "partial"
            participation2 = "total" if not fk_cols[1].nullable else "partial"

            rel = Relationship(
                name=join_table.name,
                type="N-M",
                entities=[entity1_name, entity2_name],
                via_table=join_table.name,
                cardinality={entity1_name: "N", entity2_name: "M"},
                participation={entity1_name: participation1, entity2_name: participation2},
                attributes=rel_attrs
            )
            relationships.append(rel)

        elif len(fk_cols) == 3:
            # Ternary relationship
            entity_names = [fk.ref['table'] for fk in fk_cols]

            rel = Relationship(
                name=join_table.name,
                type="3-way",
                entities=entity_names,
                via_table=join_table.name,
                cardinality={name: "N" for name in entity_names},
                participation={name: "partial" for name in entity_names},
                attributes=[]
            )
            relationships.append(rel)
            warnings.append(f"Table '{join_table.name}' represents a ternary (3-way) relationship")

        elif len(fk_cols) >= 4:
            # Quaternary or higher
            warnings.append(
                f"Table '{join_table.name}' has {len(fk_cols)} foreign keys (quaternary+ relationship) - please verify design"
            )

    # Process regular entities (1:N relationships)
    for entity in regular_entities:
        for col in entity.columns:
            if col.is_fk and col.ref:
                ref_table = col.ref['table']

                # Skip if referenced table is a join table
                if ref_table in [jt.name for jt in join_tables]:
                    continue

                # Determine relationship type
                if col.is_unique:
                    rel_type = "1-1"
                    card_from = "1"
                    card_to = "1"
                else:
                    rel_type = "1-N"
                    card_from = "1"
                    card_to = "N"

                # Participation
                part_from = "partial"  # Referenced entity
                part_to = "total" if not col.nullable else "partial"  # Referencing entity

                rel = Relationship(
                    name=f"{ref_table}_{entity.name}",
                    type=rel_type,
                    entities=[ref_table, entity.name],
                    via_table=None,
                    cardinality={ref_table: card_from, entity.name: card_to},
                    participation={ref_table: part_from, entity.name: part_to},
                    attributes=[]
                )
                relationships.append(rel)

    return relationships, warnings


# ==================== Graphviz DOT Generation ====================

def generate_dot(schema: Dict, layout: str = "neato", show_all_attrs: bool = True) -> str:
    """
    Generate Graphviz DOT notation for ER diagram.

    Args:
        schema: Schema dictionary with entities and relationships
        layout: Layout engine (neato, fdp, dot, circo, twopi)
        show_all_attrs: Whether to show all attributes or only keys

    Returns:
        DOT language string
    """
    entities = schema.get('entities', [])
    relationships = schema.get('relationships', [])

    dot_lines = []

    # Graph configuration
    dot_lines.append(f'graph ER {{')
    dot_lines.append(f'    layout={layout};')
    dot_lines.append(f'    rankdir=LR;')
    dot_lines.append(f'    bgcolor=white;')
    dot_lines.append(f'    fontname="Arial";')
    dot_lines.append(f'    splines=spline;')
    dot_lines.append(f'    overlap=false;')
    dot_lines.append(f'    nodesep=1.5;')
    dot_lines.append(f'    ranksep=2.0;')
    dot_lines.append(f'    sep="+25,25";')
    dot_lines.append(f'')
    dot_lines.append(f'    node [fontname="Arial", fontsize=11, margin=0.15, style=filled, fillcolor=white];')
    dot_lines.append(f'    edge [fontname="Arial", fontsize=9, labeldistance=1.5, labelangle=45];')
    dot_lines.append(f'')

    # Generate entities and attributes
    for entity in entities:
        if isinstance(entity, dict):
            entity_name = entity['name']
            is_weak = entity.get('is_weak', False)
            columns = entity.get('columns', [])
        else:
            entity_name = entity.name
            is_weak = entity.is_weak
            columns = entity.columns

        # Entity node
        peripheries = 1
        penwidth = 1.5
        dot_lines.append(
            f'    {entity_name} [shape=box, peripheries={peripheries}, penwidth={penwidth}, '
            f'width=2.0, height=0.8, fixedsize=true, '
            f'label="{entity_name}", fontsize=13, fontname="Arial Bold"];'
        )

        # Attribute nodes
        for col in columns:
            if isinstance(col, dict):
                col_name = col['name']
                is_pk = col.get('is_pk', False)
                is_fk = col.get('is_fk', False)
            else:
                col_name = col.name
                is_pk = col.is_pk
                is_fk = col.is_fk

            # Skip non-key attributes if show_all_attrs is False
            if not show_all_attrs and not is_pk and not is_fk:
                continue

            attr_id = f'{entity_name}_{col_name}'

            if is_pk:
                # Primary key: white ellipse with bold text
                dot_lines.append(f'    {attr_id} [shape=ellipse, width=1.8, height=0.6, fixedsize=true, label="{col_name}", fontname="Arial Bold"];')
            else:
                # Regular attribute: white ellipse with single border
                dot_lines.append(f'    {attr_id} [shape=ellipse, width=1.8, height=0.6, fixedsize=true, label="{col_name}"];')

            # Connect attribute to entity
            dot_lines.append(f'    {entity_name} -- {attr_id};')

        dot_lines.append(f'')

    # Generate relationships
    for idx, rel in enumerate(relationships):
        if isinstance(rel, dict):
            rel_name = rel['name']
            rel_type = rel.get('type', '')
            rel_entities = rel.get('entities', [])
            cardinality = rel.get('cardinality', {})
            participation = rel.get('participation', {})
            attributes = rel.get('attributes', [])
            via_table = rel.get('via_table')
        else:
            rel_name = rel.name
            rel_type = rel.type
            rel_entities = rel.entities
            cardinality = rel.cardinality
            participation = rel.participation
            attributes = rel.attributes
            via_table = rel.via_table

        rel_id = f'rel_{idx}'

        # Relationship node
        peripheries = 2 if rel_type == "3-way" else 1
        penwidth = 2 if rel_type == "3-way" else 1.5
        dot_lines.append(
            f'    {rel_id} [shape=diamond, peripheries={peripheries}, penwidth={penwidth}, '
            f'width=2.2, height=0.8, fixedsize=true, '
            f'label="{rel_name}", fontsize=11];'
        )

        # Connect entities to relationship
        for entity_name in rel_entities:
            card = cardinality.get(entity_name, '')
            part = participation.get(entity_name, 'partial')

            # Edge style based on participation
            penwidth = 2 if part == 'total' else 1

            # Edge label with cardinality
            label = f'  {card}  ' if card else ''

            dot_lines.append(f'    {entity_name} -- {rel_id} [label="{label}", penwidth={penwidth}];')

        # Relationship attributes
        for attr in attributes:
            if isinstance(attr, dict):
                attr_name = attr['name']
            else:
                attr_name = attr

            attr_id = f'{rel_id}_{attr_name}'
            dot_lines.append(f'    {attr_id} [shape=ellipse, width=1.8, height=0.6, fixedsize=true, label="{attr_name}"];')
            dot_lines.append(f'    {rel_id} -- {attr_id};')

        dot_lines.append(f'')

    dot_lines.append('}')

    return '\n'.join(dot_lines)


# ==================== Export Functions ====================

def export_svg(dot_source: str) -> bytes:
    """
    Render DOT source to SVG.

    Args:
        dot_source: DOT language string

    Returns:
        SVG as bytes
    """
    try:
        graph = graphviz.Source(dot_source)
        svg_data = graph.pipe(format='svg')
        return svg_data
    except Exception as e:
        st.error(f"Error rendering SVG: {str(e)}")
        return b''


# ==================== Example SQL Schemas ====================

EXAMPLE_SIMPLE = """
CREATE TABLE users (
    id INT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

EXAMPLE_MEDIUM = """
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
"""

EXAMPLE_COMPLEX = """
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
"""


# ==================== Streamlit UI ====================

def main():
    """Main Streamlit application."""

    # Page configuration
    st.set_page_config(
        page_title="SQL to ER Diagram",
        page_icon="🗂️",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Initialize session state
    if 'schema' not in st.session_state:
        st.session_state.schema = None
    if 'dot_source' not in st.session_state:
        st.session_state.dot_source = None

    # Sidebar configuration
    with st.sidebar:
        st.header("配置")

        # Layout engine
        layout_options = {
            "自动布局（推荐）": "neato",
            "自动布局（紧凑）": "fdp",
            "分层布局（树状）": "dot",
            "圆环布局": "circo",
            "放射布局": "twopi",
        }
        layout_label = st.selectbox(
            "图表布局",
            list(layout_options.keys()),
            index=0,
            help="控制 ER 图节点的大致排布方式"
        )
        layout_engine = layout_options[layout_label]

        # Attribute display
        show_all_attrs = st.checkbox(
            "显示所有属性",
            value=True,
            help="取消勾选则只显示主键和外键"
        )

        # Manual join tables
        manual_joins_input = st.text_area(
            "手动指定中间表",
            placeholder="例如：user_role, a_b, ...",
            help="强制将指定表识别为连接表（逗号分隔）",
            height=80
        )

        manual_joins = []
        if manual_joins_input:
            manual_joins = [t.strip() for t in manual_joins_input.split(',') if t.strip()]

        # Example SQL
        st.subheader("示例 SQL")

        col_a, col_b, col_c = st.columns(3)

        if col_a.button("简单示例", use_container_width=True):
            st.session_state.sql_input = EXAMPLE_SIMPLE
            st.rerun()

        if col_b.button("中等示例", use_container_width=True):
            st.session_state.sql_input = EXAMPLE_MEDIUM
            st.rerun()

        if col_c.button("复杂示例", use_container_width=True):
            st.session_state.sql_input = EXAMPLE_COMPLEX
            st.rerun()

    # Main title
    st.title("🗂️ SQL to ER Diagram Converter")
    st.markdown("Convert SQL DDL to **Chen's Notation** ER diagrams")

    # Main layout
    col1, col2 = st.columns([1, 1], gap="large")

    with col1:
        st.header("📝 SQL DDL Input")

        # Initialize default value
        if 'sql_input' not in st.session_state:
            st.session_state.sql_input = ""

        sql_input = st.text_area(
            "Paste your SQL here",
            value=st.session_state.sql_input,
            height=500,
            placeholder="CREATE TABLE users (\n  id INT PRIMARY KEY,\n  ...);"
        )

        parse_btn = st.button("🔄 Parse & Generate", type="primary", use_container_width=True)

        if parse_btn and sql_input:
            with st.spinner("Parsing SQL..."):
                # Parse SQL
                parse_result = parse_sql_ddl(sql_input)

                # Infer relationships
                if parse_result['entities']:
                    relationships, warnings = infer_relationships(
                        parse_result['entities'],
                        manual_joins
                    )

                    # Convert entities to dict for JSON serialization
                    entities_dict = [asdict(e) for e in parse_result['entities']]
                    relationships_dict = [asdict(r) for r in relationships]

                    schema = {
                        "entities": entities_dict,
                        "relationships": relationships_dict,
                        "warnings": warnings + parse_result['warnings'],
                        "errors": [asdict(e) for e in parse_result['errors']]
                    }

                    # Performance optimization
                    num_tables = len(entities_dict)
                    if num_tables > 50:
                        st.warning(f"⚠️ Large schema detected ({num_tables} tables). Forcing 'dot' layout and hiding attributes for performance.")
                        layout_engine = "dot"
                        show_all_attrs = False
                    elif num_tables > 30:
                        st.info(f"ℹ️ Medium-sized schema ({num_tables} tables). Consider using 'dot' layout for better performance.")

                    # Generate DOT
                    dot_source = generate_dot(schema, layout_engine, show_all_attrs)

                    # Store in session state
                    st.session_state.schema = schema
                    st.session_state.dot_source = dot_source

                    st.success(f"✅ Parsed {len(entities_dict)} entities and {len(relationships_dict)} relationships")
                else:
                    st.error("❌ No entities found. Please check your SQL syntax.")

    with col2:
        st.header("📊 ER Diagram")

        if st.session_state.dot_source:
            try:
                # Render diagram
                st.graphviz_chart(st.session_state.dot_source, use_container_width=True)

                # Download buttons
                st.subheader("💾 Export")
                col_download_1, col_download_2, col_download_3 = st.columns(3)

                # DOT download
                col_download_1.download_button(
                    label="⬇️ DOT",
                    data=st.session_state.dot_source,
                    file_name="schema.dot",
                    mime="text/plain",
                    use_container_width=True
                )

                # SVG download
                svg_data = export_svg(st.session_state.dot_source)
                if svg_data:
                    col_download_2.download_button(
                        label="⬇️ SVG",
                        data=svg_data,
                        file_name="schema.svg",
                        mime="image/svg+xml",
                        use_container_width=True
                    )

                # JSON download
                json_data = json.dumps(st.session_state.schema, indent=2)
                col_download_3.download_button(
                    label="⬇️ JSON",
                    data=json_data,
                    file_name="schema.json",
                    mime="application/json",
                    use_container_width=True
                )

            except Exception as e:
                st.error(f"❌ Error rendering diagram: {str(e)}")
        else:
            st.info("👈 Paste SQL DDL on the left and click 'Parse & Generate'")

        # Logs and errors
        if st.session_state.schema:
            schema = st.session_state.schema

            # Warnings
            if schema.get('warnings'):
                with st.expander("⚠️ Warnings", expanded=False):
                    for warning in schema['warnings']:
                        st.warning(warning)

            # Errors
            with st.expander("📋 Parser Log", expanded=bool(schema.get('errors'))):
                if schema.get('errors'):
                    for err in schema['errors']:
                        severity_icon = "❌" if err['severity'] == 'error' else "⚠️"
                        st.markdown(f"{severity_icon} **Line {err['line']}**: {err['message']}")
                        if err.get('statement'):
                            st.code(err['statement'], language="sql")
                else:
                    st.success("✅ No errors")

    # Footer
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: gray;'>"
        "Built with Streamlit • Supports MySQL, PostgreSQL, and SQLite dialects"
        "</div>",
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
