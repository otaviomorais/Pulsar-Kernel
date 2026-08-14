# Backport do DAMON para a base do Pulsar (staging-bpf)

Registro do backport do DAMON (Data Access MONitor) para a base do Pulsar
(branch `staging-bpf`, kernel 4.19.404) e da entrega como
`patches/damon/0001-damon-api.patch` (header da API) +
`patches/damon/0002-damon-core-vaddr-dbgfs.patch` (implementação completa)
no repo `Pulsar-Kernel`.

## 1. Contexto

O patch `0001-damon-api.patch` adiciona apenas a etapa 1 do upstream:
`include/linux/damon.h` (API header). O commit original indica
"Implementation and userspace interfaces are added separately" — a
implementação nunca foi feita. Este backport entrega a etapa completa:
core (framework), vaddr (primitivas por endereço virtual) e dbgfs
(interface debugfs `/sys/kernel/debug/damon`).

Fontes tomadas do mainline v5.15 (primeira versão estável da série, que usa
as primitivas `damon_va_*` e a API debugfs sem `features`/`vaddr`:
`mm/damon/core.c`, `mm/damon/vaddr.c`, `mm/damon/dbgfs.c`,
`include/linux/damon.h`, `include/trace/events/damon.h`).

## 2. Adaptações para o 4.19

| Arquivo | Adaptação |
|---|---|
| `mm/damon/vaddr.c` | `mmap_read_lock/mmap_read_unlock` → `down_read(&mm->mmap_sem)/up_read(&mm->mmap_sem)` (4.19 usa `mmap_sem`) |
| `mm/damon/vaddr.c` | `#include "vaddr-test.h"` removido (kunit não portado) |
| `mm/damon/core.c` | `#include "core-test.h"` removido |
| `mm/damon/dbgfs.c` | `#include "dbgfs-test.h"` removido |
| `mm/damon/dbgfs.c` | `dbgfs_kunit_suite` removido (kunit) |
| `mm/Kconfig` | menu `Data Access Monitoring` com `DAMON`, `DAMON_VADDR` (depende de `DAMON && MMU`, `select IDLE_PAGE_TRACKING`), `DAMON_DBGFS` (depende de `DAMON_VADDR && DEBUG_FS`). Kunit tests removidos. |
| `mm/Makefile` | `obj-$(CONFIG_DAMON) += damon/` |
| `arch/arm64/configs/vendor/alioth_defconfig` | `CONFIG_DAMON=y`, `CONFIG_DAMON_VADDR=y`, `CONFIG_DAMON_DBGFS=y`, `CONFIG_DEBUG_FS=y` |

Observações de compatibilidade confirmadas:
- `CONFIG_PAGE_IDLE_FLAG` não existe no 4.19 → `DAMON_VADDR` usa
  `select IDLE_PAGE_TRACKING` (equivalente da base).
- `walk_page_range` do 4.19 já é ops-based (`struct mm_walk_ops`), mesma
  assinatura do v5.15 — sem adaptação.
- `ktime_get_coarse_ts64`, `follow_pte`, `kthread_run`, `page_idle_*`
  existem na base.

## 3. Ativação de CONFIG_DEBUG_FS (efeitos colaterais corrigidos)

`DAMON_DBGFS` exige `CONFIG_DEBUG_FS`. O `configs/droidspace.config`
desligava `CONFIG_ZSMALLOC_STAT` justamente para evitar `select DEBUG_FS`,
que compilava código nunca testado com debugfs na base. Com `DEBUG_FS=y`,
estes bugs latentes foram corrigidos:

| Arquivo | Bug latente | Correção |
|---|---|---|
| `drivers/gpu/msm/kgsl_device.h` | `kgsl_debugfs.c` usa `device->set_isdb_breakpoint` inexistente | +`bool set_isdb_breakpoint;` no `struct kgsl_device` |
| `drivers/soc/qcom/msm_bus/msm_bus_core.h` | `#if 0` desligava protótipos reais e ativava stubs `static inline`, colidindo com `msm_bus_dbg_rpmh.c` | `#if 0` → `#ifdef CONFIG_DEBUG_FS` |
| `drivers/platform/msm/gsi/Makefile` | `gsi_debugfs_init` definido no stub `#ifndef CONFIG_DEBUG_FS` de `gsi.c`, mas a versão real (`gsi_dbg.c`) nunca era compilada | +`obj-$(CONFIG_DEBUG_FS) += gsi_dbg.o` |
| `techpack/display/msm/msm_drv.c` | `msm_drv.c` chama `msm_debugfs_late_init()` (declarado com DEBUG_FS) mas a função não era definida em lugar nenhum | +definição `int msm_debugfs_late_init(struct drm_device *dev) { return 0; }` |

## 4. Verificações

- `git apply --check` dos patches na ordem da CI (glob `patches/*/*.patch`)
  sobre checkout fresco de `staging-bpf` passa limpo, e a árvore resultante é
  idêntica à árvore de desenvolvimento nos 12 arquivos do backport.
- Build completo local (Clang 20, `vendor/alioth_defconfig` + fragment
  `droidspace.config`): `Image` (31.3 MB) e `Image.gz-dtb` gerados sem erro.
- Símbolo `damon_dbgfs_init` presente no `Image`.
- `mm/damon/core.o`, `mm/damon/vaddr.o`, `mm/damon/dbgfs.o`,
  `drivers/gpu/msm/kgsl_debugfs.o`, `drivers/soc/qcom/msm_bus/msm_bus_dbg_rpmh.o`,
  `drivers/platform/msm/gsi/gsi_dbg.o`, `techpack/display/msm/msm_drv.o`
  compilam.
- No device: `/sys/kernel/debug/damon` deve aparecer após instalar a release
  (depende de DEBUG_FS montado).

## 5. Entrega

- `patches/damon/0001-damon-api.patch` — header da API (etapa 1, já existente).
- `patches/damon/0002-damon-core-vaddr-dbgfs.patch` — implementação completa
  (12 arquivos: `mm/damon/{core,vaddr,dbgfs}.c` + `Makefile`,
  `include/trace/events/damon.h`, `mm/Kconfig`, `mm/Makefile`,
  `arch/arm64/configs/vendor/alioth_defconfig`, e os 4 fixes de
  DEBUG_FS acima).
- `configs/droidspace.config` — inalterado (não mexe em DAMON/DEBUG_FS).
