from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine, Column, ForeignKey
from sqlalchemy.types import BigInteger, Unicode, DateTime, SmallInteger
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import sessionmaker, relationship
from redis import Redis

user = 'ns'
password = 'ns'
host = 'localhost'
database = 'ns_dev'
engine = create_engine('postgresql://%s:%s@%s/%s' % (user, password, host, database))
Base = declarative_base()
Session = sessionmaker(bind=engine, autocommit=True, expire_on_commit=False)
session = Session()
redis = Redis(host='localhost', db=0)


def transactional(f):
    def decorator(*args, **kwargs):
        session.begin(subtransactions=True)
        try:
            result = f(*args, **kwargs)
            session.commit()
            return result
        except:
            session.rollback()
            raise   # Re-raise last exception.
    return decorator


class AuthBase(object):
    @classmethod
    def get(cls, get_first=False, **kwargs):
        filtered_rows = session.query(cls)
        for key, value in kwargs.iteritems():
            filtered_rows = filtered_rows.filter(cls.__getattribute__(cls, key) == value)
        return filtered_rows.first() if get_first else filtered_rows.all()

    @transactional
    def save(self):
        session.add(self)
        # session.merge(self)

    @transactional
    def update(self, **kwargs):
        for key, value in kwargs.iteritems():
            if value or (type(value) in [int, long] and value is not None):
                self.__setattr__(key, value)
        return

    @classmethod
    @transactional
    def add(cls, **kwargs):
        obj = cls(**kwargs)
        obj.save()


class AuthClient(AuthBase, Base):
    __tablename__ = 'auth_client'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(Unicode, nullable=False, unique=True)
    oauth_id = Column(Unicode, nullable=False, unique=True)
    oauth_secret = Column(Unicode, nullable=False)
    status = Column(SmallInteger, default=1)


class AuthUser(AuthBase, Base):
    __tablename__ = 'auth_user'

    id = Column(BigInteger, primary_key=True)
    meta_info = Column(JSONB, default='{}')
    oauth_username = Column(Unicode, unique=True)
    oauth_password = Column(Unicode)
    status = Column(SmallInteger, default=0)
    client_id = Column(BigInteger, ForeignKey('auth_client.id'))
    client = relationship(AuthClient)

    @classmethod
    def get_by_metadata(cls, **kwargs):
        auth_users = session.query(cls)
        for key, value in kwargs.iteritems():
            auth_users = auth_users.filter(cls.meta_info[key].astext == str(value))
        return auth_users.first()


if __name__ == '__main__':
    AuthUser.add_or_update_user(username='testvishal', account_password='as')
