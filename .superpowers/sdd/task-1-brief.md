### Task 1: Package scaffolding

**Files:**
- Create: `vpbar/__init__.py`
- Create: `vpbar/__main__.py`
- Create: `pyproject.toml`

**Interfaces:**
- Produces: Runnable `python -m vpbar` that prints usage

- [ ] **Step 1: Create `vpbar/` package directory** (already exists when we create files)

- [ ] **Step 2: Create `vpbar/__init__.py`**

```python
"""vpbar - Video Progress Bar CLI Tool."""
```

- [ ] **Step 3: Create `vpbar/__main__.py`**

```python
"""Allow running as python -m vpbar."""
from vpbar.cli import main

if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Create `pyproject.toml`**

```toml
[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.backends._legacy:_Backend"

[project]
name = "vpbar"
version = "0.1.0"
requires-python = ">=3.8"
dependencies = []

[project.scripts]
vpbar = "vpbar.cli:main"

[tool.setuptools.packages.find]
include = ["vpbar*"]
```

- [ ] **Step 5: Install in dev mode**

```bash
pip install -e .
```

- [ ] **Step 6: Verify it runs**

```bash
python -m vpbar
# Should exit with non-zero and print: "usage: vpbar [-h] {progress,gif} ..."
```

- [ ] **Step 7: Commit**

```bash
git add vpbar/ pyproject.toml
git commit -m "feat: scaffold vpbar package and pyproject.toml"
```
