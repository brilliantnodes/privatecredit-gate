// Bradbury helper used by tools/live_cases.py (genlayer-js 2). Usage:
//   npm install            (in this folder)
//   BRADBURY_KEY_FILE=/path/to/key node gl.mjs deploy <contract.py> '<json args>'
//   BRADBURY_KEY_FILE=... node gl.mjs write <address> <fn> '<json args>' <value wei> <payees,comma,separated>
//   BRADBURY_KEY_FILE=... node gl.mjs read <address> <fn> '<json args>'
//   BRADBURY_KEY_FILE=... node gl.mjs tx <hash> | balance <address>
// Prints JSON lines. The key is read from a file and never printed.
// For withdraw(), pass your own address as the only payee: the transaction
// then carries an external-message fee allocation for the transfer to you.
import fs from "node:fs";
import { createClient, createAccount, MessageType, encodeExternalMessageFeeParams } from "genlayer-js";
import { testnetBradbury } from "genlayer-js/chains";
import { TransactionStatus } from "genlayer-js/types";

if (!process.env.BRADBURY_KEY_FILE) { console.log(JSON.stringify({ ok: false, error: "set BRADBURY_KEY_FILE" })); process.exit(1); }
const key = fs.readFileSync(process.env.BRADBURY_KEY_FILE, "utf8").trim();
const account = createAccount(key.startsWith("0x") ? key : "0x" + key);
const RPC = process.env.GL_RPC || "https://rpc-bradbury.genlayer.com";
const chain = { ...testnetBradbury, rpcUrls: { default: { http: [RPC] } } };
const client = createClient({ chain, account });
const [cmd, a1, a2, a3, a4, a5] = process.argv.slice(2);
// Payouts are external messages funded from this transaction's fee deposit:
// one External allocation per payee (100k gas at 1 gwei), unused budget refunded.
const PAYOUT_GAS = 100000n, PAYOUT_GAS_PRICE = 1000000000n;
async function feesFor(payees) {
  const messageAllocations = payees.length ? payees.map((p) => ({ messageType: MessageType.External, onAcceptance: false, recipient: p,
    budget: PAYOUT_GAS * PAYOUT_GAS_PRICE, callKey: "0x" + "00".repeat(32), feeParams: encodeExternalMessageFeeParams({ gasLimit: PAYOUT_GAS, maxGasPrice: PAYOUT_GAS_PRICE }) })) : undefined;
  const e = await client.estimateTransactionFees(messageAllocations ? { messageAllocations } : {});
  console.error("fee estimate (GEN):", Number(e.feeValue) / 1e18, "payees:", payees.length);
  return { distribution: e.distribution, feeValue: e.feeValue, ...(messageAllocations && { messageAllocations: e.messageAllocations }) };
}
const big = (_, v) => (typeof v === "bigint" ? v.toString() : v);
const out = (o) => console.log(JSON.stringify(o, big));

async function receipt(hash) {
  const r = await client.waitForTransactionReceipt({ hash, status: TransactionStatus.ACCEPTED, interval: 5000, retries: 240 });
  return r;
}
function brief(r) {
  const o = {};
  for (const k of ["statusName", "status_name", "status", "result", "resultName", "txExecutionResultName", "recipient", "to_address", "toAddress", "txId"]) if (r?.[k] !== undefined) o[k] = r[k];
  o.keys = Object.keys(r || {}).slice(0, 60);
  return o;
}
try {

  if (cmd === "deploy") {
    const code = fs.readFileSync(a1, "utf8");
    const t0 = Date.now();
    const est = await client.estimateTransactionFees();
    console.error("fee estimate (GEN):", Number(est.feeValue) / 1e18);
    const hash = await client.deployContract({ code, args: JSON.parse(a2 || "[]"), leaderOnly: false, fees: est });
    const r = await receipt(hash);
    out({ ok: true, hash, secs: Math.round((Date.now() - t0) / 1000), receipt: brief(r), raw: r });
  } else if (cmd === "write") {
    const t0 = Date.now();
    const payees = (a5 || "").split(",").filter(Boolean);
    const hash = await client.writeContract({ address: a1, functionName: a2, args: JSON.parse(a3 || "[]"), value: BigInt(a4 || "0"), fees: await feesFor(payees) });
    console.log(JSON.stringify({ sent: hash }));
    let r;
    try { r = await receipt(hash); } catch (e) { out({ ok: false, hash, error: String(e?.message || e).slice(0, 1500) }); process.exit(0); }
    out({ ok: true, hash, secs: Math.round((Date.now() - t0) / 1000), receipt: brief(r), raw: r });
  } else if (cmd === "read") {
    out({ ok: true, result: await client.readContract({ address: a1, functionName: a2, args: JSON.parse(a3 || "[]") }) });
  } else if (cmd === "send") {
    const hash = await client.sendTransaction({ to: a1, value: BigInt(a2) });
    out({ ok: true, hash });
  } else if (cmd === "balance") {
    out({ ok: true, result: (await client.getBalance({ address: a1 })).toString() });
  } else if (cmd === "status") {
    const t = await client.getTransaction({ hash: a1 });
    out({ ok: true, result: { status: t.statusName ?? t.status_name ?? String(t.status), execution: t.txExecutionResultName, resultName: t.resultName } });
  } else if (cmd === "tx") {
    out({ ok: true, raw: await client.getTransaction({ hash: a1 }) });
  }
} catch (e) {
  out({ ok: false, error: String(e?.message || e).slice(0, 1500) });
  process.exit(1);
}
