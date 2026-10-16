"""VBot Workplace: sizing + monthly cost model (single source of truth).

Every number in the quote (BaoGia) and on the slides comes from this file.
Run:  python3 model/vbot_model.py          -> prints summary, writes model/out/*.json
Unit prices were read from the official Google Cloud pricing pages on 2026-10-16
(raw page snapshots in evidence/raw/). Region: asia-southeast1 (Singapore),
Vertex AI models via the Global endpoint (Global price column).
"""
import json, math, os

HERE = os.path.dirname(os.path.abspath(__file__))

# ----------------------------------------------------------------------------
# 1. Evidence sources (sheet BangChung). id -> (description, url)
# ----------------------------------------------------------------------------
EVIDENCE = {
    'E01': ('Vertex AI (Agent Platform) pricing, bảng Gemini 3 Standard: Gemini 3.8 Flash (giá chuẩn từ 01/2027) '
            '$1.50/$0.15/$7.50, Gemini 3.1 Flash-Lite $0.25/$0.025/$1.50, cột Global',
            'https://cloud.google.com/vertex-ai/generative-ai/pricing'),
    'E02': ('GKE pricing, Singapore: Autopilot vCPU $0.0549, RAM $0.0060729; Flexible CUD 1 năm; Spot',
            'https://cloud.google.com/kubernetes-engine/pricing'),
    'E03': ('Cloud SQL for PostgreSQL pricing, Singapore: vCPU/RAM/HA, SSD, backup, CUD 1 năm',
            'https://cloud.google.com/sql/pricing'),
    'E04': ('Memorystore for Redis pricing, Singapore: Standard tier M1',
            'https://cloud.google.com/memorystore/docs/redis/pricing'),
    'E05': ('Cloud Storage pricing, Asia (multi-region): Standard $0.026/GiB-tháng',
            'https://cloud.google.com/storage/pricing'),
    'E06': ('Network pricing, Singapore: Cloud Load Balancing 5 forwarding rule đầu $0.028/giờ, data processed $0.009/GiB',
            'https://cloud.google.com/vpc/network-pricing'),
    'E07': ('Cloud NAT pricing: gateway theo số VM, IP, data processed',
            'https://cloud.google.com/nat/pricing'),
    'E08': ('Cloud Armor pricing: Standard policy, rule, request',
            'https://cloud.google.com/armor/pricing'),
    'E09': ('Cloud KMS pricing: key version SOFTWARE/HSM, cryptographic operations',
            'https://cloud.google.com/kms/pricing'),
    'E10': ('Secret Manager pricing: active secret version, access operations',
            'https://cloud.google.com/secret-manager/pricing'),
    'E11': ('Identity Platform pricing: Tier 2 providers OIDC/SAML $0.015/MAU',
            'https://cloud.google.com/identity-platform/pricing'),
    'E12': ('Google Cloud Observability pricing: Logging storage $0.50/GiB, retention $0.01/GiB-tháng',
            'https://cloud.google.com/stackdriver/pricing'),
    'E13': ('Pub/Sub pricing: throughput $40/TiB',
            'https://cloud.google.com/pubsub/pricing'),
    'E14': ('Security Command Center pricing, mục Model Armor standalone $0.10/1M tokens',
            'https://cloud.google.com/security-command-center/pricing'),
    'E15': ('Sensitive Data Protection (DLP) pricing: content inspection $3/GB',
            'https://cloud.google.com/sensitive-data-protection/pricing'),
    'E16': ('Artifact Registry pricing: storage $0.10/GiB-tháng',
            'https://cloud.google.com/artifact-registry/pricing'),
    'E17': ('Cloud Build pricing: e2-standard-2 $0.006/phút',
            'https://cloud.google.com/build/pricing'),
    'E18': ('Google Cloud Customer Care: Standard Support 3% chi phí cloud (tối thiểu $29)',
            'https://cloud.google.com/support'),
    'E19': ('Vertex AI locations, tab Global: Gemini 3.8 Flash, Gemini 3.1 Flash-Lite, Gemini 3.1 Flash-Lite Image có ở Global endpoint',
            'https://cloud.google.com/vertex-ai/generative-ai/docs/learn/locations'),
    'E20': ('GKE Sandbox (gVisor) cho Autopilot và Standard: cô lập code không tin cậy',
            'https://cloud.google.com/kubernetes-engine/docs/concepts/sandbox-pods'),
    'E21': ('Vertex AI pricing, bảng OpenAI models: gpt-oss-120b $0.09 in / $0.36 out mỗi 1M token',
            'https://cloud.google.com/vertex-ai/generative-ai/pricing'),
    'E22': ('Vertex AI pricing, bảng image: Gemini 3.1 Flash-Lite Image, image output $30/1M token (1120 token/ảnh 1K)',
            'https://cloud.google.com/vertex-ai/generative-ai/pricing'),
    'E23': ('Vertex AI pricing, bảng Embedding: Gemini Embedding $0.00015 / 1.000 token online',
            'https://cloud.google.com/vertex-ai/generative-ai/pricing'),
    'E24': ('Vertex AI pricing, tab Flex/Batch: Gemini 3.8 Flash $0.75/$3.75, Gemini 3.1 Flash-Lite $0.125/$0.75',
            'https://cloud.google.com/vertex-ai/generative-ai/pricing'),
    'E25': ('GKE pricing: cluster management fee $0.10 / cluster / giờ',
            'https://cloud.google.com/kubernetes-engine/pricing'),
    'E26': ('Cloud SQL pricing, Singapore, HA Storage: SSD $0.000652055/GiB-h, Backups (used) $0.000153425/GiB-h',
            'https://cloud.google.com/sql/pricing'),
    'E27': ('Cloud Storage pricing: inter-region replication, Asia (multi-region) $0.08/GiB',
            'https://cloud.google.com/storage/pricing'),
    'E28': ('Cloud Storage pricing: Class A/B operations cho bucket dual-region/multi-region',
            'https://cloud.google.com/storage/pricing'),
    'E29': ('Cloud Storage pricing, Singapore: Archive storage $0.0015/GiB-tháng',
            'https://cloud.google.com/storage/pricing'),
    'E30': ('Network pricing, Singapore: internet egress Premium tới Asia $0.12/GiB (0-1 TiB)',
            'https://cloud.google.com/vpc/network-pricing'),
    'E31': ('Network pricing: data transfer giữa các zone trong cùng region $0.01/GiB',
            'https://cloud.google.com/vpc/network-pricing'),
    'E32': ('Observability pricing: Managed Service for Prometheus $0.06/triệu sample',
            'https://cloud.google.com/stackdriver/pricing'),
    'E33': ('Observability pricing: Cloud Trace $0.20/triệu span',
            'https://cloud.google.com/stackdriver/pricing'),
    'E34': ('Cloud SQL pricing, Singapore, Storage (zonal, dùng cho staging): SSD $0.000326027/GiB-h',
            'https://cloud.google.com/sql/pricing'),
}

# ----------------------------------------------------------------------------
# 2. Unit prices (USD, list price, Standard tier) -> each tied to an evidence id
# ----------------------------------------------------------------------------
P = {
    # Vertex AI, Global endpoint, <=200K context (E01)
    'f38_in': 1.50, 'f38_cached': 0.15, 'f38_out': 7.50,        # Gemini 3.8 Flash (giá chuẩn, áp dụng từ 01/2027; không dùng giá giới thiệu)
    'fl_in': 0.25, 'fl_cached': 0.025, 'fl_out': 1.50,          # Gemini 3.1 Flash-Lite
    'f38flex_in': 0.75, 'f38flex_cached': 0.075, 'f38flex_out': 3.75,   # Flex/Batch tier
    'flflex_in': 0.125, 'flflex_cached': 0.0125, 'flflex_out': 0.75,    # Flex/Batch tier
    'oss_in': 0.09, 'oss_out': 0.36,                            # gpt-oss-120b (MaaS)
    'img_1k': 0.0336,                                           # Gemini 3.1 Flash-Lite Image: 1120 token x $30/1M
    'emb': 0.15,                                                # Gemini Embedding $0.00015 / 1K token = $0.15/1M
    # GKE (E02), Singapore
    'gke_fee_h': 0.10,
    'ap_vcpu': 0.0549, 'ap_mem': 0.0060729,                     # Autopilot general-purpose on-demand
    'ap_vcpu_cud1': 0.039528, 'ap_mem_cud1': 0.004372488,       # Compute Flexible CUD 1 năm
    'ap_vcpu_spot': 0.0165, 'ap_mem_spot': 0.0018219,           # Spot Pod
    # Cloud SQL PostgreSQL Enterprise (E03), Singapore
    'sql_vcpu': 0.0578, 'sql_mem': 0.0098,
    'sql_ha_vcpu_cud1': 0.0867, 'sql_ha_mem_cud1': 0.0147,      # HA, CUD 1 năm
    'sql_ssd_ha_h': 0.000652055, 'sql_ssd_h': 0.000326027, 'sql_backup_h': 0.000153425,
    # Memorystore Redis Standard M1 (E04)
    'redis_std_m1': 0.114,
    # Cloud Storage (E05)
    'gcs_asia_std': 0.026, 'gcs_repl_asia': 0.08, 'gcs_ops_a_mr': 0.01, 'gcs_ops_b': 0.0004,
    'gcs_sg_archive': 0.0015,
    # Network (E06, E07, E08)
    'lb_rule_h': 0.028, 'lb_data': 0.009, 'egress_asia': 0.12, 'interzone': 0.01,
    'nat_vm_h': 0.0014, 'nat_ip_h': 0.005, 'nat_data': 0.045,
    'armor_policy_h': 0.006849315, 'armor_rule_h': 0.001369863, 'armor_req_per_m': 0.75,
    # Security (E09, E10, E11, E14, E15)
    'kms_soft_h': 0.000082192, 'kms_hsm_h': 0.001369863, 'kms_op_10k': 0.03,
    'sm_version_h': 0.000082192, 'sm_access_10k': 0.03,
    'idp_mau_t2': 0.015,
    'armor_model_per_m': 0.10, 'dlp_gb': 3.00,
    # Observability (E12), messaging (E13), CI/CD (E16, E17)
    'log_ingest_gb': 0.50, 'log_retention_gb': 0.01, 'prom_per_m_samples': 0.06, 'trace_per_m_spans': 0.20,
    'pubsub_tib': 40.0,
    'ar_gb': 0.10, 'build_min': 0.006,
    'support_pct': 0.03,
}

TOKEN_PRICE_MULT = 1.0   # dùng cho kịch bản giá token +30% / -50%
EV_LLM = {'L1': 'E01; E19', 'L2': 'E01; E19', 'L3': 'E21; E01', 'L4': 'E21; E24; E01', 'L5': 'E01; E22'}

H_MONTH = 730          # 24/7
H_BIZ = 22 * 10        # giờ hành chính / tháng
H_OFF = H_MONTH - H_BIZ

# ----------------------------------------------------------------------------
# 3. Workload assumptions (từ 2.000 DAU)
# ----------------------------------------------------------------------------
A = {
    'dau': 2000, 'mau': 2400, 'days': 22, 'biz_hours': 10,
    'req_per_user_day': 25,          # khớp hằng số REQ_PER_USER trong trang đề
    'peak_hour_share': 0.18,         # 18% request trong ngày rơi vào giờ cao điểm 9-10h
    'burst_factor': 2.0,             # đỉnh theo phút so với trung bình giờ cao điểm
    'stream_seconds': 10,            # thời gian 1 phiên trả lời streaming
}

# Mỗi cấp tác vụ: tỉ lệ request, token / request (gộp mọi lần gọi LLM), routing
TIERS = [
    dict(id='L1', name='Email và hỏi đáp', share=0.52,
         calls=[dict(model='fl', share=0.95, tin=3500, tout=350, cache=0.35),
                dict(model='f38', share=0.05, tin=3500, tout=350, cache=0.35)],
         sandbox=0.0, guard_tokens=2800, connector_calls=1.0),
    dict(id='L2', name='Tài liệu và slide', share=0.22,
         calls=[dict(model='fl', share=0.90, tin=9000, tout=2200, cache=0.25),
                dict(model='f38', share=0.10, tin=9000, tout=2200, cache=0.25)],
         sandbox=0.5, guard_tokens=3000, connector_calls=1.5),
    dict(id='L3', name='Dữ liệu và code', share=0.12,
         calls=[dict(model='oss', share=1.00, tin=20000, tout=3500, cache=0.0),
                dict(model='oss', share=0.25, tin=12000, tout=2500, cache=0.0),     # retry gpt-oss kèm log lỗi
                dict(model='f38', share=0.08, tin=20000, tout=3500, cache=0.40)],   # leo thang khi vẫn fail
         sandbox=2.5, guard_tokens=2500, connector_calls=0.5),
    dict(id='L4', name='Agent dự án', share=0.09,
         calls=[dict(model='oss', share=0.85, tin=10000, tout=2000, cache=0.0),     # planner
                dict(model='f38', share=0.15, tin=10000, tout=2000, cache=0.40, flex=0.9),    # planner leo thang
                dict(model='fl', share=1.00, tin=36000, tout=2400, cache=0.60, flex=0.9)],    # 6 bước executor
         sandbox=0.2, guard_tokens=9000, connector_calls=8.0),
    dict(id='L5', name='Thiết kế', share=0.05,
         calls=[dict(model='fl', share=1.00, tin=5000, tout=3000, cache=0.30)],
         sandbox=1.0, guard_tokens=1300, connector_calls=0.3, images=0.4),
]

SANDBOX = dict(seconds=45, vcpu=1.0, mem_gib=2.0, spot_share=0.8, warm_pods=4, warm_vcpu=0.5, warm_mem=1.0)

STORAGE = dict(
    workspace_gib_per_user=1.0,          # dùng thực tế TB 1 GB / quota 10 GB
    workspace_new_gib_month=300,         # dữ liệu mới ghi mỗi tháng (replication tính trên phần này)
    kb_docs=300_000, chunks_per_doc=8, tokens_per_chunk=500,
    kb_churn_month=0.10,                 # 10% tài liệu đổi mỗi tháng -> re-embed
    chat_kb_per_req=8, chat_retention_months=12,
    vector_bytes_per_chunk=4096,         # halfvec 768 + text + ACL + HNSW
)


def tier_tokens():
    req_month = A['dau'] * A['req_per_user_day'] * A['days']
    out = []
    for t in TIERS:
        n = req_month * t['share']
        rows = []
        for c in t['calls']:
            k = n * c['share']
            tin, tout = k * c['tin'], k * c['tout']
            cached = tin * c['cache']
            m = c['model']
            fx = c.get('flex', 0.0)
            if m == 'oss':
                cost = tin / 1e6 * P['oss_in'] + tout / 1e6 * P['oss_out']
            else:
                def at(pre):
                    return (tin - cached) / 1e6 * P[pre + '_in'] + cached / 1e6 * P[pre + '_cached'] + tout / 1e6 * P[pre + '_out']
                cost = (1 - fx) * at(m) + fx * at(m + 'flex')
            cost *= TOKEN_PRICE_MULT
            rows.append(dict(model=m, req=k, tin=tin, tout=tout, cached=cached, cost=cost, flex=fx))
        img = n * t.get('images', 0)
        out.append(dict(id=t['id'], name=t['name'], share=t['share'], req=n, rows=rows, images=img,
                        img_cost=img * P['img_1k'], cost=sum(r['cost'] for r in rows) + img * P['img_1k']))
    return req_month, out


def r2(x):
    return round(x + 1e-9, 2)


def build():
    req_month, tiers = tier_tokens()
    req_day = A['dau'] * A['req_per_user_day']
    peak_rps = req_day * A['peak_hour_share'] / 3600
    tin_total = sum(r['tin'] for t in tiers for r in t['rows'])
    tout_total = sum(r['tout'] for t in tiers for r in t['rows'])
    per_req_in = tin_total / req_month
    per_req_out = tout_total / req_month
    S = {}  # sizing facts for slides
    S.update(req_month=req_month, req_day=req_day, peak_rps=peak_rps, burst_rps=peak_rps * A['burst_factor'],
             peak_in_tps=peak_rps * per_req_in, peak_out_tps=peak_rps * per_req_out,
             concurrent_streams=peak_rps * A['burst_factor'] * A['stream_seconds'],
             tin_month=tin_total, tout_month=tout_total, per_req_in=per_req_in, per_req_out=per_req_out)

    rows = []

    def add(comp, meaning, note, cost, ev):
        rows.append(dict(component=comp, y_nghia=meaning, ghi_chu=note, chi_phi=r2(cost), bang_chung=ev))

    # ---------------- LLM ----------------
    names = {'fl': 'Gemini 3.1 Flash-Lite', 'f38': 'Gemini 3.8 Flash', 'oss': 'gpt-oss-120b'}
    for t in tiers:
        parts = []
        for r in t['rows']:
            m = r['model']
            if m == 'oss':
                parts.append(f"{names[m]}: {r['tin']/1e6:,.0f}M in x $0.09 + {r['tout']/1e6:,.1f}M out x $0.36 = {r['cost']:,.2f}")
            elif r['flex']:
                fx = r['flex']; q = m + 'flex'
                parts.append(f"{names[m]} ({(r['tin']-r['cached'])/1e6:,.0f}M in, {r['cached']/1e6:,.0f}M cached, {r['tout']/1e6:,.1f}M out): "
                             f"{int(fx*100)}% Flex/Batch (${P[q+'_in']}/${P[q+'_cached']}/${P[q+'_out']}) + {int(round((1-fx)*100))}% Standard "
                             f"(${P[m+'_in']}/${P[m+'_cached']}/${P[m+'_out']}) = {r['cost']:,.2f}")
            else:
                pin, pc, po = P[m + '_in'], P[m + '_cached'], P[m + '_out']
                parts.append(f"{names[m]}: {(r['tin']-r['cached'])/1e6:,.0f}M in x ${pin} + {r['cached']/1e6:,.0f}M cached x ${pc} + "
                             f"{r['tout']/1e6:,.1f}M out x ${po} = {r['cost']:,.2f}")
        note = (f"{t['req']:,.0f} req/tháng ({int(t['share']*100)}% của {req_month:,.0f}). " + '; '.join(parts) +
                '. Vertex AI Global endpoint, giá Standard/1M token, gọi qua Private Google Access.')
        if t['images']:
            note += f" Ảnh: {t['images']:,.0f} ảnh 1K x ${P['img_1k']} (1120 token x $30/1M) = {t['img_cost']:,.2f}."
        add('llm', f"LLM cấp {t['id'][1]} - {t['name']} (routing theo cấp, leo thang lên model tham chiếu)", note, t['cost'], EV_LLM[t['id']])
    S['tiers'] = tiers
    S['llm_total'] = sum(t['cost'] for t in tiers)

    # ---------------- Embedding ----------------
    st = STORAGE
    kb_chunks = st['kb_docs'] * st['chunks_per_doc']
    kb_tokens = kb_chunks * st['tokens_per_chunk']
    emb_initial_amort = kb_tokens / 12
    emb_churn = kb_tokens * st['kb_churn_month']
    emb_query = req_month * 0.9 * 60     # query embedding cũng dùng cho semantic router
    emb_tokens = emb_initial_amort + emb_churn + emb_query
    emb_cost = emb_tokens / 1e6 * P['emb']
    add('embedding', 'Gemini Embedding cho index KB, truy vấn RAG và semantic router',
        f"Index ban đầu {kb_tokens/1e9:.1f}B token ({st['kb_docs']:,} tài liệu x {st['chunks_per_doc']} chunk x {st['tokens_per_chunk']}) "
        f"chia 12 tháng = {emb_initial_amort/1e6:.0f}M; re-embed 10%/tháng = {emb_churn/1e6:.0f}M; query {emb_query/1e6:.0f}M "
        f"(90% req x 60 token). Tổng {emb_tokens/1e6:.0f}M x $0.15/1M = {emb_cost:,.2f}", emb_cost, 'E23')
    S.update(kb_chunks=kb_chunks, kb_tokens=kb_tokens)

    # ---------------- Compute (GKE Autopilot prod, regional multi-AZ) ----------------
    def pod_cost(vcpu_h, mem_h, kind='od'):
        if kind == 'cud':
            return vcpu_h * P['ap_vcpu_cud1'] + mem_h * P['ap_mem_cud1']
        if kind == 'spot':
            return vcpu_h * P['ap_vcpu_spot'] + mem_h * P['ap_mem_spot']
        return vcpu_h * P['ap_vcpu'] + mem_h * P['ap_mem']

    # cluster fee
    add('compute', 'GKE Autopilot cluster prod (regional, 3 zone, multi-AZ control plane 99.95%)',
        'Phí quản lý cluster $0.10/giờ x 730 giờ = 73.00; asia-southeast1', P['gke_fee_h'] * H_MONTH, 'E25')
    # API + orchestrator: baseline 2 replica 24/7 (CUD 1 năm) + 4 replica thêm giờ hành chính (on-demand), 1 vCPU / 2 GiB
    k = A['dau'] / 2000                      # hệ số tải so với đề
    nb = math.ceil(4 * k)
    base_v = 2 * 1 * H_MONTH; base_m = 2 * 2 * H_MONTH
    burst_v = nb * 1 * H_BIZ; burst_m = nb * 2 * H_BIZ
    c_api = pod_cost(base_v, base_m, 'cud') + pod_cost(burst_v, burst_m)
    add('compute', 'Pod API backend + orchestrator agent (web, chat streaming, điều phối tác vụ)',
        f"Baseline 2 pod x 1 vCPU/2 GiB x 730 giờ, CUD 1 năm (${P['ap_vcpu_cud1']}/vCPU-h, ${P['ap_mem_cud1']}/GiB-h) = "
        f"{pod_cost(base_v, base_m, 'cud'):,.2f}; thêm {nb} pod x 220 giờ hành chính on-demand (${P['ap_vcpu']}, ${P['ap_mem']}) = "
        f"{pod_cost(burst_v, burst_m):,.2f}. HPA theo RPS, trải 3 zone (HA)", c_api, 'E02')
    S['api_pods'] = '2 → 6 pod'

    # ---------------- Gateway (LiteLLM self-host trên GKE) ----------------
    gv = 2 * 1 * H_MONTH; gm = 2 * 2 * H_MONTH
    gbv = 1 * 1 * H_BIZ; gbm = 1 * 2 * H_BIZ
    c_gw = pod_cost(gv, gm, 'cud') + pod_cost(gbv, gbm)
    add('gateway', 'LLM gateway LiteLLM (OSS) 2-3 replica: routing, quota, rate limit, retry, fallback, log token',
        f"2 pod x 1 vCPU/2 GiB x 730 giờ CUD 1 năm = {pod_cost(gv, gm, 'cud'):,.2f} + 1 pod x 220 giờ on-demand = "
        f"{pod_cost(gbv, gbm):,.2f}; 2 zone khác nhau, không điểm lỗi đơn (HA); GKE Autopilot Singapore", c_gw, 'E02')

    # ---------------- Load balancer ----------------
    lb_gb = req_month * 80 / 1024 / 1024 + A['dau'] * A['days'] * 5 / 1024  # 80 KB/req + 5 MB file/user/ngày
    c_lb = P['lb_rule_h'] * H_MONTH + lb_gb * P['lb_data']
    add('load_balancer', 'Global external Application Load Balancer + managed TLS cert (prod + staging dùng chung rule)',
        f"Forwarding rule (5 rule đầu) $0.028/giờ x 730 = 20.44; data processed {lb_gb:,.0f} GiB x $0.009 = {lb_gb*P['lb_data']:,.2f}. "
        f"LB là dịch vụ phân tán của Google, không điểm lỗi đơn (HA multi-zone)", c_lb, 'E06')
    S['lb_gb'] = lb_gb

    # ---------------- AuthN ----------------
    c_idp = A['mau'] * P['idp_mau_t2'] + 50 * P['idp_mau_t2']
    add('authn', 'Identity Platform: SSO OIDC/SAML liên kết IdP tập đoàn (Entra ID + Google Workspace), MFA bắt buộc',
        f"Tier 2 OIDC/SAML: {A['mau']:,} MAU prod + 50 MAU staging = {A['mau']+50:,} x $0.015 = {c_idp:,.2f} "
        f"(tính toàn bộ MAU theo giá trả phí); MFA thực thi bằng Conditional Access của IdP gốc", c_idp, 'E11')

    # ---------------- AuthZ (OPA policy engine) ----------------
    av = 2 * 0.25 * H_MONTH; am = 2 * 0.5 * H_MONTH
    c_authz = pod_cost(av, am, 'cud')
    add('authz', 'Policy engine OPA (RBAC/ABAC) + lọc ACL tài liệu theo quyền gốc khi truy vấn',
        f"2 pod x 0.25 vCPU/0.5 GiB x 730 giờ, CUD 1 năm = {c_authz:,.2f}; ACL lưu cùng chunk trong pgvector "
        f"(lọc trước khi xếp hạng); scope OAuth tối thiểu cho từng connector", c_authz, 'E02')

    # ---------------- Database (Cloud SQL PostgreSQL HA) ----------------
    vcpu, mem = (4, 16) if k <= 1.25 else (8, 32)
    c_sql_inst = (vcpu * P['sql_ha_vcpu_cud1'] + mem * P['sql_ha_mem_cud1']) * H_MONTH
    chat_gib = req_month * st['chat_kb_per_req'] * st['chat_retention_months'] / 1024 / 1024
    db_ssd = 160 if k <= 1.25 else 300
    c_sql_ssd = db_ssd * P['sql_ssd_ha_h'] * H_MONTH
    add('database', 'Cloud SQL PostgreSQL Enterprise HA (primary + standby khác zone): user, chat, memory, token vault, audit index',
        f"HA {vcpu} vCPU/{mem} GB, CUD 1 năm: ({vcpu} x ${P['sql_ha_vcpu_cud1']} + {mem} x ${P['sql_ha_mem_cud1']}) x 730 = {c_sql_inst:,.2f}; failover tự động ~60s. "
        f"Lịch sử chat {chat_gib:,.0f} GiB/12 tháng", c_sql_inst, 'E03')
    add('database', 'Dung lượng SSD HA cho dữ liệu ứng dụng Cloud SQL',
        f"{db_ssd} GiB SSD HA x $0.000652055/GiB-h x 730 = {c_sql_ssd:,.2f}", c_sql_ssd, 'E26')
    S.update(chat_gib=chat_gib)

    # ---------------- Vector DB (pgvector trên cùng instance) ----------------
    vec_gib = kb_chunks * st['vector_bytes_per_chunk'] / 1024 ** 3
    vec_ssd = math.ceil(vec_gib * 2 / 10) * 10  # x2 cho HNSW + tăng trưởng
    c_vec = vec_ssd * P['sql_ssd_ha_h'] * H_MONTH
    add('vector_db', 'pgvector (HNSW, halfvec 768) trên Cloud SQL HA ở trên, lọc theo ACL + user_id',
        f"{kb_chunks/1e6:.1f}M vector x 4 KB = {vec_gib:,.1f} GiB, x2 cho index HNSW + tăng trưởng = {vec_ssd} GiB SSD HA "
        f"x $0.000652055 x 730 = {c_vec:,.2f}; CPU/RAM nằm trong dòng database", c_vec, 'E26')
    S.update(vec_gib=vec_gib)

    # ---------------- Object storage (workspace) ----------------
    ws_gib = A['dau'] * st['workspace_gib_per_user']
    st = dict(st, workspace_new_gib_month=st['workspace_new_gib_month'] * k)
    c_ws = ws_gib * P['gcs_asia_std']
    c_repl = st['workspace_new_gib_month'] * P['gcs_repl_asia']
    ops_a = A['dau'] * A['days'] * 40 / 1000       # 40 lượt ghi / user / ngày
    ops_b = A['dau'] * A['days'] * 150 / 1000
    c_ops = ops_a * P['gcs_ops_a_mr'] + ops_b * P['gcs_ops_b']
    add('object_storage', 'Cloud Storage multi-region ASIA: workspace riêng mỗi user (prefix + IAM + khóa riêng), quota 10 GB',
        f"{ws_gib:,.0f} GiB (TB 1 GB/user) x $0.026 = {c_ws:,.2f}; replication {st['workspace_new_gib_month']} GiB mới x $0.08 = {c_repl:,.2f}; "
        f"ops A {ops_a*1000/1e6:.2f}M x $0.01/1K + B {ops_b*1000/1e6:.1f}M x $0.0004/1K = {c_ops:,.2f}. Lifecycle xóa file tạm sau 30 ngày",
        c_ws + c_repl + c_ops, 'E05; E27; E28')

    # ---------------- Cache + queue ----------------
    c_redis = 1 * P['redis_std_m1'] * H_MONTH
    add('cache_queue', 'Memorystore Redis Standard 1 GB (replica khác zone, HA): cache phiên, rate limit, kết quả',
        f"1 GiB x $0.114/GiB-h x 730 = {c_redis:,.2f}; failover tự động", c_redis, 'E04')
    msgs = req_month * 1.0
    pub_gib = msgs * 4 / 1024 / 1024 * 2   # 4 KB/msg, publish + deliver
    c_pub = pub_gib / 1024 * P['pubsub_tib']
    add('cache_queue', 'Pub/Sub: hàng đợi agent chạy nền (cấp 4), job sandbox, thông báo xong việc; retry + dead-letter',
        f"{msgs/1e6:.1f}M message x 4 KB x 2 (publish + deliver) = {pub_gib:,.1f} GiB x $40/TiB = {c_pub:,.2f}", c_pub, 'E13')

    # ---------------- Sandbox ----------------
    runs = sum(req_month * t['share'] * t['sandbox'] for t in TIERS)
    sv = runs * SANDBOX['seconds'] / 3600 * SANDBOX['vcpu']
    sm = runs * SANDBOX['seconds'] / 3600 * SANDBOX['mem_gib']
    c_sb_spot = pod_cost(sv * SANDBOX['spot_share'], sm * SANDBOX['spot_share'], 'spot')
    c_sb_od = pod_cost(sv * (1 - SANDBOX['spot_share']), sm * (1 - SANDBOX['spot_share']))
    add('sandbox', 'Pod sandbox GKE Sandbox (gVisor) chạy code agent: không egress, chỉ mount workspace của đúng user, hủy sau khi chạy',
        f"{runs:,.0f} lượt/tháng x 45 giây x 1 vCPU/2 GiB = {sv:,.0f} vCPU-h, {sm:,.0f} GiB-h. 80% Spot Pod (${P['ap_vcpu_spot']}, ${P['ap_mem_spot']}) "
        f"= {c_sb_spot:,.2f}; 20% on-demand khi Spot bị thu hồi = {c_sb_od:,.2f}", c_sb_spot + c_sb_od, 'E02; E20')
    wv = SANDBOX['warm_pods'] * SANDBOX['warm_vcpu'] * H_BIZ; wm = SANDBOX['warm_pods'] * SANDBOX['warm_mem'] * H_BIZ
    c_warm = pod_cost(wv, wm)
    add('sandbox', 'Warm pool sandbox gVisor giờ hành chính (giảm cold start, giữ p95 TTFT dưới 3 giây)',
        f"4 pod x 0.5 vCPU/1 GiB x 220 giờ on-demand = {wv:,.0f} vCPU-h x $0.0549 + {wm:,.0f} GiB-h x $0.0060729 = {c_warm:,.2f}", c_warm, 'E02; E20')
    S.update(sandbox_runs=runs, sandbox_vcpu_h=sv)

    # ---------------- Connectors ----------------
    cv = 2 * 0.5 * H_MONTH; cm = 2 * 1 * H_MONTH
    c_conn_svc = pod_cost(cv, cm, 'cud')
    sv2 = 1 * 2 * H_BIZ; sm2 = 1 * 4 * H_BIZ   # KB chung không đổi theo DAU
    c_sync = pod_cost(sv2, sm2)
    conn_calls = sum(req_month * t['share'] * t['connector_calls'] for t in TIERS)
    add('connectors', 'Connector service: Gmail, Drive, Calendar, Docs/Sheets/Slides, Outlook, M365, OneDrive/SharePoint, Teams, Notion, Jira, Confluence',
        f"2 pod x 0.5 vCPU/1 GiB x 730 giờ CUD 1 năm = {c_conn_svc:,.2f}; {conn_calls/1e6:.1f}M lệnh gọi API/tháng bằng OAuth ủy nhiệm "
        f"của user, webhook + backoff theo rate limit; API SaaS nằm trong license hiện có của tập đoàn", c_conn_svc, 'E02')
    add('connectors', 'Worker đồng bộ + index KB chung (Confluence, Notion, SharePoint/Drive dùng chung) theo ACL gốc',
        f"1 pod x 2 vCPU/4 GiB x 220 giờ on-demand: 440 vCPU-h x $0.0549 + 880 GiB-h x $0.0060729 = {c_sync:,.2f}", c_sync, 'E02')
    S.update(conn_calls=conn_calls)

    # ---------------- Secrets / KMS ----------------
    kms_ops = conn_calls + A['dau'] * A['days'] * 60   # giải mã token + unwrap DEK workspace
    c_kms = 8 * P['kms_soft_h'] * H_MONTH + 2 * P['kms_hsm_h'] * H_MONTH + kms_ops / 1e4 * P['kms_op_10k']
    add('secrets_kms', 'Cloud KMS: CMEK cho Cloud SQL, GCS, log; khóa HSM bọc token vault OAuth (envelope encryption)',
        f"8 key SOFTWARE x $0.06/tháng = 0.48; 2 key HSM x $1.00/tháng = 2.00; {kms_ops/1e6:.2f}M crypto ops x $0.03/10K = "
        f"{kms_ops/1e4*P['kms_op_10k']:,.2f}. Xoay khóa 90 ngày", c_kms, 'E09')
    sm_ops = 2_000_000
    c_sm = 60 * P['sm_version_h'] * H_MONTH + sm_ops / 1e4 * P['sm_access_10k']
    add('secrets_kms', 'Secret Manager: API key, client secret OAuth, mật khẩu DB (prod + staging)',
        f"60 version x $0.06 = 3.60; 2M lượt truy cập x $0.03/10K = 6.00 (tính toàn bộ theo giá trả phí)", c_sm, 'E10')

    # ---------------- Governance ----------------
    guard = sum(req_month * t['share'] * t['guard_tokens'] for t in TIERS) + emb_churn + emb_initial_amort
    c_guard = guard / 1e6 * P['armor_model_per_m']
    add('governance', 'Model Armor: guardrail vào/ra, phát hiện prompt injection trong email/tài liệu, lọc PII cơ bản',
        f"Quét prompt user + nội dung connector chưa tin cậy + output: {guard/1e9:.2f}B token/tháng x $0.10/1M = {c_guard:,.2f}. "
        f"Nội dung KB quét 1 lần khi index", c_guard, 'E14')
    dlp_gb = 7
    c_dlp = dlp_gb * P['dlp_gb']
    add('governance', 'Sensitive Data Protection: phân loại dữ liệu khi index, che PII trước khi gửi email/tạo ticket ra ngoài',
        f"{dlp_gb} GB nội dung/tháng (6 GB tài liệu mới + 1 GB hành động ghi) x $3/GB = {c_dlp:,.2f}", c_dlp, 'E15')
    eval_in, eval_out = 6000 * 4000, 6000 * 300
    c_eval = eval_in / 1e6 * P['f38flex_in'] + eval_out / 1e6 * P['f38flex_out']
    add('governance', 'Cổng eval: chạy bộ test vàng trước khi đổi model/prompt, LLM-judge bằng model tham chiếu',
        f"4 lần/tháng x 5 cấp x 300 case = 6.000 case x (4K in, 300 out) trên Gemini 3.8 Flash Flex/Batch: 24M x $0.75 + 1.8M x $3.75 = {c_eval:,.2f}",
        c_eval, 'E24')
    audit_gib = req_month * 3 / 1024 / 1024
    c_audit = audit_gib * P['log_ingest_gb'] + audit_gib * 11 * P['log_retention_gb'] + audit_gib * 12 * P['gcs_sg_archive']
    add('governance', 'Audit log 12 tháng: log bucket khóa retention 365 ngày + bản sao Archive (bucket lock)',
        f"{audit_gib:,.1f} GiB/tháng x $0.50 ingest = {audit_gib*P['log_ingest_gb']:,.2f}; lưu > 30 ngày: {audit_gib*11:,.0f} GiB x $0.01 = "
        f"{audit_gib*11*P['log_retention_gb']:,.2f}; Archive {audit_gib*12:,.0f} GiB x $0.0015 = {audit_gib*12*P['gcs_sg_archive']:,.2f}", c_audit, 'E12; E29')

    # ---------------- Network ----------------
    egress_gib = req_month * 50 / 1024 / 1024 + 150
    nat_gib = conn_calls * 30 / 1024 / 1024 + 50
    c_nat = 12 * P['nat_vm_h'] * H_MONTH + 2 * P['nat_ip_h'] * H_MONTH + nat_gib * P['nat_data']
    add('network', 'Cloud NAT cho egress tới API SaaS (chỉ pod connector được phép), IP tĩnh để SaaS allowlist',
        f"12 node x $0.0014 x 730 = 12.26; 2 IP x $0.005 x 730 = 7.30; {nat_gib:,.0f} GiB x $0.045 = {nat_gib*P['nat_data']:,.2f}",
        c_nat, 'E07')
    c_egress = egress_gib * P['egress_asia'] + 300 * P['interzone']
    add('network', 'Internet egress tới người dùng (Việt Nam) + traffic inter-zone giữa các AZ',
        f"{egress_gib:,.0f} GiB ra Asia x $0.12 = {egress_gib*P['egress_asia']:,.2f}; inter-zone 300 GiB x $0.01 = 3.00", c_egress, 'E30; E31')
    armor_req = 5.0
    c_armor = P['armor_policy_h'] * H_MONTH + 10 * P['armor_rule_h'] * H_MONTH + armor_req * P['armor_req_per_m']
    add('network', 'Cloud Armor WAF (OWASP rules, rate limit theo IP) trước Load Balancer',
        f"1 policy x $5/tháng + 10 rule x $1/tháng + {armor_req:.0f}M request x $0.75/1M = {c_armor:,.2f}", c_armor, 'E08')
    add('network', 'VPC riêng, Private Google Access + VPC Service Controls tới Vertex AI (private endpoint, không ra internet)',
        'Không phát sinh phí riêng: nằm trong dòng Cloud NAT/egress ở trên (traffic tới Google API đi trong mạng Google)', 0, 'E06; E19')

    # ---------------- Monitoring ----------------
    log_gib = 40
    samples_m = 5000 * 2 * 60 * H_MONTH / 1e6
    spans_m = req_month * 20 / 1e6
    c_mon = log_gib * P['log_ingest_gb'] + samples_m * P['prom_per_m_samples'] + spans_m * P['trace_per_m_spans']
    add('monitoring', 'Cloud Logging + Managed Prometheus + Cloud Trace; LLM observability (token, chi phí, latency theo user và đơn vị)',
        f"Log {log_gib} GiB x $0.50 = 20.00; metric 5.000 series x 2/phút x 730 giờ = {samples_m:,.0f}M sample x $0.06 = {samples_m*P['prom_per_m_samples']:,.2f}; "
        f"trace {spans_m:,.0f}M span x $0.20 = {spans_m*P['trace_per_m_spans']:,.2f}. Spend log của gateway lưu trong database", c_mon, 'E12; E32; E33')

    # ---------------- Backup / DR ----------------
    bk_gib = 400
    c_bk = bk_gib * P['sql_backup_h'] * H_MONTH
    add('backup_dr', 'Backup Cloud SQL: tự động hằng ngày + on-demand mỗi giờ (RPO 1 giờ) + PITR 7 ngày, lưu ở asia-southeast2',
        f"{bk_gib} GiB backup (incremental) x $0.000153425/GiB-h x 730 = {c_bk:,.2f}; RTO 4 giờ: dựng lại bằng Terraform ở Jakarta", c_bk, 'E26')
    drill_v, drill_m = 4 * 4, 16 * 4
    c_drill = drill_v * P['sql_vcpu'] + drill_m * P['sql_mem'] + 50
    c_drill = (drill_v * P['sql_vcpu'] + drill_m * P['sql_mem'])
    add('backup_dr', 'Diễn tập khôi phục hằng tháng: restore backup vào instance tạm 4 vCPU/16 GB trong 4 giờ',
        f"(4 vCPU x $0.0578 + 16 GB x $0.0098) x 4 giờ = {c_drill:,.2f}; GCS multi-region ASIA tự sao chép 2 vùng (nằm trong dòng object_storage)",
        c_drill, 'E03')

    # ---------------- CI/CD + staging ----------------
    build_min = 20 * A['days'] * 8
    c_build = build_min * P['build_min'] + 30 * P['ar_gb']
    add('cicd', 'Cloud Build pipeline (test, scan image, deploy) + Artifact Registry; IaC Terraform',
        f"{build_min:,} phút x $0.006 = {build_min*P['build_min']:,.2f}; registry 30 GiB x $0.10 = 3.00", c_build, 'E17; E16')
    stg_fee = P['gke_fee_h'] * H_MONTH
    stg_pods = pod_cost(3 * H_BIZ, 6 * H_BIZ)
    add('cicd', 'Staging: GKE Autopilot cluster riêng, pod chỉ chạy giờ hành chính (scale về 0 ngoài giờ)',
        f"Phí cluster 73.00 + pod 3 vCPU/6 GiB x 220 giờ = {3*H_BIZ} vCPU-h x $0.0549 + {6*H_BIZ} GiB-h x $0.0060729 = {stg_pods:,.2f}",
        stg_fee + stg_pods, 'E02; E25')
    stg_sql = (1 * P['sql_vcpu'] + 3.75 * P['sql_mem']) * H_BIZ + 20 * P['sql_ssd_h'] * H_MONTH
    add('cicd', 'Staging: Cloud SQL PostgreSQL 1 vCPU/3.75 GB single-zone, tắt ngoài giờ hành chính',
        f"(1 x $0.0578 + 3.75 x $0.0098) x 220 giờ = {(1*P['sql_vcpu']+3.75*P['sql_mem'])*H_BIZ:,.2f}; 20 GiB SSD x $0.000326027 x 730 = "
        f"{20*P['sql_ssd_h']*H_MONTH:,.2f}", stg_sql, 'E03; E34')
    stg_llm = 300 * 3000 * 22 / 1e6 * P['fl_in'] + 300 * 600 * 22 / 1e6 * P['fl_out']
    add('cicd', 'Staging: lưu lượng LLM test (smoke test + QA nội bộ) trên Gemini 3.1 Flash-Lite',
        f"300 req/ngày x 22 ngày x (3K in x $0.25 + 600 out x $1.5)/1M = {stg_llm:,.2f}", stg_llm, 'E01')

    # ---------------- Ops labor ----------------
    fte, rate = (1.5 if k <= 1.25 else 2.0), 2800
    add('ops_labor', 'Nhân sự vận hành: 1 SRE/platform + 0.5 security/MLOps, trực giờ hành chính, on-call luân phiên',
        f"{fte} FTE x {rate:,} USD/tháng (lương + bảo hiểm + phúc lợi, mặt bằng kỹ sư Việt Nam) = {fte*rate:,.2f}", fte * rate, 'NA')

    # ---------------- Licenses / support ----------------
    cloud_sub = sum(r['chi_phi'] for r in rows if r['component'] != 'ops_labor')
    c_sup = max(29, cloud_sub * P['support_pct'])
    add('licenses', 'Google Cloud Standard Support (P2 phản hồi 4 giờ) cho môi trường production',
        f"3% x chi phí cloud {cloud_sub:,.2f} = {c_sup:,.2f} (tối thiểu $29); LiteLLM, OPA, gVisor là mã nguồn mở, không có phí license",
        c_sup, 'E18')

    total = r2(sum(r['chi_phi'] for r in rows))
    S['total'] = total
    S['per_dau'] = total / A['dau']
    S['per_req'] = total / req_month
    return rows, S


if __name__ == '__main__':
    rows, S = build()
    os.makedirs(os.path.join(HERE, 'out'), exist_ok=True)
    by = {}
    for r in rows:
        by[r['component']] = by.get(r['component'], 0) + r['chi_phi']
    for k, v in sorted(by.items(), key=lambda kv: -kv[1]):
        print(f'{k:15s} {v:10,.2f}')
    print(f"{'TOTAL':15s} {S['total']:10,.2f}   /DAU {S['per_dau']:.2f}   /req {S['per_req']:.4f}")
    print(f"req/month {S['req_month']:,.0f}  peak rps {S['peak_rps']:.2f}  burst {S['burst_rps']:.1f}  in tok/s {S['peak_in_tps']:,.0f}  out tok/s {S['peak_out_tps']:,.0f}")
    print(f"tokens in {S['tin_month']/1e9:.2f}B out {S['tout_month']/1e9:.2f}B  per req in {S['per_req_in']:,.0f} out {S['per_req_out']:,.0f}")
    print(f"sandbox runs {S['sandbox_runs']:,.0f}  vCPU-h {S['sandbox_vcpu_h']:,.0f}  connector calls {S['conn_calls']:,.0f}  vectors {S['kb_chunks']:,}")
    for t in S['tiers']:
        print(f"  {t['id']} {t['name']:20s} req {t['req']:>9,.0f}  cost {t['cost']:9,.2f}")
    json.dump(dict(rows=rows, sizing={k: v for k, v in S.items() if k != 'tiers'},
                   tiers=[{k: v for k, v in t.items()} for t in S['tiers']], assumptions=A, prices=P, evidence=EVIDENCE),
              open(os.path.join(HERE, 'out', 'model.json'), 'w'), ensure_ascii=False, indent=1)
