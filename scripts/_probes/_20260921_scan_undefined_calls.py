import re
import sys

KEYWORDS = {
    "if", "for", "while", "switch", "catch", "function", "return", "typeof",
    "in", "of", "new", "delete", "void", "yield", "await", "do", "else",
    "throw", "try", "finally", "with", "case", "default", "break", "continue",
    "var", "let", "const", "class", "extends", "super", "this", "null",
    "true", "false", "undefined", "instanceof", "get", "set", "static",
    "async", "import", "export", "from", "as",
}

KNOWN_GLOBALS = {
    "window", "document", "console", "Math", "JSON", "Object", "Array",
    "String", "Number", "Boolean", "Date", "RegExp", "Map", "Set",
    "WeakMap", "WeakSet", "Promise", "Symbol", "Error", "TypeError",
    "RangeError", "SyntaxError", "fetch", "URL", "URLSearchParams",
    "FormData", "Headers", "Request", "Response", "Intl", "isNaN",
    "isFinite", "parseInt", "parseFloat", "encodeURIComponent",
    "decodeURIComponent", "encodeURI", "decodeURI", "setTimeout",
    "clearTimeout", "setInterval", "clearInterval", "requestAnimationFrame",
    "cancelAnimationFrame", "alert", "confirm", "prompt", "structuredClone",
    "Chart", "echarts", "IQTheme", "Node", "Element", "HTMLElement",
    "CustomEvent", "Event", "MutationObserver", "IntersectionObserver",
    "ResizeObserver", "localStorage", "sessionStorage", "navigator",
    "location", "history", "getComputedStyle", "matchMedia", "btoa", "atob",
    "self", "globalThis", "performance", "crypto", "gtag", "dataLayer",
    "requestIdleCallback", "cancelIdleCallback", "queueMicrotask",
    "ChartAnnotation", "webkitURL", "ClipboardItem", "Blob", "FileReader",
    "customElements", "Proxy", "Reflect", "BigInt", "escape", "unescape",
    "print", "open", "close", "focus", "blur", "scroll", "scrollTo",
    "scrollBy",
}


def strip_strings_and_comments(src):
    out = []
    i = 0
    n = len(src)
    while i < n:
        c = src[i]
        if c == "/" and i + 1 < n and src[i + 1] == "/":
            j = src.find("\n", i)
            if j == -1:
                j = n
            out.append(" " * (j - i))
            i = j
        elif c == "/" and i + 1 < n and src[i + 1] == "*":
            j = src.find("*/", i + 2)
            if j == -1:
                j = n
            else:
                j += 2
            out.append(" " * (j - i))
            i = j
        elif c in ("'", '"'):
            quote = c
            j = i + 1
            while j < n and src[j] != quote:
                if src[j] == "\\":
                    j += 1
                j += 1
            j = min(j + 1, n)
            out.append(" " * (j - i))
            i = j
        elif c == "`":
            # template literal: keep ${...} expressions, blank out the rest
            j = i + 1
            buf = ["`"]
            while j < n and src[j] != "`":
                if src[j] == "\\":
                    buf.append(" ")
                    j += 1
                    if j < n:
                        buf.append(" ")
                        j += 1
                    continue
                if src[j] == "$" and j + 1 < n and src[j + 1] == "{":
                    depth = 1
                    k = j + 2
                    expr_start = k
                    while k < n and depth > 0:
                        if src[k] == "{":
                            depth += 1
                        elif src[k] == "}":
                            depth -= 1
                        k += 1
                    expr = src[expr_start:k - 1]
                    buf.append("  ")  # for "${"
                    buf.append(expr)
                    buf.append(" ")  # for "}"
                    j = k
                    continue
                buf.append(" ")
                j += 1
            j = min(j + 1, n)
            out.append("".join(buf) + " ")
            i = j
        else:
            out.append(c)
            i += 1
    return "".join(out)


def find_defined_names(src):
    defined = set()
    for m in re.finditer(r"\bfunction\s*\*?\s*([A-Za-z_$][A-Za-z0-9_$]*)\s*\(", src):
        defined.add(m.group(1))
    for m in re.finditer(r"\b(?:const|let|var)\s+([A-Za-z_$][A-Za-z0-9_$]*)\s*[=;,]", src):
        defined.add(m.group(1))
    for m in re.finditer(r"\bclass\s+([A-Za-z_$][A-Za-z0-9_$]*)", src):
        defined.add(m.group(1))
    # destructuring const {a, b: c} = ... / const [a,b] = ...
    for m in re.finditer(r"\b(?:const|let|var)\s*\{([^}]*)\}\s*=", src):
        for part in m.group(1).split(","):
            part = part.strip()
            if not part:
                continue
            name = part.split(":")[-1].strip().split("=")[0].strip()
            name = name.lstrip("...").strip()
            if re.match(r"^[A-Za-z_$][A-Za-z0-9_$]*$", name):
                defined.add(name)
    for m in re.finditer(r"\b(?:const|let|var)\s*\[([^\]]*)\]\s*=", src):
        for part in m.group(1).split(","):
            part = part.strip().lstrip("...").strip()
            if re.match(r"^[A-Za-z_$][A-Za-z0-9_$]*$", part):
                defined.add(part)
    # function params (named function + anonymous function + arrow with parens)
    for m in re.finditer(r"function\s*\*?\s*[A-Za-z_$0-9]*\s*\(([^)]*)\)", src):
        for part in m.group(1).split(","):
            name = part.strip().lstrip("...").split("=")[0].strip()
            name = re.sub(r"[{}\[\]]", "", name).strip()
            if re.match(r"^[A-Za-z_$][A-Za-z0-9_$]*$", name):
                defined.add(name)
    for m in re.finditer(r"\(([^()]*)\)\s*=>", src):
        for part in m.group(1).split(","):
            name = part.strip().lstrip("...").split("=")[0].strip()
            name = re.sub(r"[{}\[\]]", "", name).strip()
            if re.match(r"^[A-Za-z_$][A-Za-z0-9_$]*$", name):
                defined.add(name)
    for m in re.finditer(r"([A-Za-z_$][A-Za-z0-9_$]*)\s*=>", src):
        defined.add(m.group(1))
    for m in re.finditer(r"\bcatch\s*\(\s*([A-Za-z_$][A-Za-z0-9_$]*)", src):
        defined.add(m.group(1))
    for m in re.finditer(r"\bfor\s*\(\s*(?:const|let|var)\s+([A-Za-z_$][A-Za-z0-9_$]*)", src):
        defined.add(m.group(1))
    return defined


def find_calls(src):
    calls = {}
    for m in re.finditer(r"(?<![.\w$])([A-Za-z_$][A-Za-z0-9_$]*)\s*\(", src):
        name = m.group(1)
        if name in KEYWORDS:
            continue
        line = src.count("\n", 0, m.start()) + 1
        calls.setdefault(name, []).append(line)
    return calls


def main():
    path = sys.argv[1]
    with open(path, "r", encoding="utf-8") as f:
        html = f.read()
    scripts = re.findall(r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>", html, re.DOTALL)
    combined = "\n".join(scripts)
    stripped = strip_strings_and_comments(combined)
    defined = find_defined_names(stripped)
    calls = find_calls(stripped)
    unresolved = {
        name: lines for name, lines in calls.items()
        if name not in defined and name not in KNOWN_GLOBALS
    }
    print(f"=== {path} ===")
    if not unresolved:
        print("  no unresolved call-site identifiers")
    else:
        for name, lines in sorted(unresolved.items()):
            print(f"  {name}  (called at source-relative lines {lines[:5]}{'...' if len(lines)>5 else ''}, {len(lines)} call sites)")


if __name__ == "__main__":
    main()
