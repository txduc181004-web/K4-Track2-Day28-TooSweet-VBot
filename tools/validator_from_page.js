/*VALIDATOR-START*/
/* Mirrors .claude/skills/review-vbot-submission/scripts/quote_check.py — keep both in sync (tests/parity.mjs). */
const DAU = 2000, MAX_ROWS = 150;
const SHEET_QUOTE = 'BaoGia', SHEET_EVIDENCE = 'BangChung';
const COLUMNS = [['component','Component'],['y_nghia','Ý nghĩa'],['ghi_chu','Ghi chú'],['chi_phi','Chi phí/tháng (USD)'],['bang_chung','Bằng chứng']];
const KEYS = COLUMNS.map(c => c[0]), LABEL = Object.fromEntries(COLUMNS);
const COMPONENTS = {
  compute:['Máy chủ ứng dụng, node Kubernetes, serverless',true,'Loại máy hoặc node, số lượng, autoscale theo giờ hành chính'],
  llm:['LLM serving: API theo token hoặc GPU tự host',true,'Model cho từng cấp tác vụ, API hay tự host, loại GPU, routing'],
  embedding:['Embedding, rerank',false,'Model embedding, chi phí index lần đầu và hằng ngày'],
  gateway:['API gateway, LLM gateway',true,'Quota, rate limit, retry, fallback model, ghi log token'],
  load_balancer:['Load balancer',true,'Loại LB, TLS, health check, đặt trước thành phần nào'],
  authn:['Xác thực: SSO, IdP, MFA',true,'IdP, giao thức SSO, MFA, phiên đăng nhập'],
  authz:['Phân quyền: RBAC/ABAC, policy engine, ACL',true,'Mô hình quyền, ACL tài liệu theo quyền gốc, scope OAuth'],
  database:['CSDL quan hệ hoặc NoSQL',true,'Engine, cấu hình HA, kích thước, dữ liệu gì'],
  vector_db:['Vector DB, search index',true,'Engine, số vector, lọc kết quả theo quyền'],
  object_storage:['Lưu trữ file, workspace riêng',true,'Tách workspace từng user, quota, lifecycle'],
  cache_queue:['Cache, hàng đợi tác vụ agent',true,'Cache phiên và kết quả, hàng đợi cho agent chạy nền'],
  sandbox:['Sandbox chạy code và tác vụ agent',true,'Công nghệ cô lập, giới hạn tài nguyên, egress, vòng đời'],
  connectors:['Tích hợp Google Workspace, M365, Notion, Jira, Confluence',true,'Cách gọi API từng SaaS, webhook, rate limit, lưu token'],
  secrets_kms:['Secrets, KMS, token vault',true,'Khóa mã hóa, nơi lưu secret và OAuth token, xoay khóa'],
  backup_dr:['Backup, DR',true,'Lịch backup, nơi lưu, RTO và RPO, diễn tập khôi phục'],
  monitoring:['Log, metric, trace, LLM observability',true,'Đo gì, cảnh báo gì, chi phí theo user và đơn vị'],
  governance:['AI và data governance',true,'Guardrail, chống prompt injection, DLP, audit, eval gate'],
  network:['VPC, NAT, egress, WAF, private endpoint',true,'Subnet riêng, kiểm soát egress, WAF, private endpoint tới API model'],
  cicd:['CI/CD, registry, IaC, staging',true,'Pipeline, registry, IaC, môi trường staging'],
  ops_labor:['Nhân sự vận hành (FTE)',true,'Số FTE, ca trực, phụ trách gì'],
  licenses:['Giấy phép, SaaS, gói support',false,'Gói support của cloud, license phần mềm'],
  contingency:['Dự phòng',false,'Vì sao cần, tính trên phần nào'],
  other:['Khác',false,'']
};
const REQUIRED_COMPONENTS = Object.keys(COMPONENTS).filter(k => COMPONENTS[k][1]);
const NO_EVIDENCE = new Set(['ops_labor','contingency']);
const EVID_RE = /^E\d{2,3}$/, URL_RE = /^https?:\/\/\S+$/, PLACEHOLDER_URL_RE = /^https?:\/\/(www\.)?example\.(com|org)/i;
const NUM_RE = /^\d+(\.\d+)?$/, EXAMPLE_RE = /^\[VÍ DỤ\]/i, INCLUDED_RE = /included|nằm trong|đã bao gồm|bao gồm trong/iu;
const DIGIT_RE = /\d/;
const TRIAL_RE = /free[\s_-]*tier|free[\s_-]*trial|\btrial\b|free[\s_-]*credits?|promo(?:tional)?[\s_-]*credits?|startup[\s_-]*credits?|miễn[\s_-]*phí|dùng[\s_-]*thử|khuyến[\s_-]*mãi/iu;
const HA_RE = /multi[\s_-]*az|\bha\b|high[\s_-]*availability|replica|standby|failover|\bzones?\b|đa vùng|dự phòng nóng/iu;
const STAGING_RE = /staging|\bstage\b|non[\s_-]*prod/iu;

function normalizeHeader(s){ return String(s).trim().toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/đ/g, 'd').replace(/[^a-z0-9]/g, ''); }
function headerKey(s){
  const h = normalizeHeader(s);
  if(['component','thanhphan','tencomponent'].includes(h)) return 'component';
  if(h === 'ynghia') return 'y_nghia';
  if(h === 'ghichu') return 'ghi_chu';
  if(h.startsWith('chiphi')) return 'chi_phi';
  if(['bangchung','evidence'].includes(h)) return 'bang_chung';
  return null;
}
function pad2(n){ return String(n).padStart(2, '0'); }
function normCell(XLSX, cell){
  if(!cell || cell.v === undefined || cell.v === null) return '';
  if(cell.t === 'd' && cell.v instanceof Date) return cell.v.getUTCFullYear() + '-' + pad2(cell.v.getUTCMonth()+1) + '-' + pad2(cell.v.getUTCDate());
  if(cell.t === 'n'){
    if(cell.z && XLSX.SSF.is_date(cell.z)){ const p = XLSX.SSF.parse_date_code(cell.v); return p.y + '-' + pad2(p.m) + '-' + pad2(p.d); }
    return cell.v;
  }
  if(cell.t === 'b') return cell.v ? 'TRUE' : 'FALSE';
  if(cell.t === 'e') return String(cell.w || '#ERROR');
  return String(cell.v).trim();
}
function sheetRows(XLSX, ws, minRow){
  if(!ws || !ws['!ref']) return [];
  const rg = XLSX.utils.decode_range(ws['!ref']); const rows = [];
  for(let r = Math.max(rg.s.r, (minRow || 1) - 1); r <= rg.e.r; r++){
    const cells = [];
    for(let c = 0; c <= rg.e.c; c++) cells.push(normCell(XLSX, ws[XLSX.utils.encode_cell({r, c})]));
    while(cells.length && cells[cells.length-1] === '') cells.pop();
    if(cells.length) rows.push({line: r + 1, cells});
  }
  return rows;
}
/* Workbook (from XLSX.read(data,{type:'array',cellNF:true})) -> {rows, evidenceIds} */
function workbookToInput(XLSX, wb){
  const rows = wb.SheetNames.includes(SHEET_QUOTE) ? sheetRows(XLSX, wb.Sheets[SHEET_QUOTE], 1) : [];
  let evidenceIds = null;
  if(wb.SheetNames.includes(SHEET_EVIDENCE)){
    evidenceIds = sheetRows(XLSX, wb.Sheets[SHEET_EVIDENCE], 2).map(r => String(r.cells[0] === undefined ? '' : r.cells[0]).trim()).filter(Boolean);
  }
  return {rows, evidenceIds, sheets: wb.SheetNames};
}

function validateQuote(rows, evidenceIds){
  const errors = [], warnings = [];
  const E = (line, col, msg) => errors.push({line, col, msg});
  const W = (line, col, msg) => warnings.push({line, col, msg});
  const out = {errors, warnings, summary:null, ok:false, items:[]};
  if(!rows || !rows.length){ E(0, '', "Không có sheet '" + SHEET_QUOTE + "' hoặc sheet trống."); return out; }
  const s = v => typeof v === 'string' ? v : (v === '' || v === undefined || v === null ? '' : String(v));

  const headLine = rows[0].line, pos = {}, unknown = [];
  rows[0].cells.forEach((h, j) => {
    const hs = s(h);
    if(hs.trim() === '') return;
    const k = headerKey(hs);
    if(k === null) unknown.push(hs.trim());
    else if(k in pos) E(headLine, 'header', 'Cột "' + LABEL[k] + '" xuất hiện hai lần.');
    else pos[k] = j;
  });
  const missing = KEYS.filter(k => !(k in pos)).map(k => LABEL[k]);
  if(missing.length) E(headLine, 'header', 'Thiếu cột: ' + missing.join(', ') + '. Dòng đầu phải là: ' + KEYS.map(k => LABEL[k]).join(' | ') + '.');
  if(unknown.length) E(headLine, 'header', 'Cột không có trong đề: ' + unknown.join(', ') + '.');
  if(errors.length) return out;

  const used = new Set(Object.values(pos));
  const data = rows.slice(1).map(r => {
    const o = {line: r.line};
    KEYS.forEach(k => { const j = pos[k]; const v = j < r.cells.length ? r.cells[j] : ''; o[k] = typeof v === 'string' ? v.trim() : v; });
    o.extra = r.cells.some((v, j) => !used.has(j) && s(v) !== '');
    return o;
  });
  const items = data.filter(r => s(r.component).toUpperCase() !== 'TOTAL');
  const totals = data.filter(r => s(r.component).toUpperCase() === 'TOTAL');

  const num = r => {
    const v = r.chi_phi; let x;
    if(typeof v === 'number') x = v;
    else if(typeof v === 'string' && NUM_RE.test(v)) x = Number(v);
    else {
      const sv = s(v); let hint = '';
      if(/[$đ₫]|usd|vnd/i.test(sv)) hint = ' Bỏ ký hiệu tiền tệ.';
      else if(/,/.test(sv)) hint = ' Bỏ dấu phân cách hàng nghìn, dùng dấu chấm cho phần thập phân.';
      else if(sv === '') hint = ' Ô đang trống (nếu là công thức: mở và lưu lại bằng Excel hoặc Google Sheets).';
      E(r.line, LABEL.chi_phi, 'Phải là số USD, ví dụ 1250.50 (đang là "' + sv + '").' + hint);
      return null;
    }
    if(x < 0){ E(r.line, LABEL.chi_phi, 'Không được âm.'); return null; }
    return x;
  };

  const evSet = new Set(evidenceIds || []), evUsed = new Set();
  let subtotal = 0, labor = 0, maxItem = {name:'', cost:0};
  const byComp = {}, seen = new Map(), textAll = [];

  items.forEach(r => {
    const L = r.line;
    if(r.extra) E(L, '', 'Dòng có dữ liệu ở cột ngoài 5 cột của đề. Xóa các ô thừa.');
    const comp = s(r.component);
    if(!Object.prototype.hasOwnProperty.call(COMPONENTS, comp)) E(L, LABEL.component, '"' + comp + '" không thuộc danh sách. Chọn trong dropdown: ' + Object.keys(COMPONENTS).join(', ') + '.');
    const yn = s(r.y_nghia), gc = s(r.ghi_chu);
    if(yn === '') E(L, LABEL.y_nghia, 'Ghi hạng mục này là gì, dùng để làm gì.');
    const cost = num(r);
    if(gc.length < 15) E(L, LABEL.ghi_chu, 'Ghi dịch vụ hoặc SKU, region và cách tính chi phí (ít nhất 15 ký tự).');
    else if(cost !== 0 && !DIGIT_RE.test(gc)) W(L, LABEL.ghi_chu, 'Ghi chú chưa có con số. Nên ghi cách tính: đơn giá × số lượng.');
    if(EXAMPLE_RE.test(yn) || EXAMPLE_RE.test(gc)) E(L, LABEL.y_nghia, 'Còn dòng ví dụ của file mẫu. Thay nội dung hoặc xóa dòng.');
    if(cost === 0 && !INCLUDED_RE.test(gc)) E(L, LABEL.chi_phi, 'Chi phí bằng 0 chỉ dùng cho hạng mục đã nằm trong dòng khác: ghi chú phải nói rõ "nằm trong" dịch vụ nào.');
    if(comp === 'ops_labor' && cost !== null) labor += cost;
    const ev = s(r.bang_chung);
    const refs = ev.split(';').map(t => t.trim()).filter(Boolean);
    if(!NO_EVIDENCE.has(comp) && !refs.length) E(L, LABEL.bang_chung, 'Thiếu bằng chứng: link (trang giá, bản tính giá đã lưu, ảnh) hoặc mã ảnh E01… trong sheet ' + SHEET_EVIDENCE + '.');
    refs.forEach(t => {
      if(t.toUpperCase() === 'NA' && NO_EVIDENCE.has(comp)) return;
      if(EVID_RE.test(t)){
        evUsed.add(t);
        if(evidenceIds === null) E(L, LABEL.bang_chung, 'Dùng mã ' + t + ' nhưng file không có sheet ' + SHEET_EVIDENCE + '.');
        else if(!evSet.has(t)) E(L, LABEL.bang_chung, 'Mã ' + t + ' không có trong cột A của sheet ' + SHEET_EVIDENCE + '.');
      } else if(URL_RE.test(t)){
        if(PLACEHOLDER_URL_RE.test(t)) E(L, LABEL.bang_chung, 'example.com chỉ là link mẫu.');
      } else E(L, LABEL.bang_chung, '"' + t + '" không phải link http(s) hay mã ảnh E01….');
    });
    if(TRIAL_RE.test([yn, gc, ev].join(' '))) E(L, LABEL.ghi_chu, 'Có dấu hiệu free tier, dùng thử hoặc credit khuyến mãi. Báo giá enterprise phải dùng giá niêm yết trả phí.');
    textAll.push(yn + ' ' + gc);
    if(cost !== null){
      subtotal += cost;
      byComp[comp] = (byComp[comp] || 0) + cost;
      if(cost > maxItem.cost) maxItem = {name: yn, cost};
    }
    const key = (comp + '|' + yn).toLowerCase();
    if(yn && seen.has(key)) W(L, LABEL.y_nghia, 'Trùng hạng mục với dòng ' + seen.get(key) + '. Kiểm tra có tính hai lần không.');
    else if(yn) seen.set(key, L);
    out.items.push({line: L, component: comp, y_nghia: yn, ghi_chu: gc, chi_phi: cost, bang_chung: ev});
  });

  let totalVal = null;
  if(!totals.length) E(0, 'TOTAL', 'Thiếu dòng cuối có Component = TOTAL.');
  else {
    if(totals.length > 1) E(totals[1].line, LABEL.component, 'Chỉ được có 1 dòng TOTAL.');
    const t = totals[0];
    if(t !== data[data.length-1]) E(t.line, LABEL.component, 'Dòng TOTAL phải là dòng cuối cùng của sheet.');
    totalVal = num(t);
  }
  if(items.length > MAX_ROWS) E(0, '', 'Tối đa ' + MAX_ROWS + ' dòng chi phí, hiện có ' + items.length + '.');
  const present = new Set(items.map(r => s(r.component)));
  const lack = REQUIRED_COMPONENTS.filter(c => !present.has(c));
  if(lack.length) E(0, LABEL.component, 'Thiếu thành phần hạ tầng bắt buộc: ' + lack.join(', ') + '.');
  if(totalVal !== null && Math.abs(totalVal - subtotal) > Math.max(0.05, 0.001 * subtotal)) E(totals[0].line, LABEL.chi_phi, 'TOTAL ghi ' + totalVal + ' nhưng tổng các dòng là ' + subtotal.toFixed(2) + '.');

  const joined = textAll.join(' ');
  if(items.length >= 3 && !STAGING_RE.test(joined)) W(0, '', 'Không thấy hạng mục nào nhắc tới staging. Đề yêu cầu prod và 1 staging.');
  if(items.length >= 3 && !HA_RE.test(joined)) W(0, '', 'Không thấy hạng mục nào nhắc tới HA (multi-AZ, replica, standby). Kiểm tra lại số lượng cho tính sẵn sàng cao.');
  if(items.length && !present.has('embedding')) W(0, LABEL.component, 'Chưa có dòng embedding. Nếu embedding nằm trong dòng llm, ghi rõ trong ghi chú.');
  if(subtotal > 0 && maxItem.cost / subtotal > 0.6) W(0, '', 'Hạng mục "' + maxItem.name + '" chiếm ' + (maxItem.cost / subtotal * 100).toFixed(0) + '% tổng. Hội đồng sẽ hỏi kỹ sizing của dòng này.');
  if(evidenceIds && evidenceIds.length){
    const unused = evidenceIds.filter(e => !evUsed.has(e));
    if(unused.length) W(0, LABEL.bang_chung, 'Mã bằng chứng không được dòng nào dùng: ' + unused.join(', ') + '.');
  }
  out.summary = {rows: items.length, subtotal: Math.round(subtotal * 100) / 100, total: totalVal, perDau: subtotal / DAU, laborUsd: labor,
    byComponent: byComp, missingComponents: lack, evidenceIds};
  out.ok = errors.length === 0;
  return out;
}
/*VALIDATOR-END*/
module.exports = { workbookToInput, validateQuote, REQUIRED_COMPONENTS, COMPONENTS };
