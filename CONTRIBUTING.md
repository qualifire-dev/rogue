# Contributing to Rogue

Thank you for your interest in contributing to Rogue! We welcome contributions of all sizes - from small bug fixes to major feature additions, and from code contributions to constructive discussions. Every contribution helps make Rogue better for everyone.

## Code of Conduct

This project adheres to a Code of Conduct that all contributors are expected to follow. Please read [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) before contributing.

## Ways to Contribute

There are many ways you can contribute to Rogue:

- **Report bugs**: If you find a bug, please open an issue with a clear description and steps to reproduce
- **Suggest features**: Have an idea for a new feature? Open an issue to discuss it
- **Improve documentation**: Help us improve our docs, examples, or code comments
- **Submit pull requests**: Fix bugs, add features, or improve existing code
- **Participate in discussions**: Share your thoughts and help others in issues and pull requests
- **Write tutorials or blog posts**: Help others learn about Rogue

## Getting Started

### Prerequisites

- Python 3.10 or higher
- [uv](https://docs.astral.sh/uv/getting-started/installation/) - A fast Python package manager
- Git
- For Go components (TUI): Go 1.21 or higher

### Development Setup

1. **Fork and clone the repository**

   ```bash
   git clone https://github.com/qualifire-dev/rogue.git
   cd rogue
   ```

2. **Install dependencies**

   We use `uv` for dependency management. Install all dependencies including dev tools:

   ```bash
   uv sync --all-groups
   ```

   Or install specific groups:

   ```bash
   uv sync --group dev --group examples
   ```

3. **Install Lefthook (Pre-commit Framework)**

   We use [Lefthook](https://github.com/evilmartians/lefthook) as our pre-commit framework. It ensures code quality by running various checks before each commit.

   **Installation**:

    Please follow [Lefthook's documentation](https://lefthook.dev/installation/) on how to install.
   
   **Activate Lefthook** in the repository:

   ```bash
   lefthook install
   ```

   This will set up the git hooks defined in `lefthook.yaml`. Now, every time you commit, Lefthook will automatically run:
   - **Python linters**: `black`, `flake8`, `mypy`, `bandit`, `isort`, `add-trailing-comma`
   - **Go formatters**: `gofmt`, `goimports`, `go vet` (for TUI code)
   - **Security checks**: `gitleaks` (prevents committing secrets)
   - **YAML validation**: Checks YAML syntax
   - **Dependency checks**: Ensures `uv.lock` is up to date

   If any check fails, the commit will be blocked until you fix the issues.

4. **Set up environment variables (optional)**

   Create a `.env` file in the root directory if you need API keys for testing:

   ```env
   OPENAI_API_KEY="sk-..."
   ```

## Development Workflow

### Code Style

We follow strict code style guidelines to maintain consistency:

#### Python

- **Formatting**: We use `black` for code formatting
- **Import sorting**: Follow `isort` conventions
- **Type hints**: All function signatures must have type hints
- **Naming conventions**: Follow PEP 8
  - `snake_case` for variables and functions
  - `PascalCase` for classes
  - `UPPER_CASE` for constants
- **Error handling**: Use try/except blocks for code that may raise exceptions
- **Docstrings**: Use Google-style docstrings for public functions and classes

#### Go (for TUI components)

- Use `gofmt` and `goimports` for formatting
- Follow standard Go naming conventions

### Running Tests

```bash
# Run all tests
uv run pytest
```

### Linting and Code Quality

Before submitting a PR, ensure your code passes all quality checks:

```bash
# Format code with black
uv run black .

# Check code style with flake8
uv run flake8 .

# Type check with mypy
uv run mypy --config-file .mypy.ini .

# Security check with bandit
uv run bandit -c .bandit.yaml -r .
```

**Note**: If you have Lefthook installed, these checks will run automatically on commit.

### Building the Project

```bash
uv build
```

### Running Rogue Locally

```bash
# Run with TUI (default)
uv run python -m rogue

# Run server only
uv run python -m rogue server

# Run web UI
uv run python -m rogue ui

# Run CLI
uv run python -m rogue cli

# Run with example agent
uv run rogue-ai --example=tshirt_store
```

## Submitting Changes

### Pull Request Process

1. **Create a feature branch**

   ```bash
   git checkout -b feature/your-feature-name
   ```

   Use descriptive branch names:
   - `feature/add-new-evaluation-type` for new features
   - `fix/issue-123-bug-description` for bug fixes
   - `docs/improve-contributing-guide` for documentation

2. **Make your changes**

   - Write clear, concise commit messages
   - Follow the code style guidelines
   - Add tests for new functionality
   - Update documentation as needed

3. **Test your changes**

   Before creating a pull request, you are expected to test you changes manually as well as running the unit tests.

   ```bash
   # Run tests
   uv run pytest

   # Run linters
   uv run black .
   uv run flake8 .
   uv run mypy --config-file .mypy.ini .
   ```

4. **Commit your changes**

   ```bash
   git add .
   git commit -m "Add descriptive commit message"
   ```

   If you have Lefthook installed, pre-commit hooks will run automatically. Fix any issues before continuing.

5. **Open a pull request**

   - Go to the [Rogue repository](https://github.com/qualifire-dev/rogue)
   - Click "New Pull Request"
   - Select your feature branch
   - Fill out the PR template with:
     - A clear description of the changes
     - The motivation for the changes
     - Any related issues (use "Fixes #123" to auto-close issues)
     - Screenshots or examples if applicable

6. **Address review feedback**

   - Respond to comments and questions
   - Make requested changes
   - Push additional commits to your branch

### Commit Message Guidelines

- Use the present tense ("Add feature" not "Added feature")
- Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
- Limit the first line to 72 characters or less
- Reference issues and pull requests liberally after the first line

Examples:
```
Add support for custom evaluation metrics

- Implement EvaluationMetric base class
- Add metric registration system
- Update documentation

Fixes #123
```

## Reporting Issues

When reporting issues, please include:

- A clear, descriptive title
- Steps to reproduce the issue
- Expected behavior
- Actual behavior
- Your environment (OS, Python version, etc.)
- Relevant logs or error messages
- Screenshots if applicable

Use the provided issue templates when available.

## Feature Requests

We love hearing your ideas! When suggesting a feature:

- Check if it has already been suggested
- Clearly describe the feature and its benefits
- Explain your use case
- Consider how it fits with Rogue's goals
- Be open to discussion and feedback

## Development Tips

### Working with Dependencies

```bash
# Add a new dependency
# Edit pyproject.toml, then:
uv sync

# Update dependencies
uv sync --upgrade

# Check lock file
uv lock --check
```

### Project Structure

- `rogue/`: Main Python package
  - `server/`: Backend server and API
  - `ui/`: Gradio web interface
  - `common/`: Shared utilities
  - `evaluator_agent/`: Evaluator agent implementation
  - `prompt_injection_evaluator/`: Prompt injection testing
- `tests/`: Test suite
- `examples/`: Example agent implementations
- `packages/`: Additional packages (SDK, TUI)
- `sdks/`: SDK implementations for different languages

### Debugging

```bash
# Run with debug logging
uv run python -m rogue --debug

# Run specific component with debug
uv run python -m rogue server --debug
```

## Getting Help

If you need help:

- Check the [README.md](README.md) for basic usage
- Look through existing [issues](https://github.com/qualifire-dev/rogue/issues)
- Open a new issue with the "question" label
- Join discussions in pull requests

## Recognition

All contributors will be recognized in our release notes and can be added to a CONTRIBUTORS file if the project grows.

## License

By contributing to Rogue, you agree that your contributions will be licensed under the same ELASTIC license that covers the project. See [LICENSE.md](LICENSE.md) for details.

---

Thank you for contributing to Rogue! Your efforts help make AI agent evaluation better for everyone. 🚀

