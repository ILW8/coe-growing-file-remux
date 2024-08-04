import os
import subprocess
import datetime
import concurrent.futures


# PREFIXES = ["tournament gameplay_", "audience cam_", "main cam_", "wireless cam_"]
PREFIXES = ["main cam_"]
REC_PATH = r"S:/"
STAGE_PATH = r"P:/coe replays and highlights/staging"
OUT_PATH = r"P:/coe replays and highlights/"

FFMPEG_CMD_TEMPLATE = ["ffmpeg", "-sseof", "-300", "-i", None, "-t", "300", "-c", "copy", None]

def main():
    dir_files: list[str] = sorted(os.listdir(REC_PATH), reverse=True)
    task_queue = []
    batch_datetime: str = datetime.datetime.now().isoformat().replace(":", ".")

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

        cmd = FFMPEG_CMD_TEMPLATE.copy()

        # ew
        cmd[4] = os.path.join(REC_PATH, fname)
        cmd[7+2] = os.path.join(OUT_PATH, f"{prefix}_{batch_datetime}.mp4")

        task_queue.append(cmd)

    with concurrent.futures.ThreadPoolExecutor() as tpe:
        futures = {tpe.submit(run_proc, task): task for task in task_queue}
        for future in concurrent.futures.as_completed(futures):
            print(f"remux for {futures[future][-1]} completed")
    print("all done")

def run_proc(cmd: list[str]):
    print(" ".join(cmd))
    print()
    proc = subprocess.Popen(cmd)
    proc.wait()
    return proc


if __name__ == "__main__":
    main()
