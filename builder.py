import multiprocessing
import subprocess
import shutil
import os
import types
import platform
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
        try:
            os.mkdir(path)
            if subprocess.run(["cmake", "..", *self.options], cwd=path).returncode != 0:
                self.clean()
            if subprocess.run(["cmake", "--build", ".", "--target", self.target, "--parallel", str(self.parallel)],
                              cwd=path).returncode != 0:
                self.clean()
        except FileExistsError:
            print("build existed for", self.name)
        return os.path.abspath(path + "/" + self.lib)

    def library(self):
        path = self.workdir + "/bench_build_" + self.name
        return os.path.abspath(path + "/" + self.lib)

    def size(self):
        return os.path.getsize(self.library())

    def version(self):
        return subprocess.run(["git", "log", "-1", "--oneline"], cwd=self.workdir, capture_output=True).stdout.decode().split()[
            0]


class SystemLibc:
    def __init__(self):
        self.name = "system"

    def clean(self):
        pass

    def library(self):
        return "/lib64/libc.so.6"
    
    def build(self):
        pass
    
    def size(self):
        return os.path.getsize(self.library())

    def version(self):
        return subprocess.run(["/lib64/libc.so.6", "--version"], capture_output=True).stdout.decode().split('\n')[0]


class GeneralBuilder:
    def __init__(self, name: str, workdir: str, lib: str, target: Optional[Union[str, List[str]]] = None,
                 options: Iterable = (), parallel: Optional[int] = None, prepare=None, generator="make"):
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
        if isinstance(target, list):
            self.build_cmd = [generator, *target]
        elif target:
            self.build_cmd = [generator, target]
        else:
            self.build_cmd = [generator]
        self.options = list(options)

    def clean(self):
        subprocess.run(["git", "reset", "--hard"], cwd=self.workdir)
        subprocess.run(["git", "clean", "-fdx"], cwd=self.workdir)

    def version(self):
        return subprocess.run(["git", "log", "-1", "--oneline"], cwd=self.workdir, capture_output=True).stdout.decode().split()[
            0]

    def build(self) -> str:
        if self.prepare:
            self.prepare()
        subprocess.run([*self.build_cmd, "-j", str(self.parallel), *self.options], cwd=self.workdir)
        return os.path.abspath(self.workdir + "/" + self.lib)

    def size(self):
        return os.path.getsize(self.library())

    def library(self) -> str:
        return os.path.abspath(self.workdir + "/" + self.lib)


def __tcmalloc_prepare(self):
    subprocess.run(["sh", "autogen.sh"], cwd=self.workdir)
    subprocess.run(["sh", "configure", "--enable-minimal"], cwd=self.workdir)


def __jemalloc_prepare(self):
    subprocess.run(["sh", "autogen.sh"], cwd=self.workdir)


def __rpmalloc_prepare(self):
    subprocess.run(["python", "configure.py"], cwd=self.workdir)


def __scalloc_prepare(self):
    subprocess.run(["gyp", "--depth=.", "scalloc.gyp"], cwd=self.workdir)


def __super_prepare(self):
    subprocess.run(["sed", "-i", "s/-Werror//", "Makefile.include"], cwd=self.workdir + "/..")


builder_list = {
    "snmalloc": CMAKEBuilder("snmalloc", "snmalloc", "snmallocshim", "libsnmallocshim.so"),
    "snmalloc-1mib": CMAKEBuilder("snmalloc-1mib", "snmalloc", "snmallocshim-1mib", "libsnmallocshim-1mib.so"),
    "mimalloc": CMAKEBuilder("mimalloc", "mimalloc", "mimalloc", "libmimalloc.so"),
    "mimalloc-secure": CMAKEBuilder("mimalloc-secure", "mimalloc", "mimalloc", "libmimalloc-secure.so",
                                    options=("-DCMAKE_BUILD_TYPE=Release", "-DMI_SECURE=4")),
    "tcmalloc": GeneralBuilder("tcmalloc", "gperftools", ".libs/libtcmalloc_minimal.so", prepare=__tcmalloc_prepare),
    "tbb": GeneralBuilder("intel-tbb", "tbb", "build/bench_release/libtbbmalloc.so.2", "tbbmalloc",
                          options=["-e", "tbb_build_prefix=bench"]),
    "hoard": GeneralBuilder("hoard", "Hoard/src", "libhoard.so"),
    "jemalloc": GeneralBuilder("jemalloc", "jemalloc", "lib/libjemalloc.so", prepare=__jemalloc_prepare),
    "rpmalloc": GeneralBuilder("rpmalloc", "rpmalloc",
                               "bin/" + platform.system().lower() + '/release/'
                               + platform.machine().replace('_', '-') + '/librpmallocwrap.so',
                               generator='ninja', prepare=__rpmalloc_prepare),
    # "scalloc": GeneralBuilder("scalloc", "scalloc", "out/Release/lib.target/libscalloc.so", prepare=__scalloc_prepare,
    #                          options=["-e", "BUILDTYPE=Release", "CC=clang", "CXX=clang++"]),
    # emmm, this will make some tests run into segment fault even with the required flags; What's more, setting the flag will make other allocator fail
    "mesh": GeneralBuilder("mesh", "mesh", "bazel-bin/src/libmesh.so", target=["build", "lib"]),
    "super": GeneralBuilder("super_malloc", "SuperMalloc/release", "lib/libsupermalloc.so", prepare=__super_prepare),
    "hardened": GeneralBuilder("hardened_malloc", "hardened_malloc", "libhardened_malloc.so",
                               target="libhardened_malloc.so"),
    "system": SystemLibc()
}


def build_all() -> List[Tuple[str, str, str]]:
    return [(i.name, i.version(), i.build()) for i in builder_list.values()]
