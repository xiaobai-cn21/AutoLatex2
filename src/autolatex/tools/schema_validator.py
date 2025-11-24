import json
import os
from typing import Any, Dict

from jsonschema import ValidationError, validate

SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "../config/document_schema.json")


def load_document_schema(schema_path: str = SCHEMA_PATH) -> Dict[str, Any]:
    """从文件系统加载文档Schema。"""
    with open(schema_path, "r", encoding="utf-8") as schema_file:
        return json.load(schema_file)


def validate_parsed_document(data: Dict[str, Any], schema: Dict[str, Any]) -> bool:
    """验证解析后的文档数据是否符合Schema。"""
    try:
        validate(instance=data, schema=schema)
        return True
    except ValidationError as exc:
        print(f"Parsed JSON data is NOT valid against the schema. Error: {exc.message}")
        return False
    except Exception as exc:  # pylint: disable=broad-except
        print(f"An unexpected error occurred during schema validation: {exc}")
        return False
