""" Tests for fields """
import os
from datetime import datetime, date

import json
from decimal import Decimal

from . import BaseSystemTest
from flywheel import (Field, Model, NUMBER, BINARY, STRING_SET, NUMBER_SET,
                      BINARY_SET, GlobalIndex)


class Widget(Model):

    """ Model for testing default field values """
    __metadata__ = {
        'global_indexes': [
            GlobalIndex('gindex', 'string2', 'num'),
        ],
    }
    string = Field(hash_key=True)
    string2 = Field()
    num = Field(data_type=NUMBER, check=lambda x: x >= 0)
    binary = Field(data_type=BINARY, coerce=True)
    str_set = Field(data_type=STRING_SET)
    num_set = Field(data_type=NUMBER_SET)
    bin_set = Field(data_type=BINARY_SET)

    def __init__(self, **kwargs):
        self.string = 'abc'
        for key, val in kwargs.iteritems():
            setattr(self, key, val)


class TestFields(BaseSystemTest):

    """ Tests for default values """
    models = [Widget]

    def test_field_default(self):
        """ If fields are not set, they default to a reasonable value """
        w = Widget()
        self.assertIsNone(w.string2)
        self.assertIsNone(w.binary)
        self.assertEquals(w.num, 0)
        self.assertEquals(w.str_set, set())
        self.assertEquals(w.num_set, set())
        self.assertEquals(w.bin_set, set())

    def test_valid_check(self):
        """ Widget saves if validation checks pass """
        w = Widget(num=5)
        self.engine.save(w)

    def test_invalid_check(self):
        """ Widget raises error on save if validation checks fail """
        w = Widget(num=-5)
        with self.assertRaises(ValueError):
            self.engine.save(w)

    def test_no_save_defaults(self):
        """ Default field values are not saved to dynamo """
        w = Widget(string2='abc')
        self.engine.sync(w)
        table = w.meta_.ddb_table(self.dynamo)
        result = dict(list(table.scan())[0])
        self.assertEquals(result, {
            'string': w.string,
            'string2': w.string2,
        })

    def test_sync_twice_no_defaults(self):
        """ Syncing twice should still not save any defaults """
        w = Widget(string2='abc')
        self.engine.sync(w)
        w.string2 = 'def'
        w.sync()
        table = w.meta_.ddb_table(self.dynamo)
        result = dict(list(table.scan())[0])
        self.assertEquals(result, {
            'string': w.string,
            'string2': w.string2,
        })

    def test_set_updates(self):
        """ Sets track changes and update during sync() """
        w = Widget(string='a')
        self.engine.save(w)
        w.str_set.add('hi')
        w.sync()
        stored_widget = self.engine.scan(Widget).all()[0]
        self.assertEquals(w.str_set, stored_widget.str_set)

    def test_set_updates_fetch(self):
        """ Items retrieved from db have sets that track changes """
        w = Widget(string='a', str_set=set(['hi']))
        self.engine.save(w)
        w = self.engine.scan(Widget).all()[0]
        w.str_set.add('foo')
        w.sync()
        stored_widget = self.engine.scan(Widget).all()[0]
        self.assertEquals(w.str_set, stored_widget.str_set)

    def test_set_updates_replace(self):
        """ Replaced sets also track changes for updates """
        w = Widget(string='a')
        w.str_set = set(['hi'])
        self.engine.sync(w)
        w.str_set.add('foo')
        w.sync()
        stored_widget = self.engine.scan(Widget).all()[0]
        self.assertEquals(w.str_set, stored_widget.str_set)

    def test_store_extra_number(self):
        """ Extra number fields are stored as numbers """
        w = Widget(string='a', foobar=5)
        self.engine.sync(w)

        table = Widget.meta_.ddb_table(self.dynamo)
        result = list(table.scan())[0]
        self.assertEquals(result['foobar'], 5)
        stored_widget = self.engine.scan(Widget).all()[0]
        self.assertEquals(stored_widget.foobar, 5)

    def test_store_extra_string(self):
        """ Extra string fields are stored as json strings """
        w = Widget(string='a', foobar='hi')
        self.engine.sync(w)

        table = Widget.meta_.ddb_table(self.dynamo)
        result = list(table.scan())[0]
        self.assertEquals(result['foobar'], json.dumps('hi'))
        stored_widget = self.engine.scan(Widget).all()[0]
        self.assertEquals(stored_widget.foobar, 'hi')

    def test_store_extra_set(self):
        """ Extra set fields are stored as sets """
        foobar = set(['hi'])
        w = Widget(string='a', foobar=foobar)
        self.engine.sync(w)

        table = Widget.meta_.ddb_table(self.dynamo)
        result = list(table.scan())[0]
        self.assertEquals(result['foobar'], foobar)
        stored_widget = self.engine.scan(Widget).all()[0]
        self.assertEquals(stored_widget.foobar, foobar)

    def test_store_extra_dict(self):
        """ Extra dict fields are stored as json strings """
        foobar = {'foo': 'bar'}
        w = Widget(string='a', foobar=foobar)
        self.engine.save(w)

        table = Widget.meta_.ddb_table(self.dynamo)
        result = list(table.scan())[0]
        self.assertEquals(result['foobar'], json.dumps(foobar))
        stored_widget = self.engine.scan(Widget).all()[0]
        self.assertEquals(stored_widget.foobar, foobar)


class PrimitiveWidget(Model):

    """ Model for testing python data types """
    __metadata__ = {
        'global_indexes': [
            GlobalIndex('gindex', 'string2', 'num'),
            GlobalIndex('gindex2', 'num2', 'binary'),
        ],
    }
    string = Field(data_type=str, hash_key=True)
    string2 = Field(data_type=unicode)
    num = Field(data_type=int, coerce=True)
    num2 = Field(data_type=float)
    binary = Field(data_type=BINARY, coerce=True)
    myset = Field(data_type=set)
    data = Field(data_type=dict)
    friends = Field(data_type=list)
    created = Field(data_type=datetime)
    birthday = Field(data_type=date)
    wobbles = Field(data_type=bool)
    price = Field(data_type=Decimal)

    def __init__(self, **kwargs):
        self.string = 'abc'
        for key, val in kwargs.iteritems():
            setattr(self, key, val)


class TestPrimitiveDataTypes(BaseSystemTest):

    """ Tests for default values """
    models = [PrimitiveWidget]

    def test_field_default(self):
        """ If fields are not set, they default to a reasonable value """
        w = PrimitiveWidget()
        self.assertIsNone(w.string2)
        self.assertIsNone(w.binary)
        self.assertEquals(w.num, 0)
        self.assertEquals(w.num2, 0)
        self.assertEquals(w.myset, set())
        self.assertEquals(w.data, {})
        self.assertEquals(w.wobbles, False)
        self.assertEquals(w.friends, [])
        self.assertIsNone(w.created)
        self.assertIsNone(w.birthday)
        self.assertEquals(w.price, 0)
        self.assertTrue(isinstance(w.price, Decimal))

    def test_dict_updates(self):
        """ Dicts track changes and update during sync() """
        w = PrimitiveWidget(string='a')
        self.engine.save(w)
        w.data['foo'] = 'bar'
        w.sync()
        stored_widget = self.engine.scan(PrimitiveWidget).all()[0]
        self.assertEquals(w.data, stored_widget.data)

    def test_store_bool(self):
        """ Dicts track changes and update during sync() """
        w = PrimitiveWidget(string='a', wobbles=True)
        self.engine.sync(w)
        stored_widget = self.engine.scan(PrimitiveWidget).all()[0]
        self.assertTrue(stored_widget.wobbles is True)

    def test_str(self):
        """ Str type always converts value to bytestring """
        w = PrimitiveWidget(string=os.urandom(10))
        self.assertTrue(isinstance(w.string, str))
        self.engine.save(w)
        stored_widget = self.engine.scan(PrimitiveWidget).all()[0]
        self.assertTrue(isinstance(stored_widget.string, str))
        self.assertEquals(stored_widget.string, w.string)

    def test_datetime(self):
        """ Can store datetime & it gets returned as datetime """
        w = PrimitiveWidget(string='a', created=datetime.utcnow())
        self.engine.sync(w)
        stored_widget = self.engine.scan(PrimitiveWidget).all()[0]
        self.assertEquals(w.created, stored_widget.created)

    def test_date(self):
        """ Can store date & it gets returned as date """
        w = PrimitiveWidget(string='a', birthday=date.today())
        self.engine.sync(w)
        stored_widget = self.engine.scan(PrimitiveWidget).all()[0]
        self.assertEquals(w.birthday, stored_widget.birthday)

    def test_decimal(self):
        """ Can store decimal & it gets returned as decimal """
        w = PrimitiveWidget(string='a', price=Decimal('3.50'))
        self.engine.sync(w)
        stored_widget = self.engine.scan(PrimitiveWidget).all()[0]
        self.assertEquals(w.price, stored_widget.price)
        self.assertTrue(isinstance(stored_widget.price, Decimal))

    def test_int_no_data_loss(self):
        """ Int fields refuse to drop floating point data """
        w = PrimitiveWidget()
        with self.assertRaises(ValueError):
            w.num = 4.5
        with self.assertRaises(ValueError):
            w.num = Decimal('4.5')

    def test_int_coerce(self):
        """ Int fields can coerce floats """
        w = PrimitiveWidget()
        w.num = 4.0
        self.assertEquals(w.num, 4)
        self.assertTrue(isinstance(w.num, int))

    def test_list_updates(self):
        """ Lists track changes and update during sync() """
        w = PrimitiveWidget(string='a')
        self.engine.save(w)
        w.friends.append('Fred')  # pylint: disable=E1101
        w.sync()
        stored_widget = self.engine.scan(PrimitiveWidget).all()[0]
        self.assertEquals(w.friends, stored_widget.friends)
