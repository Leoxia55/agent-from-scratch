"""这是Agent 工具助手类
把普通 Python 函数转换成大模型可以识别的 Tool 定义，并执行模型返回的 Tool Call。
它承担了两部分工作：
 1. **注册工具**：读取函数签名、类型注解和文档字符串，生成 OpenAI function calling 格式的 JSON Schema。
 2. **执行工具**：接收模型返回的工具调用，解析参数并调用对应的 Python 函数。
"""

import inspect
import json
from typing import Any, get_args, get_origin, get_type_hints


def function_to_input_schema(func: Any) -> dict[str, Any]:
    """把一个Python 的函数签名转换成工具的 JSON Schema"""

    try:
        hints = get_type_hints(func)

    except Exception:
        hints = {
            name: param.annotation
            for name, param in inspect.signature(func).parameters.items()
            if param.annotation is not inspect.Parameter.empty
        }
    sig = inspect.signature(func)

    properties: dict[str, Any] = {}
    required: list[str] = []

    for name, param in sig.parameters.items():
        if name in ("self", "context"):
            continue

        prop: dict[str, Any] = {}
        hint = hints.get(name)

        if hint == str:
            prop["type"] = "string"
        elif hint == int:
            prop["type"] = "integer"
        elif hint == float:
            prop["type"] = "number"
        elif hint == bool:
            prop["type"] = "boolean"
        elif hint is list or get_origin(hint) is list:
            prop["type"] = "array"
            # Try to get item type
            args = get_args(hint)
            if args:
                item_type = args[0]
                items_schema: dict[str, Any]
                if item_type == str:
                    items_schema = {"type": "string"}
                elif item_type == int:
                    items_schema = {"type": "integer"}
                elif hasattr(item_type, "model_json_schema"):
                    items_schema = item_type.model_json_schema()
                else:
                    items_schema = {"type": "string"}
                prop["items"] = items_schema
        elif hint is not None and hasattr(hint, "model_json_schema"):
            # Pydantic model
            prop = hint.model_json_schema()
        else:
            prop["type"] = "string"

        # 根据参数名生成了一个描述，待改进从函数描述中获取
        prop["description"] = f"Parameter:{name}"

        properties[name] = prop

        if param.default is inspect.Parameter.empty:
            required.append(name)

    schema = {"type": "object", "properties": properties}
    if required:
        schema["required"] = required

    return schema


def format_tool_definition(name: str, description: str, parameters: dict) -> dict:
    """把工具函数定义格式化成一个 openai function calling format"""
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": parameters,
        },
    }


def function_to_tool_definition(func) -> dict:
    """将 Python 函数转换为 OpenAI 格式的工具定义。
    使用函数名称、文档字符串以及类型提示.
    """

    name = func.__name__
    description = inspect.getdoc(func) or f"Function: {name}"
    parameters = function_to_input_schema(func)
    return format_tool_definition(name, description, parameters)


def tool_execution(tool_box: dict, tool_call) -> str:
    """使用工具_box 映射执行一次工具调用.

    Args:
        tool_box: Dict mapping tool names to callables
        tool_call: Tool call object with function.name and function.arguments
    """

    func_name = tool_call.function.name
    if func_name not in tool_box:
        return f"Error: Unknown tool '{func_name}'"

    try:
        args = json.loads(tool_call.function.arguments)
        result = tool_box[func_name](**args)
        return str(result)
    except Exception as e:
        return f"Error executing {func_name}: {str(e)}"
