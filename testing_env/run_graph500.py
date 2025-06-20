import argparse
from pathlib import Path
import subprocess
import os
import filecmp

TIMEOUT = 7200  # seconds
test_max_str = os.getenv('TESTMAX')
if not test_max_str:
    print('TESTMAX not set. Setting to 10100200300')
    max_nodes = 10100200300
else:
    max_nodes = int(test_max_str)


def run_tests(break_on_fail, local):
    Path("outputs").mkdir(parents=True, exist_ok=True)
    for solution in Path(".").iterdir():
        if solution.is_dir() and not solution.name in ["tests", "outputs"]:
            make = subprocess.run("make", cwd=solution.name, capture_output=True, timeout=300)
            if make.returncode != 0:
                print(f"{solution.name}: FAILED (make)")
                if break_on_fail:
                    print(make.stdout)
                    exit(1)
                continue
            print(f"Solution: {solution.name}")
            for test in Path("tests").iterdir():
                if 'scale-26' in test.name or 'scale-25' in test.name or 'scale-24' in test.name or 'scale-23' in test.name:
                    print(f"Skipping: {test.name}", flush=True)
                    continue
                if 'bench' not in test.name:
                    print(f"Skipping: {test.name}", flush=True)
                    continue
                print(f"Running: {test.name}", flush=True)
                nodes = int(test.name[test.name.find("_") + 1: test.name.rfind("_")])
                if nodes > max_nodes:
                    print(f"    {test.name}: SKIPPED (LARGE)", flush=True)
                    continue
                workers = int(test.name[test.name.rfind("_") + 1:])
                # Remove old outputs
                for f in Path("outputs").iterdir():
                    f.unlink()
                if local:
                    command = "mpiexec"
                else:
                    command = "srun"
                
                cmd = [
                    command, "-n", str(workers),
                    "./test_command.sh", solution.name, test.name, "25",
                    "--noios",
                    "--nolocal-bypass",
                    "--logging", "progress",
                    ]
                execution = subprocess.run(cmd, capture_output=True, timeout=TIMEOUT)
                print('Executing:', ' '.join(cmd))
                if execution.returncode != 0:
                    print(f"    {test.name}: FAILED ({command})" + execution.stdout.decode('UTF-8') + "ERR:" + execution.stderr.decode('UTF-8'))
                    if break_on_fail:
                        print(execution.stdout.decode('utf-8'))
                        exit(1)
                    continue
                failed = False
                # for i in range(workers):
                #     if not filecmp.cmp(f"tests/{test.name}/{i}.out", f"outputs/{i}.out", shallow=False):
                #         print(f"    {test.name}: FAILED (outputs differ on rank {i})")
                #         failed = True
                #         if break_on_fail:
                #             exit(1)
                #         break
                if not failed:
                    print(f"    {test.name}: Finished! Skipping validation", flush=True)
                    print('stdout:', execution.stdout.decode('utf-8'))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Test runner')
    parser.add_argument('-b', '--breakonfail', action='store_true', help='break and print stdout on fail')
    parser.add_argument('-l', '--local', action='store_true', help='run tests locally (without slurm)')

    args = parser.parse_args()
    run_tests(args.breakonfail, args.local)
