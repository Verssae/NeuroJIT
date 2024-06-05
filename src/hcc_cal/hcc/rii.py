import subprocess
from pathlib import Path

from hcc_cal.commit import Method


def shorten(file_path: Path, max_length=250) -> Path:
    if len(str(file_path)) <= max_length:
        return file_path
    left_length = max_length - len(str(file_path.parent)) - len(file_path.suffix) - 3
    window = left_length // 3
    shortened_file_path = (
        file_path.stem[:window] + "..." + file_path.stem[-window:] + file_path.suffix
    )

    return file_path.parent / shortened_file_path


def incorrect_indentation_ratio(
    method: Method, commit_hash: str, cache_dir, checkstyle_path, xml_path
) -> float:
    cache = Path(cache_dir)
    java_file = cache / commit_hash / f"{method.signature}.java"
    java_file = shorten(java_file)
    save_file = cache / commit_hash / f"{method.signature}.txt"
    save_file = shorten(save_file)

    java_file.parent.mkdir(exist_ok=True, parents=True)

    if not save_file.exists():
        if not java_file.exists():
            java_file.write_text(method.code)
        ck_output = run_checkstyle(java_file)

        incorrect = sum(
            1
            for line in range(method.start_line, method.end_line + 1)
            if line in ck_output
        )
        value = incorrect / method.loc
        save_file.write_text(str(value))
    else:
        value = float(save_file.read_text())

    return value


def run_checkstyle(
    java_file: Path, checkstyle_path="checkstyle.jar", xml_path="indentation_config.xml"
) -> list[int]:
    command = [
        "java",
        "-jar",
        checkstyle_path,
        "-c",
        xml_path,
        str(java_file),
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.stdout.startswith("Files to process must be specified"):
        raise Exception("Checkstyle failed to run")

    errors = [
        int(line.split(".java:")[1].split(":")[0])
        for line in result.stdout.splitlines()[1:-1]
    ]
    return errors
