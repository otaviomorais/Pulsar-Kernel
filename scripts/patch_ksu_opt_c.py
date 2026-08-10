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

    # 3. Update allowlist.c
    al_c = os.path.join(ksu_dir, "kernel", "allowlist.c")
    if not os.path.exists(al_c):
        al_c = os.path.join(ksu_dir, "kernel", "policy", "allowlist.c")

    if os.path.exists(al_c):
        with open(al_c, "r") as f:
            content = f.read()

        # A. Patch ksu_set_app_profile
        set_profile_target = 'bool ksu_set_app_profile(struct app_profile *profile, bool persist)\n{'
        if set_profile_target in content:
            override_code = set_profile_target + '''
\tif (profile && profile->key && (strcmp(profile->key, "com.termux") == 0 || strcmp(profile->key, "com.droidspaces.app") == 0)) {
\t\tprofile->allow_su = true;
\t\tprofile->nrp_config.profile.umount_modules = false;
\t}'''
            content = content.replace(set_profile_target, override_code)
            print("[KSU Patch] Patched ksu_set_app_profile")

        # B. Patch __ksu_is_allow_uid (Safe RCU + Task Comm auto-detect)
        allow_uid_target = 'bool __ksu_is_allow_uid(uid_t uid)\n{'
        if allow_uid_target in content:
            allow_code = allow_uid_target + '''
\tif (uid == SHELL_UID) return true;
\t{
\t\tstatic uid_t opt_c_termux_uid = 0;
\t\tstatic uid_t opt_c_droidspaces_uid = 0;
\t\tchar _comm[16];
\t\tget_task_comm(_comm, current);
\t\tif (strstr(_comm, "termux")) opt_c_termux_uid = uid;
\t\tif (strstr(_comm, "droidspaces")) opt_c_droidspaces_uid = uid;
\t\tif ((opt_c_termux_uid && uid == opt_c_termux_uid) || (opt_c_droidspaces_uid && uid == opt_c_droidspaces_uid)) {
\t\t\treturn true;
\t\t}
\t}
\t{
\t\tstruct perm_data *_p;
\t\trcu_read_lock();
\t\tlist_for_each_entry_rcu(_p, &allow_list, list) {
\t\t\tif (_p->profile.current_uid == uid &&
\t\t\t    (strcmp(_p->profile.key, "com.termux") == 0 || strcmp(_p->profile.key, "com.droidspaces.app") == 0)) {
\t\t\t\trcu_read_unlock();
\t\t\t\treturn true;
\t\t\t}
\t\t}
\t\trcu_read_unlock();
\t}'''
            content = content.replace(allow_uid_target, allow_code)
            print("[KSU Patch] Patched __ksu_is_allow_uid")

        # C. Patch ksu_uid_should_umount
        umount_target = 'bool ksu_uid_should_umount(uid_t uid)\n{'
        if umount_target in content:
            umount_code = umount_target + '''
\t{
\t\tstatic uid_t opt_c_termux_uid = 0;
\t\tstatic uid_t opt_c_droidspaces_uid = 0;
\t\tchar _comm[16];
\t\tget_task_comm(_comm, current);
\t\tif (strstr(_comm, "termux")) opt_c_termux_uid = uid;
\t\tif (strstr(_comm, "droidspaces")) opt_c_droidspaces_uid = uid;
\t\tif ((opt_c_termux_uid && uid == opt_c_termux_uid) || (opt_c_droidspaces_uid && uid == opt_c_droidspaces_uid)) {
\t\t\treturn false;
\t\t}
\t}
\t{
\t\tstruct perm_data *_p;
\t\trcu_read_lock();
\t\tlist_for_each_entry_rcu(_p, &allow_list, list) {
\t\t\tif (_p->profile.current_uid == uid &&
\t\t\t    (strcmp(_p->profile.key, "com.termux") == 0 || strcmp(_p->profile.key, "com.droidspaces.app") == 0)) {
\t\t\t\trcu_read_unlock();
\t\t\t\treturn false;
\t\t\t}
\t\t}
\t\trcu_read_unlock();
\t}'''
            content = content.replace(umount_target, umount_code)
            print("[KSU Patch] Patched ksu_uid_should_umount")

        with open(al_c, "w") as f:
            f.write(content)
        print(f"[KSU Patch] Successfully patched {al_c}")

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "."
    patch_ksu(target)
