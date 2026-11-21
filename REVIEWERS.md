# PrivateCreditGate: start here (for reviewers, 5 minutes)

**What it is, in plain words:** a private loan whose covenant tests run on GenLayer. Validators read the borrower's own published compliance report and copy four figures; plain code applies the facility agreement (draws, margin, breach, cure, waiver, default, acceleration). Today someone at the lender keys those figures in by hand. Market: private credit, estimated at about $1.7trn to over $3trn ([Universal Asset Owners](https://www.universalassetowners.com/private-credit-market-size/), [S&P Global](https://www.spglobal.com/en/research-insights/special-reports/look-forward/partner-perspectives/unlocking-potential-ahead-with-vanguard/unlocking-the-next-stage-of-private-credit-growth)).

## 1. How consensus binds the money

- **The model copies; code decides.** Each validator renders the frozen report page; its model fills a fixed form (page kind, company, period end, currency, draft flag, decimal mark, and for LTM EBITDA, LTM net finance costs, total debt and cash: the value as printed, scale, LTM label, duplicates, line label). Code checks, converts and rounds them, computes the ratios by cross-multiplication and applies the agreement. README, [What validators do, and what code does](README.md#what-validators-do-and-what-code-does).
- **Exact agreement on everything stored.** A validator accepts the leader only if the outcome kind (READ, NOT_PUBLISHED, NO_READING), the reason code and, for a READ, all four figures after conversion and rounding equal its own. Every ratio, covenant result, margin band and money effect is computed in code from that agreed reading.
- **Every money effect has a set date.** Cure deadlines, events of default, margin changes and default interest fall on dates frozen at creation and run at the start of every write by the transaction's own timestamp, so the result does not depend on who calls. README, [Every money effect has a set date](README.md#every-money-effect-has-a-set-date).
- **Payouts are credits**; each address withdraws its own. The balance reconciles as `get_locked()` + `get_claims_total()`.

## 2. Check it in five steps

1. Open the site: https://privatecredit.brilliantnodes.com and click any of the five live facilities (every reading links the report page the validators read, and every transaction).
2. Import the Studio contract: [`0x6f07…f478`](https://studio.genlayer.com/?import-contract=0x6f07a7aa418701c7f02C54BE13cA776De7B1f478) and call `get_rules()` or `get_facility(id, at)`.
3. Run your own facility on the site with free temporary accounts (Kelvardine stays compliant; Pellingrove breaches leverage in period 1, which you can cure).
4. Read the five stories in the README ([Live runs](README.md#live-runs-second-deployment-17-november-2026)): compliant; margin steps up; breach cured with equity; uncurable breach, acceleration and write-off; late report waived.
5. Testnet Bradbury: [`0x8c17…e1f0`](https://scan.bradbury.genlayer.com/address/0x8c17b9742700539D3A2Ec97111073e5c93A6e1f0), 63 transactions, all decided by majority agreement; record checked against the chain, 63 of 63 match ([`examples/live/bradbury-bradbury-2-merged.json`](examples/live/bradbury-bradbury-2-merged.json)).

## 3. Links

- Video (71 s): https://www.youtube.com/watch?v=d7g2sU8bzn0
- Source: [`contracts/privatecredit_gate.py`](contracts/privatecredit_gate.py)

*Every company, figure and report page is fictional. Test GEN only. Not an offer of credit.*
