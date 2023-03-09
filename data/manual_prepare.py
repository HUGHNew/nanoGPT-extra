"""
folder structure:
- target_dir (make the files type the same)
    - tarball_0
    - tarball_1
- bins (intermediate files)
- val.man.bin (expected output)
- train.man.bin (expected output)
- tr.list
procedure:
1. get all tarballs
1.5. ignore if target file exists
2. get tarball members and process each one in work process
3. write tokenized data into train.$pid.bin or val.$pid.bin
4. combine all .bins
"""
from __future__ import annotations
from typing import Iterable, Literal
import os, shutil, tarfile, logging
import numpy as np
from concurrent.futures import ProcessPoolExecutor, Future
import tiktoken

logFile = "../logs/man_prepare.log"
# logFile = "logs/man_prepare.log"
logging.basicConfig(filename=logFile, level=logging.INFO,
                    format="[%(asctime)s] %(levelname)s %(message)s", encoding="utf-8")
encoder = tiktoken.get_encoding("gpt2")
dtype = np.uint16
eol_token = encoder.encode_ordinary("\n")[0]
# eol_token = 198
HARD_LIMIT = 20 * 1024 * 1024 * 1024 # 20G memory only for files

def _process_bytes_to_binary(content:list[bytes])->list[int]:
    result:list[int] = []
    for text in content:
        for line in text.decode().split('\n'):
            if line.isspace(): continue
            result.extend(encoder.encode_ordinary(line))
            result.append(eol_token)
        result.extend([encoder.eot_token, encoder.eot_token])
    return result

def _extract_files_from_tarball(tarfile:tarfile.TarFile, members:list[tarfile.TarInfo])->list[bytes]:
    result = []
    for mem in members:
        exf = tarfile.extractfile(mem)
        if not exf: continue
        result.append(exf.read())
        exf.close()
    return result

def process_tar_members(tar_name:str, mems: list[bytes], prefix:Literal["train", "val"], root:str)->tuple[str,str]:
    filename = f"{prefix}.{tar_name.replace('.', '_')}.bin"
    encodings = _process_bytes_to_binary(mems)
    shape_len = len(encodings)
    logging.info(f"create memmap file:{root}/{filename}")
    binary = np.memmap(f"bins/{filename}", dtype=dtype, mode="w+", shape=(shape_len,))
    binary[0 : shape_len] = encodings
    binary.flush()
    logging.info(f"write {tar_name}'s content into {filename}")
    return filename, tar_name


def process_tars(worker_count:int, tarballs:Iterable[str], root:str, test_rate:float=0.0005):
    pool = ProcessPoolExecutor(max_workers=worker_count)
    logging.info(f"launching with max_worker:{worker_count}")
    if not os.path.exists("bins"): os.mkdir("bins")
    current_usage = [0]
    train_set:set[Future[tuple[str,str]]] = set()
    for tarball in tarballs:
        tar_path = f"{root}/{tarball}"

        # memory limit by hand
        current_usage[0] += os.stat(tar_path).st_size
        while current_usage[0] >= HARD_LIMIT:
            for train_future in train_set:
                _, name = train_future.result() # wait for usage release
                # else train_future.res
                train_set.remove(train_future)
                current_usage[0] -= os.stat(f"{root}/{name}").st_size
                break

        logging.info(f"processing tarball:{tar_path}")
        with tarfile.open(tar_path) as tf:
            train_mem = tf.getmembers()
            mem_count = len(train_mem)
            test_count = round(mem_count * test_rate)
            if test_count != 0:
                train_count = mem_count-test_count
                test_mem = train_mem[train_count:]
                train_mem[:] = train_mem[:train_count]
                test_idx:list[bytes] = _extract_files_from_tarball(tf, test_mem) # bytes text
                logging.info(f"submit {tar_path}.val")
                # process_tar_members(tarball, test_idx, "val", root)
                pool.submit(process_tar_members, tarball, test_idx, "val", root)
            
            train_idx:list[bytes] = _extract_files_from_tarball(tf, train_mem)
            logging.info(f"submit {tar_path}.train")
            # process_tar_members(tarball, train_idx, "train", root)

            # collect train future for usage record
            nf = pool.submit(process_tar_members, tarball, train_idx, "train", root)
            # def __train_future_callback(names:Future[tuple[str,str]]) -> object:
            #     current_usage[0] -= os.stat(names.result()[1]).st_size
            #     train_set.remove(names)
            # nf.add_done_callback(__train_future_callback)
            train_set.add(nf)
    pool.shutdown()
    logging.info("finish extracting tarballs")

def _combine_binaries_group(target:str, addons:dict[str, int], root:str, clean:bool=True):
    with open(f"{root}/{target}", "ab") as tgt:
        for addon in addons.keys():
            logging.info(f"appending {addon} to {target}")
            adfile = f"{root}/{addon}"
            with open(adfile,"rb") as ad:
                tgt.write(ad.read())
            if clean:
                os.remove(adfile)

def combine_binaries(path:str="bins"):
    files = os.listdir(path)
    train_bins, val_bins = {}, {}
    max_train, max_val = "", ""
    for file in files:
        file_size = os.stat(f"{path}/{file}").st_size
        if file.startswith("train"):
            if not max_train or train_bins[max_train] < file_size:
                max_train = file
            train_bins[file] = file_size
        else:
            if not max_val or val_bins[max_val] < file_size:
                max_val = file
            val_bins[file] = file_size
    pool = ProcessPoolExecutor(max_workers=2)
    logging.info(f"the larggest train file: {max_train} with size:{train_bins[max_train]}")
    train_target = f"{path}/train.man.bin"
    shutil.move(f"{path}/{max_train}", train_target)
    del train_bins[max_train]
    pool.submit(_combine_binaries_group, train_target, train_bins, path)
    logging.info(f"the larggest val file: {max_val} with size:{val_bins[max_val]}")

    val_target = f"{path}/val.man.bin"
    shutil.move(f"{path}/{max_val}", val_target)
    del val_bins[max_val]
    pool.submit(_combine_binaries_group, val_target, val_bins, path)
    pool.shutdown()
    logging.info(f"concatenate all binary to {train_target} and {val_target}")

def check_log(log_file:str, tarballs:set[str], remove_imcomplete:str|None=None) -> set[str]:
    with open(log_file) as man:
        logs = [
            line
            for line in man.readlines()
            if "create" in line or "write" in line
        ]

    creation = set([
        line.split('/')[-1].strip()
        for line in logs
        if "create" in line
    ])

    submission = set([
        line.split(' ')[-1].strip()
        for line in logs
        if "write" in line
    ])

    incomplete = creation - submission
    logging.info(f"incomplete files: {incomplete}")
    if remove_imcomplete:
        for f in incomplete:
            file = f"{remove_imcomplete}/{f}"
            if os.path.exists(file):
                os.remove(file)
        logging.info(f"incomplete files are removed")
    lst_tbs = list(tarballs)
    for file in lst_tbs:
        if f"train.{file.replace('.', '_')}.bin" in submission:
            tarballs.remove(file)
    return tarballs

def main(source:str, worker_count:int, test_rate:float=0.0005, pure_text:bool=False)->bool:
    """
    :source: src dir to process
    """
    if not (os.path.exists(source) and os.path.isdir(source)):
        logging.error(f"{source=} is not a folder")
        return True # no need for call this again
    if pure_text:
        # TODO: process_files
        raise RuntimeError("")
    else:
        raw_tarballs = set(os.listdir(source))
        tarballs = check_log(logFile, raw_tarballs.copy())
        logging.info(f"ignore completed files: {raw_tarballs - tarballs}")
        if len(tarballs) == 0: return True
        logging.info(f"tarballs: {tarballs}")
        process_tars(worker_count, tarballs, source, test_rate)
    return True

def self_host():
    finish = False
    times = 0
    while not finish:
        try:
            finish = main("newbio", 16)
            combine_binaries()
        except Exception as e:
            if finish:
                logging.error("convert to binary successfully but error occurs when concatenate binary files")
            else:
                finish = False
                times += 1
                logging.error(f"run with error {e}. Restart the task {times=}")


if __name__=="__main__":
    # main("newbio", 3)
    # combine_binaries()
    self_host()