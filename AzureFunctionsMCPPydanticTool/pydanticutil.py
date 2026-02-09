import json
from pydantic import ValidationError, BaseModel, Field


def pydantic_to_tool_properties(model: type[BaseModel]) -> str:
    """
    Convertit un modèle Pydantic en format toolProperties pour Azure Functions MCP.
    """
    schema = model.model_json_schema()
    properties = []
    
    def convert_property(name: str, prop_schema: dict, required: list) -> dict:
        tool_prop = {
            "propertyName": name,
            "propertyType": map_type(prop_schema.get("type", "string")),
            "description": prop_schema.get("description", "")
        }

        # Marquer les propriétés requises
        if name in required:
            tool_prop["isRequired"] = True
        
        # Gérer les objets nested
        if prop_schema.get("type") == "object" and "properties" in prop_schema:
            nested_props = []
            nested_required = prop_schema.get("required", [])
            for nested_name, nested_schema in prop_schema["properties"].items():
                nested_props.append(convert_property(nested_name, nested_schema, nested_required))
            tool_prop["properties"] = nested_props
        
        # Gérer les arrays
        elif prop_schema.get("type") == "array" and "items" in prop_schema:
            items_schema = prop_schema["items"]
            if items_schema.get("type") == "object":
                tool_prop["items"] = convert_property("item", items_schema, items_schema.get("required", []))
            else:
                tool_prop["items"] = {
                    "propertyType": map_type(items_schema.get("type", "string")),
                    "description": items_schema.get("description", "")
                }
        
        return tool_prop
    
    def map_type(pydantic_type: str) -> str:
        """Map Pydantic/JSON Schema types to MCP types"""
        type_mapping = {
            "string": "string",
            "number": "number",
            "integer": "number",
            "boolean": "boolean",
            "array": "array",
            "object": "object"
        }
        return type_mapping.get(pydantic_type, "string")
    
    required_fields = schema.get("required", [])
    for prop_name, prop_schema in schema.get("properties", {}).items():
        properties.append(convert_property(prop_name, prop_schema, required_fields))
    
    return json.dumps(properties)