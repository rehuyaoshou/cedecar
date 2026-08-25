import re
import shlex
import subprocess

CXX = "ez80-clang"

LINEMARK = re.compile(r'^#\s+\d+\s+"([^"]*)"')

def _preprocess(source_file, flags):
    cmd = [CXX, "-E", *flags, source_file]

    proc = subprocess.run(cmd, capture_output=True, text=True)

    if proc.returncode != 0:
        raise RuntimeError(f'moddeps: {shlex.join(cmd)}\n{proc.stderr}')

    return proc.stdout


def _source_owned_lines(source_file, preprocessed):
    current_file = source_file

    for line in preprocessed.splitlines():
        if marker := LINEMARK.match(line):
            current_file = marker.group(1)
            continue
            
        if current_file == source_file:
            yield line


if __name__ == "__main__":
    file = "strata/ok.cpp"

    for line in _source_owned_lines(file, _preprocess(file, [])):
        print(line)
