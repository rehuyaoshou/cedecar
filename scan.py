import subprocess


def preprocess(source, flags):
    cmd = ["ez80-clang", "-E", *flags, source]

    result = subprocess.run(
        cmd, capture_output=True, text=True
    )

    if result.returncode != 0:
        raise RuntimeError(f'{cmd} failed:\n{result.stderr}')

    return result.stdout


if __name__ == "__main__":
    print(preprocess("strata/ok.cpp", []))
