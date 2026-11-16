# PrivateCreditGate

**A covenant-gated credit facility on GenLayer: validators read the borrower's published compliance report, and plain code applies the facility agreement.**

> Test GEN only, on GenLayer Studio and Testnet Bradbury Phase 2. Every company, figure and report page is fictional (Harbourline Logistics Ltd, Quarrystone Materials plc, Brightwater Foods SA, Northgate Retail Group, Fenwick Aerospace Components). MIT licence.

## The trust problem

In private credit a lender commits money that the borrower draws in stages. Every period the borrower publishes figures, and covenant tests on those figures decide three things: whether new money may be drawn, what margin applies, and whether the lender may call the loan. Today someone at the lender reads each compliance certificate and keys the numbers in by hand. Mistakes, delays and arguments about "what the report says" all happen at that step, and disputes end with lawyers.

PrivateCreditGate moves that step onto GenLayer. Validators each read the borrower's own published report and copy four figures into a fixed form. Plain Python checks them, computes the ratios and applies the facility agreement. Money moves only on figures that every accepting validator copied exactly the same.

## How it works

1. **Offer.** The lender calls `create` with the whole commitment (payable). Every term is frozen: borrower, company name, currency, one report address per period (`report_base_url` + `period-{n}.html`), covenants, margin grid, rates, dates and windows.
2. **Accept.** The borrower funds a debt-service reserve (DSRA) with `accept` (payable, exact amount): one period's interest on the whole commitment at the top margin band. Accepting means agreeing to every frozen term, including the report addresses.
3. **Test.** After each period end, anyone may call `test_period` during that period's report window. The first READ is the period's official reading.
4. **Draw.** The borrower draws tranches with `draw` while the facility is ACTIVE, before `availability_end`, within the tranche cap. From each period end until that period has a compliant (or cured or waived) official reading, draws stop. The period-0 reading is the condition precedent to the first draw.
5. **Pay.** The borrower pays with `pay` (payable). The payment goes to fees, then interest, then principal that is due (all of it from maturity or after acceleration). Before that, principal is prepaid only up to the `prepay` amount the borrower names. Any excess comes back.
6. **Breach, cure, waiver.** A failed covenant puts the facility in BREACH. Before the cure deadline the borrower may send an equity cure (`cure`, payable). The lender may `waive` a period.
7. **Default and acceleration.** Events of default fall on fixed dates. In DEFAULT the lender may `accelerate`: the undrawn commitment comes back, the DSRA is applied through the waterfall and the whole loan is due. After acceleration the lender may `close` with a write-off.
8. **Close.** The facility closes once nothing is owed and nothing is left to draw. The DSRA goes back to the borrower. The borrower may `cancel_undrawn` at any time.

Transfers are messages that run when a transaction is **finalized**, so an appeal can still change an outcome before any GEN moves.

## What validators do, and what code does

**The model copies; code decides.** For each period, every validator renders the frozen page, and its model fills in a fixed form:
- the page kind;
- the company name;
- the period end as printed;
- the currency;
- whether the figures are marked draft;
- the decimal mark;
- for each of the four figures: the value exactly as printed (as text), its scale, whether it is labelled LTM, whether the page shows it in more than one version, and the line label copied verbatim.

The four figures are LTM EBITDA, LTM net finance costs, total debt and cash.

Plain Python then does everything else:
- checks the company, the period end (to the minute), the currency, the LTM labels and the scales;
- converts each figure to whole currency units with integer arithmetic;
- decides whether a finance-cost line is a cost or income from its label (see below);
- rounds every figure to the facility's resolution against the borrower: debt and finance costs up, EBITDA and cash down;
- decides the outcome.

**Agreement is exact on everything stored.** A validator accepts the leader's result only if it equals its own: the outcome kind (READ, NOT_PUBLISHED or NO_READING), the reason code of a NO_READING, and, for a READ, all four figures. Nothing is tolerated. So the stored record, and every ratio, covenant result, margin band and money effect computed from it, is the same whichever validator leads.

A NO_READING binds nothing, so a disagreement about it only means the test can be run again.

After agreement, code compares the reported total debt with this facility's own principal at the period end, converted at the frozen `units_per_gen`. A report showing less debt than this facility alone contradicts the chain and becomes a NO_READING (`N2_DEBT_BELOW_DRAWN`).

**Only READ is final.** NOT_PUBLISHED and NO_READING are recorded and bind nothing. If there is no READ by the window close, the report counts as missing.

## Rules

| Area | Rule |
|---|---|
| Leverage | Passes if EBITDA > 0 and (debt − cash − cure) × 100 ≤ `max_leverage_x100` × EBITDA (350 means 3.50x). Compared by cross-multiplication, never as a rounded ratio. Net debt ≤ 0 with positive EBITDA is 0x. |
| Interest cover | Passes if net finance costs ≤ 0, or EBITDA × 100 ≥ `min_cover_x100` × net finance costs. |
| Minimum cash | Passes if cash ≥ `min_cash`. |
| Finance-cost sign | Decided from the line label in code. A label naming only costs, expense or charges is a cost, whatever its brackets, because reports print expenses in brackets. A label naming only income is income as printed, so a negative income is a cost. A label naming both must bracket exactly one of them as a whole word: "income/(costs)" means a bracketed figure is a cost, "(income)/costs" means a bracketed figure is income. Anything else, including "costs (income statement)", is a NO_READING. |
| Margin | Up to four leverage bands, with inclusive upper edges, and margins that never fall. The band comes from the uncured leverage; EBITDA ≤ 0 gives the top band. It applies from the window close, and a missing report applies the top band. |
| Interest and fees | Principal × (base + margin, plus the default add-on while an event of default continues) × seconds ÷ (10,000 × `year_seconds`). Accrued as an exact numerator and rounded down once, so splitting time into more steps never changes an amount. A commitment fee accrues on the undrawn amount until the availability end. Interest and fees are due at every period end from period 1. |
| E1 | A covenant breach not cured or waived by the cure deadline (window close + `cure_seconds`). |
| E2 | No official reading by the window close, and not waived by the cure deadline. |
| E3 | Interest and fees due at a period end still unpaid `cure_seconds` later. Remedied once paid. |
| E4 | Principal unpaid `cure_seconds` after maturity (the last period end). Cannot be waived. |
| Equity cure | Must arrive before the cure deadline; at most 2 per facility, never in consecutive periods. The GEN sent pays fees and interest owed first, then prepays exactly the principal the cure needs, and the rest comes back. Only that principal counts, converted at `units_per_gen` and deducted from net debt for that test. It fixes the leverage test only. `quote_cure` gives the exact amount for a given time, or says why no cure is possible. |
| Waiver | The lender may waive a period's breach or missing report, and its E1, E2 or E3 events. Each waiver is recorded. |
| Waterfall | Fees, then interest (default interest included), then principal that is due, plus any prepayment named. Any excess comes back. |
| DSRA | One period's interest on the whole commitment at the top band, rounded up. Held as cash collateral, applied only on acceleration, returned at closing. |

## Every money effect has a set date

The new margin applies from the window close, never from when the test happened. Cure deadlines, E1–E4, default interest and accrual splits all fall on dates fixed at creation. These steps run at the start of every write, using the transaction's own timestamp, so the result does not depend on who calls first or in what order.

The facility's clock never runs backwards. A transaction stamped earlier than steps already applied is handled at the stored time. Anyone may call `apply_time`.

| Money | Direction | When |
|---|---|---|
| Commitment | lender → contract | `create` |
| DSRA | borrower → contract | `accept` |
| Draws | contract → borrower | `draw` |
| Payments and cures | borrower → lender, through the waterfall (excess back) | `pay`, `cure` |
| Undrawn commitment | contract → lender | availability end, `cancel_undrawn`, acceleration, or expiry of an unaccepted offer |
| DSRA | contract → lender (claims) and borrower (rest) | acceleration |
| DSRA | contract → borrower | closing |

A payable call never reverts after money arrives: any refused request sends the value straight back with the reason. Every write checks that what was held plus what arrived equals what is held now plus what left.

## Limits and disclosures

- **Trust in the published figures.** The facility trusts the borrower's published figures, as a real compliance certificate does. Misreporting is outside what any reading can catch.
- **Agreement risk is the borrower's.** A report that validators cannot agree on by the window close counts as missing, as with a defective certificate. Exact agreement is strict on purpose; the report windows are at least 30 minutes so a test can be retried.
- **Ambiguous figures are refused, never guessed.** Refused formats include:
  - "12.450", which is 12,450 in much of Europe;
  - "6,28" and "0,450";
  - apostrophe separators ("40'000");
  - pages that use a decimal comma;
  - a period end in another time zone or with seconds;
  - a page showing a figure in more than one version, for example reported and adjusted EBITDA, or debt with and without leases (IFRS 16);
  - a finance line without a clear label.

  Each of these is a NO_READING, and at the window close the report counts as missing, which means the top band and then E2. The residual risk is a decimal-comma page whose decimal mark the model misreads as a dot.
- **Report addresses.** The lender sets the report addresses at creation; the borrower agrees to them by accepting.
- **Who tests first.** Within a report window, whoever tests first fixes the moment of the official reading. This changes no money, because margins and deadlines are fixed. Lender, borrower and anyone else may test as soon as the period ends.
- **Late transactions.** A payment stamped before a deadline but processed after a later-stamped transaction is handled at the stored time, so it can count as late. An E3 is then recorded and immediately remedied, and default interest is charged for the gap.
- **Cure money.** The contract cannot tell whether the GEN sent as an equity cure is new equity. It counts only the principal the cure actually prepays. The cure pays all interest accrued on the whole loan first; LMA practice requires only accrued interest on the amount prepaid.
- **Default interest** applies to the whole loan while an event of default continues. LMA usually charges it on overdue amounts only.
- **Condition precedent and grace.**
  - The first draw needs the period-0 reading, which comes after the first period end, not a report from before signing.
  - A failed opening test is treated like any breach: it becomes E1 unless cured or waived.
  - The same grace (`cure_seconds`) applies to payments and to covenants.
  - Draws are allowed while interest due is unpaid but still within its grace.
- **Day count.** `year_seconds` sets the day count: 365 days for ACT/365, 360 days for ACT/360. The demo compresses a year into four 65-minute periods so the amounts are visible.
- **Term facility.** Repaid amounts cannot be redrawn. The undrawn commitment stays available until the availability end unless the borrower cancels it.
- **Write-off.** A write-off ends this facility's record, not any legal claim.
- **Indexes.** The offers list (`get_offers`) is a convenience index of the latest 200 offers to a borrower and can be flooded. A facility can always be opened by id.
- **Finality.** Transfers reach wallets when the transaction is finalized.

## Methods

| Method | Who | What |
|---|---|---|
| `create(...)` payable | lender | Offer a facility; send the whole commitment. |
| `cancel(id)` | lender | Withdraw an offer that is not yet accepted. |
| `accept(id)` payable | borrower | Fund the exact DSRA. |
| `draw(id, amount)` | borrower | Draw a tranche. |
| `pay(id, prepay=0)` payable | borrower | Pay through the waterfall; name any prepayment. |
| `cancel_undrawn(id)` | borrower | Cancel the undrawn commitment. |
| `cure(id, period)` payable | borrower | Equity cure for a leverage breach. |
| `test_period(id, period)` | anyone | Covenant test during the report window. |
| `apply_time(id)` | anyone | Apply set-date steps up to now. |
| `waive(id, period)` | lender | Waive a period. |
| `accelerate(id)` | lender | Call the loan in DEFAULT. |
| `close(id)` | lender | Close after acceleration, writing off the rest. |
| `get_facility(id, at)` | view | The facility, or a projection to time `at` with pending payouts. |
| `quote_cure(id, period, at)` | view | The exact cure amount at time `at`, or why none is possible. |
| `get_rules()` | view | Every rule, for audit. |
| `get_latest`, `get_by_party`, `get_offers`, `get_count`, `get_locked` | view | Indexes and totals. |

## Checks

- `PYTHONPATH=. pytest tests/direct` runs the direct-mode tests, with web pages and the model mocked. They cover:
  - every rule, refusal and money path;
  - set-date timing at every edge, plus a randomised test that keeps the books exact over random action sequences;
  - validator acceptance and refusal, including lying, malformed and one-unit-off leaders, and a different reason;
  - the number parser, including the float trap, European formats, scale words, currencies, time zones and finance labels;
  - the demo pages and stories;
  - a check that the Bradbury build equals this source.
- `PYTHONPATH=. python tools/mutate.py` breaks the contract on purpose, one change at a time, and checks that the tests catch every break: 175 of 175 caught. The equivalent mutants left out are listed in the tool.
- `genvm-lint check contracts/privatecredit_gate.py` runs the GenLayer linter.
- The same test files pass on GenVM v0.6 against the Bradbury build (`bradbury/build/`, made by `tools/port_bradbury.py --pack`).
- Four independent reviews, each by an agent wearing private-credit and GenLayer hats, preceded deployment. Every finding was fixed with a test.

## Live runs

The five demo facilities ran end to end on both networks on 16 November 2026, from offer to close. Real validators read the report pages; nothing was mocked. Every transaction is listed on the site under each facility, and the full record of every step is in `examples/live/`.

| | Studio | Bradbury testnet (Phase 2) |
|---|---|---|
| Contract | [`0xd962…cA01`](https://explorer-studio.genlayer.com/address/0xd9622598107edAaF059A84Bb563bB2765655cA01) | [`0x4170…C67B`](https://scan.bradbury.genlayer.com/address/0x4170241d2F9547EEe7FcD6fdfe6E061f5F87C67B) |
| Facilities | #3 to #7 | #1 to #5 |
| Amounts | commitment 10 GEN, 1 GEN = EUR 1m | commitment 1 GEN of real test GEN, 1 GEN = EUR 10m |
| Record | `examples/live/studio-studio-1.json` (56 transactions) | `examples/live/bradbury-bradbury-1.json` (59 transactions) |
| Report pages | `/reports/<company>/studio-1/` | `/reports/<company>/bradbury-1/` |

Every reading (leverage, cover, band) and every outcome was the same on both networks:

| Company | What happened | End |
|---|---|---|
| Harbourline | Three tranches; interest paid on each date; band 1 every period (leverage 1.73x, 1.79x, 1.67x) | Repaid in full; DSRA returned |
| Quarrystone | Prose-only reports read correctly; leverage 3.01x moved the margin to band 3 at the period-1 window close | Repaid in full |
| Brightwater | Period-1 leverage 3.75x breached 3.50x; the quoted cure of EUR 3.5m prepaid principal, and the surplus came back | Cured; repaid in full |
| Northgate | Period-1 cover 3.11x breached 4.00x; the cure was refused as unable to fix cover; E1 fell at the deadline; accelerated; DSRA applied | Closed by the lender with a write-off |
| Fenwick | Period 1 was first `NOT_PUBLISHED`, then published without units (`N2_UNITS_MISSING`); E2 fell at the deadline; the lender waived | Repaid in full |

On Studio the runner also sent the refusals with value: a wrong DSRA amount and a cure that was too small. Each came straight back with the reason (`refunded` in the record).

Three things happened on Bradbury that a test can't show:
- **Early receipts.** Some receipts came back before the result was applied. The runner then tested again, and the repeat was refused because the period already had its official reading. That is the one-reading rule working on a live network. Each repeat is labelled on the site.
- **A failed round.** In one round (Harbourline, period 1) the validators disagreed. Nothing was stored, and the next test read the period.
- **Payouts.** Payouts (draws, refunds, DSRA returns) are external messages, so each write carried a fee budget for both parties.

## Reuse

The pattern carries over to any agreement that turns on figures someone publishes: royalty audits, revenue-share notes, ESG-linked margins, rent reviews. The pattern has four parts:
- freeze the source address per period;
- let the model copy, not judge;
- convert and decide in code;
- agree exactly on everything stored, and put every money effect on a set date.
