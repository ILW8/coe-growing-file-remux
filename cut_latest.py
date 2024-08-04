import os
import subprocess
import datetime
import concurrent.futures
import io

from tqdm import tqdm


# PREFIXES = ["tournament gameplay_", "audience cam_", "main cam_", "wireless cam_"]
PREFIXES = ["main cam_"]
REC_PATH = r"S:/"
STAGE_PATH = r"P:/coe replays and highlights/staging"
COPY_CHUNK_SIZE = 128 * 1024
OUT_PATH = r"P:/coe replays and highlights/"

FFMPEG_CMD_TEMPLATE = ["ffmpeg", "-sseof", "-300", "-i", None, "-t", "300", "-c", "copy", None]


def make_growing_local_copy(remote_fname_relative: str):
    """
    takes filename (no path) and tries to grow local copy to the same size
    """
    print(f"checking {remote_fname_relative}")

    local_file_size = None
    # check local file exists
    if os.path.isfile(stage_path := os.path.join(STAGE_PATH, remote_fname_relative)):
        with open(stage_path, "rb") as f:
            f.seek(0, io.SEEK_END)
            local_file_size = f.tell()

    with open(staging_file := os.path.join(REC_PATH, remote_fname_relative), "rb") as source_file:
        source_file.seek(0, io.SEEK_END)
        fsize = source_file.tell()
        if local_file_size is not None and local_file_size >= fsize:
            print("source file is same size or larger than statging file, skipping sync")
            return
        
        source_file.seek(local_file_size if local_file_size is not None else 0, io.SEEK_SET)
        with open(stage_path, "ab") as dest_fh:
            # dest_fh.seek(local_file_size, io.SEEK_SET)
            # os.sendfile()

            pbar = tqdm(unit="B", unit_divisor=1024, unit_scale=True)
            while True:
                data = source_file.read(COPY_CHUNK_SIZE)
                if not data:
                    break
                pbar.update(len(data))
                dest_fh.write(data)
    return staging_file


def process_one_source(source_fname: str, prefix: str, destination_fname: str):
    staged_file = make_growing_local_copy(source_fname)
    
    if staged_file is None:
        print(f"oops, staged file is None for input {source_fname}")
        return False, destination_fname

    cmd = FFMPEG_CMD_TEMPLATE.copy()

    cmd[4] = os.path.join(REC_PATH, staged_file)
    cmd[7+2] = os.path.join(OUT_PATH, destination_fname)

    run_proc(cmd)

    return True, destination_fname
    


def main():
    dir_files: list[str] = sorted(os.listdir(REC_PATH), reverse=True)
    task_queue = []
    batch_datetime: str = datetime.datetime.now().isoformat().replace(":", ".")

    test_queue = []

    for prefix in PREFIXES:
        print(prefix)
        found_file = None

        matches = [f for f in dir_files if f.startswith(prefix)]

        print(matches)

        for fname in dir_files:
            if fname.startswith(prefix):
                found_file = fname
                break

        if found_file is None:
            print(f"file with prefix {prefix} not found, skipping")
            continue
            
        test_queue.append((found_file, prefix))

    with concurrent.futures.ThreadPoolExecutor() as tpe:
        futures = [tpe.submit(process_one_source, filename, prefix, os.path.join(OUT_PATH, f"{prefix}_{batch_datetime}.mp4")) for filename, prefix in test_queue]

        for future in concurrent.futures.as_completed(futures):
            ok, destination_file = future.result()
            
            if not ok:
                print(f"something went wrong with {destination_file}")
                continue

            print(f"done with {destination_file}")
            print(f"done with {destination_file}")
            print(f"done with {destination_file}")
            print(f"done with {destination_file}")
            print(f"done with {destination_file}")
            print(f"done with {destination_file}")
            print(f"done with {destination_file}")

def run_proc(cmd: list[str]):
    print(" ".join(cmd))
    print()
    proc = subprocess.Popen(cmd)
    proc.wait()
    return proc


if __name__ == "__main__":
    main()
