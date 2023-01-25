from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models import User, Organization, User_organization as UO
from database.models import Base

DATABASE_NAME = 'bot_db.sqlite'
engine = create_engine(f'sqlite:///{DATABASE_NAME}')

Session = sessionmaker(bind=engine)
session = Session()


def create_tables():
    """
    Создает таблицы и связи из models.py
    """
    Base.metadata.create_all(engine)
    print('Созданы таблицы согласно models.py')


def drop_tables():
    """
    Удаляет созданные таблицы вместе с данными
    """
    Base.metadata.drop_all(engine)
    print('Все таблицы и данные удалены')


def create_user_if_not_exist(tg_id, tg_username):
    '''
    Создает пользователя в БД если его там нет
    '''
    for user in session.query(User).all():
        if user.tg_id == tg_id:
            print(f'Пользователь {user} уже существует')
            return user

    user = User(tg_id=tg_id, tg_username=tg_username)
    session.add(user)
    session.commit()
    print(f'Пользователь {user} создан')
    return user


def create_organization_if_not_exist(org_name, id):
    '''
    Создает организацию в БД если ее там нет
    '''
    for org in session.query(Organization).all():
        if org.id == id:
            print(f'Организация {org} уже существует')
            return org

    org = Organization(org_name=org_name, id=id)
    session.add(org)
    session.commit()
    print(f'Организация {org} создана')
    return org


def bind_user_org(user, org, is_active=False):
    '''
    Создает связь пользователя и организации в БД, если подобной связи еще нет
    '''
    for bind in session.query(UO).all():
        if bind.user_id == user.tg_id and bind.org_id == org.id:
            print('Связь уже существует')
            return None

    bind = UO(user=user, organization=org, is_active=is_active)
    session.add(bind)
    session.commit()
    print(f'Организация {org.org_name} привязана к пользователю {user.tg_username}')


def activate_org(tg_id, org_id):
    '''
    Активирует указанную организацию у пользователя
    '''
    for bind in session.query(UO).filter(UO.user_id == tg_id).filter(UO.org_id == org_id).all():
        bind.is_active = True
        session.commit()
        print(f'Для пользователя {bind.user_id} группа {bind.org_id} стала активной')
        return


def deactivate_all(tg_id):
    '''
    Деактевирует все организации пользователя
    '''
    for bind in session.query(UO).filter(UO.user_id == tg_id).all():
        bind.is_active = False
        session.commit()

    print(f'Для пользователя {tg_id} все группы деактивированы')


def get_all_organizations(tg_id):
    '''
    Возвращает json с организациями пользователя и их статусом
    '''
    org_list = []
    for org in session.query(Organization).join(UO.organization).filter(UO.user_id == tg_id):
        status = session.query(UO).filter(UO.user_id == tg_id).filter(UO.org_id == org.id).first()
        org_list.append({"name": org.org_name, "id": org.id, "status": status.is_active})
    return org_list


def find_active_organization(tg_id):
    '''
    Находит активную организацию. Возвращает id активной организации
    '''
    active_group_id = session.query(UO).filter(UO.user_id == tg_id).filter(UO.is_active == True).first()
    return active_group_id.org_id
