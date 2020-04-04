import tempfile
import subprocess
import copy
from typing import *
class PreloadBencher:
    def __init__(self, exec, args=(), extra_env : Mapping[str, str] = None, stdin: Optional[bytes] = None, lib_path=None):
        self.exec = exec
        self.args = args
        self.lib_path = lib_path
        if extra_env:
            self.env = extra_env
        else:
            self.env = {}
        self.stdin = stdin
        self.stderr = None
        self.stdout = None

    def run(self):
        with tempfile.NamedTemporaryFile() as time_record:
            env = copy.deepcopy(self.env)
            if self.lib_path:
                env["LD_PRELOAD"] = self.lib_path
            child = subprocess.run(["env", "time", "-f", "%F %e %M", "-o", time_record.name, self.exec, *self.args], env=env, stderr=subprocess.PIPE, stdin=self.stdin, stdout=subprocess.PIPE)
            with open(time_record.name) as file:
                res = file.readline().split()
                self.stdout = str(child.stdout)
                self.stderr = str(child.stderr)
                self.returncode = child.returncode
                self.page_fault = int(res[0])
                self.time_escape = float(res[1])
                self.mem_peak = int(res[2])

class CFRAC(PreloadBencher):
    def __init__(self, lib_path=None):
        super().__init__("benchmark/cfrac", args=["17545186520507317056371138836327483792789528"], lib_path=lib_path)

class AllocTest(PreloadBencher):
    def __init__(self, lib_path=None, size=16):
        self.size = size
        super().__init__("benchmark/alloc-test", args=[str(size)], lib_path=lib_path)

class Z3(PreloadBencher):
    def __init__(self, lib_path=None):
        super().__init__("z3", args=["-smt2", "mimalloc-bench/bench/z3/test1.smt2"], lib_path=lib_path)
