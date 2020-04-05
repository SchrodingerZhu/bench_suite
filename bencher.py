import tempfile
import subprocess
import multiprocessing
import time
from typing import *

BARNES_TEMPLATE = """
327680
123

0.025
0.05
1.0
2.0
5.0
0.075
0.25
1
"""


class PreloadBencher:
    attribute_list = ("mem_peak", "time_elapsed", "page_fault")

    def __init__(self, exec, args=(), extra_env: Mapping[str, str] = None, stdin=None, lib_path=None,
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
        self.time_elapsed = None
        self.mem_peak = None
        self.cwd = cwd
        if self.lib_path:
            self.env["LD_PRELOAD"] = self.lib_path

    def __getitem__(self, item):
        return self.__dict__[item]

    def run(self):
        with tempfile.NamedTemporaryFile() as time_record:
            child = subprocess.run(["env", "time", "-f", "%R %e %M", "-o", time_record.name, self.exec, *self.args],
                                   cwd=self.cwd, env=self.env, stderr=subprocess.PIPE, stdin=self.stdin,
                                   stdout=subprocess.PIPE)
            with open(time_record.name) as file:
                res = file.readline().split()
                self.stdout = child.stdout.decode()
                self.stderr = child.stderr.decode()
                self.returncode = child.returncode
                self.page_fault = int(res[0])
                self.time_elapsed = float(res[1])
                self.mem_peak = int(res[2])


class CFrac(PreloadBencher):
    def __init__(self, lib_path=None):
        super().__init__("benchmark/cfrac", args=["17545186520507317056371138836327483792789528"], lib_path=lib_path)


class MallocLarge(PreloadBencher):
    def __init__(self, lib_path=None):
        super().__init__("benchmark/malloc-large", lib_path=lib_path)


class Z3(PreloadBencher):
    def __init__(self, lib_path=None):
        super().__init__("z3", args=["-smt2", "mimalloc-bench/bench/z3/test1.smt2"], lib_path=lib_path)


class Agda(PreloadBencher):
    def __init__(self, lib_path=None):
        super().__init__("agda", args=["./IO.agda"], lib_path=lib_path, cwd="agda-stdlib/src")


class RpTest(PreloadBencher):
    attribute_list = ("mem_peak", "time_elapsed", "page_fault", "thd", "op_per_sec")

    def __init__(self, lib_path=None, thd=None):
        self.op_per_sec = None
        if thd:
            self.thd = thd
        else:
            self.thd = multiprocessing.cpu_count()
        super().__init__("benchmark/rptest", args=[str(self.thd), "0", "2", "2", "500", "1000", "200", "8", "64000"],
                         lib_path=lib_path)

    def run(self):
        super().run()
        res = str(self.stdout.split()[-13])
        self.op_per_sec = int(res.strip('.'))


class MStress(PreloadBencher):
    attribute_list = ("mem_peak", "time_elapsed", "page_fault", "thd")

    def __init__(self, lib_path=None, thd=None):
        self.op_per_sec = None
        if thd:
            self.thd = thd
        else:
            self.thd = multiprocessing.cpu_count()
        super().__init__("benchmark/mstress", args=[str(self.thd), "100", "10"],
                         lib_path=lib_path)


class RbStress(PreloadBencher):
    attribute_list = ("mem_peak", "time_elapsed", "page_fault", "thd")

    def __init__(self, lib_path=None, thd=None):
        self.op_per_sec = None
        if thd:
            self.thd = thd
        else:
            self.thd = multiprocessing.cpu_count()
        super().__init__("ruby", args=["mimalloc-bench/bench/rbstress/stress_mem.rb", str(self.thd)],
                         lib_path=lib_path)

    def run(self):
        super().run()
        self.time_elapsed = float(self.stdout.split()[-1].strip())


class AllocTest(PreloadBencher):
    attribute_list = ("mem_peak", "time_elapsed", "page_fault", "thd")

    def __init__(self, lib_path=None, thd=None):
        if thd:
            self.thd = thd
        else:
            self.thd = multiprocessing.cpu_count()
        super().__init__("benchmark/alloc-test", args=[str(self.thd)], lib_path=lib_path)

    def run(self):
        super().run()
        self.time_elapsed = float(self.stdout.split()[-7].strip()) / 1000.0


class Larson(PreloadBencher):
    attribute_list = ("mem_peak", "time_elapsed", "page_fault", "thd", "op_per_sec")

    def __init__(self, lib_path=None, thd=None):
        self.op_per_sec = None
        if thd:
            self.thd = thd
        else:
            self.thd = multiprocessing.cpu_count()
        super().__init__("benchmark/larson", args=['2.5', '8', '256', '1000', '200', '42', str(self.thd)],
                         lib_path=lib_path)

    def run(self):
        super().run()
        self.op_per_sec = int(self.stdout.split()[2])


class XmallocTest(PreloadBencher):
    attribute_list = ("mem_peak", "time_elapsed", "page_fault", "thd", "op_per_sec", "rtime")

    def __init__(self, lib_path=None, thd=None):
        self.op_per_sec = None
        self.rtime = None
        if thd:
            self.thd = thd
        else:
            self.thd = multiprocessing.cpu_count()
        super().__init__("benchmark/xmalloc-test", args=["-w", str(self.thd), "-s", "-1", "-t", "20"],
                         lib_path=lib_path)

    def run(self):
        super().run()
        output = self.stdout.split()
        self.rtime = float(output[1].strip(','))
        self.op_per_sec = float(output[-2])


class Barnes(PreloadBencher):
    def __init__(self, lib_path=None):
        self.__temp = None
        self.__temp = tempfile.NamedTemporaryFile()
        with open(self.__temp.name, "w") as file:
            file.write(BARNES_TEMPLATE)
        super().__init__("benchmark/barnes", stdin=open(self.__temp.name), lib_path=lib_path)


class Redis(PreloadBencher):
    attribute_list = ("mem_peak", "page_fault", "op_per_sec")

    def __init__(self, lib_path=None):
        self.op_per_sec = None
        super().__init__("redis-benchmark",
                         args=["-r", "1000000", "-n", "1000000", "-P", "8", "-q", "lpush", "a", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "lrange", "a", "1", "10"], lib_path=lib_path)

    def run(self):
        with tempfile.NamedTemporaryFile() as time_record:
            with subprocess.Popen(["env", "time", "-f", "%R %e %M", "-o", time_record.name, "redis-server", "--save", "", "--appendonly", "no"],
                                  env=self.env, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as server:
                try:
                    time.sleep(1)
                    super().run()
                    time.sleep(1)
                    subprocess.run(["redis-cli", "shutdown"])
                    time.sleep(0.5)
                    with open(time_record.name) as file:
                        res = file.readline().split()
                        self.page_fault = int(res[0])
                        self.time_elapsed = float(res[1])
                        self.mem_peak = int(res[2])
                        self.op_per_sec = float(self.stdout.split()[-4])
                except Exception as e:
                    server.kill()
                    print(server.stdout.read().decode())
                    print(server.stderr.read().decode())
                    time.sleep(1)
                    raise e



class Espresso(PreloadBencher):
    def __init__(self, lib_path=None):
        super().__init__("benchmark/espresso", args=["mimalloc-bench/bench/espresso/largest.espresso"],
                         lib_path=lib_path)


class Sh6Bench(PreloadBencher):
    attribute_list = ("mem_peak", "time_elapsed", "page_fault", "thd")

    def __init__(self, lib_path=None, thd=None):
        if thd:
            self.thd = thd
        else:
            self.thd = multiprocessing.cpu_count()
        super().__init__("benchmark/sh6bench", args=[str(self.thd)], lib_path=lib_path)


class Sh8Bench(PreloadBencher):
    attribute_list = ("mem_peak", "time_elapsed", "page_fault", "thd")

    def __init__(self, lib_path=None, thd=None):
        if thd:
            self.thd = thd
        else:
            self.thd = multiprocessing.cpu_count()
        super().__init__("benchmark/sh8bench", args=[str(self.thd)], lib_path=lib_path)


class CacheThrash(PreloadBencher):
    attribute_list = ("mem_peak", "time_elapsed", "page_fault", "thd")

    def __init__(self, lib_path=None, thd=None):
        if thd:
            self.thd = thd
        else:
            self.thd = multiprocessing.cpu_count()
        super().__init__("benchmark/cache-thrash", args=[str(self.thd), '5000', '1', '2000000', str(self.thd)],
                         lib_path=lib_path)


class CacheScratch(PreloadBencher):
    attribute_list = ("mem_peak", "time_elapsed", "page_fault", "thd")

    def __init__(self, lib_path=None, thd=None):
        if thd:
            self.thd = thd
        else:
            self.thd = multiprocessing.cpu_count()
        super().__init__("benchmark/cache-scratch", args=[str(self.thd), '5000', '1', '2000000', str(self.thd)],
                         lib_path=lib_path)


class Ebizzy(PreloadBencher):
    attribute_list = ("mem_peak", "page_fault", "thd", "op_per_sec")

    def __init__(self, lib_path=None, thd=None):
        self.op_per_sec = None
        if thd:
            self.thd = thd
        else:
            self.thd = multiprocessing.cpu_count()
        super().__init__("ltp/utils/benchmark/ebizzy-0.3/ebizzy",
                         args=["-t", str(self.thd), "-M", "-S", "5", "-s", "128"],
                         lib_path=lib_path)

    def run(self):
        super().run()
        output = self.stdout.split()
        self.op_per_sec = int(output[0])


bencher_list = {
    "c_frac": CFrac,
    "malloc_large": MallocLarge,
    "z3": Z3,
    "agda": RpTest,
    "mstress": MStress,
    "rbstress": RbStress,
    "alloc_test": AllocTest,
    "alloc_larson": Larson,
    "xmalloc_test": XmallocTest,
    "barnes": Barnes,
    "redis": Redis,
    "espresso": Espresso,
    "sh6bench": Sh6Bench,
    "sh8bench": Sh8Bench,
    "cache_scratch": CacheScratch,
    "cache_trash": CacheThrash,
    "ebizzy": Ebizzy
}
