# Azure Functions MCP Pydantic Tool

Convert Pydantic models to Azure Functions MCP toolProperties format.

## Installation

```bash
pip install git+https://github.com/zecloud/azurefunctionsmcpydantic.git
```

## Usage

```python
from AzureFunctionsMCPPydanticTool import pydantic_to_tool_properties
from pydantic import BaseModel

class MyModel(BaseModel):
    name: str
    age: int
    email: str

# Convert to toolProperties
properties_json = pydantic_to_tool_properties(MyModel)
print(properties_json)
```

## License

MIT