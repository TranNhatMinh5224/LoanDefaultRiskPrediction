import os

class Settings:
    PROJECT_NAME: str = "Home Credit Default Risk API"
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "my_secure_password")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "loandefault_db")
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "loan_default_db")
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "5432")

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

settings = Settings()
