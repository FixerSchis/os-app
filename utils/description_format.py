"""Substitute {rank} and {num} maths in descriptions.

The same placeholders mods already use are available in skill descriptions.
{rank} and {num} both mean the current count. A single operation such as
{rank * 30} is shown as (30/rank) before a rank is chosen. Richer expressions
such as {70 - rank * 10} are calculated directly.
"""

import ast
import re

_BRACE_PATTERN = re.compile(r"\{([^{}]*)\}")
_VARIABLE_PATTERN = re.compile(r"(?:rank|num)\Z")
_SIMPLE_OPERATION_PATTERN = re.compile(r"(?:rank|num)\s*([*+\-/])\s*(\d+)\Z")


def format_rank_description(description, count, *, per_rank=False):
    """Replace rank placeholders in description.

    per_rank annotates a single {rank * 30} style operation as (30/rank),
    which is how an unpurchased mod or skill is shown.
    """
    if not description:
        return ""

    try:
        count = int(count)
    except (TypeError, ValueError):
        return description

    def replace(match):
        original = match.group(0)
        expression = match.group(1).strip()
        if not expression or len(expression) > 200:
            return original

        if _VARIABLE_PATTERN.fullmatch(expression):
            return str(count)

        operation = _SIMPLE_OPERATION_PATTERN.fullmatch(expression)
        if operation:
            try:
                result = _apply_operation(count, operation.group(1), int(operation.group(2)))
            except ZeroDivisionError:
                return original
            if per_rank:
                return f"({result}/rank)"
            return str(result)

        try:
            result = _evaluate_expression(expression, count)
        except (SyntaxError, ValueError, ZeroDivisionError, TypeError, OverflowError):
            return original
        return str(result)

    return _BRACE_PATTERN.sub(replace, description)


def _apply_operation(count, operator, operand):
    if operator == "*":
        return count * operand
    if operator == "+":
        return count + operand
    if operator == "-":
        return count - operand
    if operator == "/":
        if operand == 0:
            raise ZeroDivisionError
        return count // operand
    raise ValueError("unsupported operation")


def _evaluate_expression(expression, count):
    tree = ast.parse(expression, mode="eval")
    return _evaluate_node(tree.body, count)


def _evaluate_node(node, count):
    if isinstance(node, ast.Constant):
        if isinstance(node.value, bool) or not isinstance(node.value, int):
            raise ValueError("only whole numbers are allowed")
        return node.value

    if isinstance(node, ast.Name):
        if node.id not in {"rank", "num"}:
            raise ValueError("unknown name")
        return count

    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        value = _evaluate_node(node.operand, count)
        if isinstance(node.op, ast.USub):
            return -value
        return value

    if isinstance(node, ast.BinOp) and isinstance(
        node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv)
    ):
        left = _evaluate_node(node.left, count)
        right = _evaluate_node(node.right, count)
        if isinstance(node.op, ast.Add):
            return left + right
        if isinstance(node.op, ast.Sub):
            return left - right
        if isinstance(node.op, ast.Mult):
            return left * right
        if right == 0:
            raise ZeroDivisionError
        return left // right

    raise ValueError("unsupported expression")
