from pprint import pprint
from enum import Enum
from copy import copy, deepcopy

import unittest

from .example_data import (SimulatorFastTemplate, SimulatorFastConfig)

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

    def test_frozen(self):
        frozen = TypedDict(mydict, frozentypes=dict)
        frozen.a = 5
        assert frozen['a'] == 5
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
    def test_basic(self):
        venum = TypedEnum(abc)
        venum.value = 'a'
        venum.value = 1
        venum.value = abc.a
        with self.assertRaises(ValueError):
            venum.value = 6

    def test_descriptor(self):
        '''test mostly the features of __get__ and __set__
        Basically when they are just objects they are fair game,
        but when they become a member of a class they are super
        protected (I can't even figure out a way to get access to
        the base object)'''
        venum = TypedEnum(abc)
        assert isinstance(venum, TypedEnum)
        # set works normally when not a member of an object
        venum = 0
        assert isinstance(venum, int)

        venum = TypedEnum(abc)
        x = venum
        assert isinstance(x, TypedEnum)


        # But when it is a member of a class/object, it is hidden
        class C:
            e = venum

        c = C()
        assert c.e == 'a' and isinstance(c.e, str)
        c.e = 'b'
        assert c.e == 'b' and isinstance(c.e, str)
        self.assertRaises(ValueError, setattr, c, 'e', 'z')

        # However, when it is added on in init it doesn't behave the same
        # way
        class C:
            def __init__(self):
                self.e = venum

        c = C()
        assert c.e != 'a' and isinstance(c.e, TypedEnum)

        # to implement this, we need to overload the getattr
        class D(C):
            def __getattribute__(self, attr):
                obj = object.__getattribute__(self, attr)
                if hasattr(obj, '__get__'):
                    print('getting __get__')
                    return obj.__get__(self)
                else:
                    return obj

            def __setattr__(self, attr, value):
                if not hasattr(self, attr):
                    object.__setattr__(self, attr, value)
                    return
                obj = object.__getattribute__(self, attr)
                if hasattr(obj, '__set__'):
                    print('setting __set__')
                    obj.__set__(self, value)
                else:
                    setattr(self, attr, value)

        c = D()
        c.e = 'b'
        assert c.e == 'b' and isinstance(c.e, str)
        self.assertRaises(ValueError, setattr, c, 'e', 'z')


class TestLoadProperties(unittest.TestCase):
    def test_load_simulator_template(self):
        blk = load_block(SimulatorFastTemplate)
        print()
        pprint(blk)

    def test_set_simulator(self):
        blk = load_block(SimulatorFastTemplate)
        blk.attribute.name = 'newsim'
        blk.attribute.value.end = 5.8
        blk.interval.days = 100
        pprint(blk)

    def test_typecheck_simulator(self):
        blk = load_block(SimulatorFastTemplate)
        self.assertRaises(TypeError, setattr, blk.attribute.value.end, 'bad')
        self.assertRaises(TypeError, setattr, blk.interval.days, 'bad')
