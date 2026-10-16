"""What-if scenarios for the slides: savings levers, DAU x2, token price changes.

Each lever is measured as (cost without the lever) - (base cost), all other assumptions fixed.
usage: python3 model/scenarios.py  -> prints table, writes model/out/scenarios.json
"""
import copy, json, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vbot_model as M

HERE = os.path.dirname(os.path.abspath(__file__))


def total(**patch):
    saved = {n: copy.deepcopy(getattr(M, n)) for n in ('A', 'TIERS', 'SANDBOX', 'P', 'STORAGE', 'TOKEN_PRICE_MULT')}
    try:
        for fn in patch.values():
            fn()
        rows, S = M.build()
        by = {}
        for r in rows:
            by[r['component']] = by.get(r['component'], 0) + r['chi_phi']
        return S['total'], by, S
    finally:
        for n, v in saved.items():
            setattr(M, n, v)


def no_routing():
    # mọi request chạy model tham chiếu Gemini 3.8 Flash (Standard), giữ nguyên token và cache
    for t in M.TIERS:
        main = [c for c in t['calls'] if c['share'] >= 0.85]
        t['calls'] = [dict(model='f38', share=1.0, tin=sum(c['tin'] for c in main), tout=sum(c['tout'] for c in main),
                           cache=max(c['cache'] for c in main))]


def no_flex():
    for t in M.TIERS:
        for c in t['calls']:
            c['flex'] = 0.0
    M.P['f38flex_in'], M.P['f38flex_out'] = M.P['f38_in'], M.P['f38_out']


def no_cache():
    for t in M.TIERS:
        for c in t['calls']:
            c['cache'] = 0.0


def no_spot():
    M.SANDBOX['spot_share'] = 0.0


def no_cud():
    M.P['ap_vcpu_cud1'], M.P['ap_mem_cud1'] = M.P['ap_vcpu'], M.P['ap_mem']
    M.P['sql_ha_vcpu_cud1'], M.P['sql_ha_mem_cud1'] = 0.1156, 0.0196


def no_offhours_scale():
    # staging + burst pod chạy 24/7 thay vì giờ hành chính: xấp xỉ bằng H_BIZ -> H_MONTH
    M.H_BIZ_SAVED = M.H_BIZ
    M.H_BIZ = M.H_MONTH


def dau_x2():
    M.A['dau'], M.A['mau'] = 4000, 4800


def tok_up():
    M.TOKEN_PRICE_MULT = 1.3


def tok_down():
    M.TOKEN_PRICE_MULT = 0.5


if __name__ == '__main__':
    base, base_by, S = total()
    out = {'base': base, 'per_dau': base / 2000, 'by_component': base_by}
    levers = [
        ('Routing theo cấp (Flash-Lite, gpt-oss) thay vì mọi request chạy Gemini 3.8 Flash', dict(a=no_routing)),
        ('Prompt caching ngầm của Gemini (prefix hệ thống, ngữ cảnh agent)', dict(a=no_cache)),
        ('Flex/Batch cho agent chạy nền cấp 4 và cổng eval', dict(a=no_flex)),
        ('Spot Pod cho sandbox (80% lượt chạy)', dict(a=no_spot)),
        ('CUD 1 năm cho pod nền + Cloud SQL HA', dict(a=no_cud)),
    ]
    out['levers'] = []
    for name, patch in levers:
        t, _, _ = total(**patch)
        out['levers'].append(dict(name=name, without=round(t, 2), saving=round(t - base, 2)))
    # off-hours scale: H_BIZ is read at call time inside build via module global
    h = M.H_BIZ
    M.H_BIZ = M.H_MONTH
    t_off, _, _ = total()
    M.H_BIZ = h
    out['levers'].append(dict(name='Scale theo giờ hành chính (burst pod, staging, warm pool tắt ngoài giờ)',
                              without=round(t_off, 2), saving=round(t_off - base, 2)))
    t2, by2, S2 = total(a=dau_x2)
    out['dau_x2'] = dict(total=t2, per_dau=t2 / 4000, by_component=by2)
    tu, _, _ = total(a=tok_up)
    td, _, _ = total(a=tok_down)
    out['token_up30'] = tu
    out['token_down50'] = td
    oss = sum(r['cost'] for t in S['tiers'] for r in t['rows'] if r['model'] == 'oss')
    out['oss_api_cost'] = oss
    out['h100_premium_2gpu'] = 2 * 1.443429 * 730
    json.dump(out, open(os.path.join(HERE, 'out', 'scenarios.json'), 'w'), ensure_ascii=False, indent=1)
    print(f"base {base:,.2f}  /DAU {base/2000:.2f}")
    for l in out['levers']:
        print(f"  -{l['saving']:>9,.2f}  (không có: {l['without']:>10,.2f})  {l['name']}")
    print(f"DAU x2: {t2:,.2f} ({t2/base:.2f}x)  /DAU {t2/4000:.2f}")
    for k in sorted(by2, key=lambda k: -by2[k])[:8]:
        print(f"   {k:14s} {base_by.get(k,0):9,.2f} -> {by2[k]:9,.2f}  x{by2[k]/max(base_by.get(k,1),1):.2f}")
    print(f"token +30%: {tu:,.2f} ({tu-base:+,.2f})   token -50%: {td:,.2f} ({td-base:+,.2f})")
    print(f"gpt-oss API cost {oss:,.2f} vs 2x H100 premium {out['h100_premium_2gpu']:,.2f}")
