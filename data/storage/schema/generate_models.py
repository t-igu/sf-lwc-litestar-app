import json
from pathlib import Path

# スキーマファイルのパス
SCHEMA_PATH = Path("./schema.json")

# 出力先（複数）
OUTPUT_PATHS = [
    # apps/salesforce_app/server_app
    Path("../../../apps/salesforce_app/server/models.py"),
    Path("../../../apps/storage_app/models/models.py"),
]

def load_schema():
    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(f"Schema file not found: {SCHEMA_PATH}")
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

def python_type(type_name: str) -> str:
    """スキーマの type を Python の型表現に変換"""
    mapping = {
        "str": "str",
        "int": "int",
        "float": "float",
        "bool": "bool",
        "datetime": "datetime.datetime",
    }
    return mapping.get(type_name, type_name)

def generate_struct(model_name: str, model_def: dict) -> str:
    fields = model_def.get("fields", {})

    # 並び順：
    # 1. required=true & defaultなし
    # 2. required=true & defaultあり
    # 3. required=false（＝default=None）
    def sort_key(item):
        name, rule = item
        required = rule.get("required", False)
        default = rule.get("default", None)

        if required and default is None:
            return 0
        if required and default is not None:
            return 1
        return 2  # required=false

    sorted_fields = sorted(fields.items(), key=sort_key)

    lines = [f"class {model_name}(msgspec.Struct):"]

    for field_name, rule in sorted_fields:
        typ = python_type(rule["type"])
        required = rule.get("required", False)
        default = rule.get("default", None)

        # required=false → Optional + default=None
        if not required:
            typ = f"{typ} | None"
            lines.append(f"    {field_name}: {typ} = None")
            continue

        # required=true & defaultあり
        if default is not None:
            lines.append(f"    {field_name}: {typ} = {default!r}")
            continue

        # required=true & defaultなし
        lines.append(f"    {field_name}: {typ}")

    return "\n".join(lines)

def generate_models_py(schema: dict) -> str:
    """models.py 全体を生成"""
    lines = [
        "# AUTO-GENERATED FILE. DO NOT EDIT MANUALLY.",
        "# Generated from storage/schema/schema.json",
        "import msgspec",
        "import datetime",
        "",
    ]

    for model_name, model_def in schema["models"].items():
        struct_code = generate_struct(model_name, model_def)
        lines.append(struct_code)
        lines.append("")

    return "\n".join(lines)

def main():
    schema = load_schema()
    models_py = generate_models_py(schema)

    for path in OUTPUT_PATHS:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(models_py, encoding="utf-8")
        print(f"Generated: {path}")

if __name__ == "__main__":
    main()
