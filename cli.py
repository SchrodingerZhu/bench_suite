import fire
import auto_bench
import bencher
import builder
import bench_suite
import json

class MallocBench:
    """Memory allocator benchmark suite"""

    def clean_bench_suite(self):
        bench_suite.clean()

    def compile_bench_suite(self):
        bench_suite.compile()

    def compile_allocator(self, name: str):
        print(builder.builder_list[name].build())

    def clean_allocator(self, name: str):
        builder.builder_list[name].clean()

    def clean_allocators(self, name: str):
        for i in builder.builder_list.values():
            i.clean()

    def compile_allocators(self):
        builder.build_all()

    def list_allocators(self):
        for i in builder.builder_list.keys():
            print(i)

    def list_benches(self):
        for i in bencher.bencher_list.keys():
            print(i)

    def run(self, allocator_name: str, bencher_name: str, time: int = 1, ave=True):
        res = auto_bench.auto_run_single(bencher.bencher_list[bencher_name], builder.builder_list[allocator_name], time, ave)
        print(json.dumps(res))

    def run_bencher(self, name: str, time: int=1, ave=True):
        res = auto_bench.auto_run_bencher(bencher.bencher_list[name], time, ave)
        print(json.dumps(res))

    def run_allocator(self, name: str, time: int = 1, ave=True):
        res = auto_bench.auto_run_builder(builder.builder_list[name], time, ave)
        print(json.dumps(res))


if __name__ == '__main__':
    fire.Fire(MallocBench)
