import multiprocessing
import subprocess
import shutil
import os
from typing import *


class CMAKEBuilder:
    """
    A base class for cmake project
    """

    def __init__(self, name: str, workdir: str, target: str, lib: str, options: Iterable = ("-DCMAKE_BUILD_TYPE=Release",),
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
    def __init__(self):
        pass
    def prepare(self):
        pass
    def build(self):
        pass


builder_list = {
    "snmalloc": CMAKEBuilder("snmalloc", "snmalloc", "snmallocshim", "libsnmallocshim.so"),
    "snmalloc-1mib": CMAKEBuilder("snmalloc-1mib", "snmalloc", "snmallocshim-1mib", "libsnmallocshim-1mib.so"),
    "mimalloc": CMAKEBuilder("mimalloc", "mimalloc", "mimalloc", "libmimalloc.so"),
    "mimalloc-secure": CMAKEBuilder("mimalloc-secure", "mimalloc", "mimalloc", "libmimalloc-secure.so",options=("-DCMAKE_BUILD_TYPE=Release","-DMI_SECURE=4")),
}
