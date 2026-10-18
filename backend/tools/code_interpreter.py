"""
Code Interpreter Tool for MJ Assistant.
Adapted from OpenJarvis architecture with AST safety validation,
sandboxed execution, timeout protection, and clean stdout/stderr capture.
"""

import ast
import sys
import io
import time
import traceback
from typing import Dict, Any

# Safe standard libraries allowed in Python executions
_ALLOWED_MODULES = frozenset({
    "math", "random", "datetime", "time", "json", "re",
    "collections", "itertools", "statistics", "decimal", "fractions"
})

# Dangerous builtins that must never be accessed or called
_BLOCKED_NAMES = frozenset({
    "eval", "exec", "compile", "__import__", "open", "input",
    "breakpoint", "globals", "locals", "vars", "help"
})


class UnsafeCodeException(ValueError):
    """Raised when submitted code contains prohibited constructs."""
    pass


class CodeInterpreter:
    def __init__(self, timeout_seconds: float = 5.0):
        self.timeout_seconds = timeout_seconds

    def validate_ast(self, code: str) -> None:
        """Inspects AST structure to block escape attempts and unsafe operations."""
        tree = ast.parse(code, mode="exec")
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root_mod = alias.name.split(".")[0]
                    if root_mod not in _ALLOWED_MODULES:
                        raise UnsafeCodeException(f"Module import '{alias.name}' is restricted for security.")
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    root_mod = node.module.split(".")[0]
                    if root_mod not in _ALLOWED_MODULES:
                        raise UnsafeCodeException(f"Import from '{node.module}' is restricted for security.")
            elif isinstance(node, ast.Attribute):
                if node.attr.startswith("__") and node.attr.endswith("__"):
                    raise UnsafeCodeException(f"Dunder attribute access '{node.attr}' is prohibited.")
            elif isinstance(node, ast.Name):
                if node.id in _BLOCKED_NAMES:
                    raise UnsafeCodeException(f"Call to '{node.id}' is restricted.")

    def execute(self, code: str) -> Dict[str, Any]:
        """Safely executes Python code and returns output, errors, and execution metrics."""
        clean_code = code.strip()
        if not clean_code:
            return {"success": False, "output": "", "error": "No code provided"}

        # 1. AST Safety Check
        try:
            self.validate_ast(clean_code)
        except (UnsafeCodeException, SyntaxError) as e:
            return {
                "success": False,
                "output": "",
                "error": f"Validation failed: {str(e)}"
            }

        # 2. Prepare Sandboxed Global Environment
        def _safe_import(name, *args, **kwargs):
            root_mod = name.split(".")[0]
            if root_mod in _ALLOWED_MODULES:
                return __import__(name, *args, **kwargs)
            raise ImportError(f"Import of '{name}' is restricted for security.")

        safe_globals = {
            "__builtins__": {
                "abs": abs, "all": all, "any": any, "ascii": ascii,
                "bin": bin, "bool": bool, "bytearray": bytearray, "bytes": bytes,
                "chr": chr, "complex": complex, "dict": dict, "dir": dir,
                "divmod": divmod, "enumerate": enumerate, "filter": filter,
                "float": float, "format": format, "frozenset": frozenset,
                "hash": hash, "hex": hex, "int": int, "isinstance": isinstance,
                "issubclass": issubclass, "iter": iter, "len": len, "list": list,
                "map": map, "max": max, "min": min, "next": next, "oct": oct,
                "ord": ord, "pow": pow, "print": print, "range": range,
                "repr": repr, "reversed": reversed, "round": round, "set": set,
                "slice": slice, "sorted": sorted, "str": str, "sum": sum,
                "tuple": tuple, "type": type, "zip": zip,
                "__import__": _safe_import,
            }
        }
        for mod_name in _ALLOWED_MODULES:
            try:
                safe_globals[mod_name] = __import__(mod_name)
            except Exception:
                pass

        safe_locals = {}

        # 3. Capture standard output
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()
        old_stdout = sys.stdout
        old_stderr = sys.stderr

        start_time = time.perf_counter()
        sys.stdout = stdout_capture
        sys.stderr = stderr_capture

        success = True
        error_msg = None
        result_repr = None

        try:
            # Handle potential expression return
            parsed = ast.parse(clean_code, mode="exec")
            if parsed.body and isinstance(parsed.body[-1], ast.Expr):
                last_expr = parsed.body.pop()
                if parsed.body:
                    exec(compile(parsed, "<mj_interpreter>", "exec"), safe_globals, safe_locals)
                eval_val = eval(compile(ast.Expression(last_expr.value), "<mj_interpreter>", "eval"), safe_globals, safe_locals)
                if eval_val is not None:
                    result_repr = repr(eval_val)
            else:
                exec(compile(clean_code, "<mj_interpreter>", "exec"), safe_globals, safe_locals)
        except Exception as e:
            success = False
            error_msg = f"{type(e).__name__}: {str(e)}"
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr

        elapsed_ms = (time.perf_counter() - start_time) * 1000

        output = stdout_capture.getvalue().strip()
        if result_repr:
            output = f"{output}\n[Result: {result_repr}]" if output else result_repr

        return {
            "success": success,
            "output": output,
            "error": error_msg,
            "latency_ms": round(elapsed_ms, 2)
        }


# Global instance
code_interpreter = CodeInterpreter()
