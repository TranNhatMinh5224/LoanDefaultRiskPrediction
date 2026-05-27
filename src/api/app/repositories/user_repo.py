from sqlalchemy.orm import Session
from app.models.user_model import User
from app.models.refresh_token_model import RefreshToken

class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_user_by_email(self, email: str) -> User | None:
        return self.db.query(User).filter(User.email == email).first()
        
    def get_user_by_username(self, username: str) -> User | None:
        return self.db.query(User).filter(User.username == username).first()

    def create_user(self, user: User) -> User:
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def save_refresh_token(self, token_entry: RefreshToken):
        self.db.add(token_entry)
        self.db.commit()
    
    def get_refresh_token(self, token: str) -> RefreshToken | None:
        return self.db.query(RefreshToken).filter(RefreshToken.token == token).first()

    def revoke_refresh_token(self, token: str):
        token_entry = self.get_refresh_token(token)
        if token_entry:
            token_entry.is_revoked = True
            self.db.commit()
