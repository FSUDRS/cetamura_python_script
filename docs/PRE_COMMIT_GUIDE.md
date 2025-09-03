# Setting Up Pre-commit Hooks

This guide explains how to set up and use pre-commit hooks for the Cetamura Batch Tool project.

## What are Pre-commit Hooks?

Pre-commit hooks are scripts that run automatically before each commit, helping to catch issues early and maintain code quality. For this project, we've configured hooks for:

- Code formatting (Black)
- Linting (Flake8)
- Type checking (MyPy)
- Basic file checks (trailing whitespace, file endings, etc.)

## Installation

1. Install the pre-commit package:

```bash
pip install pre-commit
```

2. Install the git hook scripts:

```bash
pre-commit install
```

## Usage

Once installed, the hooks will run automatically on each `git commit` operation. If any issues are found:

1. The commit will be aborted
2. Issues will be displayed in the terminal
3. Some issues will be fixed automatically

After issues are fixed, you'll need to add the changes and commit again:

```bash
git add .
git commit -m "Your commit message"
```

## Manual Usage

You can also run the hooks manually on all files:

```bash
pre-commit run --all-files
```

Or run a specific hook:

```bash
pre-commit run black --all-files
```

## Skip Hooks (Temporarily)

In rare cases where you need to bypass the hooks:

```bash
git commit -m "Your message" --no-verify
```

**Note:** This should be used sparingly, as it bypasses all quality checks.

## Configuration

The pre-commit configuration is in `.pre-commit-config.yaml`. You can modify this file to:

- Add new hooks
- Adjust hook settings
- Remove hooks you don't want

## Troubleshooting

If you encounter issues with pre-commit:

1. **Hooks failing but code looks correct**: Try running the specific tool manually to see detailed errors
2. **Hook installation issues**: Make sure you have the tool installed (`pip install pre-commit`)
3. **Performance issues**: Some hooks like MyPy can be slow - consider excluding large files or directories
