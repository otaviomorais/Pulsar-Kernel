#!/usr/bin/env python3
import os
import re
import sys

def patch_ksu(kernel_dir):
    ksu_dir = os.path.join(kernel_dir, "KernelSU")
    if not os.path.exists(ksu_dir):
        ksu_dir = kernel_dir

    print(f"[KSU Patch] Target directory: {ksu_dir}")

    # 1. Update KSU_VERSION to 33235 in Makefile & Kbuild
    for fname in ["Makefile", "Kbuild"]:
        fpath = os.path.join(ksu_dir, "kernel", fname)
        if os.path.exists(fpath):
            with open(fpath, "r") as f:
                content = f.read()
            content = re.sub(r'KSU_VERSION\s*[:=]\s*\d+', 'KSU_VERSION := 33235', content)
            content = re.sub(r'KSU_VERSION=\d+', 'KSU_VERSION=33235', content)
            with open(fpath, "w") as f:
                f.write(content)
            print(f"[KSU Patch] Updated KSU_VERSION in {fname}")

    # 2. Update ksu.c (allow_shell = true)
    ksu_c = os.path.join(ksu_dir, "kernel", "ksu.c")
    if os.path.exists(ksu_c):
        with open(ksu_c, "r") as f:
            content = f.read()
        content = content.replace("bool allow_shell = IS_ENABLED(CONFIG_KSU_DEBUG);", "bool allow_shell = true;")
        with open(ksu_c, "w") as f:
            f.write(content)
        print("[KSU Patch] Enabled allow_shell = true in ksu.c")

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "."
    patch_ksu(target)
