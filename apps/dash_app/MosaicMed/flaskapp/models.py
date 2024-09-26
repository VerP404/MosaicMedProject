# # models.py
# from sqlalchemy import Column, Integer, String, Date, Text
# from sqlalchemy.orm import declarative_base
#
# Base = declarative_base()
#
#
# class UserModel(Base):
#     __tablename__ = 'user'
#     __table_args__ = {'schema': 'users'}
#
#     id = Column(Integer, primary_key=True, index=True)
#     username = Column(String, unique=True, index=True)
#     hashed_password = Column(String)
#     last_name = Column(String)
#     first_name = Column(String)
#     middle_name = Column(String)
#     birth_date = Column(Date)
#     position = Column(String)
#     role = Column(String)
#     category = Column(String)
#
#
# class User(UserMixin):
#     def __init__(self, id, username, hashed_password, last_name, first_name, middle_name, birth_date, position, role,
#                  category):
#         self.id = id
#         self.username = username
#         self.hashed_password = hashed_password
#         self.last_name = last_name
#         self.first_name = first_name
#         self.middle_name = middle_name
#         self.birth_date = birth_date
#         self.position = position
#         self.role = role
#         self.category = category
#
#     @staticmethod
#     def get(user_id):
#         session = SessionLocal()
#         user = session.query(UserModel).filter(UserModel.id == user_id).first()
#         session.close()
#         if user:
#             return User(user.id, user.username, user.hashed_password, user.last_name, user.first_name, user.middle_name,
#                         user.birth_date, user.position, user.role, user.category)
#         return None
#
#     @staticmethod
#     def validate(username, password):
#         session = SessionLocal()
#         user = session.query(UserModel).filter(UserModel.username == username).first()
#         session.close()
#         if user and bcrypt.check_password_hash(user.hashed_password, password):
#             return User(user.id, user.username, user.hashed_password, user.last_name, user.first_name, user.middle_name,
#                         user.birth_date, user.position, user.role, user.category)
#         return None
#
#     @staticmethod
#     def create(username, password, last_name, first_name, middle_name, birth_date, position, role, category):
#         hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
#         session = SessionLocal()
#         user = UserModel(username=username, hashed_password=hashed_password, last_name=last_name, first_name=first_name,
#                          middle_name=middle_name, birth_date=birth_date, position=position, role=role,
#                          category=category)
#         session.add(user)
#         session.commit()
#         session.close()
#
#     @staticmethod
#     def get_by_username(username):
#         session = SessionLocal()
#         user = session.query(UserModel).filter(UserModel.username == username).first()
#         session.close()
#         if user:
#             return User(user.id, user.username, user.hashed_password, user.last_name, user.first_name, user.middle_name,
#                         user.birth_date, user.position, user.role, user.category)
#         return None
#
#     def has_role(self, *roles):
#         return self.role in roles
#
#
# class RoleModuleAccess(Base):
#     __tablename__ = 'role_module_access'
#     id = Column(Integer, primary_key=True, autoincrement=True)
#     role = Column(String, nullable=False)
#     module = Column(String, nullable=False)
#
#
# class RolePageAccess(Base):
#     __tablename__ = 'role_page_access'
#     id = Column(Integer, primary_key=True, autoincrement=True)
#     role = Column(String, nullable=False)
#     page = Column(String, nullable=False)
#
#
# def user_has_access(role, page):
#     session = SessionLocal()
#     access = session.query(RolePageAccess).filter_by(role=role, page=page).first()
#     session.close()
#     return access is not None
#
#
# class Setting(Base):
#     __tablename__ = 'settings'
#     __table_args__ = {'schema': 'settings'}
#
#     id = Column(Integer, primary_key=True)
#     name = Column(String(50), unique=True, nullable=False)
#     value = Column(Text, nullable=False)
#
#
# class Department(Base):
#     __tablename__ = 'departments'
#     __table_args__ = {'schema': 'info'}
#
#     id = Column(Integer, primary_key=True, index=True)
#     kvazar = Column(String, nullable=True)
#     weboms = Column(String, nullable=True)
#     miskauz = Column(String, nullable=True)
#     infopanel = Column(String, nullable=True)
