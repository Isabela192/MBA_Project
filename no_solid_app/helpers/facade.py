from datetime import datetime
from decimal import Decimal
from typing import Any, Dict
from uuid import UUID, uuid4

from database.models import Account, Transaction, TransactionStatus, TransactionType
from sqlmodel import Session, select


# Facade Pattern
class TransactionFacade:
    def deposit(
        self, account_id: UUID, amount: Decimal, session: Session
    ) -> Dict[str, Any]:
        statement = select(Account).where(Account.account_id == account_id)
        account = session.exec(statement).first()

        if not account:
            return {"status": "failed", "message": f"Account {account_id} not found"}

        transaction = Transaction(
            transaction_id=uuid4(),
            type=TransactionType.DEPOSIT,
            amount=amount,
            status=TransactionStatus.COMPLETED,
            to_account_id=account.id,
        )

        account.balance += amount
        account.updated_at = datetime.now()

        session.add(transaction)
        session.commit()
        session.refresh(account)

        return {
            "status": "success",
            "message": "Deposit successful",
            "transaction_id": str(transaction.transaction_id),
            "new_balance": str(account.balance),
        }

    def withdraw(
        self, account_id: UUID, amount: Decimal, session: Session
    ) -> Dict[str, Any]:
        statement = select(Account).where(Account.account_id == account_id)
        account = session.exec(statement).first()

        if not account:
            return {"status": "failed", "message": f"Account {account_id} not found"}

        if account.balance < amount:
            return {
                "status": "failed",
                "message": f"Insufficient funds in account {account_id}",
            }

        transaction = Transaction(
            transaction_id=uuid4(),
            type=TransactionType.WITHDRAW,
            amount=amount,
            status=TransactionStatus.COMPLETED,
            from_account_id=account.id,
        )

        account.balance -= amount
        account.updated_at = datetime.now()

        session.add(transaction)
        session.commit()
        session.refresh(account)

        return {
            "status": "success",
            "message": "Withdraw successful",
            "transaction_id": str(transaction.transaction_id),
            "new_balance": str(account.balance),
        }

    def transfer(
        self,
        from_account_id: UUID,
        to_account_id: UUID,
        amount: Decimal,
        session: Session,
    ) -> Dict[str, Any]:
        # Verificando conta de origem
        from_statement = select(Account).where(Account.account_id == from_account_id)
        from_account = session.exec(from_statement).first()

        if not from_account:
            return {
                "status": "failed",
                "message": f"Source account {from_account_id} not found",
            }

        if from_account.balance < amount:
            return {
                "status": "failed",
                "message": f"Insufficient funds in account {from_account_id}",
            }

        # Verificando conta de destino
        to_statement = select(Account).where(Account.account_id == to_account_id)
        to_account = session.exec(to_statement).first()

        if not to_account:
            return {
                "status": "failed",
                "message": f"Destination account {to_account_id} not found",
            }

        # Criando transação
        transaction = Transaction(
            transaction_id=uuid4(),
            type=TransactionType.TRANSFER,
            amount=amount,
            status=TransactionStatus.COMPLETED,
            from_account_id=from_account.id,
            to_account_id=to_account.id,
        )

        # Atualizando saldos
        from_account.balance -= amount
        to_account.balance += amount
        from_account.updated_at = datetime.now()
        to_account.updated_at = datetime.now()

        session.add(transaction)
        session.commit()
        session.refresh(transaction)

        return {
            "status": "success",
            "message": "Transfer successful",
            "transaction_id": str(transaction.transaction_id),
            "from_account_balance": str(from_account.balance),
        }

    def get_balance(self, account_id: UUID, session: Session) -> Dict[str, Any]:
        """Retorna o saldo atual da conta."""
        statement = select(Account).where(Account.account_id == account_id)
        account = session.exec(statement).first()

        if not account:
            return {"status": "failed", "message": f"Account {account_id} not found"}

        return {
            "status": "success",
            "account_id": str(account.account_id),
            "balance": str(account.balance),
        }

    def get_transactions(self, account_id: UUID, session: Session) -> Dict[str, Any]:
        # Verificando se a conta existe
        account_statement = select(Account).where(Account.account_id == account_id)
        account = session.exec(account_statement).first()

        if not account:
            return {"status": "failed", "message": f"Account {account_id} not found"}

        statement = (
            select(Transaction)
            .where(
                (Transaction.from_account_id == account.id)
                | (Transaction.to_account_id == account.id)
            )
            .order_by(Transaction.timestamp)
        )

        transactions = session.exec(statement).all()

        formatted_transactions = [
            {
                "transaction_id": str(transaction.transaction_id),
                "type": transaction.type,
                "amount": str(transaction.amount),
                "status": transaction.status,
                "timestamp": transaction.timestamp,
                "direction": (
                    "OUTGOING"
                    if transaction.from_account_id == account.id
                    else "INCOMING"
                ),
            }
            for transaction in transactions
        ]

        return {
            "status": "success",
            "account_id": str(account_id),
            "transactions": formatted_transactions,
        }


transaction_facade = TransactionFacade()
