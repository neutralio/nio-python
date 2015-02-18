import unittest
from pynio import Instance, Block, Service

host = '127.0.0.1'
port = 7357
creds = 'Admin', 'Admin'



class TestLive(unittest.TestCase):
    NUM_SERVICES = 200

    def test_simple(self):
        nio = Instance(host, port, creds)
        sim = Block('sim', 'SimulatorFast')
        log = Block('log', 'LoggerBlock')
        nio.add_block(sim)
        nio.add_block(log)

        service = Service('testsdk')
        service.connect(sim, log)
        nio.add_service(service)
        try:
            service.stop()
        except:
            pass
        service.start()
        service.stop()

        sim.delete()
        log.delete()
        service.delete()

    def test_start_stop(self):
        '''Create instance with blocks'''
        nio = Instance(host, port, creds)
        nio.DELETE_ALL()
        services = [Service('sim_{}'.format(n)) for n in
                    range(self.NUM_SERVICES)]
        sim = Block('sim', 'SimulatorFast')
        log = Block('log', 'LoggerBlock')
        sim = sim
        log = log
        nio.add_block(sim)
        nio.add_block(log)
        for s in services:
            s.connect(sim, log)
            nio.add_service(s)

        nio.start(services)
        nio.stop(services)
        nio.DELETE_ALL()
        self.assertFalse(nio.services)
        self.assertFalse(nio.blocks)
