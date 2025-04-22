from abc import ABC, abstractmethod
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, Optional
from uuid import UUID

from database.models import Account, Transaction
from sqlmodel import Session, select


# Abstract Factory Pattern
class AccountInterface(ABC):
    @abstractmethod
    def get_balance(
        self, account_id: UUID, session: Session
    ) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    def update_balance(
        self, account_id: UUID, amount: Decimal, session: Session
    ) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_transactions(
        self, account_id: UUID, session: Session
    ) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_account_details(
        self, account_id: UUID, session: Session
    ) -> Optional[Dict[str, Any]]:
        pass


class AccountFactory:
    def create_account_handler(self) -> AccountInterface:
        """Cria um handler de conta"""
        pass


class AccountHandler(AccountInterface):
    """Implementação concreta para contas padrão"""

    def get_balance(
        self, account_id: UUID, session: Session
    ) -> Optional[Dict[str, Any]]:
        statement = select(Account).where(Account.account_id == account_id)
        account = session.exec(statement).first()

        if not account:
            return None

        return {
            "account_id": str(account.account_id),
            "balance": str(account.balance),
            "account_type": account.account_type,
            "status": account.status,
        }

    def update_balance(
        self, account_id: UUID, amount: Decimal, session: Session
    ) -> Optional[Dict[str, Any]]:
        statement = select(Account).where(Account.account_id == account_id)
        account = session.exec(statement).first()

        if not account:
            return None

        if account.balance + amount < 0:
            return {
                "status": "failed",
                "message": "Operation would result in negative balance",
                "current_balance": str(account.balance),
            }

        account.balance += amount
        account.updated_at = datetime.now()

        session.add(account)
        session.commit()
        session.refresh(account)

        return {
            "status": "success",
            "account_id": str(account.account_id),
            "new_balance": str(account.balance),
            "account_type": account.account_type,
        }

    def get_transactions(
        self, account_id: UUID, session: Session
    ) -> Optional[Dict[str, Any]]:
        # Verificar se a conta existe
        account_statement = select(Account).where(Account.account_id == account_id)
        account = session.exec(account_statement).first()

        if not account:
            return None

        # Buscar transações
        statement = (
            select(Transaction)
            .where(
                (Transaction.from_account_id == account.id)
                | (Transaction.to_account_id == account.id)
            )
            .order_by(Transaction.timestamp)
        )

        transactions = session.exec(statement).all()

        # Formatação padrão para contas standard
        formatted_transactions = [
            {
                "transaction_id": str(transaction.transaction_id),
                "type": transaction.type,
                "amount": str(transaction.amount),
                "status": transaction.status,
                "timestamp": transaction.timestamp,
            }
            for transaction in transactions
        ]

        return {
            "account_id": str(account_id),
            "transactions": formatted_transactions,
            "count": len(formatted_transactions),
        }

    def get_account_details(
        self, account_id: UUID, session: Session
    ) -> Optional[Dict[str, Any]]:
        statement = select(Account).where(Account.account_id == account_id)
        account = session.exec(statement).first()

        if not account:
            return None

        return {
            "account_id": str(account.account_id),
            "balance": str(account.balance),
            "account_type": account.account_type,
            "status": account.status,
            "created_at": account.created_at,
            "updated_at": account.updated_at,
        }


class HandlerAccountFactory(AccountFactory):
    """Factory para criar handlers de contas padrão"""

    def create_account_handler(self) -> AccountInterface:
        return AccountHandler()


account_factory = HandlerAccountFactory()
