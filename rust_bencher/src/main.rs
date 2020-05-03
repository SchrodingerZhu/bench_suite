#![feature(core_intrinsics)]
#![recursion_limit = "1024"]
#![feature(type_ascription)]
mod tremor;

use std::collections::BTreeSet;
use xactor::*;
use exec_time::*;
use rand::prelude::*;
use structopt::*;
use std::sync::Arc;
use crossbeam_skiplist::SkipSet;

#[cfg(feature = "bench_rpmalloc")]
#[global_allocator]
static GLOBAL: rpmalloc::RpMalloc = rpmalloc::RpMalloc;

#[cfg(any(feature = "bench_mimalloc", feature = "bench_smimalloc-secure"))]
#[global_allocator]
static GLOBAL: mimalloc::MiMalloc = mimalloc::MiMalloc;

#[cfg(feature = "bench_jemalloc")]
#[global_allocator]
static GLOBAL: jemallocator::Jemalloc = jemallocator::Jemalloc;

#[cfg(feature = "bench_weealloc")]
#[global_allocator]
static GLOBAL: wee_alloc::WeeAlloc = wee_alloc::WeeAlloc::INIT;

#[cfg(feature = "bench_tcmalloc")]
#[global_allocator]
static GLOBAL: tcmalloc::TCMalloc = tcmalloc::TCMalloc;

#[cfg(any(feature = "bench_snmalloc", feature = "bench_snmalloc-1mib"))]
#[global_allocator]
static GLOBAL: snmalloc_rs::SnMalloc = snmalloc_rs::SnMalloc;

#[cfg(feature = "bench_dlmalloc")]
#[global_allocator]
static GLOBAL: dlmalloc::GlobalDlmalloc = dlmalloc::GlobalDlmalloc;

const SEED: u64 = 0xffff_1145_14ab_cdef;

#[exec_time]
fn rayon(data: Vec<u128>, expand_size: usize) {
    use rayon::prelude::*;
    data.into_par_iter()
        .map(|x: u128| std::intrinsics::wrapping_add(x, x))
        .map(|x| {
            let mut temp = Vec::new();
            for _ in 0..expand_size {
                temp.push(x);
            }
            temp
        })
        .flatten()
        .filter(|x| x & 1 == 0)
        .collect::<Vec<_>>();
}

#[exec_time]
fn btree_container(rand: StdRng,
                   iteration: usize,
                   insertion: usize,
                   deletion: usize) {
    let mut set: BTreeSet<u128> = std::collections::BTreeSet::new();
    let mut rand = rand;
    for _ in 0..iteration {
        for _ in 0..insertion {
            set.insert(rand.gen());
        }
        for _ in 0..deletion {
            set.remove(&rand.gen());
        }
    }
}

#[exec_time]
fn thread_skiplist(thread: usize, insertion: usize, deletion: usize) {
    let set : Arc<SkipSet<usize>> = Arc::new(crossbeam_skiplist::SkipSet::new());
    let mut handle = Vec::new();
    for i in 0..thread {
        let set = set.clone();
        handle.push(std::thread::spawn(move || {
            let mut rng: StdRng = rand::SeedableRng::seed_from_u64(SEED ^ (i * i * i * i * i * i * i * i) as u64);
            for _ in 0..insertion {
                set.insert(rng.gen());
            }
            for _ in 0..deletion {
                set.remove(&rng.gen());
            }
            for _ in 0..insertion {
                set.insert(rng.gen());
            }
        }));
    }
    for i in handle {i.join().unwrap();}
}

const DATA: &[u8] = include_bytes!("gsoc-2018.json");

#[exec_time]
fn simdjson(iteration: usize) {
    for _ in 0..iteration {
        let mut data = DATA.to_vec();
        simd_json::to_borrowed_value(data.as_mut_slice()).unwrap();
    }
}

#[exec_time]
fn hash_brown(rand: StdRng, iteration: usize, insertion: usize, deletion: usize) {
    let mut set: hashbrown::HashSet<u128> = hashbrown::HashSet::new();
    let mut rand = rand;
    for _ in 0..iteration {
        for _ in 0..insertion {
            set.insert(rand.gen());
        }
        for _ in 0..deletion {
            set.remove(&rand.gen());
        }
    }
}
#[derive(StructOpt, Debug)]
enum Opt {
    #[structopt(about = "Benchmark rayon")]
    Rayon {
        #[structopt(short, long, help = "initial vector size", default_value = "200000")]
        base_size: usize,
        #[structopt(short, long, help = "extra allocate size in subtask", default_value = "1000")]
        expand_size: usize,
    },
    #[structopt(about = "Benchmark b-tree container")]
    BTree {
        #[structopt(short = "t", long, help = "iteration time", default_value = "20")]
        iteration: usize,
        #[structopt(short, long, help = "random insertion size", default_value = "500000")]
        insertion: usize,
        #[structopt(short, long, help = "random insertion size", default_value = "150000")]
        deletion: usize,
    },
    #[structopt(about = "Benchmark simdjson")]
    Simdjson {
        #[structopt(short = "t", long, help = "iteration time", default_value = "1000")]
        iteration: usize
    },
    #[structopt(about = "Benchmark hashbrown")]
    Hashbrown {
        #[structopt(short = "t", long, help = "iteration time", default_value = "30")]
        iteration: usize,
        #[structopt(short, long, help = "random insertion size", default_value = "1000000")]
        insertion: usize,
        #[structopt(short, long, help = "random insertion size", default_value = "150000")]
        deletion: usize,
    },
    #[structopt(about = "Benchmark threaded skiplist")]
    Skiplist {
        #[structopt(short = "t", long, help = "thread", default_value = "12")]
        thread: usize,
        #[structopt(short, long, help = "random insertion size", default_value = "200000")]
        insertion: usize,
        #[structopt(short, long, help = "random insertion size", default_value = "50000")]
        deletion: usize,
    },
    #[structopt(about = "Benchmark Xactor")]
    Xactor {
        #[structopt(short = "t", long, help = "iteration time", default_value = "500000")]
        iteration: usize
    },
    Tremor
}


#[message(result = "u128")]
struct Sum([u128; 64]);

struct MyActor;

impl Actor for MyActor {}

#[async_trait::async_trait]
impl Handler<Sum> for MyActor {
    async fn handle(&mut self, _ctx: &Context<Self>, msg: Sum) -> u128 {
        let mut res = 0;
        msg.0.iter().for_each(|x| res += x);
        res
    }
}

async fn test_actor(iteration: usize) -> Result<String> {
    let mut rng: StdRng = rand::SeedableRng::seed_from_u64(SEED);
    let a = std::time::SystemTime::now();
    for _ in 0..iteration {
        let mut addr = MyActor.start().await;
        let mut data = [0; 64];
        rng.fill(&mut data);
        addr.call(Sum(data)).await?;
    }
    let b = std::time::SystemTime::now();
    Ok(format!("actor {} millis", b.duration_since(a).unwrap().as_millis()))
}

#[async_std::main]
async fn main() -> Result<()> {
    let opt = Opt::from_args();
    match opt {
        Opt::Rayon { base_size, expand_size }
        => {
            let mut rng: StdRng = rand::SeedableRng::seed_from_u64(SEED);
            let mut data = Vec::new();
            for _ in 0..base_size {
                data.push(rng.gen());
            }
            rayon(data, expand_size)
        }
        Opt::BTree { iteration, insertion, deletion } => {
            let rng: StdRng = rand::SeedableRng::seed_from_u64(SEED);
            btree_container(rng, iteration, insertion, deletion)
        },
        Opt::Simdjson { iteration } => {
            simdjson(iteration)
        },
        Opt::Hashbrown { iteration, insertion, deletion } => {
            let rng: StdRng = rand::SeedableRng::seed_from_u64(SEED);
            hash_brown(rng, iteration, insertion, deletion)
        },
        Opt::Skiplist { thread, insertion, deletion }
        => {
            thread_skiplist(thread, insertion, deletion);
        }
        Opt::Xactor { iteration } => {
            let result = test_actor(iteration).await.unwrap();
            println!("{}", result);
        }
        Opt::Tremor => {
            std::env::set_var("TREMOR_PATH", std::fs::canonicalize(
                "../tremor-runtime/tremor-script/lib").unwrap());
            tremor::run_dun().await.unwrap();
        }
    };
    Ok(())
}

//--no-api -c $file bench/link.yaml --query ./bench/$1/*.trickle