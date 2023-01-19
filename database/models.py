import sqlalchemy as sq
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Organization(Base):
    __tablename__ = 'Organization'

    # id = sq.Column(sq.Integer, primary_key=True)
    id = sq.Column(sq.Integer, primary_key=True, nullable=False)
    org_name = sq.Column(sq.String, nullable=False)

    def __str__(self):
        return f'id: {self.id}, name: {self.org_name}'


class User(Base):
    __tablename__ = 'User'

    # id = sq.Column(sq.Integer, primary_key=True)
    tg_id = sq.Column(sq.Integer, primary_key=True, nullable=False)
    tg_username = sq.Column(sq.String, nullable=False)

    def __str__(self):
        return f'id: {self.tg_id}, telegram_username: {self.tg_username}'


class User_organization(Base):
    __tablename__ = "User_organization"

    id = sq.Column(sq.Integer, primary_key=True)

    user_id = sq.Column(sq.Integer, sq.ForeignKey("User.tg_id"))
    user = relationship(User, backref="User_organization")

    org_id = sq.Column(sq.Integer, sq.ForeignKey("Organization.id"))
    organization = relationship(Organization, backref="User_organization")

    is_active = sq.Column(sq.Boolean)

    def __str__(self):
        return f'{self.is_active}'
