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

    # 3. Update allowlist.c (Option C: Auto-allow Shell & Termux)
    al_c = os.path.join(ksu_dir, "kernel", "allowlist.c")
    if not os.path.exists(al_c):
        al_c = os.path.join(ksu_dir, "kernel", "policy", "allowlist.c")

    if os.path.exists(al_c):
        with open(al_c, "r") as f:
            content = f.read()

        opt_c_code = """\tif (uid == SHELL_UID) {
\t\treturn true;
\t}
\t{
\t\tstruct perm_data *p;
\t\trcu_read_lock();
\t\tlist_for_each_entry_rcu(p, &allow_list, list) {
\t\t\tif (p->profile.current_uid == uid && 
\t\t\t    (strcmp(p->profile.key, "com.termux") == 0 || strcmp(p->profile.key, "com.droidspaces.app") == 0)) {
\t\t\t\trcu_read_unlock();
\t\t\t\treturn true;
\t\t\t}
\t\t}
\t\trcu_read_unlock();
\t}
"""
        target_str = 'if (forbid_system_uid(uid)) {\n\t\t// do not bother going through the list if it\'s system\n\t\treturn false;\n\t}'
        if target_str in content:
            content = content.replace(target_str, 'if (forbid_system_uid(uid)) {\n\t\treturn false;\n\t}\n' + opt_c_code)
        else:
            # Fallback insertion after forbid_system_uid check
            content = re.sub(
                r'(if\s*\(forbid_system_uid\(uid\)\)\s*\{[^}]*return false;\s*\})',
                r'\1\n' + opt_c_code,
                content,
                count=1
            )

        set_profile_target = 'bool ksu_set_app_profile(struct app_profile *profile)\n{'
        if set_profile_target in content:
            content = content.replace(
                set_profile_target,
                'bool ksu_set_app_profile(struct app_profile *profile)\n{\n\tif (profile && profile->key && (strcmp(profile->key, "com.termux") == 0 || strcmp(profile->key, "com.droidspaces.app") == 0)) profile->allow_su = true;'
            )

        with open(al_c, "w") as f:
            f.write(content)
        print(f"[KSU Patch] Applied Option C auto-root to {al_c}")

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "."
    patch_ksu(target)

