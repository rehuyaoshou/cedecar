import re
import shlex
import subprocess

CXX = "ez80-clang"

# yes, I used box art simply to dodge:
# 
#   # <line> "<file>" [flags]
#
# the double pound bothered me that much.

# *-----------------------------*
# |  # <line> "<file>" [flags]  |
# *-----------------------------*
LINEMARK = re.compile(r'^#\s+\d+\s+"([^"]*)"')

# *--------------------------------*
# |  export module <name[:part]>;  |
# *--------------------------------*
IFACE_UNIT = re.compile(r"^\s*export\s+module\s+([\w.]+(?::[\w.]+)?)\s*;")
# *---------------------------*
# |  module <name>[<:part>];  |
# *---------------------------*
IMPL_UNIT = re.compile(r"^\s*module\s+([\w.]+)(:[\w.]+)?\s*;")
# *---------------------------------------*
# |  [export] import [:]<module[:part]>;  |
# *---------------------------------------*
IMPORT_DECL = re.compile(r"^\s*(export\s+)?import\s+(:?[\w.]+(?::[\w.]+)?)\s*;")

# *------------------------*
# |  [export] import <...  |
# |  [export] import "...  |
# *------------------------*
HEADER_IMPORT = re.compile(r'^\s*(?:export\s+)?import\s*[<"]')
# *---------------------*
# |  module;            |
# |  module : private;  |
# *---------------------*
FRAGMENT = re.compile(r"^\s*module\s*(?::\s*private)?\s*;")

# *------------------------------------------------*
# |  [export] (module|import) <module-ish text>;   |
# *------------------------------------------------*
UNRECOGNIZED = re.compile(r"^\s*(?:export\s+)?(?:module|import)(?!\w)\s*[\w.\s:]*;")


def _preprocess(source_file, flags):
    cmd = [CXX, "-E", *flags, source_file]

    proc = subprocess.run(cmd, capture_output=True, text=True)

    if proc.returncode != 0:
        raise RuntimeError(
            f"moddeps: {shlex.join(cmd)}\n"
            "\n"
            f"{proc.stderr}\n"
            "\n"
        )

    return proc.stdout


def _source_owned_lines(source_file, preprocessed):
    current_file = source_file

    for line in preprocessed.splitlines():
        if marker := LINEMARK.match(line):
            current_file = marker.group(1)
            continue

        if current_file == source_file:
            yield line


def parse_unit(source_file, preprocessed):
    for line in _source_owned_lines(source_file, preprocessed):

        if HEADER_IMPORT.match(line):
            raise RuntimeError(
                f"moddeps: {source_file}\n"
                f"  { line.strip() }\n"
                "\n"
                "header units aren't currently possible! please use a global module fragment:\n"
                "\n"
                "  module;\n"
                "\n"
                "  #include <header1>\n"
                "  #include <header2>\n"
                "\n"
                '  #include "header3"\n'
                '  #include "header4"\n'
                "\n"
                "  export module my_iface;\n"
                "\n"
            )

        if IFACE_UNIT.match(line):
            print(f"[IFACE_UNIT] {line}")
            continue

        if IMPL_UNIT.match(line):
            print(f"[IMPL_UNIT] {line}")
            continue

        if IMPORT_DECL.match(line):
            print(f"[IMPORT_DECL] {line}")
            continue

        if UNRECOGNIZED.match(line) and not FRAGMENT.match(line):
            raise RuntimeError(
                f"moddeps: {source_file}\n"
                "\n"
                "this module declaration is unrecognized:\n"
                "\n"
                f"  { line.strip() }\n"
                "\n"
                "hint: use canonical spacing.\n"
                "\n"
                "BAD:                          GOOD:                         \n"
                "  import:iface;                 import :iface;              \n"
                "  import: iface;                                            \n"
                "  import : iface;                                           \n"
                "\n"
                "don't be a freak with your linter ;)\n"
                "\n"
            )


if __name__ == "__main__":
    source = "strata/zoo.cpp"
    parse_unit(source, _preprocess(source, []))
