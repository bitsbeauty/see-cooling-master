# im Terminal: python -m pwiz -e mysql -u root -P seelandtraum seebier > blog_models.py

from peewee import *

database = MySQLDatabase('seebier', **{'password': 'seelandtraum', 'user': 'root'})

class UnknownField(object):
    def __init__(self, *_, **__): pass

class BaseModel(Model):
    class Meta:
        database = database

class Header(BaseModel):
    starttime = IntegerField(null=True)
    temp_air = DecimalField(null=True)
    temp_beer = DecimalField(null=True)
    temp_target = DecimalField(null=True)

    class Meta:
        db_table = 'header'

class Steps(BaseModel):
    step_duration = IntegerField()
    step_temperature = DecimalField()
    tank = IntegerField(db_column='tank_id')

    class Meta:
        db_table = 'steps'

