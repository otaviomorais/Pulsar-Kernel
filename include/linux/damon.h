/* SPDX-License-Identifier: GPL-2.0 */
#ifndef _LINUX_DAMON_H
#define _LINUX_DAMON_H
#include <linux/list.h>
#include <linux/mutex.h>
#include <linux/types.h>
#include <linux/time64.h>
#define DAMON_MIN_REGION PAGE_SIZE
struct damon_addr_range { unsigned long start; unsigned long end; };
struct damon_region { struct damon_addr_range ar; unsigned int nr_accesses; struct list_head list; };
struct damon_target { unsigned long id; unsigned int nr_regions; struct list_head regions_list; struct list_head list; };
struct damon_ctx;
struct damon_primitive { void (*init)(struct damon_ctx *ctx); void (*update)(struct damon_ctx *ctx); void (*prepare_access_checks)(struct damon_ctx *ctx); unsigned int (*check_accesses)(struct damon_ctx *ctx); void (*reset_aggregated)(struct damon_ctx *ctx); bool (*target_valid)(void *target); void (*cleanup)(struct damon_ctx *ctx); };
struct damon_callback { void *private; int (*before_start)(struct damon_ctx *ctx); int (*after_sampling)(struct damon_ctx *ctx); int (*after_aggregation)(struct damon_ctx *ctx); int (*before_terminate)(struct damon_ctx *ctx); };
struct damon_ctx { unsigned long sample_interval; unsigned long aggr_interval; unsigned long primitive_update_interval; struct timespec64 last_aggregation; struct timespec64 last_primitive_update; struct task_struct *kdamond; bool kdamond_stop; struct mutex kdamond_lock; struct damon_primitive primitive; struct damon_callback callback; unsigned long min_nr_regions; unsigned long max_nr_regions; struct list_head adaptive_targets; };
#define damon_next_region(r) container_of((r)->list.next, struct damon_region, list)
#define damon_prev_region(r) container_of((r)->list.prev, struct damon_region, list)
#define damon_for_each_region(r, t) list_for_each_entry(r, &(t)->regions_list, list)
#define damon_for_each_region_safe(r, next, t) list_for_each_entry_safe(r, next, &(t)->regions_list, list)
#define damon_for_each_target(t, ctx) list_for_each_entry(t, &(ctx)->adaptive_targets, list)
#define damon_for_each_target_safe(t, next, ctx) list_for_each_entry_safe(t, next, &(ctx)->adaptive_targets, list)
#ifdef CONFIG_DAMON
struct damon_region *damon_new_region(unsigned long start, unsigned long end);
void damon_add_region(struct damon_region *r, struct damon_target *t);
void damon_destroy_region(struct damon_region *r, struct damon_target *t);
struct damon_target *damon_new_target(unsigned long id);
void damon_add_target(struct damon_ctx *ctx, struct damon_target *t);
void damon_free_target(struct damon_target *t);
void damon_destroy_target(struct damon_target *t);
unsigned int damon_nr_regions(struct damon_target *t);
struct damon_ctx *damon_new_ctx(void);
void damon_destroy_ctx(struct damon_ctx *ctx);
int damon_set_targets(struct damon_ctx *ctx, unsigned long *ids, ssize_t nr_ids);
int damon_set_attrs(struct damon_ctx *ctx, unsigned long sample_int, unsigned long aggr_int, unsigned long primitive_upd_int, unsigned long min_nr_reg, unsigned long max_nr_reg);
int damon_nr_running_ctxs(void);
int damon_start(struct damon_ctx **ctxs, int nr_ctxs);
int damon_stop(struct damon_ctx **ctxs, int nr_ctxs);
#endif
#endif
