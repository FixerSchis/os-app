# Contributing to OS App

Thank you for your interest in contributing to OS App! This document provides guidelines and information for contributors.

## Getting Started

### Prerequisites
- Python 3.10 or higher
- Git
- pip

### Setting up the development environment

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/your-username/os-app.git
   cd os-app
   ```

3. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # Development dependencies
   ```

5. Set up the database:
   ```bash
   flask db upgrade
   ```

6. Run the application:
   ```bash
   python app.py
   ```

## Development Workflow

### 1. Create a new branch
Always create a new branch for your changes:
```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

### 2. Make your changes
- Write clear, readable code
- Follow the existing code style
- Add tests for new functionality
- Update documentation as needed

### 3. Run tests locally
Before submitting a pull request, ensure all tests pass:
```bash
pytest
```

### 4. Code formatting
Ensure your code follows the project's formatting standards:
```bash
black .
isort .
flake8 .
```

### 5. Commit your changes
Use conventional commit messages:
```bash
git commit -m "feat: add new character creation feature"
git commit -m "fix: resolve database connection issue"
git commit -m "docs: update README with installation instructions"
```

### 6. Push and create a pull request
```bash
git push origin feature/your-feature-name
```

## Code Style Guidelines

### Python
- Follow PEP 8 style guidelines
- Use type hints where appropriate
- Keep functions small and focused
- Write docstrings for public functions and classes

### Flask
- Use blueprints for route organization
- Follow Flask best practices
- Use proper error handling

### Testing
- Write unit tests for new functionality
- Aim for good test coverage
- Use descriptive test names
- Mock external dependencies

## Pull Request Guidelines

1. **Title**: Use a clear, descriptive title
2. **Description**: Provide a detailed description of your changes
3. **Tests**: Ensure all tests pass
4. **Documentation**: Update documentation if needed
5. **Screenshots**: Include screenshots for UI changes

## Issue Reporting

When reporting issues, please include:
- A clear description of the problem
- Steps to reproduce
- Expected vs actual behavior
- Environment details (OS, Python version, etc.)
- Screenshots if applicable

## Getting Help

- Check existing issues and pull requests
- Join our discussions in GitHub Discussions
- Create an issue for questions or problems

## Code of Conduct

Please be respectful and inclusive in all interactions. We welcome contributors from all backgrounds and experience levels.

## License

By contributing to this project, you agree that your contributions will be licensed under the same license as the project.
