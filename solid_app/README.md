# SOLID Bank Application

A banking application built using SOLID principles and design patterns.

## Features

- User management (client and manager types)
- Account management
- Transactions (deposit, withdraw, transfer)
- Balance tracking
- Transaction history

## Technical Stack

- Python 3.10+
- FastAPI
- SQLModel/SQLAlchemy
- SQLite database
- Design Patterns:
  - Factory Pattern
  - Proxy Pattern
  - Command Pattern

## Running the Application

1. Install dependencies:
   ```
   poetry install
   ```

2. Start the server:
   ```
   poetry run uvicorn main:app --reload
   ```

3. Access the API at http://localhost:8000

## Running Tests

```
poetry run pytest
```

## Load Testing

The application includes a Locust configuration for load testing.

1. Run the FastAPI application:
   ```
   poetry run uvicorn main:app --reload
   ```

2. In a separate terminal, start Locust:
   ```
   poetry run locust -f locustfile.py
   ```

3. Open http://localhost:8089 in your browser to access the Locust web interface.

4. Enter the following parameters:
   - Number of users: (e.g., 10)
   - Spawn rate: (e.g., 1)
   - Host: http://localhost:8000

5. Start the test and observe the results.

The load test simulates users performing various banking operations:
- Creating accounts
- Checking balances
- Making deposits and withdrawals
- Transferring funds
- Viewing transaction history

## API Endpoints

- `GET /` - Welcome message
- `GET /users/` - Get all users with their accounts
- `POST /users/` - Create a new user with an account
- `GET /accounts/{account_id}/balance` - Get account balance
- `PUT /accounts/{account_id}/balance` - Update account balance directly
- `POST /accounts/{account_id}/deposit` - Deposit funds
- `POST /accounts/{account_id}/withdraw` - Withdraw funds
- `POST /accounts/{account_id}/transfer` - Transfer funds
- `GET /accounts/{account_id}/transactions` - Get transaction history
- `DELETE /users/{user_id}` - Delete a user
