import ast
import re
from pathlib import Path

ZERO_WIDTH = re.compile(r"[\u200b-\u200f\u2060\ufeff]")
BIDI = re.compile(r"[\u202a-\u202e\u2066-\u2069]")
OVERRIDE = re.compile(
    r"(?i)\b(ignore (all )?previous|disregard (all )?previous|"
    r"system prompt|do not tell the user|new instructions)\b"
)


def _call_name(node: ast.AST) -> str:
    if isinstance(node, ast.Attribute):
        return node.attr
    if isinstance(node, ast.Name):
        return node.id
    return ""


def _string_constants(tree: ast.Module) -> dict[str, str]:
    constants: dict[str, str] = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant):
            if isinstance(node.value.value, str):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        constants[target.id] = node.value.value
    return constants


def _keyword(call: ast.Call, name: str, constants: dict[str, str]) -> str:
    for keyword in call.keywords:
        if keyword.arg != name:
            continue
        if isinstance(keyword.value, ast.Constant) and isinstance(
            keyword.value.value, str
        ):
            return keyword.value.value
        if isinstance(keyword.value, ast.Name):
            return constants.get(keyword.value.id, "")
    return ""


def _declarations(tree: ast.Module, constants: dict[str, str]) -> list[dict]:
    tools: list[dict] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and _call_name(node.func) == "FunctionDeclaration":
            tools.append(
                {
                    "name": _keyword(node, "name", constants) or "<unnamed>",
                    "description": _keyword(node, "description", constants),
                }
            )

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for decorator in node.decorator_list:
            target = decorator.func if isinstance(decorator, ast.Call) else decorator
            if _call_name(target) != "tool":
                continue
            description = ""
            if isinstance(decorator, ast.Call):
                description = _keyword(decorator, "description", constants)
            tools.append(
                {
                    "name": node.name,
                    "description": description or (ast.get_docstring(node) or ""),
                }
            )

    return tools


def scan_tool_descriptions(paths: list[Path | str]) -> dict:
    reviewed: list[str] = []
    findings: list[dict] = []

    for path in paths:
        source = Path(path)
        tree = ast.parse(source.read_text(encoding="utf-8"))
        constants = _string_constants(tree)

        for tool in _declarations(tree, constants):
            reviewed.append(tool["name"])
            text = tool["description"]
            reasons: list[str] = []
            if ZERO_WIDTH.search(text):
                reasons.append("zero_width")
            if BIDI.search(text):
                reasons.append("bidi_control")
            if OVERRIDE.search(text):
                reasons.append("instruction_override")
            if reasons:
                findings.append(
                    {
                        "tool": tool["name"],
                        "source": str(source),
                        "reasons": reasons,
                    }
                )

    return {
        "tools_reviewed": len(reviewed),
        "names": reviewed,
        "findings": findings,
    }
