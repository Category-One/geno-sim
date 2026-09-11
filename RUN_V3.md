# Running the v3 demand model on your own machine

You do not need to understand the code. You type commands. If anything goes
wrong, copy the error text and send it back.

Three model versions are in this package. **v3 is the current one.** v1 and
v2 are kept so results can be compared; do not mix them.

---

## Step 1 — Check Python

Open Terminal (Mac: Cmd+Space, type "Terminal").

    python3 --version

Needs 3.10 or higher. If it shows 3.9, macOS is using its built-in version.
Find your newer one:

    ls /Library/Frameworks/Python.framework/Versions/

If that shows e.g. 3.13, use `python3.13` in place of `python3` everywhere
below, and `python3.13 -m pip` in place of `pip3`.

---

## Step 2 — Delete any old copy first

**Important.** If you have an older geno-sim folder, delete it. Having two
copies is how you end up running the wrong one.

Then unzip this package somewhere findable (Documents is fine).

---

## Step 3 — Go to the folder

Type `cd ` (c, d, space), then drag the `geno-sim` folder onto the Terminal
window and press Enter. Check:

    ls

You should see: README.md, ASSUMPTIONS.md, LICENSE, RUN_V3.md, src, configs,
tests, run_lhs_v3.py.

---

## Step 4 — Install requirements (once)

    pip3 install -r requirements.txt

If it complains about permissions, add `--user` at the end.

---

## Step 5 — Point Python at the code (EVERY new Terminal window)

Mac/Linux:

    export PYTHONPATH=src

Windows:

    set PYTHONPATH=src

If you later see "No module named genosim", this is the step you forgot.

---

## Step 6 — Verify it works

    pytest

Expect **51 passed, 4 skipped**. If anything fails, stop and send the output.
This step proves the code gives the same answers on your machine as on mine.

---

## The jobs

### Job 1 — the headline table (1 minute)

    python3 v3_report.py

Prints the ten-year projection and the market breakdown.

### Job 2 — sensitivity, emerging markets (about 25 minutes)

    python3 run_lhs_v3.py 0 1 4000 em_high

### Job 3 — sensitivity, developed markets (about 25 minutes)

    python3 run_lhs_v3.py 0 1 4000 dm

Jobs 2 and 3 print nothing until they finish. That is normal. Leave the
Terminal window open — closing it stops the job.

When done, `results/` will contain:

    lhs_v3_em_high_0.csv
    lhs_v3_dm_0.csv

Send me those two files.

---

## If something goes wrong

| Message | Fix |
|---|---|
| `command not found: python3` | Install Python from python.org |
| `No module named genosim` | You skipped Step 5 |
| `No module named pandas` | You skipped Step 4 |
| `Permission denied` | Add `--user` to the pip3 command |
| `No module named scipy` | Run: `pip3 install scipy` |
| A test fails | Stop. Send the output. |
| Nothing is happening | It is working. Jobs 2 and 3 are slow. |

Nothing here can break anything. The scripts read files and write new ones
into `results/`.

---

## Before using any number from this

Read `ASSUMPTIONS.md`. It records which parameters are cited, which are
derived, and which are invented. Most behavioural parameters are invented and
swept. The defensible output is the **range** and the finding that adoption
occurs across essentially the whole parameter space — not any single figure.
