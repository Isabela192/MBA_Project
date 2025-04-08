from abc import ABC, abstractmethod
from decimal import Decimal
from sqlmodel import Session, select
from database.models import Account
from datetime import datetime
from uuid import UUID
from typing import List, Dict, Any, Optional

# Proxy Pattern


class AccountInterface(ABC):
    @abstractmethod
    def get_balance(self, account_id: UUID, session: Session) -> Optional[Decimal]:
        pass

    @abstractmethod
    def update_balance(
        self, account_id: UUID, amount: Decimal, session: Session
    ) -> bool:
        pass


class RealAccount(AccountInterface):
    def get_balance(self, account_id: UUID, session: Session) -> Optional[Decimal]:
        statement = select(Account).where(Account.account_id == account_id)
        account = session.exec(statement).first()
        return account.balance if account else None

    def update_balance(
        self, account_id: UUID, amount: Decimal, session: Session
    ) -> bool:
        statement = select(Account).where(Account.account_id == account_id)
        account = session.exec(statement).first()

        if not account:
            return False

        account.balance += amount
        account.updated_at = datetime.now()
        session.add(account)
        session.commit()
        session.refresh(account)
        return True


class AccountProxy(AccountInterface):
    def __init__(self, real_account: RealAccount):
        self.real_account = real_account
        self.access_log: List[Dict[str, Any]] = []

    def get_balance(self, account_id: UUID, session: Session) -> Optional[Decimal]:
        self.access_log.append(
            {
                "account_id": account_id,
                "action": "get_balance",
                "timestamp": datetime.now(),
            }
        )
        return self.real_account.get_balance(account_id, session)

    def update_balance(
        self, account_id: UUID, amount: Decimal, session: Session
    ) -> bool:
        self.access_log.append(
            {
                "account_id": account_id,
                "action": "update_balance",
                "timestamp": datetime.now(),
            }
        )
        return self.real_account.update_balance(account_id, amount, session)
