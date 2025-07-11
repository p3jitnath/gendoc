import os
import sys
import subprocess
import difflib
import toml
import re

from transformers import pipeline

# Initialize LLM
generator = pipeline("text-generation", model="Qwen/Qwen2.5-Coder-7B-Instruct")

def generate_docstring(code: str, style: str = "numpy") -> str:
    prompt = f"""
Write a {style}-style Python docstring (inside \"\"\" ) for the function below.
Include examples if appropriate.
Only generate the docstring following Ruff's D-class requirements. Do NOT include any comments, code, or extra explanation.
Start with \"\"\" and end with \"\"\". Do NOT have \"\"\" inside.

{code}
    """
    response = generator(prompt, max_new_tokens=300)[0]["generated_text"]
    print(response)

    # Remove echoed prompt if present
    response = response.split(code)[-1]

    # Extract the first triple-quoted docstring block
    match = re.search(r'("""|\'\'\')(.*?)(\1)', response, re.DOTALL)
    if match:
        docstring_content = match.group(2).strip()
        return docstring_content
    else:
        print("Warning: No valid docstring found. Returning fallback.")
        return None

def make_patch(original: str, modified: str, filename: str) -> str:
    diff = difflib.unified_diff(
        original.splitlines(keepends=True),
        modified.splitlines(keepends=True),
        fromfile=f"a/{filename}",
        tofile=f"b/{filename}"
    )
    return ''.join(diff) + "\n"

def apply_patch(patch: str):
    os.makedirs("tmp", exist_ok=True)
    patch_file = "tmp/tmp.patch"
    with open(patch_file, "w") as f:
        f.write(patch)
    result = subprocess.run(["git", "apply", patch_file], capture_output=True, text=True)
    if result.returncode != 0:
        print("Patch failed to apply:\n", result.stderr)
        sys.exit(1)
    else:
        print("Patch applied successfully.")

def get_config():
    if os.path.exists("pyproject.toml"):
        config = toml.load("pyproject.toml")
        return config.get("tool", {}).get("docstringhook", {})
    return {}

def get_ruff_output(filename):
    result = subprocess.run(["ruff", "check", "--select", "D", filename], capture_output=True, text=True)
    return result.stdout

def extract_code_blocks(filename, issues):
    with open(filename) as f:
        lines = f.readlines()
    seen = set()
    blocks = []
    for issue in issues:
        try:
            parts = issue.split(":")
            lineno = int(parts[1]) - 1  # Ruff uses 1-based line numbers
        except (IndexError, ValueError):
            continue  # Malformed issue

        if not (0 <= lineno < len(lines)):
            print(f"Skipping issue with invalid line: {issue.strip()}")
            continue
        if lineno in seen:
            continue  # Skip duplicate
        seen.add(lineno)

        line = lines[lineno]
        if "def " in line or "class " in line:
            blocks.append((lineno, line))

    return blocks

def main(filename, dry_run=False):
    cfg = get_config()
    style = cfg.get("style", "numpy")
    ruff_output = get_ruff_output(filename)
    issues = [line for line in ruff_output.splitlines() if filename in line]

    blocks = extract_code_blocks(filename, issues)

    with open(filename) as f:
        original = f.read()
    modified = original.splitlines()

    offset = 0
    for lineno, block in blocks:
        docstring = generate_docstring(block, style)
        if docstring:
            indent = " " * (len(block) - len(block.lstrip()) + 4)
            indented_docstring = [f'{indent}"""']
            indented_docstring += [f"{indent}{line.lstrip()}" for line in docstring.splitlines()]
            indented_docstring += [f'{indent}"""']
            for i, line in enumerate(indented_docstring):
                modified.insert(lineno + 1 + offset + i, line)
            offset += len(indented_docstring)

    modified_code = "\n".join(modified)
    patch = make_patch(original, modified_code, filename)

    if not patch.strip():
        print("No changes to apply.")
        return

    if dry_run:
        print("=== Dry Run: Showing patch only ===\n")
        print(patch)
    else:
        apply_patch(patch)

if __name__ == "__main__":
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print("Usage: python main.py <filename> [--dry-run]")
        sys.exit(1)

    filepath = sys.argv[1]
    dry_run_flag = len(sys.argv) == 3 and sys.argv[2] == "--dry-run"
    main(filepath, dry_run=dry_run_flag)
