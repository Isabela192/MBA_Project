from abc import ABC, abstractmethod
from sqlmodel import Session, select

from database.models import Account, User


class AccountInterface(ABC):
    """Interface abstrata para contas bancárias"""

    @abstractmethod
    def get_type(self) -> str:
        pass

    @abstractmethod
    def get_features(self) -> dict:
        pass

    @abstractmethod
    def create_db_entry(self, document_id: str, db: Session) -> Account:
        pass


class CheckingAccount(AccountInterface):
    """Implementação de conta corrente"""

    def get_type(self) -> str:
        return "CHECKING"

    def get_features(self) -> dict:
        return {
            "overdraft_allowed": True,
            "minimum_balance": 0.0,
            "maintenance_fee": 10.0,
        }

    def create_db_entry(self, document_id: str, db: Session) -> Account:
        # Busca usuário pelo documento
        statement = select(User).where(User.document_id == document_id)
        user = db.exec(statement).first()

        # Cria a conta
        account = Account(
            document_id=document_id,
            balance=0.0,
            account_type=self.get_type(),
            status="ACTIVE",
        )

        # Adiciona a conta ao banco de dados
        db.add(account)
        db.commit()
        db.refresh(account)

        # Associa a conta ao usuário se existir
        if user:
            # No SQLModel, precisamos adicionar o user à lista de users da conta
            # Isso é uma simplificação que não segue o padrão ideal de relações many-to-many
            # Deliberadamente não otimizado para demonstrar problemas não-SOLID
            account.users.append(user)
            db.commit()

        return account


class SavingsAccount(AccountInterface):
    """Implementação de conta poupança"""

    def get_type(self) -> str:
        return "SAVINGS"

    def get_features(self) -> dict:
        return {
            "interest_rate": 0.025,
            "minimum_balance": 100.0,
            "withdrawal_limit": 6,
        }

    def create_db_entry(self, document_id: str, db: Session) -> Account:
        # Busca usuário pelo documento
        statement = select(User).where(User.document_id == document_id)
        user = db.exec(statement).first()

        # Cria a conta
        account = Account(
            document_id=document_id,
            balance=100.0,  # Saldo mínimo para conta poupança
            account_type=self.get_type(),
            status="ACTIVE",
        )

        # Adiciona a conta ao banco de dados
        db.add(account)
        db.commit()
        db.refresh(account)

        # Associa a conta ao usuário se existir
        if user:
            account.users.append(user)
            db.commit()

        return account


class InvestmentAccount(AccountInterface):
    """Implementação de conta de investimento"""

    def get_type(self) -> str:
        return "INVESTMENT"

    def get_features(self) -> dict:
        return {
            "interest_rate": 0.05,
            "minimum_balance": 1000.0,
            "lock_period_days": 30,
        }

    def create_db_entry(self, document_id: str, db: Session) -> Account:
        # Busca usuário pelo documento
        statement = select(User).where(User.document_id == document_id)
        user = db.exec(statement).first()

        # Cria a conta
        account = Account(
            document_id=document_id,
            balance=1000.0,  # Saldo mínimo para conta de investimento
            account_type=self.get_type(),
            status="ACTIVE",
        )

        # Adiciona a conta ao banco de dados
        db.add(account)
        db.commit()
        db.refresh(account)

        # Associa a conta ao usuário se existir
        if user:
            account.users.append(user)
            db.commit()

        return account


class AccountFactory(ABC):
    """Interface abstrata para fábricas de contas"""

    @abstractmethod
    def create_account(self, document_id: str, db: Session) -> AccountInterface:
        pass


class CheckingAccountFactory(AccountFactory):
    """Fábrica de contas correntes"""

    def create_account(self, document_id: str, db: Session) -> AccountInterface:
        return CheckingAccount()


class SavingsAccountFactory(AccountFactory):
    """Fábrica de contas poupança"""

    def create_account(self, document_id: str, db: Session) -> AccountInterface:
        return SavingsAccount()


class InvestmentAccountFactory(AccountFactory):
    """Fábrica de contas de investimento"""

    def create_account(self, document_id: str, db: Session) -> AccountInterface:
        return InvestmentAccount()


class AccountFactoryProducer:
    """
    Producer of account factories - follows the Abstract Factory pattern

    This implementation demonstrates the Abstract Factory pattern to create
    different types of accounts through their respective factories.
    """

    @staticmethod
    def get_factory(account_type: str) -> AccountFactory:
        """Get the appropriate factory for the account type"""

        if account_type == "CHECKING":
            return CheckingAccountFactory()
        elif account_type == "SAVINGS":
            return SavingsAccountFactory()
        elif account_type == "INVESTMENT":
            return InvestmentAccountFactory()
        else:
            # Default to checking account as a fallback
            return CheckingAccountFactory()
