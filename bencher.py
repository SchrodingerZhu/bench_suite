import tempfile
import subprocess
from typing import *


class PreloadBencher:
    def __init__(self, exec, args=(), extra_env: Mapping[str, str] = None, stdin: Optional[bytes] = None, lib_path=None,
                 cwd=None):
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
        self.returncode = None
        self.page_fault = None
        self.time_escape = None
        self.mem_peak = None
        self.cwd = cwd
        if self.lib_path:
            self.env["LD_PRELOAD"] = self.lib_path

    def run(self):
        with tempfile.NamedTemporaryFile() as time_record:
            child = subprocess.run(["env", "time", "-f", "%R %e %M", "-o", time_record.name, self.exec, *self.args],
                                   cwd=self.cwd, env=self.env, stderr=subprocess.PIPE, stdin=self.stdin,
                                   stdout=subprocess.PIPE)
            with open(time_record.name) as file:
                res = file.readline().split()
                self.stdout = str(child.stdout)
                self.stderr = str(child.stderr)
                self.returncode = child.returncode
                self.page_fault = int(res[0])
                self.time_escape = float(res[1])
                self.mem_peak = int(res[2])


class CFrac(PreloadBencher):
    def __init__(self, lib_path=None):
        super().__init__("benchmark/cfrac", args=["17545186520507317056371138836327483792789528"], lib_path=lib_path)


class AllocTest(PreloadBencher):
    def __init__(self, lib_path=None, size=16):
        self.size = size
        super().__init__("benchmark/alloc-test", args=[str(size)], lib_path=lib_path)


class Z3(PreloadBencher):
    def __init__(self, lib_path=None):
        super().__init__("z3", args=["-smt2", "mimalloc-bench/bench/z3/test1.smt2"], lib_path=lib_path)


class Agda(PreloadBencher):
    def __init__(self, lib_path=None):
        super().__init__("agda", args=["./IO.agda"], lib_path=lib_path, cwd="agda-stdlib/src")


class RpTest(PreloadBencher):
    def __init__(self, lib_path=None):
        self.op_per_sec = None
        super().__init__("benchmark/rptest", args=["12", "0", "2", "2", "500", "1000", "200", "8", "64000"],
                         lib_path=lib_path)

    def run(self):
        super().run()
        res = str(self.stdout.split()[-13])
        self.op_per_sec = int(res.strip('.'))


class Redis(PreloadBencher):
    def __init__(self, lib_path=None):
        self.req_per_sec = None
        super().__init__("redis-benchmark",
                         args=["-r", "1000000", "-n", "1000000", "-P", "8", "-q", "lpush", "a", "1", "2", "3", "4", "5",
                               "6", "7", "8", "9", "10", "lrange", "a", "1", "10"], lib_path=lib_path)

    def run(self):
        with tempfile.NamedTemporaryFile() as time_record:
            subprocess.Popen(["env", "time", "-f", "%R %e %M", "-o", time_record.name, "redis-server"],
                                      env=self.env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            super().run()
            subprocess.run(["redis-cli", "shutdown"])
            with open(time_record.name) as file:
                res = file.readline().split()
                self.page_fault = int(res[0])
                self.time_escape = float(res[1])
                self.mem_peak = int(res[2])
                self.req_per_sec = float(self.stdout.split()[-4])
