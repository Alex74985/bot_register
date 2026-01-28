from datetime import datetime
from models import session
from models import Base as BaseObj
from models import engine as BaseEngine
from sqlalchemy import func


class DataBase:
    def select_all(self, Model, **filter_s):
        query = session.query(Model)
        if len(filter_s) > 0:
            query = query.filter_by(**filter_s)
        return query.all()

    def select_regs_active(self, Model, **filter_s):
        querry = (
            session.query(Model)
            .where(Model.datetime >= datetime.now())
            .order_by(Model.datetime)
        )
        if len(filter_s) > 0:
            querry = querry.filter_by(**filter_s)
        return querry.all()

    def select_regs_expired(self, Model, **filter_s):
        querry = (
            session.query(Model)
            .where(Model.datetime < datetime.now())
            .order_by(Model.datetime)
        )
        if len(filter_s) > 0:
            querry = querry.filter_by(**filter_s)
        return querry.all()

    def select_occupied(self, Model, date, **filter_s):
        query = session.query(Model).where(func.date(Model.datetime) == date)
        if len(filter_s) > 0:
            query = query.filter_by(**filter_s)
        return query.all()

    def select_permanent(self, Model, weekday, **filter_s):
        query = (
            session.query(Model)
            .where(Model.weekday == weekday)
            .where(
                func.date(Model.time)
                == datetime.strptime("1970-01-01", "%Y-%m-%d").date()
            )
            .order_by(Model.time)
        )
        if len(filter_s) > 0:
            query = query.filter_by(**filter_s)
        return query.all()

    def select_temporary(self, Model, date, **filter_s):
        query = (
            session.query(Model)
            .where(func.date(Model.time) == date)
            .order_by(Model.time)
        )
        if len(filter_s) > 0:
            query = query.filter_by(**filter_s)
        return query.all()

    def get_one(self, Model, **filter_s):
        query = session.query(Model)
        if len(filter_s) > 0:
            query = query.filter_by(**filter_s)
        return query.first()

    def test(self, Model, **filter_s):
        if self.get_one(Model, **filter_s):
            return True
        else:
            return False

    def new(self, Model, *args):
        tmp_new = Model(*args)
        session.add(tmp_new)
        session.commit()
        return tmp_new

    def delete(self, Model, **filter_s):
        obj = self.select_all(Model, **filter_s)
        if obj:
            for i in obj:
                session.delete(i)
            session.commit()
            return True
        else:
            return False

    def update(self, Model, set, **filter_s):
        query = session.query(Model)
        if len(filter_s) > 0:
            query = query.filter_by(**filter_s)
        query.update(set)
        session.commit()
        return True

    def set_state(self, Model, *args):
        to_byte = Model(*args)
        session.add(to_byte)
        session.commit()

    def base_init(self):
        BaseObj.metadata.create_all(BaseEngine)


d = DataBase()
d.base_init()
print("ok")
