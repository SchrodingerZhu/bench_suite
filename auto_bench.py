import builder
import collections
import bencher


def auto_run_single(bencher, builder, time=5, ave=True):
    runner = bencher(builder.library())
    result = collections.defaultdict(list)
    try:
        for i in range(time):
            print("-- round #{}".format(i))
            runner.run()
            for i in bencher.attribute_list:
                result[i].append(runner[i])
        if ave:
            for i in bencher.attribute_list:
                result[i] = sum(result[i]) / time
        return result
    except Exception as e:
        print("Error during execution", e)
        print("STDERR", runner.stderr)
        print("CODE", runner.returncode)
        return None


def auto_run_bencher(bencher, time=5, ave=True):
    res = dict()
    for b in builder.builder_list.values():
        print("running", bencher.__name__, "with", b.name)
        single = auto_run_single(bencher, b, time, ave)
        res[b.name] = single
    return res


def auto_run_builder(builder, time=5, ave=True):
    res = dict()
    for b in bencher.bencher_list.values():
        print("running", b.__name__, "with", builder.name)
        single = auto_run_single(b, builder, time, ave)
        res[b.__name__] = single
    return res


def run_all(time=5, ave=True):
    res = dict()
    for b in bencher.bencher_list.values():
        single = auto_run_bencher(b, time, ave)
        res[b.__name__] = single
    return res


