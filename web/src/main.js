import "./style.css";
import { createClient, createAccount, generatePrivateKey } from "genlayer-js";
import { studionet } from "genlayer-js/chains";
import { NET, NETWORKS, CONTRACT_ADDRESS, EXPLORER_BASE, REPO_URL, SITE, STORIES, TRY_TERMS, TRY_BORROWERS } from "./config.js";

// Bradbury Phase 2 needs genlayer-js 2; Studio stays on genlayer-js 1, which
// Studio's RPC supports. The Bradbury view only reads, so it needs no wallet.
const BRADBURY = NET.key === "bradbury";
const v2 = BRADBURY ? await import("genlayer-js-v2") : null;
const v2chains = BRADBURY ? await import("genlayer-js-v2/chains") : null;

const $ = (id) => document.getElementById(id);
const el = (tag, cls, text) => {
  const n = document.createElement(tag);
  if (cls) n.className = cls;
  if (text !== undefined) n.textContent = String(text); // always plain text
  return n;
};
const link = (href, text) => {
  const a = el("a", null, text);
  a.href = href;
  a.target = "_blank";
  a.rel = "noopener noreferrer";
  return a;
};
const RPC = studionet.rpcUrls.default.http[0];
const reader = BRADBURY ? v2.createClient({ chain: v2chains.testnetBradbury, endpoint: NET.rpc }) : createClient({ chain: studionet });

function plain(v) {
  if (v instanceof Map) return Object.fromEntries([...v.entries()].map(([k, x]) => [k, plain(x)]));
  if (Array.isArray(v)) return v.map(plain);
  if (typeof v === "bigint") return Number(v);
  if (v && typeof v === "object") return Object.fromEntries(Object.entries(v).map(([k, x]) => [k, plain(x)]));
  return v;
}
const read = async (functionName, args = []) => plain(await reader.readContract({ address: CONTRACT_ADDRESS, functionName, args }));
const short = (e) => String((e && (e.shortMessage || e.message)) || e).slice(0, 300);
const shortAddr = (a) => (a ? `${a.slice(0, 6)}…${a.slice(-4)}` : "");
const same = (a, b) => !!a && !!b && a.toLowerCase() === b.toLowerCase();
const nowS = () => Math.floor(Date.now() / 1000);

// ------------------------------------------------------------ amounts

function toWei(text) {
  const s = String(text).trim();
  if (!/^\d+(\.\d{1,18})?$/.test(s)) return null;
  const [w, f = ""] = s.split(".");
  return BigInt(w) * 10n ** 18n + BigInt((f + "0".repeat(18)).slice(0, 18));
}
function gen(wei, keep = 4) {
  const n = BigInt(wei);
  const neg = n < 0n;
  const a = neg ? -n : n;
  const w = a / 10n ** 18n;
  const f = (a % 10n ** 18n).toString().padStart(18, "0").slice(0, keep).replace(/0+$/, "");
  return `${neg ? "-" : ""}${w}${f ? "." + f : ""} GEN`;
}
function eur(units) {
  const n = Number(units);
  const neg = n < 0;
  const m = Math.abs(n) / 1e6;
  const s = m >= 100 ? m.toFixed(1) : m.toFixed(3).replace(/0$/, "");
  return `${neg ? "(" : ""}EUR ${s}m${neg ? ")" : ""}`;
}
const bp = (b) => `${(Number(b) / 100).toFixed(2)}%`;
const x100 = (v) => `${(Number(v) / 100).toFixed(2)}x`;

// -------------------------------------------------------------- times

const pad = (n) => String(n).padStart(2, "0");
const utcFull = (ts) => new Date(ts * 1000).toISOString().replace("T", " ").slice(0, 16) + " UTC";
const utc = (ts) => {
  const d = new Date(ts * 1000);
  return `${pad(d.getUTCHours())}:${pad(d.getUTCMinutes())} UTC`;
};
function inWords(secs) {
  if (secs <= 0) return "now";
  const m = Math.ceil(secs / 60);
  return m < 60 ? `in ${m} min` : `in ${Math.floor(m / 60)} h ${m % 60} min`;
}

// ------------------------------------------------------- page chrome

for (const n of Object.values(NETWORKS)) {
  const a = el("a", n.key === NET.key ? "on" : "", n.label);
  a.href = n.key === "studio" ? "./" : `./?net=${n.key}`;
  $("nets").append(a);
}
$("repo-link").href = REPO_URL;
$("readme-link").href = `${REPO_URL}#readme`;
$("net-note").textContent = BRADBURY
  ? "You are viewing GenLayer Testnet Bradbury Phase 2, read-only: these facilities were run end to end with testnet wallets. Switch to Studio to try every step yourself."
  : "You are viewing GenLayer Studio. Open a live facility below, or run your own with free temporary accounts.";
if (CONTRACT_ADDRESS) {
  $("foot-contract").append(el("span", null, `Contract on ${NET.name}: `), link(`${EXPLORER_BASE}/address/${CONTRACT_ADDRESS}`, CONTRACT_ADDRESS));
} else {
  $("foot-contract").textContent = `The ${NET.name} deployment is being prepared.`;
}
if (BRADBURY || !CONTRACT_ADDRESS) $("try").hidden = true;

// ------------------------------------------------------------- cards

async function drawCards() {
  const box = $("cards");
  box.replaceChildren();
  if (!NET.examples.length) {
    box.append(el("p", "small", "The live runs of the five borrowers are being recorded on this network; they appear here as soon as they start."));
    return;
  }
  for (const ex of NET.examples) {
    const card = el("article", "card");
    const h = el("h3", null, ex.company);
    const st = el("span", "badge", "…");
    const p = el("p", "small", STORIES[ex.slug] || "");
    const b = el("button", null, `Open facility #${ex.id}`);
    b.type = "button";
    b.addEventListener("click", () => openFacility(ex.id));
    card.append(h, st, p, b);
    box.append(card);
    read("get_facility", [ex.id, nowS()]).then((f) => setBadge(st, f.status)).catch(() => (st.textContent = "?"));
  }
  if ((NET.withdrawals || []).length) {
    // On this network the five facilities share two wallets, which withdrew
    // what the facilities credited them once, at the end of the run.
    const p = el("p", "small", "Withdrawals at the end of the run: ");
    NET.withdrawals.forEach(([label, hash], i) => {
      if (i) p.append(" · ");
      p.append(el("span", null, `${label} `), link(`${EXPLORER_BASE}/tx/${hash}`, `${hash.slice(0, 10)}…`));
    });
    box.after(p);
  }
}

function setBadge(node, status) {
  node.textContent = status;
  node.className = `badge s-${String(status).toLowerCase()}`;
}

$("lookup").addEventListener("submit", (e) => {
  e.preventDefault();
  const id = $("lookup-id").value.trim();
  if (/^\d+$/.test(id)) openFacility(id);
});

// ---------------------------------------------------------- facility

let current = null; // the facility view on screen
let timer = null;

async function openFacility(id) {
  current = { id };
  $("fac").hidden = false;
  $("fac-title").textContent = `Facility #${id}`;
  $("fac-status").textContent = "loading…";
  $("fac").scrollIntoView({ behavior: "smooth", block: "start" });
  await refresh();
  clearInterval(timer);
  timer = setInterval(() => { if (!busy) refresh(); }, 20000);
  history.replaceState(null, "", `${location.pathname}?${new URLSearchParams({ ...(BRADBURY ? { net: "bradbury" } : {}), id })}`);
}

async function refresh() {
  if (!current) return;
  try {
    const f = await read("get_facility", [current.id, nowS()]);
    current.f = f;
    render(f);
  } catch (e) {
    $("fac-status").textContent = "not found";
    $("fac-asof").textContent = `Could not read facility #${current.id}: ${short(e)}`;
  }
}
$("fac-reload").addEventListener("click", refresh);

function kv(dl, rows) {
  dl.replaceChildren();
  for (const [k, v] of rows) {
    dl.append(el("dt", null, k));
    const dd = el("dd");
    if (v instanceof Node) dd.append(v);
    else dd.textContent = v;
    dl.append(dd);
  }
}

const PERIOD_STATUS = {
  UPCOMING: "Period not ended",
  TESTING: "Report window open",
  COMPLIANT: "Compliant",
  BREACH: "Covenant breach",
  CURED: "Breach cured",
  WAIVED: "Waived by the lender",
  MISSING: "No official reading (missing)",
  NOT_TESTED: "Not tested: facility closed or accelerated",
};

function render(f) {
  const t = f.terms;
  $("fac-title").textContent = `Facility #${f.id}: ${t.company_name}`;
  setBadge($("fac-status"), f.status);
  const pending = f.as_of > f.stored_up_to;
  $("fac-asof").textContent = `As of ${utcFull(f.as_of)}${pending ? " (set-date steps since the last transaction are projected; they are applied by the next transaction)" : ""}.` +
    (f.closed_reason ? ` Closed: ${f.closed_reason}.` : "");

  const m = f.money;
  kv($("fac-money"), [
    ["Principal outstanding", gen(m.principal)],
    ["Drawn in total", gen(m.drawn_total)],
    ["Undrawn commitment held", gen(m.undrawn_held)],
    ["DSRA held", gen(m.dsra_held)],
    ["Interest and fees owed now", gen(BigInt(m.interest_owed) + BigInt(m.fees_owed))],
    ["Payoff now", gen(m.payoff)],
    ["Paid: fees / interest / principal", `${gen(m.paid_fees)} / ${gen(m.paid_interest)} / ${gen(m.paid_principal)}`],
    ["Default interest accrued", gen(m.default_interest_accrued)],
    ["Margin now", ["CLOSED", "CANCELLED"].includes(f.status) ? `none (facility ${f.status.toLowerCase()}; last band ${f.pricing.band})` : `band ${f.pricing.band}, ${bp(f.pricing.margin_bp)} (all-in ${bp(f.pricing.rate_bp)}${f.pricing.default_interest_on ? ", default add-on on" : ""})`],
    ["Draws", f.draw.allowed ? "allowed now" : f.draw.reason],
  ]);
  const grid = t.grid.map((g) => `${g.upper_leverage_x100 ? "≤ " + x100(g.upper_leverage_x100) : "above"}: ${bp(g.margin_bp)}`).join(" · ");
  kv($("fac-terms"), [
    ["Lender", f.lender],
    ["Borrower", f.borrower],
    ["Commitment", `${gen(t.commitment)} (largest draw ${gen(t.tranche_cap)})`],
    ["Covenants", `leverage ≤ ${x100(t.max_leverage_x100)}, interest cover ≥ ${x100(t.min_cover_x100)}, cash ≥ ${eur(t.min_cash)}`],
    ["Margin grid (by leverage)", grid],
    ["Base rate, fee, default add-on", `${bp(t.base_bp)}, ${bp(t.fee_bp)} on undrawn, ${bp(t.default_bp)}`],
    ["Periods", `${t.num_periods} of ${Math.round(t.period_seconds / 60)} min; first ends ${utcFull(t.first_period_end)}; maturity ${utcFull(t.maturity)}`],
    ["Windows", `report ${t.report_seconds / 60} min, cure ${t.cure_seconds / 60} min; acceleration ${t.grace_seconds / 60} min after an event; availability ends ${utcFull(t.availability_end)}`],
    ["Conversion", `1 GEN = ${eur(t.units_per_gen)}; figures rounded to EUR ${Number(t.resolution).toLocaleString("en-GB")}`],
    ["DSRA required", gen(t.dsra_required)],
  ]);

  // covenant table
  const tb = $("fac-periods");
  tb.replaceChildren();
  const head = el("tr");
  ["Period", "Status", "LTM EBITDA", "Net finance costs", "Total debt", "Cash", "Leverage", "Cover", "Band", "Report"].forEach((h) => head.append(el("th", null, h)));
  const thead = el("thead");
  thead.append(head);
  tb.append(thead);
  const body = el("tbody");
  for (const p of f.periods) {
    const tr = el("tr");
    const c1 = el("td");
    c1.append(el("strong", null, `#${p.period}`), el("br"), el("span", "small", `ends ${utc(p.end)}`), el("br"), el("span", "small", `window to ${utc(p.window_close)}`));
    tr.append(c1);
    const st = el("td");
    st.append(el("span", `pill p-${p.status === "NOT_TESTED" ? "upcoming" : p.status.toLowerCase()}`, PERIOD_STATUS[p.status] || p.status));
    if (p.attempt_count) st.append(el("br"), el("span", "small", `${p.attempt_count} test${p.attempt_count > 1 ? "s" : ""}: ${p.attempts.map((a) => a.kind + (a.reason ? " " + a.reason : "")).join(", ")}`));
    if (p.cure) st.append(el("br"), el("span", "small", `cured ${utc(p.cure.at)}: ${gen(p.cure.principal)} principal prepaid`));
    tr.append(st);
    const o = p.official;
    if (o) {
      const a = o.assessment;
      const fig = o.figures;
      tr.append(el("td", "num", eur(fig.ltm_ebitda)), el("td", "num", eur(fig.ltm_net_finance_costs)), el("td", "num", eur(fig.total_debt)), el("td", `num ${a.cash_ok ? "" : "bad"}`, eur(fig.cash)));
      tr.append(el("td", `num ${a.leverage_ok ? "ok" : "bad"}`, a.leverage_text), el("td", `num ${a.cover_ok ? "ok" : "bad"}`, a.cover_text), el("td", "num", `${a.band}`));
    } else {
      for (let i = 0; i < 7; i++) tr.append(el("td", "num muted", "–"));
    }
    const r = el("td");
    r.append(link(p.report_url, "page"));
    tr.append(r);
    body.append(tr);
  }
  tb.append(body);

  // events
  const ev = $("fac-events");
  ev.replaceChildren();
  if (!f.events.length) ev.append(el("li", "muted", "None."));
  for (const e of f.events) {
    const li = el("li");
    li.append(el("strong", null, e.code), el("span", null, ` ${e.period >= 0 ? "period " + e.period + ", " : ""}fell at ${utcFull(e.at)}`));
    if (e.waived_at) li.append(el("span", "ok", ` · waived ${utc(e.waived_at)}`));
    if (e.remedied_at) li.append(el("span", "ok", ` · remedied ${utc(e.remedied_at)}`));
    ev.append(li);
  }
  if (f.written_off) ev.append(el("li", null, `Written off at closing: principal ${gen(f.written_off.principal)}, interest ${gen(f.written_off.interest)}, fees ${gen(f.written_off.fees)}.`));
  for (const pp of f.pending_payouts || []) ev.append(el("li", "muted", `Pending at the next transaction: ${gen(pp.amount)} to ${shortAddr(pp.to)} (${pp.note})`));

  // transactions recorded for the demo facilities
  const txs = $("fac-txs");
  txs.replaceChildren();
  const list = (NET.txs || {})[String(f.id)] || [];
  if (!list.length) txs.append(el("li", "muted", "Every transaction of this facility is on the explorer; the demo facilities list theirs here."));
  for (const [label, hash] of list) {
    const li = el("li");
    li.append(el("span", null, `${label}: `), link(`${EXPLORER_BASE}/tx/${hash}`, `${hash.slice(0, 10)}…`));
    txs.append(li);
  }
  txs.append((() => { const li = el("li"); li.append(link(`${EXPLORER_BASE}/address/${CONTRACT_ADDRESS}`, "Contract on the explorer")); return li; })());

  // timeline
  const h = $("fac-history");
  h.replaceChildren();
  for (const x of [...f.history].reverse()) {
    const li = el("li");
    li.append(el("span", "when", utcFull(x.at)), el("strong", null, ` ${x.what.replace(/_/g, " ").toLowerCase()}`), el("span", null, x.note ? ` · ${readableNote(x.note)}` : ""));
    h.append(li);
  }
  drawCredits(f);
  drawActions(f);
}

// The contract logs exact wei amounts; the timeline shows them in GEN.
function readableNote(note) {
  return String(note).replace(/\b(\d+) wei\b/g, (_, n) => {
    const w = BigInt(n);
    const txt = gen(w, 6);
    return w > 0n && txt === "0 GEN" ? "<0.000001 GEN" : txt;
  });
}

// What the contract has credited to this facility's parties and not yet sent:
// every payout is a credit that its owner withdraws (covering all facilities).
async function drawCredits(f) {
  const box = $("fac-credits");
  if (!box) return;
  try {
    const [l, b] = await Promise.all([read("get_claimable", [f.lender]), read("get_claimable", [f.borrower])]);
    box.textContent = `Credited and not yet withdrawn (all facilities): lender ${gen(l)}, borrower ${gen(b)}.`;
  } catch { box.textContent = ""; }
}

// ----------------------------------------------------------- accounts

const roles = { lender: null, borrower: null };
const store = {
  get: (k) => { try { return localStorage.getItem(k); } catch { return null; } },
  set: (k, v) => { try { localStorage.setItem(k, v); } catch {} },
};

function setRole(role, next) {
  roles[role] = next;
  $(`${role}-addr`).textContent = next ? `Temporary: ${next.address}` : "No account";
  refreshBalances();
  if (current && current.f) drawActions(current.f);
}
function tempAccount(role) {
  let key = store.get(`pcg.temp.${role}`);
  if (!key) {
    key = generatePrivateKey();
    store.set(`pcg.temp.${role}`, key);
  }
  const account = createAccount(key);
  setRole(role, { client: createClient({ chain: studionet, account }), address: account.address });
}
async function faucet(address) {
  const body = `{"jsonrpc":"2.0","id":1,"method":"sim_fundAccount","params":["${address}",100000000000000000000]}`;
  const r = await fetch(RPC, { method: "POST", headers: { "content-type": "application/json" }, body });
  const j = await r.json();
  if (j.error) throw new Error(j.error.message || "faucet error");
}
async function refreshBalances() {
  for (const role of ["lender", "borrower"]) {
    const r = roles[role];
    $(`${role}-bal`).textContent = "";
    if (!r) continue;
    try {
      const [bal, claim] = await Promise.all([reader.getBalance({ address: r.address }), CONTRACT_ADDRESS ? read("get_claimable", [r.address]) : "0"]);
      $(`${role}-bal`).textContent = `Balance: ${gen(bal)}. Credited by the contract: ${gen(claim)}.`;
      if (BigInt(claim) > 0n) {
        const b = el("button", "ghost", "Withdraw");
        b.type = "button";
        b.addEventListener("click", () => send(r, "withdraw", [], 0n, `Withdraw ${gen(claim)} (${role})`));
        $(`${role}-bal`).append(" ", b);
      }
    } catch {}
  }
}
const acctError = (m) => { $("acct-error").textContent = m; $("acct-error").hidden = !m; };
document.querySelectorAll("[data-temp]").forEach((b) => b.addEventListener("click", () => { acctError(""); tempAccount(b.dataset.temp); }));
document.querySelectorAll("[data-fund]").forEach((b) => b.addEventListener("click", async () => {
  const r = roles[b.dataset.fund];
  acctError("");
  if (!r) return acctError(`Choose a ${b.dataset.fund} account first.`);
  b.disabled = true;
  try { await faucet(r.address); await new Promise((x) => setTimeout(x, 1500)); await refreshBalances(); } catch (e) { acctError(`Faucet: ${short(e)}`); }
  b.disabled = false;
}));
if (!BRADBURY) {
  if (store.get("pcg.temp.lender")) tempAccount("lender");
  if (store.get("pcg.temp.borrower")) tempAccount("borrower");
}

// ------------------------------------------------- transaction lifecycle

const STEPS = [
  ["SENT", "Sent", "Signed and sent."],
  ["PENDING", "Queued", "Waiting for a leader."],
  ["PROPOSING", "Leader works", "One validator runs the method; for a test it reads the report page now."],
  ["COMMITTING", "Validators check", "The others run it on their own and vote."],
  ["REVEALING", "Votes revealed", "Votes are opened and counted."],
  ["ACCEPTED", "Accepted", "A majority agreed; the new state is recorded and any payout is credited."],
  ["FINALIZED", "Finalized", "The appeal window has passed. A withdrawal's GEN reaches the wallet now."],
];
const ORDER = STEPS.map((s) => s[0]);
const FINAL_BAD = {
  UNDETERMINED: "The validators did not agree, so nothing changed. This is the safe outcome when a page is unclear. You can test again while the window is open.",
  CANCELED: "The transaction was cancelled. Nothing changed.",
  LEADER_TIMEOUT: "The leader did not answer in time. Nothing changed. You can try again.",
  VALIDATORS_TIMEOUT: "The validators did not answer in time. Nothing changed. You can try again.",
};
const statusOf = (tx) => String(tx?.statusName ?? tx?.status_name ?? "").toUpperCase();
function drawSteps(cur, failed) {
  const ol = $("steps");
  ol.replaceChildren();
  const at = ORDER.indexOf(cur);
  STEPS.forEach(([key, title, help], i) => {
    const li = el("li");
    li.className = failed && i >= Math.max(at, 0) ? (i === Math.max(at, 0) ? "failed" : "todo") : i < at ? "done" : i === at ? (key === "FINALIZED" ? "done" : "now") : "todo";
    li.append(el("strong", null, title), el("span", null, help));
    ol.append(li);
  });
}
function leaderAnswer(tx) {
  try {
    const lr = tx?.consensus_data?.leader_receipt;
    const r = (Array.isArray(lr) ? lr[0] : lr)?.result;
    if (!r) return null;
    if (r.status === "rollback") return { reverted: String(r.payload || "") };
    const p = r.payload;
    if (p && typeof p === "object" && "readable" in p) { try { return JSON.parse(p.readable); } catch { return null; } }
    return null;
  } catch { return null; }
}

let busy = false;
async function send(who, functionName, args, value, what) {
  if (busy) return null;
  busy = true;
  setButtons(false);
  $("life").hidden = false;
  $("life-what").textContent = what;
  $("life-hash").replaceChildren();
  $("life-note").textContent = "Signing in this browser…";
  drawSteps("", false);
  $("life").scrollIntoView({ behavior: "smooth", block: "nearest" });
  const fire = () => who.client.writeContract({ address: CONTRACT_ADDRESS, functionName, args, value: value || 0n });
  // Never resent automatically: if the first send reached the node, a second
  // one would be a second transaction (a second draw, a second payment).
  let hash, err;
  try { hash = await fire(); } catch (e) { err = e; }
  if (err) {
    drawSteps("SENT", true);
    $("life-note").textContent = `The network did not confirm the send (${short(err)}). It may or may not have gone out, so this page does not resend it: press Reload in a minute and check the facility before trying again.`;
    busy = false;
    setButtons(true);
    return null;
  }
  $("life-hash").append(el("span", null, "Transaction: "), el("code", null, hash), el("span", null, " · "), link(`${EXPLORER_BASE}/tx/${hash}`, "view on the explorer"));
  drawSteps("SENT", false);
  const waitNote = "Simple steps take under a minute; a covenant test, where validators read the report page, takes one to three minutes.";
  let last = "SENT", final = null;
  const t0 = Date.now();
  while (Date.now() - t0 < 8 * 60 * 1000) {
    $("life-note").textContent = `Sent ${Math.round((Date.now() - t0) / 1000)} s ago. ${waitNote}`;
    await new Promise((r) => setTimeout(r, 3000));
    let tx;
    try { tx = await reader.getTransaction({ hash }); } catch { continue; }
    const st = statusOf(tx);
    if (st && st !== last && (ORDER.includes(st) || st === "FINALIZED")) { last = st; drawSteps(st, false); }
    if (st === "ACCEPTED" || st === "FINALIZED") { final = { ok: true, tx }; break; }
    if (FINAL_BAD[st]) { final = { ok: false, st }; break; }
  }
  busy = false;
  setButtons(true);
  if (!final) { $("life-note").textContent = "Not settled after eight minutes. It may still complete; press Reload later."; return null; }
  const refusedStep = (() => { const a = leaderAnswer(final.tx || {}); return !!(a && (a.reverted || a.ok === false)); })();
  if (final.ok && !refusedStep && statusOf(final.tx) !== "FINALIZED") followToFinal(hash);
  if (!final.ok) { drawSteps(last, true); $("life-note").textContent = FINAL_BAD[final.st]; return null; }
  const ans = leaderAnswer(final.tx);
  if (ans && ans.reverted) {
    drawSteps("REVEALING", true);
    $("life-note").textContent = `The contract refused this step: ${ans.reverted}`;
  } else if (ans && ans.ok === false && ans.refunded) {
    drawSteps("REVEALING", true);
    $("life-note").textContent = `The contract refused this step and credited the ${gen(ans.refunded)} straight back to you (withdraw it any time): ${ans.error}`;
  } else if (ans && ans.ok && ans.amount && functionName === "withdraw") {
    $("life-note").textContent = `Accepted: ${gen(ans.amount)} is on its way. It reaches the wallet when the transaction is finalized.`;
  } else if (ans && ans.kind) {
    $("life-note").textContent = `Accepted. Outcome: ${ans.kind}${ans.reason ? " (" + ans.reason + ")" : ""}${ans.status ? "; facility " + ans.status : ""}.`;
  } else {
    $("life-note").textContent = "Accepted by a majority of validators.";
  }
  refreshBalances();
  await refresh();
  return { hash, answer: ans };
}
// After acceptance, keep watching quietly until the transaction is finalized.
async function followToFinal(hash) {
  const t0 = Date.now();
  while (Date.now() - t0 < 40 * 60 * 1000) {
    await new Promise((r) => setTimeout(r, 10000));
    let tx;
    try { tx = await reader.getTransaction({ hash }); } catch { continue; }
    if (statusOf(tx) === "FINALIZED") {
      if ($("life-hash").textContent.includes(hash)) drawSteps("FINALIZED", false);
      refreshBalances();
      if (current) refresh();
      return;
    }
  }
}
function setButtons(on) {
  document.querySelectorAll("#fac-actions button, #btn-create").forEach((b) => (b.disabled = !on));
}

// ------------------------------------------------------------- actions

function action(label, help, fn, input) {
  const row = el("div", "act");
  const b = el("button", null, label);
  b.type = "button";
  const box = el("div");
  box.append(b);
  let inp = null;
  if (input) {
    inp = el("input");
    inp.placeholder = input.placeholder;
    inp.inputMode = "decimal";
    if (input.value) inp.value = input.value;
    box.append(inp);
  }
  row.append(box, el("p", "small", help));
  b.addEventListener("click", () => fn(inp ? inp.value : undefined));
  $("fac-actions").append(row);
}

function drawActions(f) {
  const panel = $("fac-actions-panel");
  $("fac-actions").replaceChildren();
  if (BRADBURY) { panel.hidden = true; return; }
  panel.hidden = false;
  const now = nowS();
  const L = roles.lender && same(roles.lender.address, f.lender) ? roles.lender : null;
  const B = roles.borrower && same(roles.borrower.address, f.borrower) ? roles.borrower : null;
  const anyone = roles.borrower || roles.lender;
  const st = f.status;
  if (!anyone) $("fac-actions").append(el("p", "small", "Use a temporary account (below) to act. Anyone may run a covenant test or apply time; only this facility's lender and borrower can do the rest."));
  const id = f.id;
  if (anyone && ["ACTIVE", "BREACH", "DEFAULT"].includes(st)) {
    for (const p of f.periods) {
      if (now >= p.end && now < p.window_close && !p.official) {
        action(`Run the covenant test for period ${p.period}`, `Validators read ${p.report_url} and must agree on all four figures. Window closes ${inWords(p.window_close - now)}.`, () => send(anyone, "test_period", [id, p.period], 0n, `Covenant test, period ${p.period}`));
      }
    }
    action("Apply time", "Runs the set-date steps up to now (window closes, deadlines, events). The result is the same whoever calls.", () => send(anyone, "apply_time", [id], 0n, "Apply time"));
  }
  if (B && st === "OFFERED") action(`Accept: fund the DSRA (${gen(f.terms.dsra_required)})`, "The exact amount; anything else is credited straight back.", () => send(B, "accept", [id], BigInt(f.terms.dsra_required), "Accept the facility"));
  if (L && st === "OFFERED") action("Cancel the offer", "The commitment is credited back to you.", () => send(L, "cancel", [id], 0n, "Cancel the offer"));
  if (B && f.draw.allowed) action("Draw", `Up to ${gen(f.terms.tranche_cap)} per draw, within the undrawn amount.`, (v) => { const w = toWei(v); if (w) send(B, "draw", [id, w], 0n, `Draw ${v} GEN`); }, { placeholder: "GEN", value: "2" });
  if (B && ["ACTIVE", "BREACH", "DEFAULT", "ACCELERATED"].includes(st)) {
    const owed = BigInt(f.money.interest_owed) + BigInt(f.money.fees_owed);
    if (owed > 0n) action(`Pay interest and fees owed (${gen(owed)})`, "Fees first, then interest. A late payment remedies an E3.", () => send(B, "pay", [id, 0n], owed + 10n ** 15n, "Pay interest and fees"));
    if (BigInt(f.money.principal) > 0n) action("Prepay principal", "After what is owed; name the amount. From maturity or after acceleration all principal is due anyway.", (v) => { const w = toWei(v); if (w) send(B, "pay", [id, w], owed + w + 10n ** 15n, `Prepay ${v} GEN`); }, { placeholder: "GEN", value: "1" });
    if (BigInt(f.money.payoff) > 0n && (now >= f.terms.maturity || st === "ACCELERATED")) action(`Repay everything (${gen(f.money.payoff)})`, "A small surplus is sent so interest accrued while it confirms is covered; the rest comes back.", () => send(B, "pay", [id, BigInt(f.money.principal)], BigInt(f.money.payoff) + 10n ** 16n, "Repay in full"));
  }
  if (B && st === "ACTIVE" && BigInt(f.money.undrawn_held) > 0n) action("Cancel the undrawn commitment", "It goes back to the lender; with nothing owed the facility closes and the DSRA comes back.", () => send(B, "cancel_undrawn", [id], 0n, "Cancel the undrawn commitment"));
  if (B && ["BREACH", "DEFAULT"].includes(st)) {
    for (const p of f.periods) {
      if (p.status === "BREACH" && now < p.cure_deadline) {
        action(`Equity cure for period ${p.period}`, `Before ${utc(p.cure_deadline)}. Gets the exact amount first; the cushion that is not needed comes back.`, async () => {
          const q = await read("quote_cure", [id, p.period, nowS() + 120]);
          if (!q.possible) { $("life").hidden = false; $("life-what").textContent = "Equity cure"; $("life-note").textContent = `No cure is possible: ${q.reason}`; return; }
          send(B, "cure", [id, p.period], BigInt(q.wei) + 10n ** 17n, `Equity cure, period ${p.period}: ${gen(q.principal_prepayment)} principal`);
        });
      }
    }
  }
  if (L && ["BREACH", "DEFAULT"].includes(st)) {
    for (const p of f.periods) {
      const openEv = f.events.some((e) => e.period === p.period && !e.waived_at && !e.remedied_at && e.code !== "E4");
      const covEv = f.events.some((e) => e.period === p.period && !e.waived_at && !e.remedied_at && ["E1", "E2"].includes(e.code));
      const payEv = f.events.some((e) => e.period === p.period && !e.waived_at && !e.remedied_at && e.code === "E3");
      if (["BREACH", "MISSING"].includes(p.status) || covEv) action(`Waive the covenant, period ${p.period}`, "Its breach or missing report and its E1 or E2. A payment default stays.", () => send(L, "waive", [id, p.period, "covenant"], 0n, `Waive the covenant, period ${p.period}`));
      if (payEv) action(`Waive the payment default, period ${p.period}`, "Its E3 only. The amount stays owed.", () => send(L, "waive", [id, p.period, "payment"], 0n, `Waive the payment default, period ${p.period}`));
      void openEv;
    }
  }
  if (L && st === "DEFAULT") {
    const open = f.events.filter((e) => !e.waived_at && !e.remedied_at);
    const from = open.length ? Math.min(...open.map((e) => e.at)) + f.terms.grace_seconds : now;
    action("Accelerate", `${now < from ? `Possible from ${utc(from)}, once the event has continued for ${f.terms.grace_seconds / 60} min. ` : ""}Undrawn commitment credited back to you, the DSRA applied through the waterfall, the whole loan due now.`, () => send(L, "accelerate", [id], 0n, "Accelerate"));
  }
  if (L && st === "ACCELERATED") action("Close with a write-off", "Ends this facility's record; it does not end any legal claim.", () => send(L, "close", [id], 0n, "Close with a write-off"));
}

// --------------------------------------------------------------- create

function nextSlot() {
  const now = nowS();
  let e0 = Math.ceil(now / 3600) * 3600;
  if (e0 - now < 20 * 60) e0 += 3600;
  return e0;
}
function drawSchedule() {
  const e0 = nextSlot();
  const P = TRY_TERMS.periodSeconds;
  $("c-schedule").textContent = `If offered now: accept before ${utcFull(e0)}; period 0 ends ${utc(e0)} (its test is the condition precedent to the first draw), period 1 ends ${utc(e0 + P)}, maturity ${utc(e0 + 2 * P)}.`;
}
for (const [k, b] of Object.entries(TRY_BORROWERS)) {
  const o = el("option", null, `${b.company} (${b.note})`);
  o.value = k;
  $("c-borrower").append(o);
}
drawSchedule();
setInterval(drawSchedule, 30000);

$("create").addEventListener("submit", async (e) => {
  e.preventDefault();
  acctError("");
  if (!roles.lender || !roles.borrower) return acctError("Choose a temporary lender and borrower account first, and give the lender test GEN.");
  if (same(roles.lender.address, roles.borrower.address)) return acctError("Lender and borrower must be different accounts.");
  const commit = toWei($("c-commit").value), cap = toWei($("c-cap").value);
  if (!commit || !cap || cap > commit) return acctError("Commitment and largest draw must be amounts in GEN, with the largest draw no more than the commitment.");
  const slug = $("c-borrower").value;
  const T = TRY_TERMS;
  const e0 = nextSlot();
  const m = e0 + (T.numPeriods - 1) * T.periodSeconds;
  const base = `${SITE}/reports/try/${slug}/s${e0}/`;
  // The demo report pages exist only for a fixed range of slots: refuse to
  // offer a facility whose pages are missing (a missing page reads as no report).
  const okPages = await Promise.all([...Array(T.numPeriods).keys()].map((n) => fetch(`${base}period-${n}.html`, { method: "HEAD", cache: "no-store" }).then((r) => r.ok).catch(() => false)));
  if (okPages.includes(false)) return acctError(`The demo report pages for the ${utcFull(e0)} slot are not published, so this facility could not be read. Please tell us via the GitHub repository.`);
  const args = [roles.borrower.address, TRY_BORROWERS[slug].company, T.currency, base, T.unitsPerGen, T.resolution, cap, e0, T.periodSeconds, T.numPeriods, T.reportSeconds, T.cureSeconds, T.graceSeconds, m, T.yearSeconds, T.baseBp, T.grid, T.feeBp, T.defaultBp, T.maxLeverageX100, T.minCoverX100, T.minCash];
  const r = await send(roles.lender, "create", args, commit, `Offer a facility to ${TRY_BORROWERS[slug].company}`);
  if (!r) return;
  let id = r.answer && r.answer.ok && r.answer.id;
  if (!id) {
    // The receipt did not carry the answer: the lender's latest facility is the new one.
    const mine = await read("get_by_party", [roles.lender.address]).catch(() => []);
    id = mine.length ? mine[mine.length - 1] : null;
  }
  if (id) {
    store.set("pcg.mine", JSON.stringify([...(JSON.parse(store.get("pcg.mine") || "[]")), id].slice(-20)));
    openFacility(id);
  } else if (r.answer && r.answer.ok === false) {
    $("life-note").textContent = `The contract refused the offer and credited the commitment back to you: ${r.answer.error}`;
  }
});

// ---------------------------------------------------------------- start

drawCards();
const qid = new URLSearchParams(location.search).get("id");
if (qid && /^\d+$/.test(qid)) openFacility(qid);
