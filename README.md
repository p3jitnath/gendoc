# GenDoc

GenDoc is a lightweight tool for automatically generating and inserting docstrings into Python code using a large language model (LLM). It identifies undocumented functions and classes using `ruff`, generates consistent NumPy-style docstrings, and applies them as Git patches.

This project is intended as a minimal but extensible foundation for automated documentation workflows. It is especially useful during fast-paced development or hackathons where documentation can easily fall behind.

## Features

- Detects missing docstrings using `ruff`
- Generates high-quality docstrings using LLMs (e.g., Qwen2.5-Coder)
- Applies clean Git-style patches directly to your code
- Supports dry-run mode to preview docstring diffs
- Can be extended for pre-commit hooks and CI workflows

## Requirements

- Python 3.8 or later
- `ruff` (must be installed and available in your PATH)
- `git` (used for patch application)
- `transformers` and `accelerate` libraries from Hugging Face

Install Python dependencies with:

```
pip install -r requirements.txt
```

## Usage

Run Gendoc on a specific Python file:

```
python hook/main.py path/to/your/file.py
```

To preview the generated patch without applying it:

```
python hook/main.py path/to/your/file.py --dry-run
````

This will generate docstrings for all missing function/class definitions based on `ruff` diagnostics and print the patch to the console.

## Configuration

Gendoc supports configuration via `pyproject.toml`. You can specify the docstring style using:

```toml
[tool.docstringhook]
style = "numpy"
````

Support for additional styles like "google" or "sphinx" can be added by modifying the prompt logic in `generate_docstring`.

## Example

Given a file like:

```python
def add(x, y):
    return x + y
```

Gendoc will insert:

```python
def add(x, y):
    """
    Add two numbers.

    Parameters
    ----------
    x : int or float
        The first number to be added.
    y : int or float
        The second number to be added.

    Returns
    -------
    int or float
        The sum of x and y.

    Examples
    --------
    >>> add(2, 3)
    5
    """
    return x + y
```

## Project Structure

* `hook/`: Contains modular components like LLM generation, patching, and CLI utilities
* `tmp/`: Temporary folder for storing intermediate patch files

## License

This project is licensed under the MIT License. See `LICENSE` for details.
