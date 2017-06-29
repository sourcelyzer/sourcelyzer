from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class BaseResource():

    def toDict(self):
        attrs = {}
        for c in self.__table__.columns:
            if str(c.type) == 'DATETIME':
                attrs[c.key] = str(getattr(self, c.key))
            else:
                attrs[c.key] = getattr(self, c.key)
        return attrs

Base = declarative_base(cls=BaseResource)
