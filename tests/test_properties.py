from enum import Enum
from copy import copy, deepcopy

import unittest

from .example_data import (SimulatorFastTemplate, SimulatorFastConfig,
                           SimulatorTemplate, SimulatorConfig)
from .mock import template, config

from pynio.properties import (AttrDict, SolidDict,
                              TypedDict, TypedList, TypedEnum,
                              load_block)

mystr = 'abcdefg'
mydict = dict(zip(mystr, range(len(mystr))))
mydict['own'] = copy(mydict)


class abc(Enum):
    a = 0
    b = 1
    c = 2


class TestAttrDict(unittest.TestCase):
    def test_basic(self):
        attrdict = AttrDict(mydict)
        assert copy(attrdict) is not attrdict
        assert copy(attrdict) == attrdict
        assert deepcopy(attrdict) == attrdict
        assert isinstance(attrdict['own'], AttrDict)

    def test_descriptor(self):
        '''Tests the descriptor feature of the attr dict'''
        enum = TypedEnum(abc)
        attr = AttrDict(enum=enum, a=2)
        attr.a = 3
        assert attr['a'] == 3
        attr.enum = 0
        assert attr.enum == 'a'

# class TestSolid(unittest.TestCase):
#     def test_basic(self):
#         solid = SolidDict(mydict)
#         assert isinstance(solid['own'], SolidDict)
#         solid.f = 8
#         assert solid.f is 8
#         assert solid['f'] == solid.f
#         self.assertRaises(AttributeError, setattr, solid, 'dne', 'whatever')


class TestTypedDict(unittest.TestCase):
    def test_set(self):
        convert = TypedDict(mydict)
        convert.a = 8  # works
        assert convert.a == 8
        convert['b'] = 9.3  # works
        assert convert['b'] == 9
        assert convert.b == convert['b']

    def test_error(self):
        # import ipdb; ipdb.set_trace()
        convert = TypedDict(mydict)
        self.assertRaises(ValueError, setattr, convert, 'c', 'hello')

    def test_readonly(self):
        frozen = TypedDict(mydict)
        frozen.readonly = True
        self.assertRaises(TypeError, setattr, frozen, 'a', 5)
        self.assertRaises(TypeError, setattr, frozen, 'own', TypedDict({}))
        self.assertRaises(TypeError, setattr, frozen, 'own', {})

    def test_descriptor(self):
        venum = TypedEnum(abc)
        data = dict(mydict)
        data['enum'] = venum
        data = TypedDict(data)
        data.enum = 1
        self.assertEqual(data.enum, 'b')
        self.assertRaises(ValueError, data.__setattr__, 'enum', 'z')


class TestTypedList(unittest.TestCase):
    def test_append(self):
        mylist = list(range(10))
        l = TypedList(int, mylist)
        assert l == mylist
        l.append(10)
        l.append(13.4)
        l.append('67')
        assert l[-3:] == [10, 13, 67]

    def test_type_error(self):
        mylist = list(range(10))
        l = TypedList(int, mylist)
        self.assertRaises(ValueError, l.append, 'hello')
        self.assertRaises(ValueError, l.__setitem__, 5, 'hello')

    def test_setitem(self):
        mylist = list(range(10))
        l = TypedList(int, mylist)
        l[0] = 100
        assert l[0] == 100
        l[1] = 3.23423
        assert l[1] == 3


class TestTypedEnum(unittest.TestCase):
    def test_value_enum_only(self):
        venum = TypedEnum(abc)
        venum.value = 'a'
        venum.value = 1
        venum.value = abc.a
        with self.assertRaises(ValueError):
            venum.value = 6

    def test_setting(self):
        venum = TypedEnum(abc)
        venum.value = 1
        self.assertEqual(venum.name, 'b')

    def test_descriptor(self):
        venum = TypedEnum(abc)
        venum.__set__(None, 1)
        self.assertEqual(venum.__get__(None, None), 'b')

    def test_setting_enum(self):
        '''enum should be able to be set with another enum object'''
        venum = TypedEnum(abc)
        venum2 = TypedEnum(abc)
        venum2.__set__(None, 'b')
        venum.__set__(None, venum2)
        self.assertEqual(venum.value, venum2.value)
        self.assertEqual(venum.value, 1)


class TestLoadProperties(unittest.TestCase):
    def test_load_simple(self):
        blk = load_block(template, 'type')
        blk.name = 'name'
        self.assertEqual(blk.__basic__(), config)

    def test_load_list(self):
        t = deepcopy(template)
        t['properties']['attributes'] = {
            'type': 'list',
            'template': {
                'name': {
                    'type': 'str',
                    'default': 'attrname'
                },
                'value': {
                    'type': 'float',
                    'default': 42.2
                }
            }
        }
        blk = load_block(t, 'type')
        blk.name = 'name'
        c = deepcopy(config)
        c['attributes'] = []
        self.assertEqual(blk.__basic__(), c)
        default = [{
            'name': 'othername',
            'value': -3.14
        }]

        c['attributes'].extend(default)
        # make sure that the object updates properly
        # import ipdb; ipdb.set_trace()
        blk.update(c)
        self.assertEqual(blk.__basic__(), c)

        t['properties']['attributes']['default'] = default
        blk = load_block(t, 'type')
        blk.name = 'name'
        self.assertEqual(blk.__basic__(), c)

    def test_load_simulator_template(self):
        blk = load_block(SimulatorFastTemplate)
        blk.name = 'fastsim'
        blk.type = 'SimulatorFast'
        self.assertEqual(blk.__basic__(), SimulatorFastConfig)
        blk = load_block(SimulatorTemplate)
        blk.update(SimulatorConfig)
        self.assertEqual(blk.__basic__(), SimulatorConfig)

    def test_set_simulator(self):
        '''Which api would you rather use?'''
        blk = load_block(SimulatorFastTemplate)
        blk.type = 'SimulatorFast'
        blk.name = 'newsim'
        blk.attribute.name = 'newsim'
        blk.attribute.value.end = 5.8
        blk.interval.days = 100
        config = deepcopy(SimulatorFastConfig)
        config['name'] = 'newsim'
        config['attribute']['name'] = 'newsim'
        config['attribute']['value']['end'] = 5
        config['interval']['days'] = 100
        self.assertEqual(config, blk.__basic__())

    def test_typecheck_simulator(self):
        blk = load_block(SimulatorFastTemplate)
        self.assertRaises(TypeError, setattr, blk.attribute.value.end, 'bad')
        self.assertRaises(TypeError, setattr, blk.interval.days, 'bad')
        blk.log_level = 'DEBUG'
        self.assertRaises(ValueError, setattr, blk, 'log_level', 'bad')
