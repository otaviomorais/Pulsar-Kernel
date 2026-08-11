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