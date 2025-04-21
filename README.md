# USP-Esalq MBA TCC Project

This repository contains two banking applications developed as part of a research project to evaluate the impact of applying SOLID principles and GoF design patterns in software development.

## Project Structure

The repository is divided into two main applications:

1. **`solid_app`**: A banking application built using SOLID principles and GoF design patterns.
2. **`no_solid_app`**: A banking application built without adhering to SOLID principles but still using GoF design patterns.

Each project has it's own pyproject.toml and both use pytest to run tests.

#### Features:
- User management (clients and managers)
- Account creation and management
- Financial transactions (deposits, withdrawals, transfers)
- Transaction history
- API documentation via FastAPI's Swagger UI

## Technical Stack

- Python 3.10+
- Poetry for dependency management
- FastAPI
- SQLModel/SQLAlchemy
- SQLite database
- Design Patterns:
  - Factory Pattern
  - Proxy Pattern
  - Command Pattern
  - Singleton Pattern
  - Facade Pattern
  - Abstract Factory Pattern

## Running the Application

1. On each project, install dependencies:
   ```
   poetry install
   ```

2. Start the server:
   ```
   poetry run uvicorn main:app --reload
   ```

3. Access the API at http://localhost:8000

## Quality Assurance

Pre-commit Hooks
The repository uses pre-commit hooks for code quality checks. Install them with:

   ```
   pre-commit install
   ```

Linting and Static Analysis

- Ruff: For linting and formatting Python code.
- Pylint: For additional code quality checks.
- Wily: For code complexity and maintainability analysis.

Run the quality checks:

   ```
   pylint solid_app/ no_solid_app/
   wily build solid_app/ no_solid_app/
   wily report
   ```

## Research Implications
This project demonstrates the differences in code quality, maintainability, and extensibility when applying SOLID principles and design patterns versus using design patterns alone.
