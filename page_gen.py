import subprocess
import bencher

MATRIX_TEMPLATE = """
Title: Infomation Matrix

# Infomation Matrix
- CPU
  - Number: `{}`
  - Model: `{}`
- OS
  - Kernel: `{}`
  - Version: `{}`
- Redis
  - Version: `{}`
  - Args: `["--save", "", "--appendonly", "no"]`
- Agda
  - Version: `{}`
- Ruby
  - Version: `{}`
- Z3
  - Version: `{}`
- Allocators:
{}
"""
ALLOCATOR_TEMPLATE = """
  - {}
    - Version: `{}`
    - Size: `{}`
"""


def get_cpu_info():
    import re
    command = "cat /proc/cpuinfo"
    all_info = subprocess.check_output(command, shell=True).strip()
    for line in all_info.split(b"\n"):
        if b"model name" in line:
            return re.sub(".*model name.*:", "", line.decode(), 1).strip()


def gen_allocators():
    import builder
    res = []
    for i in builder.builder_list.values():
        res.append(ALLOCATOR_TEMPLATE.format(i.name, i.version(), i.size()))
    return "".join(res)


def ruby_version():
    return subprocess.run(["ruby", "--version"], capture_output=True).stdout.decode().strip()


def agda_version():
    return subprocess.run(["agda", "--version"], capture_output=True).stdout.decode().strip()


def z3_version():
    return subprocess.run(["z3", "--version"], capture_output=True).stdout.decode().strip()


def redis_version():
    return subprocess.run(["redis-server", "--version"], capture_output=True).stdout.decode().strip()


def gen_matrix():
    import platform, multiprocessing
    uname = platform.uname()
    return MATRIX_TEMPLATE.format(
        multiprocessing.cpu_count(),
        get_cpu_info(),
        uname.release,
        uname.version,
        redis_version(),
        agda_version(),
        ruby_version(),
        z3_version(),
        gen_allocators()
    )


PICTURE_TEMPLATE = "![{}-{}]({}-{}.png)\n\n"
CONTENT_ITEM = "- [{}]({}.md)\n"
CONTENTS = """
Title: contents

# Contents
- [Information Matrix](matrix.md)
{}
"""


def gen_index():
    res = []
    for i in bencher.bencher_list.values():
        if i.rust:
            name = "(**RUST**)" + i.__name__
        else:
            name = i.__name__
        res.append(CONTENT_ITEM.format(name, i.__name__))
    return CONTENTS.format("".join(res))


PAGE_TEMPLATE = """
Title: {} Benchmark

# {}
{}
"""


def gen_page(b):
    res = []
    for i in b.attribute_list:
        res.append(
            PICTURE_TEMPLATE.format(b.__name__, i, b.__name__, i)
        )
    return PAGE_TEMPLATE.format(b.__name__, b.__name__, "".join(res))


def gen_pages():
    with open("output/index.md", "w+") as index:
        index.write(gen_index())
    with open("output/matrix.md", "w+") as matrix:
        matrix.write(gen_matrix())
    for i in bencher.bencher_list.values():
        with open("output/{}.md".format(i.__name__), "w+") as page:
            page.write(gen_page(i))
