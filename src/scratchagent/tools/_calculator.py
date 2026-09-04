""" 一个简单的数学计算工具"""

def calculator(operator: str, first_number: float, second_number: float) -> float:
    """执行简单的数学计算.

    Args:
        operator: Arithmetic operation - add, subtract, multiply, or divide
        first_number: First number
        second_number: Second number
    """
    if operator == "add":
        return first_number + second_number
    elif operator == "subtract":
        return first_number - second_number
    elif operator == "multiply":
        return first_number * second_number
    elif operator == "divide":
        if second_number == 0:
            raise ValueError("Cannot divide by zero")
        return first_number / second_number
    else:
        raise ValueError(f"Unknown operator: {operator}")