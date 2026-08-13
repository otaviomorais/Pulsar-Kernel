# Backport do syscall fchmodat2() para a base do Pulsar (staging-bpf)

## 1. Contexto

A base `staging-bpf` (4.19.404) já cobre os syscalls modernos até o nr 449
(`futex_waitv`): `faccessat2` (439) já existe nativo — implementação completa
em `fs/open.c` + wire-up 64-bit e compat. Faltava o `fchmodat2` (nr 452, v6.6),
que permite passar `AT_SYMLINK_NOFOLLOW`/`AT_EMPTY_PATH` sem depender de
`/proc/self/fd` — usado pelo glibc/musl modernos e por tooling de containers.

## 2. Commits upstream

| Commit | Origem | Conteúdo |
|---|---|---|
| `09da082b07bb` | v6.6 | `fs: Add fchmodat2()` — do_fchmodat ganha `flags` + `SYSCALL_DEFINE4` |
| `78252deb023c` | v6.6 | `arch: Register fchmodat2, usually as syscall 452` — wire-up + contadores |
| `5daeb41a6fc9` | v6.10 | `fchmodat2: add support for AT_EMPTY_PATH` |

## 3. Adaptações para a base CAF

- `do_fchmodat()` (fs/open.c) — mesma assinatura do upstream (4 parâmetros).
  O protótipo em `fs/internal.h` também foi atualizado (a base 4.19 CAF tem
  declaração própria em `fs/internal.h` — sem isso o build quebra com
  "conflicting types for 'do_fchmodat'").
  O `ksys_chmod` inline em `include/linux/syscalls.h` foi atualizado para
  passar `flags = 0` (assinatura 4-arg).
- Wire-up: nr **452** em `include/uapi/asm-generic/unistd.h` +
  `arch/arm64/include/asm/unistd32.h` (compat ARM32 usa o mesmo número).
- Contadores: `__NR_syscalls` 450 → 453 e `__NR_compat_syscalls` 450 → 453
  (o nr 449/futex_waitv já tinha elevado os contadores para 450).
- Nenhum Kconfig novo é necessário.

## 4. Ordenação do diretório `syscalls/`

O workflow aplica os patches em ordem alfabética de diretório
(`patches/*/*.patch`). Os números de syscall e o contador `__NR_syscalls`
são editados por múltiplos diretórios (`openat2/`, `pidfd/`, `futex/`,
`susfs/`); qualquer inserção feita ANTES desses diretórios quebraria o
contexto dos hunks seguintes. Por isso este diretório se chama `syscalls/`
— em ordem alfabética ele aplica **por último** (depois de `susfs/`),
mantendo os contextos estáveis.

## 5. Verificações

- `git apply --check` limpo sobre a árvore = base + todos os patches do repo.
- Compilação local completa (Clang 19, `vendor/alioth_defconfig` + fragmento
  `droidspace.config`): `fs/open.o` compila sem erro; `vmlinux` linka com o
  novo símbolo `__arm64_sys_fchmodat2`.
- Conteúdo do patch: apenas o backport (29 linhas), sem hunks de outros
  diretórios.
---

# Backports adicionais (tier-2 e tier-3)

## 0002-tier2-tier3-syscalls.patch

Aplica em cima do estado completo do repo (base staging-bpf + todos os
patches de `patches/*/`). Adiciona os syscalls que faltam para glibc/musl
e tooling modernos:

### Tier-2

| Syscall | Nr | Origem | Conteúdo |
|---|---|---|---|
| memfd_secret | 442 | v5.14 | arm64 `set_direct_map_*` + `rodata_full` (v5.6/v5.9), `mm/secretmem.c` |
| set_mempolicy_home_node | 450 | v5.17 | fix de memleak (MPOL_BIND), NUMA |
| cachestat | 451 | v6.5 | `mm/filemap.c` + fix de permissão (nr_recently_evicted) |

### Tier-3 (xattr-at)

| Syscall | Nr | Origem | Conteúdo |
|---|---|---|---|
| setxattrat | 463 | v6.13 | struct `xattr_args` (XATTR_ARGS_SIZE_VER0), fd-based incl. O_PATH |
| getxattrat | 464 | v6.13 | AT_EMPTY_PATH + AT_SYMLINK_NOFOLLOW |
| listxattrat | 465 | v6.13 | via `copy_struct_from_user` |
| removexattrat | 466 | v6.13 | UAPI final do mainline (compatível com glibc 2.4x+) |

Wire-up: 64-bit + compat ARM32; `__NR_syscalls` 453 → 467 e
`__NR_compat_syscalls` 453 → 467.

> **Nota sobre ordenação:** como `device/` vem antes de `syscalls/` em ordem
> alfabética, o `0001-device-fixes-fastcharge.patch` aplica antes deste —
> ele não toca em números de syscall, então o contexto fica estável.

## Verificação

- `git apply` sequencial (ordem do workflow) reproduz byte-a-byte a árvore
  local de desenvolvimento (`d60582dff`), validado por `diff -rq`.
