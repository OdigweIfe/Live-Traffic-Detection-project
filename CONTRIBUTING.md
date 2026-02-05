# Contributing to TrafficAI

Thank you for your interest in contributing to TrafficAI! This document outlines the process for contributing to this project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Process](#development-process)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Documentation](#documentation)
- [Pull Request Process](#pull-request-process)
- [Issue Reporting](#issue-reporting)

## Code of Conduct

This project follows the [Contributor Covenant Code of Conduct](https://www.contributor-covenant.org/). By participating, you are expected to uphold this code.

## Getting Started

### Prerequisites

- Python 3.10+
- Git
- GitHub account
- Tesseract OCR (for local testing)

### Setting Up Development Environment

1. **Fork the repository**

   Click the "Fork" button on the top right of the [TrafficAI repository](https://github.com/yourusername/TrafficAI)

2. **Clone your fork**

   ```bash
   git clone https://github.com/YOUR-USERNAME/TrafficAI.git
   cd TrafficAI
   ```

3. **Add upstream remote**

   ```bash
   git remote add upstream https://github.com/ORIGINAL-USERNAME/TrafficAI.git
   ```

4. **Create a virtual environment**

   ```bash
   python -m venv venv
   .\venv\Scripts\activate  # Windows
   source venv/bin/activate  # Linux/Mac
   ```

5. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

6. **Set up pre-commit hooks**

   ```bash
   pip install pre-commit
   pre-commit install
   ```

## Development Process

### Branch Naming Convention

- `feature/` - New features (e.g., `feature/add-red-light-detection`)
- `fix/` - Bug fixes (e.g., `fix/database-migration-error`)
- `docs/` - Documentation updates (e.g., `docs/update-api-docs`)
- `refactor/` - Code refactoring (e.g., `refactor/improve-detection-accuracy`)
- `test/` - Test-related changes (e.g., `test/add-violation-tests`)

### Workflow

1. **Sync your fork**

   ```bash
   git fetch upstream
   git checkout main
   git merge upstream/main
   ```

2. **Create a feature branch**

   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes**

   - Write code
   - Write tests
   - Update documentation

4. **Commit your changes**

   ```bash
   git add .
   git commit -m "feat: Add description of your changes"
   ```

   Follow [Conventional Commits](https://www.conventionalcommits.org/):
   - `feat:` - New features
   - `fix:` - Bug fixes
   - `docs:` - Documentation changes
   - `refactor:` - Code refactoring
   - `test:` - Test changes
   - `chore:` - Maintenance tasks

5. **Push to your fork**

   ```bash
   git push origin feature/your-feature-name
   ```

6. **Create a Pull Request**

   Go to GitHub and create a PR from your branch to the main branch.

## Coding Standards

### Python Style Guide

- Follow [PEP 8](https://pep8.org/) style guide
- Use [Black](https://black.readthedocs.io/) for code formatting
- Use [isort](https://pycqa.github.io/isort/) for import sorting
- Maximum line length: 88 characters (Black default)

### Code Style Tools

```bash
# Format code
black .

# Sort imports
isort .

# Lint code
flake8 .

# Type checking (if applicable)
mypy .
```

### Docstrings

Use Google-style docstrings:

```python
def function_name(param1: str, param2: int) -> bool:
    """Short description of the function.

    Args:
        param1: Description of param1.
        param2: Description of param2.

    Returns:
        Description of return value.

    Raises:
        ValueError: Description of when this error is raised.
    """
```

### Type Hints

Include type hints for function signatures:

```python
from typing import List, Optional

def process_violations(violation_ids: List[int]) -> Optional[dict]:
    ...
```

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_violations.py

# Run specific test
pytest tests/test_violations.py::test_create_violation
```

### Writing Tests

- Place tests in the `tests/` directory
- Use pytest framework
- Follow naming convention: `test_*.py`
- Aim for meaningful test coverage

Example test:

```python
import pytest
from app.models import Violation

def test_violation_creation():
    violation = Violation(
        type="red_light",
        license_plate="ABC123",
        speed=65,
        confidence=0.95
    )
    assert violation.type == "red_light"
    assert violation.confidence > 0.9
```

### Test Categories

- **Unit Tests**: Test individual functions/methods
- **Integration Tests**: Test module interactions
- **E2E Tests**: Test complete user workflows

## Documentation

### Updating README

Update the README.md when:
- Adding new features
- Changing configuration
- Updating installation steps
- Modifying environment variables

### Code Documentation

- Add docstrings to all public functions
- Comment complex logic
- Update docstrings when modifying functions

### API Documentation

If adding new API endpoints:
- Document the endpoint
- Include request/response examples
- Note authentication requirements

## Pull Request Process

### Before Submitting

1. **Run tests**

   ```bash
   pytest
   ```

2. **Run linting**

   ```bash
   black .
   isort .
   flake8
   ```

3. **Update documentation**

   Ensure README and inline docs are updated.

4. **Check your changes**

   ```bash
   git diff --stat
   ```

### Pull Request Template

```markdown
## Description
Brief description of the changes.

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Tests pass locally
- [ ] Added new tests

## Checklist
- [ ] My code follows the style guidelines
- [ ] I have performed a self-review
- [ ] I have commented my code
- [ ] I have updated documentation
- [ ] My changes generate no new warnings
```

### Review Process

1. Maintainers will review your PR
2. Address any requested changes
3. Once approved, your PR will be merged
4. Delete your feature branch after merge

## Issue Reporting

### Before Submitting

- Search existing issues
- Check if the issue has been reported

### Issue Template

```markdown
## Bug Report
**Describe the bug**
Clear description of the bug.

**To Reproduce**
Steps to reproduce:
1. Go to '...'
2. Click on '....'
3. See error

**Expected behavior**
What you expected to happen.

**Screenshots**
If applicable, add screenshots.

**Environment:**
- OS: [e.g., Windows 11]
- Python: [e.g., 3.10.0]
- Dependencies: [output of `pip list`]

---

## Feature Request
**Is your feature related to a problem?**
Describe the problem.

**Describe the solution**
Describe the solution you'd like.

**Additional context**
Add any context about the feature.
```

## Communication

- **GitHub Issues**: For bug reports and feature requests
- **GitHub Discussions**: For questions and ideas
- **Pull Requests**: For code contributions

## Recognition

Contributors will be recognized in the README.md and in release notes.

Thank you for contributing to TrafficAI!
