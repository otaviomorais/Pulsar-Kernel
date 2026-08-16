# AnyKernel3 Ramdisk Mod Script
# osm0sis @ xda-developers
#
# Pulsar Kernel custom installer
# POCO F3 / Xiaomi Mi 11X / Redmi K40 (alioth / aliothin)

properties() { '
kernel.string=Pulsar Kernel
do.devicecheck=1
do.modules=0
do.systemless=1
do.cleanup=1
do.cleanuponabort=0
device.name1=alioth
device.name2=aliothin
supported.versions=
'; }

# shell variables
block=auto;
is_slot_device=auto;
ramdisk_compression=auto;
patch_vbmeta_flag=auto;

## AnyKernel methods (DO NOT CHANGE)
# import patching functions/variables - see for reference
. tools/ak3-core.sh;

## AnyKernel file attributes
# set permissions/ownership for included ramdisk files
set_perm_recursive 0 0 750 750 $ramdisk/*;

## AnyKernel install
dump_boot;

# Begin Ramdisk Changes

# migrate from /overlay to /overlay.d to enable SAR Magisk
if [ -d $ramdisk/overlay ]; then
  rm -rf $ramdisk/overlay;
fi;

write_boot;
## end install

## vendor_boot shell variables
block=/dev/block/bootdevice/by-name/vendor_boot;
is_slot_device=1;
ramdisk_compression=auto;
patch_vbmeta_flag=auto;

# reset for vendor_boot patching
reset_ak;

# vendor_boot install (replaces DTB with dedicated kona-v2.1 DTB)
dump_boot;
write_boot;
## end vendor_boot install

ui_print " ";
ui_print " Pulsar Kernel — POCO F3 (alioth) ";
ui_print " --- Install Complete --- ";

