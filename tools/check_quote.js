// Runs the exact validator embedded in vbot-capstone.html against an .xlsx file.
// usage: node tools/check_quote.js deliverables/G00_baogia.xlsx
const XLSX = require('xlsx');
const { workbookToInput, validateQuote } = require('./validator_from_page.js');
const fs = require('fs');
const file = process.argv[2];
const wb = XLSX.read(fs.readFileSync(file), { type: 'buffer', cellNF: true, cellDates: false });
const { rows, evidenceIds, sheets } = workbookToInput(XLSX, wb);
const res = validateQuote(rows, evidenceIds);
console.log('sheets:', sheets.join(', '));
console.log(res.ok ? 'KẾT QUẢ: ĐẠT' : 'KẾT QUẢ: CHƯA ĐẠT');
for (const e of res.errors) console.log('  LỖI   dòng', e.line, e.col, '-', e.msg);
for (const w of res.warnings) console.log('  CẢNH BÁO dòng', w.line, w.col, '-', w.msg);
if (res.summary) console.log('summary:', JSON.stringify({ rows: res.summary.rows, subtotal: res.summary.subtotal, total: res.summary.total, perDau: +res.summary.perDau.toFixed(2), missing: res.summary.missingComponents }));
process.exit(res.ok ? 0 : 1);
