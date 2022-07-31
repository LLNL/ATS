import subprocess
import unittest

import ats.management
import ats.configuration
from ats.management import test
from ats.atsMachines.fluxScheduled import FluxScheduled

class Foo:
    def __init__(self):
        self.maxCores = 8
        self.options = []
            
    def calculateBasicCommandList(self):
        return ["./a.out", "5", "20"]

class TestFluxScheduled(unittest.TestCase):        
    def test_valid_jobspec(self):
        # ats.management.AtsManager()
        test1 = test("./a.out", "5 5", nt=4, np=1, nn=1)
        cmd = FluxScheduled.calculateCommandList(Foo(), test1)
        # cmd.append("--dry")
        return_code = subprocess.run(cmd).returncode
        self.assertGreater(return_code, -1) ## a 0 or positive return code indicates test passes

    def test_invalid_jobspec(self):
        ats.management.AtsManager.init(Foo())
        test1 = test("./a.out", "5 5", nn=0, ngpu=0)
        cmd = FluxScheduled.calculateCommandList(Foo(), test1)
        # cmd.append("--dry")
        return_code = subprocess.run(cmd).returncode
        self.assertLess(return_code, 0) ## any negative return value indicates that this fails


if __name__ == "__main__":
    unittest.main()