"""Logging middleware — pretty-prints CodeAct execute_code blocks and tool call I/O."""

from __future__ import annotations

import time
from collections.abc import Awaitable, Callable
from typing import Any

from agent_framework import FunctionInvocationContext, function_middleware

_CYAN = "\033[36m"
_YELLOW = "\033[33m"
_GREEN = "\033[32m"
_RED = "\033[31m"
_DIM = "\033[2m"
_BOLD = "\033[1m"
_RESET = "\033[0m"
_LINE = "─" * 60


def _to_dict(arguments: Any) -> dict[str, Any]:
    """Safely convert arguments (dict, Mapping, or BaseModel) to a plain dict."""
    if isinstance(arguments, dict):
        return arguments
    if hasattr(arguments, "model_dump"):
        return arguments.model_dump()
    if hasattr(arguments, "__dict__"):
        return vars(arguments)
    return {}


@function_middleware
async def log_tool_calls(
    context: FunctionInvocationContext,
    call_next: Callable[[], Awaitable[None]],
) -> None:
    """Log every tool invocation that passes through the agent middleware pipeline.

    For ``execute_code`` calls it pretty-prints the model-generated Python code
    block so you can visually see CodeAct collapsing multiple tool calls into a
    single sandbox execution turn.

    For all other tool calls it shows: function name, arguments, return value,
    and elapsed time.
    """
    function_name = context.function.name
    arguments = _to_dict(context.arguments)

    if function_name == "execute_code" and "code" in arguments:
        print(f"\n{_YELLOW}{_BOLD}{_LINE}")
        print("▶  execute_code  (CodeAct sandbox — model-generated Python)")
        print(f"{_LINE}{_RESET}")
        print(arguments["code"])
        print(f"{_YELLOW}{_LINE}{_RESET}")
    else:
        pairs = ", ".join(f"{k}={v!r}" for k, v in arguments.items())
        print(f"\n{_CYAN}▶ {function_name}({pairs}){_RESET}")

    start = time.perf_counter()
    await call_next()
    elapsed = time.perf_counter() - start

    result = context.result

    if function_name == "execute_code" and isinstance(result, list):
        for output in result:
            if output.type == "text" and output.text:
                print(f"{_GREEN}stdout:\n{output.text}{_RESET}", end="")
            elif output.type == "error" and output.error_details:
                print(f"{_RED}stderr:\n{output.error_details}{_RESET}", end="")
    else:
        print(f"{_CYAN}◀ {function_name} → {result!r}{_RESET}")

    print(f"{_DIM}  ({elapsed:.4f}s){_RESET}")
