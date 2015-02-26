import unittest
from unittest.mock import MagicMock
from copy import deepcopy

from pynio import Block
from .mock import mock_instance, config, template


class TestBlock(unittest.TestCase):

    def test_block(self):
        b = Block('name', 'type')
        self.assertEqual(b.name, 'name')
        self.assertEqual(b.type, 'type')

    def test_noname(self):
        with self.assertRaises(ValueError):
            Block('', 'type')

    def test_save(self):
        b = Block('name', 'type', config)
        b._instance = mock_instance()
        b._put = MagicMock()
        b.save()
        self.assertTrue(b._put.called)
        self.assertEqual(b._put.call_args[0][0], 'blocks/name')
        self.assertDictEqual(b._put.call_args[0][1],
                                {'name': 'name',
                                'type': 'type',
                                'value': 0})

    def test_copy(self):
        b = Block('name', 'type', {'key': 'value'})
        bcopy = b.copy('newname')
        self.assertDictEqual({
            'name': 'newname',
            'type': 'type',
            'key': 'value'
        }, bcopy.config)
        self.assertDictEqual({
            'name': 'name',
            'type': 'type',
            'key': 'value'
        }, b.config)

        with self.assertRaises(ValueError):
            b.copy('')

    def test_save_with_no_instance(self):
        b = Block('name', 'type')
        b._config = {'key': 'val'}
        b._put = MagicMock()
        with self.assertRaises(Exception) as context:
            b.save()
        self.assertTrue('Block is not associated with an instance' in
                        context.exception.args[0])
        self.assertFalse(b._put.called)

    def test_load_template(self):
        from .example_data import SimulatorFastTemplate
        instance = lambda: None
        instance.droplog = print
        btype = 'SimulatorFast'
        b = Block('sim', btype)
        b._load_template(btype, SimulatorFastTemplate, instance)
        from pprint import pprint
        print()
        pprint(b.template)
        self.assertRaises(TypeError, setattr, b.template, 'type', 'foo')

    def test_typed_config(self):
        from .example_data import SimulatorFastTemplate, SimulatorFastConfig
        instance = lambda: None
        instance.droplog = print
        btype = 'SimulatorFast'
        b = Block('sim', btype, config=SimulatorFastConfig)
        b._load_template(btype, SimulatorFastTemplate, instance)
        b.config.interval.days = 10
        self.assertEqual(b.config.interval.days, 10)
        self.assertRaises(ValueError, setattr,
                            b.config.interval, 'days', 'bad')

    def test_load_config(self):
        instance = mock_instance()
        b = Block('name', 'type', config, instance=instance)
        b.save()
        self.assertDictEqual(b.json(), config)
        self.assertTrue(instance._put.called)

    def test_config_drop(self):
        '''Ensure it drops non-existant settings'''
        c = deepcopy(config)
        c['notthere'] = 4
        instance = mock_instance()
        b = Block('name', 'type', c, instance=instance)
        b.save()
        self.assertDictEqual(b.json(), config)
        self.assertTrue(instance._put.called)

    def test_load_all_templates(self):
        from .example_data import BlocksTemplatesAll
        instance = lambda: None
        instance.droplog = MagicMock()
        for btype, template in BlocksTemplatesAll.items():
            b = Block(btype, btype)
            b._load_template(btype, template, instance)


    def test_load_all_configs(self):
        from .example_data import BlocksTemplatesAll, BlocksConfigsAll
        instance = lambda: None
        instance.droplog = MagicMock()

        blocks_types = {}
        for btype, template in BlocksTemplatesAll.items():
            b = Block(btype, btype)
            b._load_template(btype, template, instance)
            blocks_types[btype] = b
            str(b)  # verify no error is raised

        blocks = {}
        for bname, config in BlocksConfigsAll.items():
            # import ipdb; ipdb.set_trace()
            btype = config['type']
            b = deepcopy(blocks_types[btype])
            b.config = config
            blocks[bname] = b
            str(b)  # verify no error is raised

        droplog = instance.droplog
        self.assertEqual(droplog.call_count, 2)

    def test_delete_block(self):
        instance = mock_instance()
        s = instance.create_service('foo')
        b = s.create_block('one', 'type')
        b2 = s.create_block('two', 'type')
        s.connect(b, b2)
        b.delete()
        execution = s.config['execution']
        self.assertListEqual(execution, [
            {'name': 'two', 'receivers': []}
        ])

    def test_in_use(self):
        instance = mock_instance()
        s = instance.create_service('foo')
        instance.create_service('bar')
        blk = s.create_block('one', 'type')
        use = blk.in_use()
        self.assertListEqual(use, [s])
