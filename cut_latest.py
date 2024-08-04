import os
import subprocess
import datetime
import concurrent.futures
import io

from tqdm import tqdm


PREFIXES = []
PREFIXES.append("tournament gameplay_")
PREFIXES.append("audience cam_")
PREFIXES.append("main cam_")
PREFIXES.append("wireless cam_")
PREFIXES.append("player one cam_")
PREFIXES.append("player two cam_")

# PREFIXES = ["tournament gameplay_", "audience cam_", "main cam_", "wireless cam_"]
# PREFIXES = ["moonlight p1_", "moonlight p2_", "main cam_", "wireless cam_"]
# PREFIXES = ["moonlight p1_", "main cam_"]
REC_PATH = r"P:/COE2024 ISO Recordings/2024-08-03" 
STAGE_PATH = r"P:/coe replays and highlights/staging"
COPY_CHUNK_SIZE = 1024 * 1024
OUT_PATH = r"P:/coe replays and highlights/"

FFMPEG_CMD_TEMPLATE = ["ffmpeg", "-fflags", "fastseek", "-sseof", "-240", "-i", None, "-t", "240", "-c", "copy", None]


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
        with (open(cut_file := os.path.join(STAGE_PATH, f"_{remote_fname_relative}"), "wb") as dest_cut, open(stage_path, "ab") as dest_fh):
            # dest_fh.seek(local_file_size, io.SEEK_SET)
            # os.sendfile() 

            pbar = tqdm(unit="B", unit_divisor=1024, unit_scale=True)
            while True:
                data = source_file.read(COPY_CHUNK_SIZE)
                if not data:
                    break
                pbar.update(len(data))
                # TODO: seek and ftruncate for offset -- skip writing a large file
                dest_fh.write(data)
                dest_cut.write(data)
    return staging_file, cut_file


def process_one_source(source_fname: str, prefix: str, destination_fname: str):
    if not source_fname.endswith(".ts"):
        print("can only fast seek on .mpegts files")
        return False, destination_fname

    cmd = FFMPEG_CMD_TEMPLATE.copy()

    cmd[4+2] = os.path.join(REC_PATH, source_fname)
    cmd[7+2+2] = os.path.join(OUT_PATH, destination_fname)

    run_proc(cmd)

    print(f"returned from run_proc")
    return True, destination_fname
    


def main():
    dir_files: list[str] = sorted(os.listdir(REC_PATH), reverse=True)
    batch_datetime: str = datetime.datetime.now().isoformat().replace(":", ".")
    test_queue = []

    for prefix in PREFIXES:
        found_file = None

        for fname in dir_files:
            if fname.startswith(prefix):
                found_file = fname
                break

        if found_file is None:
            print(f"file with prefix {prefix} not found, skipping")
            continue
            
        test_queue.append((found_file, prefix))

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as tpe:
        futures = [tpe.submit(process_one_source, filename, prefix, os.path.join(OUT_PATH, f"{prefix}_{batch_datetime}.mp4")) for filename, prefix in test_queue]

        for future in concurrent.futures.as_completed(futures):
            ok, destination_file = future.result()
            
            if not ok:
                print(f"something went wrong with {destination_file}")
                continue
            print(f"done with {destination_file}")

def run_proc(cmd: list[str]):
    # print(" ".join(cmd))
    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, universal_newlines=True)

    pbar = tqdm(unit=" frames")

    try:
        for line in proc.stderr:
            if line.startswith("frame="):
                trimmed = line.split("frame=")[1]
                trimmed = trimmed.split("fps=")[0]
                trimmed = trimmed.strip()

                pbar.update(int(trimmed) - pbar.n)
    finally:
        poll = proc.poll()
        if poll is None:
            proc.wait()
    return proc


if __name__ == "__main__":
    main()
