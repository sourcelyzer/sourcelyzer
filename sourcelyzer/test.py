class BaseClass():
    dbobj = None

    def __init__(self):
        if self.dbobj == None:
            print "none"
        else:
            print self.dbobj

class TestObj():
    def __init__(self):
        pass

class ChildClass(BaseClass):
    def __init__(self):
        BaseClass.__init__(self)

class GoodClass(BaseClass):
    dbobj = TestObj()

    def __init__(self):
        BaseClass.__init__(self)

cc = ChildClass()
gc = GoodClass()
