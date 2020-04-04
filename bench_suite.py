import os
import subprocess
import shutil
import multiprocessing
def clean():
    path = os.path.abspath(".")
    shutil.rmtree("benchmark", ignore_errors=True)
    os.chdir("mimalloc-bench/bench/shbench")
    subprocess.run(["git", "clean", "-fdx"])
    subprocess.run(["git", "reset", "--hard"])
    os.chdir(path)

def compile():
    os.mkdir("benchmark")
    path = os.path.abspath("benchmark")
    cmake = os.path.abspath("mimalloc-bench/bench")
    os.chdir("mimalloc-bench/bench/shbench")
    subprocess.run(["wget", "-N", "http://www.microquill.com/smartheap/shbench/bench.zip"])
    subprocess.run(["wget", "-N", "http://www.microquill.com/smartheap/SH8BENCH.zip"])
    subprocess.run(["unzip", "-o", "bench.zip"])
    subprocess.run(["unzip", "-o", "SH8BENCH.zip"])
    for i in ["sh6bench.patch", "sh6bench.c", "sh8bench.patch", "SH8BENCH.C"]:
        subprocess.run(["dos2unix", i])
    subprocess.run((["patch","-p1", "-o", "sh6bench-new.c", "sh6bench.c", "sh6bench.patch"]))
    subprocess.run((["patch", "-p1", "-o", "sh8bench-new.c", "SH8BENCH.C", "sh8bench.patch"]))
    os.chdir(path)
    subprocess.run(["cmake", cmake, "-DCMAKE_BUILD_TYPE=Release"])
    subprocess.run(["cmake", "--build", ".", "--parallel", str(multiprocessing.cpu_count())])


