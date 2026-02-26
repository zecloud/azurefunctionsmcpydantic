"""Utilitaires pour convertir des modèles Pydantic en format MCP toolProperties."""
import json
from pydantic import BaseModel


def pydantic_to_tool_properties(model: type[BaseModel]) -> str:
    """
    Convertit un modèle Pydantic en format toolProperties pour Azure Functions MCP.
    Gère correctement les $ref/$defs, anyOf/oneOf (Optional), Literal, Enum,
    et les structures nested de nested.
    """
    schema = model.model_json_schema()
    defs = schema.get("$defs", schema.get("definitions", {}))

    def resolve_schema(s: dict) -> dict:
        """Résout récursivement les $ref vers les $defs."""
        if "$ref" in s:
            ref_path = s["$ref"]
            ref_name = ref_path.rsplit("/", 1)[-1]
            resolved = defs.get(ref_name, {})
            merged = {**resolved}
            for k, v in s.items():
                if k != "$ref":
                    merged[k] = v
            return resolve_schema(merged)

        for key in ("anyOf", "oneOf"):
            if key in s:
                non_null = [opt for opt in s[key] if opt.get("type") != "null"]
                if non_null:
                    resolved_inner = resolve_schema(non_null[0])
                    if "description" in s and "description" not in resolved_inner:
                        resolved_inner["description"] = s["description"]
                    return resolved_inner
                return {"type": "string", "description": s.get("description", "")}

        return s

    def map_type(json_schema_type: str) -> str:
        return {
            "string": "string", "number": "number", "integer": "number",
            "boolean": "boolean", "array": "array", "object": "object"
        }.get(json_schema_type, "string")

    def infer_type(prop_schema: dict) -> str:
        if "type" in prop_schema:
            return map_type(prop_schema["type"])
        if "enum" in prop_schema:
            return "string"
        if "properties" in prop_schema:
            return "object"
        if "items" in prop_schema:
            return "array"
        if "const" in prop_schema:
            val = prop_schema["const"]
            if isinstance(val, bool):
                return "boolean"
            if isinstance(val, (int, float)):
                return "number"
            return "string"
        return "string"

    def convert_property(name: str, prop_schema: dict, required: list) -> dict:
        prop_schema = resolve_schema(prop_schema)

        tool_prop: dict = {
            "propertyName": name,
            "propertyType": infer_type(prop_schema),
            "description": prop_schema.get("description", "")
        }

        if "enum" in prop_schema:
            tool_prop["description"] += f" (allowed values: {prop_schema['enum']})"

        if name in required:
            tool_prop["isRequired"] = True

        if prop_schema.get("type") == "object" or (
            "properties" in prop_schema and prop_schema.get("type") != "array"
        ):
            if "properties" in prop_schema:
                nested_props = []
                nested_required = prop_schema.get("required", [])
                for nested_name, nested_schema in prop_schema["properties"].items():
                    nested_props.append(
                        convert_property(nested_name, nested_schema, nested_required)
                    )
                tool_prop["properties"] = nested_props
                tool_prop["propertyType"] = "object"

        elif prop_schema.get("type") == "array" and "items" in prop_schema:
            items_schema = resolve_schema(prop_schema["items"])
            if items_schema.get("type") == "object" or "properties" in items_schema:
                tool_prop["items"] = convert_property(
                    "item", items_schema, items_schema.get("required", [])
                )
            else:
                tool_prop["items"] = {
                    "propertyType": infer_type(items_schema),
                    "description": items_schema.get("description", "")
                }

        return tool_prop

    required_fields = schema.get("required", [])
    properties = []
    for prop_name, prop_schema in schema.get("properties", {}).items():
        properties.append(convert_property(prop_name, prop_schema, required_fields))

    return json.dumps(properties)
