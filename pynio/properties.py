from enum import Enum
from copy import deepcopy


def isiter(obj):
    return (False if isinstance(obj, (str, bytes))
            else True if
            (hasattr(obj, '__iter__') or hasattr(obj, '__next__'))
            else False)


class AttrDict(dict):
    '''Dictionary that allows item access via getattr
    It also does some fun stuff with descriptors to allow objects in
    it's dictionary to use descriptors (you can define the
    __get__ and __set__ methods of items and they will be used)

    Developer Notes:
    -   This object is designed so that ALL user attributes go into the
        dictionary. Think if it as:
            attrdict.key = value := attrdict['key'] = value
    -   This upholds descriptors for lesser objects, to make for default
            item assignment and typing
    '''
    readonly = False  # doesn't allow item setting at all

    def __init__(self, *args, **kwargs):
        dict.__init__(self, *args, **kwargs)
        # Make all internal dictionaries AttrDicts. Make sure this
        # Overrides any super class's settings
        for key, value in self.items():
            if type(value) == dict:
                dict.__setitem__(self, key, self.__class__(value))

    def update(self, value):
        if isinstance(value, dict):
            value = value.items()
        for key, value in value:
            if hasattr(self[key], 'update'):
                self[key].update(value)
            else:
                self[key] = value

    def _get_attr(self, attr):
        '''Convience function to bypass the special __getattribute__
        funcitonality (specifically descriptors in items)'''
        try:
            return object.__getattribute__(self, attr)
        except AttributeError:
            return self._get_item(attr)

    def _get_item(self, item):
        '''Convinience function to pypass special machinery
        (like descriptors in items)'''
        return dict.__getitem__(self, item)

    def _get(self, obj):
        '''Uses descriptors where possible'''
        if hasattr(obj, '__get__'):
            return obj.__get__(self)
        else:
            return obj

    def _set(self, key, value):
        '''Automatically convert dictionaries set into AttrDict'''
        if isinstance(value, dict):
            value = self.__class__(value)
            assert isinstance(value, AttrDict)
        if self.readonly:
            raise TypeError('{} is read only'.format(self))
        dict.__setitem__(self, key, value)

    def __getattribute__(self, attr, keyonly=False):
        '''Where all the magic happens. Allows for item assignment through
        attribute notation'''
        try:
            if keyonly: raise AttributeError
            # First try the standard attr lookup and return that
            return object.__getattribute__(self, attr)
        except AttributeError:
            # all attributes that the user sets are stored in the dictionary
            # internal keys
            try:
                obj = dict.__getitem__(self, attr)
            except KeyError:
                raise AttributeError
        return self._get(obj)

    def __setattr__(self, attr, value, keyonly=False):
        '''keyonly should only be used from __setitem__
        It only looks inside the core dictionary keys'''
        try:
            if keyonly:
                raise AttributeError
            # make sure the attribute exists before we set it
            obj = object.__getattribute__(self, attr)
            object.__setattr__(self, attr, value)
            return
        except AttributeError:
            if attr in self:
                obj = dict.__getitem__(self, attr)
            else:  # New object, only minor checking
                return self._set(attr, value)

        if hasattr(obj, '__set__'):
            # print('setting __set__', obj, attr, value)
            obj.__set__(self, value)
        else:
            self._set(attr, value)

    def __setitem__(self, key, value):
        self.__setattr__(key, value, keyonly=True)

    def __getitem__(self, key):
        try:
            return self.__getattribute__(key, keyonly=True)
        except AttributeError as exc:
            raise KeyError from exc

    def __copy__(self, *args, **kwargs):
        return self.__class__(self)

    def __deepcopy__(self, *args, **kwargs):
        return self.__class__({key: deepcopy(value) for (key, value) in self.items()})


class SolidDict(AttrDict):
    '''Dictionary like object that doesn't allow it's shape to change
    (cannot add or remove keys)
    Does the same for all items inside of it'''
    def __setitem__(self, item, value):
        if item not in self:
            raise KeyError(item)
        AttrDict.__setitem__(self, item, value)

    def __setattr__(self, attr, value, *args, **kwargs):
        if not hasattr(self, attr):
            raise AttributeError(attr)
        AttrDict.__setattr__(self, attr, value, *args, **kwargs)


class TypedDict(AttrDict):
    '''Dictionary like object that keeps track of types. Choose whether
        to attempt to convert types (default) or not allow different types.
    Arguments:
        convert: whether to attempt to convert values that don't match
    '''
    def __init__(self, *args, convert=True, **kwargs):
        object.__setattr__(self, '_convert', convert)
        super().__init__(*args, **kwargs)

    def update(self, value, drop_unknown=False, drop_logger=None):
        if drop_unknown:
            newv = {}
            for key, value in value.items():
                if key in self:
                    newv[key] = value
                else:
                    if drop_logger is not None:
                        drop_logger("Value Dropped: {}".format(key))
            value = newv
        return AttrDict.update(self, value)

    def _convert_value(self, value, curval):
        '''Convert value to type(curvalue). Also do associated error checking'''
        curtype = type(curval)
        if not isinstance(value, curtype):
            if self._convert:
                value = curtype(value)
            else:
                raise TypeError("{} is not type {}".format(value, curtype))
        return value

    def __setitem__(self, item, value):
        actual = self._get_item(item)
        if hasattr(actual, '__set__'):
            actual.__set__(None, value)
            return
        curval = self[item]
        value = self._convert_value(value, curval)
        AttrDict.__setitem__(self, item, value)

    def __setattr__(self, attr, value, keyonly=False):
        if keyonly:
            actual = self._get_item(attr)
        else:
            actual = self._get_attr(attr)
        if hasattr(actual, '__set__'):
            actual.__set__(None, value)
            return
        curval = getattr(self, attr)
        value = self._convert_value(value, curval)
        AttrDict.__setattr__(self, attr, value, keyonly)

    def __set__(self, obj, value):
        raise TypeError("TypedDict is a protected member")

    def __basic__(self):
        '''returns self in only basic python types.'''
        out = {}
        for key in self:
            value = dict.__getitem__(self, key)
            if hasattr(value, '__basic__'):
                value = value.__basic__()
            elif hasattr(value, '__get__'):
                value = value.__get__(self, self.__class__)
            out[key] = value
        return out


class TypedList(list):
    '''A list that preserves types
        type: the type of list elements to preserve
        convert: whether to attempt automatic conversion to type
        noset: don't allow setting of existing elements
    '''
    def __init__(self, type, *args, convert=True, noset=False, **kwargs):
        self._type = type
        self._convert = convert
        self._noset = noset
        list.__init__(self)  # make self an empty list
        convert = self._convert
        self.extend(tuple(*args, **kwargs))

    def __basic__(self):
        '''returns self in only basic python types.'''
        out = []
        for value in list.__iter__(self):
            if hasattr(value, '__basic__'):
                value = value.__basic__()
            elif hasattr(value, '__get__'):
                value = value.__get__(self, self.__class__)
            out.append(value)
        return out

    def update(self, value):
        new = TypedList(self._type, value)  # check types
        self.clear()
        self.extend(new)

    def _convert_value(self, value):
        if hasattr(self._type, 'update'):
            _type = deepcopy(self._type)
            _type.update(value)
            value = _type
        elif not isinstance(value, type):
            return self._type(value)
        return value

    def append(self, value):
        value = self._convert_value(value)
        list.append(self, value)

    def extend(self, iterator):
        for i in iterator:
            self.append(i)

    def __setitem__(self, item, value):
        if self._noset:
            raise IndexError("items cannot be set with noset=True")
        value = self._convert_value(value)
        list.__setitem__(self, item, value)

    def __set__(self, obj, value):
        raise TypeError("Typed List is a protected member")


class TypedEnum:
    '''Class to make setting of enum types valid and error checked'''
    def __init__(self, enum, default=None):
        self._enum = enum
        self._enum_by_value = {e.value: e for e in enum}
        self._enum_by_name = {e.name: e for e in enum}
        self._value = next(iter(enum))
        if default is not None:
            self.value = default

    @property
    def value(self):
        return self._value.value

    @value.setter
    def value(self, value):
        if value in self._enum:
            value = getattr(self._enum, value.name)
        elif value in self._enum_by_name:
            value = self._enum_by_name[value]
        elif value in self._enum_by_value:
            value = self._enum_by_value[value]
        else:
            raise ValueError("Value does not exist in enum: {}".format(value))
        self._value = value

    @property
    def name(self):
        return self._value.name

    def __repr__(self):
        return repr(self._value.name)

    def __get__(self, obj, type=None):
        return self._value.name

    def __set__(self, obj, value):
        self.value = value


# Additional Properties
class Properties(TypedDict):
    TYPE = 'properties'


class TimeDelta(TypedDict):
    TYPE = 'timedelta'


class NioObject(TypedDict):
    TYPE = 'object'


TypedList.TYPE = 'list'
TypedEnum.TYPE = 'select'


def load_block(template, type=None):
    '''Parsing function to load a block from a template dictionary'''
    template = deepcopy(template)
    config = load_properties(template['properties'])
    if type is not None:
        config.type = type
    return config


def load_properties(properties, obj=Properties):
    out = {}
    for key, value in properties.items():
        out[key] = load_template(value)
    return obj(out)


# Functions to go into PROPERTIES
def load_template(template):
    try:
        hastype = 'type' in template
    except TypeError:
        hastype = False
    if hastype:
        ttype = template.pop('type')
        load_function = PROPERTIES[ttype]
        if 'template' in template or 'options' in template:
            return load_function(template)
        elif 'default' in template:
            return load_function(template['default'])
        else:
            return load_function()
    else:
        return template


def load_list(template):
    default = template.get('default', [])
    if 'type' not in template:
        # Lists have an interesting feature where they assume you know
        # their attributes are objects if they don't have a type
        template['type'] = 'object'
    template = load_template(template)
    return TypedList(template, default)


# Define all the properties and how to load them when you get their dict
PROPERTIES = {
    TimeDelta.TYPE: lambda p: TimeDelta(p),
    TypedEnum.TYPE: lambda p: TypedEnum(Enum('NioEnum', p['options'].items()),
                                        p['default']),
    TypedList.TYPE: load_list,
    NioObject.TYPE: lambda p: load_properties(p['template'], NioObject),
    'bool': bool,
    'str': str,
    'int': int,
    'float': float
}
