import multiprocessing
import subprocess
import shutil
import os
import types
from typing import *


class CMAKEBuilder:
    """
    A base class for cmake project
    """

    def __init__(self, name: str, workdir: str, target: str, lib: str,
                 options: Iterable = ("-DCMAKE_BUILD_TYPE=Release",),
                 parallel: Optional[int] = None, generator: Optional[str] = None):
        if not parallel:
            self.parallel = multiprocessing.cpu_count()
        else:
            self.parallel = parallel
        self.workdir = os.path.abspath(workdir)
        self.options = list(options)
        if generator:
            self.options.append("-G")
            self.options.append(generator)
        self.target = target
        self.lib = lib
        self.name = name

    def clean(self):
        shutil.rmtree(self.workdir + "/bench_build_" + self.name, ignore_errors=True)

    def build(self) -> str:
        path = self.workdir + "/bench_build_" + self.name
        os.mkdir(path)
        if subprocess.run(["cmake", "..", *self.options], cwd=path).returncode != 0:
            self.clean()
        if subprocess.run(["cmake", "--build", ".", "--target", self.target, "--parallel", str(self.parallel)],
                          cwd=path).returncode != 0:
            self.clean()
        return os.path.abspath(path + "/" + self.lib)


class MAKEBuilder:
    def __init__(self, name: str, workdir: str, lib: str, target: Optional[str]=None, options: Iterable = (), parallel: Optional[int] = None, prepare=None):
        if not parallel:
            self.parallel = multiprocessing.cpu_count()
        else:
            self.parallel = parallel
        if prepare:
            self.prepare = types.MethodType(prepare, self)
        else:
            self.prepare = None
        self.workdir = os.path.abspath(workdir)
        self.name = name
        self.lib = lib
        if target:
            self.build_cmd = ["make", target]
        else:
            self.build_cmd = ["make"]
        self.options = list(options)

    def clean(self):
        subprocess.run(["git", "clean", "-fdx"], cwd=self.workdir)

    def build(self) -> str:
        if self.prepare:
            self.prepare()
        subprocess.run([*self.build_cmd, "-j", str(self.parallel), *self.options], cwd=self.workdir)
        return os.path.abspath(self.workdir + "/" + self.lib)

def __tcmalloc_prepare(self):
    subprocess.run(["sh", "autogen.sh"], cwd=self.workdir)
    subprocess.run(["sh", "configure", "--enable-minimal"], cwd=self.workdir)



builder_list = {
    "snmalloc": CMAKEBuilder("snmalloc", "snmalloc", "snmallocshim", "libsnmallocshim.so"),
    "snmalloc-1mib": CMAKEBuilder("snmalloc-1mib", "snmalloc", "snmallocshim-1mib", "libsnmallocshim-1mib.so"),
    "mimalloc": CMAKEBuilder("mimalloc", "mimalloc", "mimalloc", "libmimalloc.so"),
    "mimalloc-secure": CMAKEBuilder("mimalloc-secure", "mimalloc", "mimalloc", "libmimalloc-secure.so",
                                    options=("-DCMAKE_BUILD_TYPE=Release", "-DMI_SECURE=4")),
    "tcmalloc": MAKEBuilder("tcmalloc", "gperftools", ".libs/libtcmalloc_minimal.so", prepare=__tcmalloc_prepare),
    "tbb": MAKEBuilder("intel-tbb", "tbb", )
}
