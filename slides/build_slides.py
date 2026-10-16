"""Generate slides/slides.html from the cost model (numbers always match the quote).

usage: python3 slides/build_slides.py [GROUP]  then  node tools/render_pdf.js slides/slides.html deliverables/G00_slide.pdf
"""
import json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'model'))
import vbot_model as M

GROUP = sys.argv[1] if len(sys.argv) > 1 else 'G00'
rows, S = M.build()
SC = json.load(open(os.path.join(ROOT, 'model', 'out', 'scenarios.json')))
assert abs(SC['base'] - S['total']) < 0.01, 'run model/scenarios.py first'
TOTAL = S['total']
by = {}
for r in rows:
    by[r['component']] = by.get(r['component'], 0) + r['chi_phi']


def usd(x, d=0):
    return '$' + f'{x:,.{d}f}'


def vn(x, d=0):
    t = f'{x:,.{d}f}'
    return t.replace(',', '_').replace('.', ',').replace('_', '.')


def pct(x):
    return f'{x * 100:.0f}%'


tiers = {t['id']: t for t in S['tiers']}
llm_noroute = SC['levers'][0]['without'] - (TOTAL - by['llm'])
top5 = sorted(by.items(), key=lambda kv: -kv[1])[:5]
NAMES = {'llm': 'LLM (5 cấp)', 'ops_labor': 'Nhân sự vận hành', 'database': 'Cloud SQL HA', 'governance': 'Governance',
         'licenses': 'Support GCP', 'sandbox': 'Sandbox gVisor', 'compute': 'GKE compute', 'cicd': 'CI/CD + staging'}

CSS = r"""
@import url('https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500;700&display=swap');
:root{--ink:#0d2a33;--teal:#0f766e;--teal2:#14b8a6;--soft:#eef5f4;--line:#d5e2e0;--muted:#5b6b70;--amber:#f59e0b;--amberbg:#fff4dc;--red:#b42318;--white:#fff}
*{box-sizing:border-box;margin:0;padding:0}
html,body{background:#fff}
body{font-family:'Be Vietnam Pro',Arial,sans-serif;color:var(--ink);-webkit-print-color-adjust:exact;print-color-adjust:exact}
@page{size:1280px 720px;margin:0}
.slide{width:1280px;height:720px;position:relative;overflow:hidden;page-break-after:always;padding:46px 56px 40px;background:#fff}
.slide.dark{background:var(--ink);color:#fff}
h1{font-size:40px;font-weight:800;letter-spacing:-.5px;line-height:1.12}
h2{font-size:30px;font-weight:800;letter-spacing:-.3px;line-height:1.15;margin-bottom:6px}
.kicker{font:600 13px 'JetBrains Mono',monospace;color:var(--teal);text-transform:uppercase;letter-spacing:1.5px;margin-bottom:8px}
.dark .kicker{color:var(--teal2)}
.lead{font-size:17px;color:var(--muted);margin-bottom:18px;max-width:1080px}
.dark .lead{color:#b9cfd0}
.foot{position:absolute;left:56px;right:56px;bottom:16px;display:flex;justify-content:space-between;font-size:11px;color:#8a9a9e}
.dark .foot{color:#6f8c90}
.code{display:inline-block;font:700 11px 'JetBrains Mono',monospace;background:var(--amberbg);color:#8a5300;border-radius:4px;padding:1px 6px;vertical-align:middle}
.grid{display:grid;gap:16px}
.card{background:var(--soft);border-radius:12px;padding:16px 18px}
.card h3{font-size:17px;font-weight:700;margin-bottom:8px}
.card p,.card li{font-size:15px;line-height:1.5;color:#28434a}
.card ul{padding-left:18px}
.card li{margin-bottom:4px}
.big{font-size:56px;font-weight:800;letter-spacing:-1.5px;line-height:1}
.mid{font-size:30px;font-weight:800;letter-spacing:-.5px}
.lbl{font-size:13px;color:var(--muted);margin-top:4px}
.dark .lbl{color:#9fb8ba}
table.t{width:100%;border-collapse:collapse;font-size:14.5px}
table.t th{text-align:left;font-weight:700;color:var(--muted);font-size:12px;text-transform:uppercase;letter-spacing:.5px;padding:7px 8px;border-bottom:2px solid var(--line)}
table.t td{padding:7px 8px;border-bottom:1px solid var(--line);vertical-align:top;line-height:1.35}
table.t td.n{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
.pill{display:inline-block;border-radius:999px;padding:3px 10px;font-size:12px;font-weight:600;background:#dff3ef;color:var(--teal);margin:2px 4px 2px 0}
.dark .pill{background:#164049;color:#9ff0e3}
.bar{height:22px;border-radius:5px;background:var(--teal)}
.note{font-size:12px;color:var(--muted)}
.step{display:flex;gap:12px;align-items:flex-start;margin-bottom:14px}
.num{flex:0 0 26px;height:26px;border-radius:50%;background:var(--teal);color:#fff;font-weight:700;font-size:13px;display:flex;align-items:center;justify-content:center}
.step b{font-size:16px}
.step span{font-size:14.5px;color:#3d5559}
/* architecture */
.arch{position:absolute;left:56px;top:150px;width:1168px;height:520px}
.box{position:absolute;border-radius:10px;padding:8px 10px;font-size:12.5px;line-height:1.3;background:#fff;border:1.5px solid var(--line)}
.box b{display:block;font-size:13.5px;margin-bottom:2px}
.zone{position:absolute;border-radius:14px;border:2px dashed #9cc9c3;background:#f6fbfa}
.zone .zt{position:absolute;top:-11px;left:14px;background:#fff;padding:0 8px;font:700 11.5px 'JetBrains Mono',monospace;color:var(--teal)}
.box.ext{background:#f3f4f6;border-color:#d1d5db}
.box.ai{background:#eef2ff;border-color:#c7d2fe}
.box.sec{background:#fff7ed;border-color:#fed7aa}
"""


def foot(n):
    return f'<div class="foot"><span>VBot Workplace · {GROUP} · Production Capstone</span><span>{n}</span></div>'


slides = []

# 0. Title
slides.append(f"""
<section class="slide dark">
  <div class="kicker">Track 2 · Production Capstone · {GROUP}</div>
  <h1 style="font-size:58px;margin-top:70px;max-width:980px">VBot Workplace: trợ lý AI văn phòng cho 2.000 người mỗi ngày</h1>
  <p class="lead" style="font-size:21px;margin-top:18px">Google Cloud asia-southeast1 · Vertex AI · GKE Autopilot + gVisor · đủ 19 thành phần bắt buộc, đạt H1–H8</p>
  <div style="display:flex;gap:70px;margin-top:70px">
    <div><div class="big" style="color:#5eead4">{usd(TOTAL, 2)}</div><div class="lbl">tổng chi phí / tháng (USD, chưa VAT)</div></div>
    <div><div class="big">{usd(TOTAL / 2000, 2)}</div><div class="lbl">mỗi người dùng hoạt động / tháng</div></div>
    <div><div class="big">{usd(TOTAL / S['req_month'] * 1000, 2)}</div><div class="lbl">mỗi 1.000 request</div></div>
  </div>
  {foot('')}
</section>""")

# 1. Executive summary
slides.append(f"""
<section class="slide">
  <div class="kicker">Tóm tắt</div>
  <h2>Rẻ nhờ routing model, không nhờ cắt thành phần</h2>
  <p class="lead">{usd(TOTAL, 2)}/tháng = {usd(by['llm'])} LLM ({pct(by['llm']/TOTAL)}) + {usd(by['ops_labor'])} nhân sự ({pct(by['ops_labor']/TOTAL)}) + {usd(TOTAL-by['llm']-by['ops_labor'])} hạ tầng còn lại. Mọi con số lấy từ một mô hình sizing duy nhất, khớp dòng TOTAL trong báo giá.</p>
  <div class="grid" style="grid-template-columns:repeat(3,1fr)">
    <div class="card"><h3>1 · API theo cấp, không tự host GPU</h3><p>Flash-Lite cho email/tài liệu, gpt-oss-120b cho code và lập kế hoạch, Gemini 3.8 Flash làm model tham chiếu và leo thang. Tiết kiệm <b>{usd(-0 + SC['levers'][0]['saving'])}</b>/tháng so với dùng model tham chiếu cho mọi request.</p></div>
    <div class="card"><h3>2 · Một cluster, cô lập bằng gVisor</h3><p>GKE Autopilot regional 3 zone chạy API, gateway, connector, policy và sandbox. Code của agent chạy trong pod gVisor không egress, 80% trên Spot Pod: sandbox chỉ <b>{usd(by['sandbox'])}</b>/tháng.</p></div>
    <div class="card"><h3>3 · Dữ liệu tách theo người dùng</h3><p>Cloud SQL HA + pgvector lọc theo ACL gốc và user_id, workspace GCS multi-region ASIA với khóa riêng, token OAuth ủy nhiệm bọc bằng khóa HSM. RTO 4 giờ, RPO 1 giờ.</p></div>
  </div>
  <div style="margin-top:22px">
    <div class="note" style="margin-bottom:6px">Ràng buộc cứng</div>
    <span class="pill">H1 một cloud, Vertex AI qua Private Google Access</span><span class="pill">H2 SSO OIDC/SAML + MFA, OPA, OAuth ủy nhiệm</span><span class="pill">H3 gVisor, deny egress</span><span class="pill">H4 Model Armor + xác nhận hành động ghi</span><span class="pill">H5 CMEK, DLP, audit 12 tháng</span><span class="pill">H6 p95 TTFT ≤ 3 giây, agent ≤ 10 phút</span><span class="pill">H7 multi-AZ, RTO 4h/RPO 1h</span><span class="pill">H8 cổng eval ≥ 95%, quota + ngân sách</span>
  </div>
  <div style="margin-top:26px">
    <div class="note" style="margin-bottom:8px">Cơ cấu {usd(TOTAL, 2)}/tháng</div>
    <div style="display:flex;height:46px;border-radius:8px;overflow:hidden;font-size:14px;font-weight:700;color:#fff">
      <div style="width:{by['llm']/TOTAL*100:.2f}%;background:#0f766e;display:flex;align-items:center;padding-left:12px">LLM {usd(by['llm'])}</div>
      <div style="width:{by['ops_labor']/TOTAL*100:.2f}%;background:#0d2a33;display:flex;align-items:center;padding-left:12px">Nhân sự {usd(by['ops_labor'])}</div>
      <div style="flex:1;background:#f59e0b;display:flex;align-items:center;padding-left:12px;color:#3b2600">Hạ tầng {usd(TOTAL-by['llm']-by['ops_labor'])}</div>
    </div>
  </div>
  {foot(2)}
</section>""")

# 2. Assumptions
tier_rows = ''
for t in M.TIERS:
    tt = tiers[t['id']]
    tin = sum(c['tin'] * c['share'] for c in t['calls'])
    tout = sum(c['tout'] * c['share'] for c in t['calls'])
    tier_rows += (f"<tr><td>{t['id']} {t['name']}</td><td class='n'>{pct(t['share'])}</td><td class='n'>{vn(tt['req'])}</td>"
                  f"<td class='n'>{vn(tin)}</td><td class='n'>{vn(tout)}</td><td class='n'>{vn(t['sandbox'], 1)}</td><td class='n'>{usd(tt['cost'])}</td></tr>")
slides.append(f"""
<section class="slide">
  <div class="kicker">Giả định và ước lượng tải</div>
  <h2>Từ 2.000 DAU ra 1,1 triệu request và 12,3 tỷ token mỗi tháng</h2>
  <div class="grid" style="grid-template-columns:400px 1fr;gap:28px;margin-top:14px">
    <div>
      <div class="step"><div class="num">1</div><div><b>2.000 × 25 req × 22 ngày = {vn(S['req_month'])} req/tháng</b><br><span>25 req/người/ngày gồm cả hỏi lại; khớp mức REQ_PER_USER của đề</span></div></div>
      <div class="step"><div class="num">2</div><div><b>Cao điểm {vn(S['peak_rps'], 1)} req/s, đỉnh {S['burst_rps']:.0f} req/s</b><br><span>18% request/ngày rơi vào 9–10h; × 2 đỉnh theo phút; ~{S['concurrent_streams']:.0f} phiên streaming đồng thời</span></div></div>
      <div class="step"><div class="num">3</div><div><b>{vn(S['per_req_in'])} token vào, {vn(S['per_req_out'])} token ra / req</b><br><span>{vn(S['peak_in_tps'])} token vào/s, {vn(S['peak_out_tps'])} token ra/s giờ cao điểm</span></div></div>
      <div class="step"><div class="num">4</div><div><b>{vn(S['sandbox_runs'])} lượt sandbox/tháng</b><br><span>45 giây × 1 vCPU/2 GiB = {vn(S['sandbox_vcpu_h'])} vCPU-giờ</span></div></div>
      <div class="step"><div class="num">5</div><div><b>Lưu trữ</b><br><span>Workspace 2.000 GiB (TB 1 GB/người, quota 10 GB) · KB 300k tài liệu = 2,4M vector ({vn(S['vec_gib'], 1)} GiB) · chat 12 tháng {S['chat_gib']:.0f} GiB · {vn(S['conn_calls']/1e6, 1)}M lệnh gọi connector</span></div></div>
    </div>
    <div>
      <table class="t"><tr><th>Cấp tác vụ</th><th style="text-align:right">Tỉ lệ</th><th style="text-align:right">Req/tháng</th><th style="text-align:right">Token vào</th><th style="text-align:right">Token ra</th><th style="text-align:right">Sandbox</th><th style="text-align:right">LLM/tháng</th></tr>{tier_rows}
      <tr><td><b>Tổng</b></td><td class='n'>100%</td><td class='n'><b>{vn(S['req_month'])}</b></td><td class='n'>{vn(S['tin_month']/1e9, 2)} tỷ</td><td class='n'>{vn(S['tout_month']/1e9, 2)} tỷ</td><td class='n'></td><td class='n'><b>{usd(by['llm'])}</b></td></tr></table>
      <p class="note" style="margin-top:10px">Token/req gộp mọi lần gọi LLM: system prompt, RAG, lịch sử, các bước agent và phần leo thang. Cache ngầm 25–60% prefix theo cấp. Chi tiết công thức ở sheet GiaDinh của báo giá.</p>
      <div class="grid" style="grid-template-columns:1fr 1fr 1fr;gap:12px;margin-top:16px">
        <div class="card"><h3>Mạng</h3><p>LB {vn(S['lb_gb'])} GiB/tháng (80 KB/req + 5 MB file/người/ngày); egress tới người dùng ~{vn(S['req_month']*50/1024/1024+150)} GiB</p></div>
        <div class="card"><h3>Log, audit</h3><p>App + GKE 40 GiB/tháng; audit ~{vn(S['req_month']*3/1024/1024, 1)} GiB/tháng, giữ 12 tháng</p></div>
        <div class="card"><h3>Ảnh cấp 5</h3><p>40% request thiết kế cần ảnh: {vn(tiers['L5']['images'])} ảnh 1K/tháng, quota 15 ảnh/người</p></div>
      </div>
    </div>
  </div>
  {foot(3)}
</section>""")

# 3. Architecture
slides.append(f"""
<section class="slide">
  <div class="kicker">Kiến trúc tổng thể</div>
  <h2>Một region, ba zone, mỗi hộp là một dòng báo giá</h2>
  <p class="lead" style="margin-bottom:0">asia-southeast1 (Singapore): gần Việt Nam, đủ dịch vụ; model gọi qua Vertex AI Global endpoint trong mạng Google.</p>
  <div class="arch">
    <svg width="1168" height="520" style="position:absolute;left:0;top:0" fill="none" stroke="#7aa9a3" stroke-width="2">
      <defs><marker id="a" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8z" fill="#7aa9a3"/></marker></defs>
      <path d="M120 70 H178" marker-end="url(#a)"/><path d="M120 190 H178" marker-end="url(#a)"/>
      <path d="M346 120 H392" marker-end="url(#a)"/>
      <path d="M868 66 H930" marker-end="url(#a)"/><path d="M868 186 H930" marker-end="url(#a)"/>
      <path d="M868 300 H930" marker-end="url(#a)"/>
      <path d="M630 330 V378" marker-end="url(#a)"/>
    </svg>
    <div class="box ext" style="left:0;top:40px;width:120px"><b>Nhân viên</b>Web, add-in Outlook/Gmail</div>
    <div class="box ext" style="left:0;top:160px;width:120px"><b>IdP tập đoàn</b>Entra ID, Google Workspace, MFA</div>
    <div class="box sec" style="left:180px;top:20px;width:166px"><b>Cloud Armor + LB</b><span class="code">network</span> <span class="code">load_balancer</span><br>WAF, TLS, rate limit</div>
    <div class="box sec" style="left:180px;top:140px;width:166px"><b>Identity Platform</b><span class="code">authn</span><br>OIDC/SAML broker</div>
    <div class="zone" style="left:392px;top:16px;width:476px;height:316px"><span class="zt">GKE Autopilot regional · 3 zone · compute</span></div>
    <div class="box" style="left:408px;top:40px;width:212px"><b>API + orchestrator</b><span class="code">compute</span><br>chat streaming, agent loop, 2→6 pod</div>
    <div class="box" style="left:640px;top:40px;width:212px"><b>LLM gateway LiteLLM</b><span class="code">gateway</span><br>routing, quota, retry, fallback, log token</div>
    <div class="box" style="left:408px;top:126px;width:212px"><b>Policy OPA</b><span class="code">authz</span><br>RBAC/ABAC, ACL tài liệu</div>
    <div class="box" style="left:640px;top:126px;width:212px"><b>Connector service</b><span class="code">connectors</span><br>OAuth ủy nhiệm, webhook, sync KB</div>
    <div class="box sec" style="left:408px;top:212px;width:444px"><b>Sandbox pool gVisor (Spot)</b><span class="code">sandbox</span> chạy code agent, xuất DOCX/XLSX/PPTX, render sơ đồ · deny egress · mount workspace của đúng 1 user · hủy sau khi chạy</div>
    <div class="box ai" style="left:930px;top:20px;width:238px"><b>Vertex AI</b><span class="code">llm</span> <span class="code">embedding</span><br>Gemini 3.1 Flash-Lite, Gemini 3.8 Flash, gpt-oss-120b, Flash-Lite Image, Gemini Embedding</div>
    <div class="box sec" style="left:930px;top:146px;width:238px"><b>Model Armor + SDP + eval</b><span class="code">governance</span><br>guardrail, prompt injection, DLP, audit</div>
    <div class="box ext" style="left:930px;top:262px;width:238px"><b>SaaS qua Cloud NAT</b><span class="code">network</span><br>Gmail, Drive, Outlook, M365, Teams, Notion, Jira, Confluence</div>
    <div class="box" style="left:392px;top:380px;width:150px"><b>Cloud SQL HA</b><span class="code">database</span> <span class="code">vector_db</span><br>PostgreSQL + pgvector</div>
    <div class="box" style="left:556px;top:380px;width:150px"><b>Redis HA + Pub/Sub</b><span class="code">cache_queue</span><br>phiên, rate limit, hàng đợi agent</div>
    <div class="box" style="left:720px;top:380px;width:148px"><b>GCS ASIA</b><span class="code">object_storage</span><br>workspace riêng</div>
    <div class="box sec" style="left:180px;top:270px;width:166px"><b>KMS + Secret Manager</b><span class="code">secrets_kms</span><br>CMEK, token vault HSM</div>
    <div class="box" style="left:180px;top:380px;width:196px"><b>Backup / DR</b><span class="code">backup_dr</span><br>backup mỗi giờ sang asia-southeast2</div>
    <div class="box" style="left:0;top:270px;width:166px"><b>Observability</b><span class="code">monitoring</span><br>Logging, Prometheus, Trace</div>
    <div class="box" style="left:0;top:380px;width:166px"><b>CI/CD + staging</b><span class="code">cicd</span><br>Cloud Build, Artifact Registry, Terraform</div>
    <div class="box" style="left:930px;top:380px;width:238px"><b>Vận hành + support</b><span class="code">ops_labor</span> <span class="code">licenses</span><br>1,5 FTE, Standard Support</div>
  </div>
  {foot(4)}
</section>""")

# 4. Request flow
slides.append(f"""
<section class="slide">
  <div class="kicker">Luồng một request</div>
  <h2>"Tóm tắt thread này và soạn trả lời" đi qua 9 bước</h2>
  <div class="grid" style="grid-template-columns:1fr 1fr;gap:34px;margin-top:16px">
    <div>
      <div class="step"><div class="num">1</div><div><b>SSO</b> <span class="code">authn</span><br><span>Identity Platform chuyển sang Entra ID/Google, MFA theo Conditional Access, cấp phiên 8 giờ</span></div></div>
      <div class="step"><div class="num">2</div><div><b>Cloud Armor → LB → API</b> <span class="code">load_balancer</span><br><span>WAF, rate limit theo IP; API kiểm quota user trong Redis</span></div></div>
      <div class="step"><div class="num">3</div><div><b>OPA</b> <span class="code">authz</span><br><span>vai trò + đơn vị + cấp tác vụ được phép; danh sách tool cho phiên này</span></div></div>
      <div class="step"><div class="num">4</div><div><b>Connector đọc thread bằng token của chính user</b> <span class="code">connectors</span><br><span>giải mã refresh token qua KMS, scope gmail.readonly; KB chung lọc theo ACL trong pgvector</span></div></div>
      <div class="step"><div class="num">5</div><div><b>Model Armor quét prompt + nội dung email</b> <span class="code">governance</span><br><span>đánh dấu nội dung ngoài là dữ liệu, không phải chỉ dẫn</span></div></div>
    </div>
    <div>
      <div class="step"><div class="num">6</div><div><b>Gateway chọn model theo cấp</b> <span class="code">gateway</span><br><span>semantic router (embedding) → Gemini 3.1 Flash-Lite; khó → Gemini 3.8 Flash</span></div></div>
      <div class="step"><div class="num">7</div><div><b>Stream câu trả lời</b> <span class="code">llm</span><br><span>Model Armor quét output; ghi token + chi phí theo user và đơn vị</span></div></div>
      <div class="step"><div class="num">8</div><div><b>Hành động ghi cần xác nhận</b><br><span>gửi email, tạo ticket, xóa file: hiện bản nháp, user bấm xác nhận; DLP che PII trước khi gửi</span></div></div>
      <div class="step"><div class="num">9</div><div><b>Audit + lưu lịch sử</b> <span class="code">database</span><br><span>Cloud SQL (chat, memory theo user_id), audit log 12 tháng</span></div></div>
      <div class="card" style="margin-top:12px;background:#eef2ff"><h3>Tác vụ nền cấp 3–4</h3><p>API → Pub/Sub → worker agent (gpt-oss lập kế hoạch, Flex) → sandbox gVisor / connector → kết quả vào workspace → thông báo qua Chat/email. Retry 3 lần, hủy được, timeout 10 phút.</p></div>
      <div class="card" style="margin-top:12px"><h3>Ngân sách p95 TTFT ≤ 3 giây (H6)</h3><p>auth + quota 80 ms · OPA 10 ms · connector 600 ms · pgvector 120 ms · Model Armor 200 ms · gateway 20 ms · TTFT model ~1.000 ms → <b>~2,0 giây</b>, còn 1 giây dự phòng.</p></div>
    </div>
  </div>
  {foot(5)}
</section>""")

# 5. Models & routing
t3 = tiers['L3']; t4 = tiers['L4']
slides.append(f"""
<section class="slide">
  <div class="kicker">Model và routing</div>
  <h2>Model tham chiếu Gemini 3.8 Flash, chỉ dùng khi model rẻ không đạt</h2>
  <table class="t" style="margin-top:14px">
    <tr><th>Cấp</th><th>Model chính</th><th>Leo thang</th><th>Lý do</th><th style="text-align:right">Giá /1M token (vào/ra)</th><th style="text-align:right">USD/tháng</th></tr>
    <tr><td>1 Email, hỏi đáp</td><td>Gemini 3.1 Flash-Lite</td><td>5% → 3.8 Flash (router)</td><td>câu ngắn, tiếng Việt tốt, TTFT thấp</td><td class="n">$0.25 / $1.50</td><td class="n">{usd(tiers['L1']['cost'])}</td></tr>
    <tr><td>2 Tài liệu, slide</td><td>Gemini 3.1 Flash-Lite</td><td>10% → 3.8 Flash</td><td>văn bản dài; xuất file trong sandbox</td><td class="n">$0.25 / $1.50</td><td class="n">{usd(tiers['L2']['cost'])}</td></tr>
    <tr><td>3 Dữ liệu, code</td><td>gpt-oss-120b</td><td>25% thử lại kèm log lỗi; 8% → 3.8 Flash</td><td>reasoning + code mạnh, có test trong sandbox để tự kiểm</td><td class="n">$0.09 / $0.36</td><td class="n">{usd(t3['cost'])}</td></tr>
    <tr><td>4 Agent dự án</td><td>gpt-oss-120b lập kế hoạch, Flash-Lite thực thi</td><td>15% planner → 3.8 Flash; 90% Flex</td><td>chạy nền, chịu được trễ Flex/Batch</td><td class="n">Flex $0.125 / $0.75</td><td class="n">{usd(t4['cost'])}</td></tr>
    <tr><td>5 Thiết kế</td><td>Flash-Lite sinh HTML/SVG/Mermaid; Flash-Lite Image</td><td>—</td><td>sơ đồ, mockup render bằng code; ảnh 1K $0.0336</td><td class="n">$0.25 / $1.50</td><td class="n">{usd(tiers['L5']['cost'])}</td></tr>
  </table>
  <div class="grid" style="grid-template-columns:1fr 1fr 1fr;margin-top:18px">
    <div class="card"><h3>Đo chất lượng (H8)</h3><p>Bộ test vàng 300 case mỗi cấp, chấm bằng LLM-judge (Gemini 3.8 Flash) + 10% người duyệt. Model rẻ phải đạt ≥ 95% điểm của model tham chiếu mới được bật.</p></div>
    <div class="card"><h3>Không tự host</h3><p>Toàn bộ phần gpt-oss qua API chỉ {usd(SC['oss_api_cost'])}/tháng; riêng phụ phí 2 GPU H100 trên Autopilot (HA) đã {usd(SC['h100_premium_2gpu'])}/tháng, chưa kể máy GPU. Tự host chỉ đáng xét khi phần gpt-oss tăng quá ~3,5 lần.</p></div>
    <div class="card"><h3>Giá chuẩn, không ưu đãi</h3><p>Gemini 3.8 Flash tính theo giá Standard $1.50/$7.50 (áp dụng từ 01/2027), không dùng mức giá giới thiệu đến hết 2026.</p></div>
  </div>
  {foot(6)}
</section>""")

# 6. Technology choices
slides.append(f"""
<section class="slide">
  <div class="kicker">Lý do chọn công nghệ</div>
  <h2>Mỗi lựa chọn lớn so ít nhất hai phương án, có số</h2>
  <table class="t" style="margin-top:14px">
    <tr><th style="width:150px">Quyết định</th><th>Chọn</th><th>Phương án loại</th><th>Số liệu quyết định</th></tr>
    <tr><td>Phục vụ LLM</td><td><b>API Vertex AI, routing 3 model</b></td><td>Tự host gpt-oss trên H100; mọi request dùng Gemini 3.8 Flash</td><td>LLM {usd(by['llm'])} so với {usd(llm_noroute)} nếu không routing; tự host ≥ {usd(SC['h100_premium_2gpu'])} chỉ riêng phụ phí GPU</td></tr>
    <tr><td>Endpoint model</td><td><b>Global endpoint</b></td><td>Regional asia-southeast1</td><td>Gemini 3.x và gpt-oss chưa có regional Singapore; giá non-global cao hơn 10%. Dữ liệu lưu trữ vẫn ở Singapore</td></tr>
    <tr><td>Compute</td><td><b>GKE Autopilot</b></td><td>GKE Standard tự quản node; VM riêng cho sandbox</td><td>Trả theo pod: compute + gateway + sandbox {usd(by['compute']+by['gateway']+by['sandbox'])}; gVisor bật sẵn trên Autopilot; không phải vá node → giữ 1,5 FTE</td></tr>
    <tr><td>Sandbox</td><td><b>gVisor + Spot Pod</b></td><td>MicroVM (Kata) cần nested virtualization; on-demand</td><td>gVisor khởi động &lt; 200 ms (giữ TTFT); Spot rẻ hơn 70% → tiết kiệm {usd(SC['levers'][3]['saving'])}/tháng</td></tr>
    <tr><td>Vector DB</td><td><b>pgvector trong Cloud SQL HA</b></td><td>Vector Search managed riêng</td><td>2,4M vector = {vn(S['vec_gib'], 1)} GiB, chỉ thêm {usd(by['vector_db'], 2)}/tháng SSD; lọc ACL bằng SQL cùng giao dịch, không phải đồng bộ quyền sang hệ thứ hai</td></tr>
    <tr><td>Workspace</td><td><b>GCS multi-region ASIA</b></td><td>Regional Singapore + job sao chép DR</td><td>$0.026 so với $0.020/GiB nhưng có sẵn bản sao 2 vùng (RPO ≤ 1 giờ) → không cần pipeline DR riêng</td></tr>
    <tr><td>LLM gateway</td><td><b>LiteLLM OSS trên GKE</b></td><td>Apigee; gọi thẳng SDK</td><td>{usd(by['gateway'])}/tháng, có budget/quota theo user và team, fallback, API kiểu OpenAI → đổi nhà cung cấp không sửa app</td></tr>
  </table>
  {foot(7)}
</section>""")

# 7. Connectors & authz
slides.append(f"""
<section class="slide">
  <div class="kicker">Connectors và phân quyền</div>
  <h2>Agent chỉ thấy những gì chính người dùng thấy</h2>
  <div class="grid" style="grid-template-columns:1.1fr 1fr;gap:26px;margin-top:14px">
    <div>
      <table class="t"><tr><th>Connector</th><th>Scope tối thiểu (OAuth ủy nhiệm)</th></tr>
        <tr><td>Gmail, Calendar</td><td>gmail.readonly, gmail.compose (gửi chỉ sau khi user xác nhận), calendar.events</td></tr>
        <tr><td>Drive, Docs/Sheets/Slides</td><td>drive.file + drive.readonly theo file được chọn</td></tr>
        <tr><td>Outlook, OneDrive/SharePoint, Teams</td><td>Mail.ReadWrite, Files.Read, Sites.Read.All (delegated), Chat.Read</td></tr>
        <tr><td>Jira, Confluence</td><td>read:jira-work, write:jira-work, read/write:confluence-content</td></tr>
        <tr><td>Notion</td><td>public integration, user chọn trang chia sẻ</td></tr>
      </table>
      <p class="note" style="margin-top:8px">Không có tài khoản dịch vụ đọc toàn tập đoàn. Gửi email, tạo ticket, sửa trang luôn qua bước người dùng xác nhận.</p>
    </div>
    <div class="grid" style="gap:12px">
      <div class="card"><h3>Token vault <span class="code">secrets_kms</span></h3><p>Refresh token mã hóa bằng DEK riêng từng user, DEK bọc bởi khóa HSM trong Cloud KMS; chỉ service account của connector có quyền decrypt, kèm AAD = user_id. Access token chỉ sống trong RAM, 60 phút.</p></div>
      <div class="card"><h3>ACL theo quyền gốc <span class="code">authz</span></h3><p>Khi index KB chung, lưu danh sách principal của tài liệu nguồn vào từng chunk; truy vấn pgvector luôn có điều kiện principal ∈ nhóm của user (đồng bộ từ IdP). Mở tài liệu: kiểm lại bằng token của user.</p></div>
      <div class="card"><h3>RBAC/ABAC</h3><p>OPA: vai trò × đơn vị × cấp tác vụ × độ nhạy dữ liệu. Ví dụ: cấp 4 chỉ cho nhóm dự án, dữ liệu "Mật" không gửi ra connector ngoài.</p></div>
    </div>
  </div>
  {foot(8)}
</section>""")

# 8. Workspace & sandbox
slides.append(f"""
<section class="slide">
  <div class="kicker">Workspace riêng và sandbox</div>
  <h2>Agent của A không đọc được file của B, kể cả khi code bị chiếm</h2>
  <div class="grid" style="grid-template-columns:1fr 1fr;gap:26px;margin-top:16px">
    <div class="card"><h3>Workspace (H3) <span class="code">object_storage</span> <span class="code">database</span></h3><ul>
      <li>GCS prefix <b>ws/&lt;user_id&gt;/</b>; app truy cập bằng signed URL 5 phút do backend cấp sau khi kiểm phiên</li>
      <li>Mỗi user một DEK (envelope encryption, CMEK); quota 10 GB kiểm ở API</li>
      <li>Chat, bộ nhớ dài hạn trong PostgreSQL với Row-Level Security theo user_id</li>
      <li>Kết quả tìm kiếm luôn lọc user_id + ACL trước khi xếp hạng</li>
      <li>Lifecycle: file tạm 30 ngày, chat 12 tháng, xóa theo yêu cầu</li></ul></div>
    <div class="card"><h3>Sandbox gVisor <span class="code">sandbox</span></h3><ul>
      <li>runtimeClassName: gvisor trên GKE Autopilot; kernel chạy trong userspace</li>
      <li>NetworkPolicy deny-all egress; không tới VPC nội bộ, metadata server hay internet</li>
      <li>automountServiceAccountToken: false; KSA riêng không gắn quyền IAM nào</li>
      <li>Chỉ mount bản sao file của đúng user (sidecar tải theo job), ghi kết quả ngược qua API</li>
      <li>Giới hạn 1 vCPU, 2 GiB, 120 giây; pod bị hủy ngay khi xong</li></ul></div>
  </div>
  <div class="card" style="margin-top:16px;background:#fff4dc"><p><b>Code cố thoát ra node hoặc gọi metadata endpoint?</b> Syscall bị gVisor chặn trước kernel host; gói tin tới 169.254.169.254 bị NetworkPolicy chặn; pod không có credential; node chỉ có IAM tối thiểu; sau 120 giây pod bị kill. {vn(S['sandbox_runs'])} lượt/tháng tốn {usd(by['sandbox'])}.</p></div>
  <div style="display:flex;align-items:center;gap:6px;margin-top:18px;font-size:13px;font-weight:600">
    <span class="pill" style="font-size:12.5px;white-space:nowrap">1 · Agent của A tạo job</span>→<span class="pill" style="font-size:12.5px;white-space:nowrap">2 · Pub/Sub</span>→<span class="pill" style="font-size:12.5px;white-space:nowrap">3 · Pod gVisor mới, Spot</span>→<span class="pill" style="font-size:12.5px;white-space:nowrap">4 · Sidecar chép ws/A/ cần dùng</span>→<span class="pill" style="font-size:12.5px;white-space:nowrap">5 · Chạy ≤ 120 giây</span>→<span class="pill" style="font-size:12.5px;white-space:nowrap">6 · Kết quả về ws/A/, pod bị xóa</span>
  </div>
  {foot(9)}
</section>""")

# 9. Governance
slides.append(f"""
<section class="slide">
  <div class="kicker">AI và data governance</div>
  <h2>Email chứa lệnh ẩn "gửi toàn bộ hợp đồng ra ngoài": bị chặn ở 4 lớp</h2>
  <div class="grid" style="grid-template-columns:repeat(4,1fr);margin-top:16px">
    <div class="card"><h3>1 · Tách dữ liệu và chỉ dẫn</h3><p>Nội dung connector được bọc như dữ liệu không tin cậy; system prompt cấm làm theo chỉ dẫn trong dữ liệu.</p></div>
    <div class="card"><h3>2 · Model Armor</h3><p>Quét prompt injection, jailbreak, URL độc, PII cho prompt, nội dung connector và output. {usd(SC['by_component']['governance'])}/tháng cho cả khối governance.</p></div>
    <div class="card"><h3>3 · Xác nhận hành động ghi</h3><p>Gửi email, tạo ticket, xóa file luôn hiện bản nháp + người nhận cho user bấm xác nhận; tool gửi ra ngoài domain bị OPA chặn với dữ liệu "Mật".</p></div>
    <div class="card"><h3>4 · DLP + egress</h3><p>Sensitive Data Protection che PII trước khi gửi; sandbox không có egress; NAT chỉ mở cho pod connector tới domain SaaS.</p></div>
  </div>
  <div class="grid" style="grid-template-columns:1fr 1fr;gap:26px;margin-top:18px">
    <div class="card"><h3>Data governance (H5)</h3><ul>
      <li>Mã hóa lúc lưu bằng CMEK (KMS), lúc truyền bằng TLS 1.2+</li>
      <li>Phân loại dữ liệu khi index: Công khai / Nội bộ / Mật</li>
      <li>Audit log 12 tháng: log bucket khóa retention + Archive có bucket lock</li>
      <li>Vertex AI không dùng dữ liệu khách hàng để huấn luyện; tắt data caching cho dữ liệu Mật</li></ul></div>
    <div class="card"><h3>Cổng eval (H4, H8)</h3><ul>
      <li>Mọi thay đổi model hoặc prompt chạy qua Cloud Build: 6.000 case, LLM-judge Flex</li>
      <li>Chặn deploy nếu điểm &lt; 95% model tham chiếu hoặc tỉ lệ vượt guardrail tăng</li>
      <li>Canary 5% người dùng trong 24 giờ trước khi bật toàn bộ</li></ul></div>
  </div>
  {foot(10)}
</section>""")

# 10. HA / DR
slides.append(f"""
<section class="slide">
  <div class="kicker">HA, backup, DR</div>
  <h2>Mất một zone lúc 10 giờ sáng: người dùng thấy chậm khoảng 1 phút</h2>
  <table class="t" style="margin-top:14px">
    <tr><th>Thành phần</th><th>Cơ chế HA</th><th>Khi 1 zone mất điện</th><th>Mất dữ liệu</th></tr>
    <tr><td>Cloud Armor + LB</td><td>Dịch vụ global, anycast</td><td>Không ảnh hưởng</td><td>—</td></tr>
    <tr><td>GKE pod (API, gateway, connector)</td><td>≥ 2 replica trải 3 zone, control plane regional 99,95%</td><td>Pod còn lại nhận tải; Autopilot dựng pod mới 1–2 phút</td><td>Request đang stream bị retry</td></tr>
    <tr><td>Cloud SQL</td><td>HA primary + standby khác zone</td><td>Failover tự động ~60 giây</td><td>0 (đồng bộ)</td></tr>
    <tr><td>Redis</td><td>Standard tier, replica khác zone</td><td>Failover tự động</td><td>Cache/rate limit, dựng lại được</td></tr>
    <tr><td>Pub/Sub, GCS ASIA, Vertex AI</td><td>Managed đa zone / đa vùng</td><td>Không ảnh hưởng; job agent tự retry</td><td>0</td></tr>
  </table>
  <div class="grid" style="grid-template-columns:repeat(3,1fr);margin-top:18px">
    <div class="card"><h3>RPO 1 giờ</h3><p>Cloud SQL backup on-demand mỗi giờ + PITR 7 ngày, lưu ở asia-southeast2. GCS multi-region sao chép mặc định ~1 giờ.</p></div>
    <div class="card"><h3>RTO 4 giờ</h3><p>Mất cả region: Terraform dựng lại cluster + restore Cloud SQL ở Jakarta (~2 giờ), đổi DNS. Không giữ môi trường chờ để tiết kiệm chi phí.</p></div>
    <div class="card"><h3>Diễn tập hằng tháng</h3><p>Restore backup mới nhất vào instance tạm 4 giờ, chạy smoke test, ghi thời gian thực tế. Chi phí {usd(sum(r['chi_phi'] for r in rows if r['component']=='backup_dr'), 2)}/tháng cho backup + diễn tập.</p></div>
  </div>
  {foot(11)}
</section>""")

# 11. Monitoring & FinOps
slides.append(f"""
<section class="slide">
  <div class="kicker">Monitoring và FinOps</div>
  <h2>Biết chi phí theo từng người, cắt trước khi vượt ngân sách</h2>
  <div class="grid" style="grid-template-columns:1fr 1fr 1fr;margin-top:16px">
    <div class="card"><h3>Đo gì <span class="code">monitoring</span></h3><ul>
      <li>p95 TTFT theo cấp, thời gian hoàn thành agent</li>
      <li>Tỉ lệ lỗi, retry, fallback model, tỉ lệ leo thang</li>
      <li>Token, USD theo user, đơn vị, cấp tác vụ (tag của LiteLLM)</li>
      <li>Cache hit, Spot bị thu hồi, hàng đợi Pub/Sub</li>
      <li>Vượt guardrail, hành động ghi bị từ chối</li></ul></div>
    <div class="card"><h3>Cảnh báo</h3><ul>
      <li>p95 TTFT &gt; 2,5 giây trong 10 phút</li>
      <li>Lỗi 5xx &gt; 1%; agent quá 8 phút</li>
      <li>Ngân sách tháng 50%, 80%, 100% (Cloud Billing budget + Pub/Sub)</li>
      <li>Một user dùng &gt; 5 lần trung vị trong ngày</li></ul></div>
    <div class="card"><h3>Quota và cách cắt</h3><ul>
      <li>Mỗi người: 400k token/ngày, 20 lượt agent, 15 ảnh/tháng</li>
      <li>Mỗi đơn vị: ngân sách USD/tháng trong gateway</li>
      <li>Vượt 80%: ép routing về Flash-Lite, tắt leo thang</li>
      <li>Vượt 100%: chỉ còn cấp 1–2, cần trưởng đơn vị duyệt</li></ul></div>
  </div>
  <div class="card" style="margin-top:16px;display:flex;gap:40px;align-items:center">
    <div><div class="mid">{usd(by['llm']/2000, 2)}</div><div class="lbl">LLM / DAU / tháng</div></div>
    <div><div class="mid">{usd(by['llm']/S['req_month']*1000, 2)}</div><div class="lbl">LLM / 1.000 request</div></div>
    <div><div class="mid">{usd(by['monitoring'])}</div><div class="lbl">chi phí observability / tháng</div></div>
    <p style="flex:1">Spend log của gateway lưu trong Cloud SQL, xuất báo cáo chi phí theo đơn vị hằng tuần cho trưởng bộ phận.</p>
  </div>
  {foot(12)}
</section>""")

# 12. Cost
maxv = top5[0][1]
bars = ''.join(f"<div style='display:flex;align-items:center;gap:12px;margin-bottom:10px'><div style='flex:0 0 150px;font-size:14px'>{NAMES.get(k,k)}</div>"
               f"<div class='bar' style='width:{int(430*v/maxv)}px'></div><div style='font-size:14px;font-weight:700'>{usd(v)}</div></div>" for k, v in top5)
levers = ''.join(f"<tr><td>{l['name']}</td><td class='n'><b>-{usd(l['saving'])}</b></td></tr>" for l in SC['levers'])
slides.append(f"""
<section class="slide">
  <div class="kicker">Chi phí</div>
  <h2>{usd(TOTAL, 2)} mỗi tháng, {usd(TOTAL/2000, 2)} mỗi DAU</h2>
  <p class="lead">USD chưa VAT, giá niêm yết trên trang Google Cloud ngày 16/10/2026; khớp dòng TOTAL trong {GROUP}_baogia.xlsx ({len(rows)} dòng, mỗi dòng có ảnh chụp bằng chứng).</p>
  <div class="grid" style="grid-template-columns:640px 1fr;gap:36px">
    <div><div class="note" style="margin-bottom:10px">5 hạng mục lớn nhất</div>{bars}
      <p class="note" style="margin-top:8px">Còn lại {usd(TOTAL-sum(v for _,v in top5))} cho 16 thành phần: LB, NAT, Redis, Pub/Sub, GCS, KMS, IdP, monitoring, backup, CI/CD…</p></div>
    <div><div class="note" style="margin-bottom:6px">Đòn bẩy tiết kiệm (so với khi không áp dụng)</div>
      <table class="t">{levers}</table>
      <p class="note" style="margin-top:8px">Giả định cần chất vấn: cache 25–60% prefix, leo thang 5–15%, Spot 80%, Flex 90% cho agent nền.</p></div>
  </div>
  {foot(13)}
</section>""")

# 13. Risks & scale
d2 = SC['dau_x2']
slides.append(f"""
<section class="slide">
  <div class="kicker">Rủi ro và mở rộng</div>
  <h2>DAU gấp đôi, hóa đơn tăng {vn(d2['total']/TOTAL, 2)} lần</h2>
  <div class="grid" style="grid-template-columns:1fr 1fr;gap:28px;margin-top:14px">
    <div>
      <div style="display:flex;gap:40px;margin-bottom:14px">
        <div><div class="mid">{usd(d2['total'])}</div><div class="lbl">4.000 DAU / tháng</div></div>
        <div><div class="mid">{usd(d2['per_dau'], 2)}</div><div class="lbl">mỗi DAU (giảm từ {usd(TOTAL/2000, 2)})</div></div>
      </div>
      <table class="t"><tr><th>Phần</th><th>Thay đổi</th></tr>
        <tr><td>Tuyến tính</td><td>LLM, embedding, Model Armor, sandbox, egress, workspace</td></tr>
        <tr><td>Bậc thang</td><td>Cloud SQL 4 → 8 vCPU khi &gt; 2.500 DAU; nhân sự 1,5 → 2 FTE</td></tr>
        <tr><td>Gần cố định</td><td>Cluster fee, LB, KMS, staging, CI/CD, IdP theo MAU</td></tr>
        <tr><td>Đổi cách phục vụ</td><td>Khi chi phí gpt-oss &gt; {usd(SC['h100_premium_2gpu'])}/tháng (~3,5 lần): đánh giá tự host trên GPU</td></tr>
      </table>
    </div>
    <div>
      <table class="t"><tr><th>Rủi ro</th><th>Tác động</th><th>Giảm thiểu</th></tr>
        <tr><td>Giá token +30%</td><td class="n">+{usd(SC['token_up30']-TOTAL)}</td><td>routing vẫn tối ưu; quota cắt sớm</td></tr>
        <tr><td>Giá token −50%</td><td class="n">−{usd(TOTAL-SC['token_down50'])}</td><td>API càng có lợi so với tự host</td></tr>
        <tr><td>Phụ thuộc Vertex AI</td><td>đổi API</td><td>gateway kiểu OpenAI, eval set dùng lại cho nhà cung cấp mới</td></tr>
        <tr><td>Global endpoint không cam kết vị trí xử lý</td><td>tuân thủ</td><td>dữ liệu lưu ở SG; dữ liệu Mật chỉ dùng model có regional</td></tr>
        <tr><td>Flex/Spot bị trễ hoặc thu hồi</td><td>độ trễ</td><td>quay về Standard/on-demand sau 2 phút, đã tính 10–20%</td></tr>
        <tr><td>Ước lượng token sai</td><td>±30% LLM</td><td>đo thực tế 2 tuần pilot, chỉnh quota</td></tr>
      </table>
    </div>
  </div>
  {foot(14)}
</section>""")

# 14. Q&A prep (panel questions)
slides.append(f"""
<section class="slide dark">
  <div class="kicker">Sẵn sàng hỏi đáp</div>
  <h2 style="color:#fff">Câu trả lời ngắn cho 6 câu hội đồng hay hỏi</h2>
  <div class="grid" style="grid-template-columns:1fr 1fr;gap:14px;margin-top:16px">
    <div class="card" style="background:#123842"><h3 style="color:#fff">A đọc được file của B?</h3><p style="color:#cfe3e3">Không: prefix + DEK riêng, RLS user_id, index lọc ACL, token connector là của A, sandbox chỉ mount file của A.</p></div>
    <div class="card" style="background:#123842"><h3 style="color:#fff">Email chứa lệnh ẩn?</h3><p style="color:#cfe3e3">Bị coi là dữ liệu, Model Armor gắn cờ, gửi ra ngoài cần user xác nhận, DLP che PII, sandbox không egress.</p></div>
    <div class="card" style="background:#123842"><h3 style="color:#fff">Thoát sandbox, gọi metadata?</h3><p style="color:#cfe3e3">gVisor chặn syscall, NetworkPolicy chặn 169.254.169.254, không SA token, giới hạn 120 giây.</p></div>
    <div class="card" style="background:#123842"><h3 style="color:#fff">DAU gấp đôi?</h3><p style="color:#cfe3e3">{usd(d2['total'])}/tháng (×{vn(d2['total']/TOTAL, 2)}); LLM tuyến tính, DB và nhân sự tăng bậc, phần nền gần cố định.</p></div>
    <div class="card" style="background:#123842"><h3 style="color:#fff">Giá token ±?</h3><p style="color:#cfe3e3">+30% → +{usd(SC['token_up30']-TOTAL)}; −50% → −{usd(TOTAL-SC['token_down50'])}. Tự host chỉ hòa vốn khi tải gấp ~3,5 lần.</p></div>
    <div class="card" style="background:#123842"><h3 style="color:#fff">Mất 1 AZ lúc 10 giờ?</h3><p style="color:#cfe3e3">SQL failover ~60 giây, pod dồn sang 2 zone còn lại, không mất dữ liệu đã commit; khớp RTO 4h, RPO 1h.</p></div>
  </div>
  {foot(15)}
</section>""")

# Appendix: quote by component + evidence
comp_rows = ''.join(f"<tr><td><span class='code'>{k}</span></td><td class='n'>{usd(v, 2)}</td><td class='n'>{pct(v/TOTAL)}</td></tr>"
                    for k, v in sorted(by.items(), key=lambda kv: -kv[1]))
half = (len(by) + 1) // 2
items = sorted(by.items(), key=lambda kv: -kv[1])
def ctab(lst):
    return "<table class='t'><tr><th>Component</th><th style='text-align:right'>USD/tháng</th><th style='text-align:right'>%</th></tr>" + ''.join(
        f"<tr><td><span class='code'>{k}</span></td><td class='n'>{usd(v, 2)}</td><td class='n'>{vn(v/TOTAL*100, 1)}%</td></tr>" for k, v in lst) + '</table>'
slides.append(f"""
<section class="slide">
  <div class="kicker">Phụ lục A · không tính vào 15 slide</div>
  <h2>Báo giá theo component (TOTAL {usd(TOTAL, 2)})</h2>
  <div class="grid" style="grid-template-columns:1fr 1fr;gap:36px;margin-top:12px">{ctab(items[:half])}{ctab(items[half:])}</div>
  {foot('A')}
</section>""")
evl = list(M.EVIDENCE.items())
def etab(lst):
    return "<table class='t' style='font-size:10.5px'>" + ''.join(f"<tr><td style='padding:3px 6px'><b>{k}</b></td><td style='padding:3px 6px'>{d}</td></tr>" for k, (d, u) in lst) + '</table>'
ev_rows = etab(evl[:17]) + etab(evl[17:])
slides.append(f"""
<section class="slide">
  <div class="kicker">Phụ lục B · bằng chứng giá</div>
  <h2>{len(M.EVIDENCE)} ảnh chụp trang giá chính thức, ngày 16/10/2026</h2>
  <div class="grid" style="grid-template-columns:1fr 1fr;gap:24px;margin-top:8px">{ev_rows}</div>
  {foot('B')}
</section>""")

html = f"""<!doctype html><html lang="vi"><head><meta charset="utf-8"><title>VBot Workplace {GROUP}</title><style>{CSS}</style></head><body>{''.join(slides)}</body></html>"""
out = os.path.join(ROOT, 'slides', 'slides.html')
open(out, 'w').write(html)
print(out, len(slides), 'slides')
