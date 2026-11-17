# PrivateCreditGate

**A covenant-gated credit facility on GenLayer: validators read the borrower's published compliance report, and plain code applies the facility agreement.**

**Try it:** https://privatecredit.brilliantnodes.com (GenLayer Studio, every step yourself with free temporary accounts) · https://privatecredit.brilliantnodes.com/?net=bradbury (Testnet Bradbury Phase 2, the live runs, read-only)

**Video (70 s, with voice-over):** https://privatecredit.brilliantnodes.com/video/privatecredit-demo.mp4, made from the Bradbury run by `tools/video/`: `shot.py` takes the site screenshots, `voice.py` makes the voice-over offline with Kokoro-82M (Apache-2.0), and `render2.py data.json --durations build3/durations.json --audio build3/narration.wav` renders it.

> Test GEN only, on GenLayer Studio and Testnet Bradbury Phase 2. Every company, figure and report page is fictional (Ashcarrow Logistics Ltd, Quillstrand Materials plc, Brenthollow Foods SA, Oskendale Retail Group, Tarrowmere Aerospace Components, and for visitors' own facilities Kelvardine Shipping Ltd and Pellingrove Foods plc). Not an offer of credit. MIT licence.

## The trust problem

In private credit a lender commits money that the borrower draws in stages. Every period the borrower publishes figures, and covenant tests on those figures decide three things: whether new money may be drawn, what margin applies, and whether the lender may call the loan. Today someone at the lender reads each compliance certificate and keys the numbers in by hand. Mistakes, delays and arguments about "what the report says" all happen at that step, and disputes end with lawyers.

PrivateCreditGate moves that step onto GenLayer. Validators each read the borrower's own published report and copy four figures into a fixed form. Plain Python checks them, converts and rounds them, computes the ratios and applies the facility agreement. A reading is stored, and money moves on it, only if a majority of validators arrived at exactly the same four figures.

## Using the site

1. **Watch the five live facilities.** Open the site (Studio) or the Bradbury view and click a card. Each facility shows its money, frozen terms, every period's official reading (figures, leverage, cover, band, a link to the report page the validators read), events of default, every transaction with an explorer link, and a timeline of every set-date step.
2. **Run your own on Studio.**
   - Under *Run your own facility*, click *Use a temporary account* for the lender and for the borrower. The keys stay in your browser. Then click *Get 100 test GEN* for each.
   - Pick a borrower: Kelvardine is compliant every period; Pellingrove breaches leverage in period 1, which you can cure. Click *Offer the facility*. The page first checks that the borrower's report pages exist for your slot.
   - Open your facility and act as either side: accept (fund the DSRA), draw, run the covenant test after each period end, pay, cure, waive, accelerate. Every action shows the transaction moving from sent to accepted to finalized.
   - Payouts and refunds are credited to your account. The *Withdraw* button next to each balance sends them to the wallet.
3. **Check it yourself.** `get_rules()` returns every rule on chain. `get_facility(id, at)` shows a facility now or projected to any time. The explorer links show each transaction.

Your facility's first period ends on the next whole hour (UTC) at least 20 minutes away. Each period is 65 minutes, with a 30-minute report window and a 30-minute cure window after each period end, so a full facility runs in about two and a half hours.

## How it works

1. **Offer.** The lender calls `create` with the whole commitment (payable). Every term is frozen:
   - the borrower and company name, and the currency;
   - one report address per period (`report_base_url` + `period-{n}.html`);
   - covenants, margin grid, rates, dates and windows;
   - the grace before acceleration (`grace_seconds`).
2. **Accept.** The borrower funds a debt-service reserve (DSRA) with `accept` (payable, exact amount): one period's interest on the whole commitment at the top margin band. Accepting means agreeing to every frozen term, including the report addresses.
3. **Test.** After each period end, anyone may call `test_period` during that period's report window. The first READ is the period's official reading.
4. **Draw.** The borrower draws tranches with `draw` while the facility is ACTIVE, before `availability_end`, within the tranche cap. From each period end until that period has a compliant (or cured or waived) official reading, draws stop. The period-0 reading is the condition precedent to the first draw.
5. **Pay.** The borrower pays with `pay` (payable). The payment goes to fees, then interest, then principal that is due (all of it from maturity or after acceleration). Before that, principal is prepaid only up to the `prepay` amount the borrower names. Any excess comes back.
6. **Breach, cure, waiver.** A failed covenant puts the facility in BREACH. Before the cure deadline the borrower may send an equity cure (`cure`, payable). The lender may `waive` a period's covenant (breach or missing report, E1 or E2) or its payment default (E3), separately.
7. **Default and acceleration.** Events of default fall on fixed dates. Once an event has continued for `grace_seconds`, the lender may `accelerate`: the undrawn commitment is credited back, the DSRA is applied through the waterfall and the whole loan is due. After acceleration the lender may `close` with a write-off.
8. **Close.** The facility closes once nothing is owed and nothing is left to draw. The DSRA goes back to the borrower. The borrower may `cancel_undrawn` at any time.

**Payouts are credits.** Every payout and refund is credited to its payee inside the contract, and each address takes its own credit with `withdraw(amount)`, where 0 means everything. No write sends GEN to someone else, so no caller's transaction can lose another party's money. On Bradbury a transfer is an external message paid from the sending transaction's fee budget, and a message sent without a budget is dropped. We confirmed this on the network before the change. The contract's balance equals `get_locked()` plus `get_claims_total()`, plus any withdrawal the network dropped. A withdrawal reaches the wallet when its transaction is finalized.

## What validators do, and what code does

**The model copies; code decides.** For each period, every validator renders the frozen page, and its model fills in a fixed form:
- the page kind;
- the company name;
- the period end as printed, with the page's own time zone;
- the currency;
- whether the figures are marked draft;
- the decimal mark;
- for each of the four figures: the value exactly as printed (as text), its scale, whether it is labelled LTM, whether the page shows it in more than one version, and the line label copied verbatim.

The four figures are LTM EBITDA, LTM net finance costs, total debt and cash.

Plain Python then does everything else:
- checks the company, the period end (to the minute, in UTC), the currency, the LTM labels and the scales;
- converts each figure to whole currency units with integer arithmetic;
- decides whether a finance-cost line is a cost or income from its label (see below);
- rounds every figure to the facility's resolution against the borrower: debt and finance costs up, EBITDA and cash down;
- decides the outcome.

**Agreement is exact on everything stored.** A validator accepts the leader's result only if it equals its own: the outcome kind (READ, NOT_PUBLISHED or NO_READING), the reason code of a NO_READING, and, for a READ, all four figures after conversion and rounding. Two copies that differ only in a digit that rounding removes give the same figures and agree. A copy whose figures differ by one unit after rounding does not. So a stored reading is one that a majority computed independently. Every ratio, covenant result, margin band and money effect is then computed from it in plain code.

A NO_READING binds nothing, so a disagreement about it only means the test can be run again.

After agreement, code compares the reported total debt with this facility's own principal at the period end, converted at the frozen `units_per_gen`. A report showing less debt than this facility alone contradicts the chain and becomes a NO_READING (`N2_DEBT_BELOW_DRAWN`).

**Only a READ binds.** NOT_PUBLISHED and NO_READING are recorded and bind nothing. If there is no READ by the window close, the report counts as missing. A READ is final for the contract once accepted. While its transaction can still be appealed, an appeal re-reads the page as it then stands; see the disclosures.

## Rules

| Area | Rule |
|---|---|
| Leverage | Passes if EBITDA > 0 and (debt − cash − cure) × 100 ≤ `max_leverage_x100` × EBITDA (350 means 3.50x). Compared by cross-multiplication, never as a rounded ratio. Net debt ≤ 0 with positive EBITDA is 0x. |
| Interest cover | Passes if net finance costs ≤ 0, or EBITDA × 100 ≥ `min_cover_x100` × net finance costs. |
| Minimum cash | Passes if cash ≥ `min_cash`. |
| Finance-cost sign | Decided from the line label in code. A label naming only costs, expense or charges, bracketed or not ("Net finance costs", "Net finance (costs)"), is a cost whatever the figure's brackets or sign, because reports print expenses in brackets ("Net finance costs (2,150)" is a cost of 2,150). Should such a line ever mean net income, reading it as a cost only lowers interest cover, which errs towards the lender. A label naming only income counts only as net finance income, as printed, so a negative one is a cost. It must say "net", name finance, financing or interest, and have no bracketed side word. A gross line ("Finance income"), "Net income", "Net revenue" and "Net finance (income)" are a NO_READING: the last is ambiguous whichever way its brackets are read. Cost words are costs, expense, charges and payable; income words are income, credit, benefit, gain, receivable and revenue. A label naming both must bracket exactly one of them as a whole word: "income/(costs)" means a bracketed figure is a cost, "(income)/costs" means a bracketed figure is income. Anything else, including a slash with one side ("Interest expense/other") or "costs (income statement)", is a NO_READING. |
| Margin | Up to four leverage bands, with inclusive upper edges, and margins that never fall. The band comes from the uncured leverage; EBITDA ≤ 0 gives the top band. Period 0's band applies from its official reading (no interest accrues before the first draw, which needs that reading). Later bands apply from the period's window close. A missing report applies the top band. |
| Interest and fees | Principal × (base + margin, plus the default add-on while an event of default continues) × seconds ÷ (10,000 × `year_seconds`). Accrued as an exact numerator and rounded down once, so splitting time into more steps never changes an amount. A commitment fee accrues on the undrawn amount until the availability end. Interest and fees are due at every period end from period 1. |
| E1 | A covenant breach not cured or waived by the cure deadline (window close + `cure_seconds`). |
| E2 | No official reading by the window close, and not waived by the cure deadline. |
| E3 | Interest and fees due at a period end still unpaid `cure_seconds` later. Remedied once paid. |
| E4 | Principal unpaid `cure_seconds` after maturity (the last period end). Cannot be waived. |
| Equity cure | Must arrive before the cure deadline; at most 2 per facility, never in consecutive periods. The GEN sent pays fees and interest owed first, then prepays exactly the principal the cure needs, and the rest comes back. Only that principal counts, converted at `units_per_gen` and deducted from net debt for that test. It fixes the leverage test only. `quote_cure` gives the exact amount for a given time, or says why no cure is possible. |
| Waiver | By scope: `covenant` (the period's breach or missing report, and its E1 or E2), `payment` (its E3; the amount stays owed) or `all`. Each waiver is recorded. E4 cannot be waived. |
| Acceleration | In DEFAULT, once the earliest open event of default has continued for `grace_seconds` (at least 10 minutes and at most `cure_seconds`; 15 minutes in the demo). |
| Waterfall | Fees, then interest (default interest included), then principal that is due, plus any prepayment named. Any excess comes back. |
| DSRA | One period's interest on the whole commitment at the top band, rounded up. Held as cash collateral, applied only on acceleration, returned at closing. |

## Every money effect has a set date

Cure deadlines, E1–E4, margin changes, default interest and accrual splits all fall on dates fixed at creation. These steps run at the start of every write, using the transaction's own timestamp. The result therefore does not depend on who calls, and anyone may call `apply_time`.

The facility's clock never runs backwards. A transaction stamped earlier than steps already applied is handled at the stored time, so the order in which the network processes transactions can matter near a deadline:
- **Payment.** A payment stamped just before an E3 date but processed after a later-stamped transaction meets an E3 that has already fallen. The payment remedies it, and default interest is charged for the gap. `grace_seconds` exists for this case: the lender cannot accelerate within it, so a payment that lands within `grace_seconds` still remedies E3.
- **Other near-deadline steps.** A cure, a covenant test, an acceptance or a draw stamped just before its deadline (cure deadline, window close, first period end, period end) but processed after it is refused. Grace does not help these: send them well before the deadline.

| Money | Direction | When |
|---|---|---|
| Commitment | lender → contract | `create` |
| DSRA | borrower → contract | `accept` |
| Draws | contract → borrower (credit) | `draw` |
| Payments and cures | borrower → lender (credit), through the waterfall; excess credited back | `pay`, `cure` |
| Undrawn commitment | contract → lender (credit) | availability end, `cancel_undrawn`, acceleration, or expiry of an unaccepted offer |
| DSRA | contract → lender (claims) and borrower (rest), credits | acceleration |
| DSRA | contract → borrower (credit) | closing |
| Credits | contract → each address's own wallet | `withdraw()` |

A payable call never reverts after money arrives: any refused request credits the value straight back to the sender with the reason. The facility's timeline logs credits to its own lender and borrower. Refunds to anyone else are credited but not logged, so nobody can push a facility's history out of the log. Every write checks that what was held plus what arrived equals what is held now plus what was credited out.

## Limits and disclosures

- **Trust in the published figures.** The facility trusts the borrower's published figures, as a real compliance certificate does. Misreporting is outside what any reading can catch.
- **The figures are public.** The report page is a public web page, and the agreed figures are stored on a public chain. Real private-credit reporting is usually confidential (LMA confidentiality undertakings). The pattern fits borrowers that already publish their figures, such as listed or bond-issuing companies. For confidential reporting it needs validators that can read access-controlled sources.
- **Page format.** Reports must be HTML pages; PDFs are not read. Validators read the rendered text, and only its first 12,000 characters (`PAGE_CHARS`).
- **Whoever hosts the report controls what is read.** The lender sets the report addresses at creation, and the borrower agrees to them by accepting.
  - A borrower should accept only addresses on a host it controls, and should not change a page once it is published.
  - In this demo the pages for the fictional borrowers are hosted on this project's own site. During the Tarrowmere story the period-1 page was replaced on purpose, while its window was open, to show "not yet published" followed by a page without units.
  - Validators read the rendered text of the page, including text a person might not see (white or off-screen text). A borrower publishing its own page has no reason to hide figures. A page that shows conflicting versions is refused.
- **Appeals.** A transaction can be appealed until it is finalized. An appeal re-reads the page as it stands then, so the reading is final only once its transaction is finalized.
- **Agreement risk is the borrower's.** A report that validators cannot agree on by the window close counts as missing, as with a defective certificate. Exact agreement is strict on purpose; the report windows are at least 30 minutes so a test can be retried.
- **Ambiguous figures are refused, never guessed.** Refused formats include:
  - "12.450", which is 12,450 in much of Europe;
  - "6,28" and "0,450";
  - apostrophe separators ("40'000");
  - pages that use a decimal comma;
  - a period end in another time zone or with seconds;
  - a page showing a figure in more than one version, for example reported and adjusted EBITDA, or debt with and without leases (IFRS 16);
  - a finance line without a clear label;
  - a currency written as a symbol joined to a scale ("€m", "12.4 EURm") or as "TEUR", and an en-dash used as a minus sign.

  Each of these is a NO_READING, and at the window close the report counts as missing, which means the top band and then E2.
  - The time-zone check relies on the model copying the zone as printed; the form asks it to and never to convert. A time printed with no zone is read as UTC.
  - The residual risk is a decimal-comma page whose decimal mark the model misreads as a dot.
- **Someone must test.** Nothing runs on its own: a covenant test happens only when someone calls `test_period` during the report window. If nobody does, the period counts as missing at the window close (top band, then E2), even if the page was published. The borrower has the strongest reason to test; the lender or anyone else may.
- **Who tests first.** Within a report window, whoever tests first fixes the moment of the official reading. This changes no money, because margins and deadlines are fixed. Lender, borrower and anyone else may test as soon as the period ends.
- **Cure money.** The contract cannot tell whether the GEN sent as an equity cure is new equity. It counts only the principal the cure actually prepays. The cure pays all interest accrued on the whole loan first; LMA practice requires only accrued interest on the amount prepaid.
- **Default interest** applies to the whole loan while an event of default continues. LMA usually charges it on overdue amounts only.
- **Condition precedent.**
  - The first draw needs the period-0 reading, which comes after the first period end, not a report from before signing.
  - If the period-0 reading fails, nothing can be drawn, and no cure is possible because there is no principal to prepay. A cure sent anyway is credited straight back. At the cure deadline the failure becomes E1 unless the lender waives it, and the lender may then accelerate to take the commitment back.
  - In LMA practice a failed condition precedent simply blocks drawing and is not usually an event of default.
- **Grace periods.** Interest unpaid at a period end becomes E3 after `cure_seconds`, and the lender can accelerate for it only `grace_seconds` later, so the borrower has `cure_seconds` + `grace_seconds` before acceleration for non-payment. A covenant breach has the cure window (`cure_seconds`). Draws are allowed while interest due is unpaid but still within its grace.
- **What the facility agreement covers.**
  - The only events of default are E1–E4. There is no cross-default, insolvency, misrepresentation or change-of-control event.
  - E2 cannot be remedied by delivering the report late; the lender can waive it.
  - The covenant figures follow the borrower's printed labels (LTM EBITDA, net finance costs, total borrowings, cash), not definitions negotiated in a facility agreement.
  - One lender per facility. No transfer, assignment or amendment of terms after creation.
  - An event of default adds default interest but does not move the margin to the top band.
  - The loan is in GEN while the covenants are in the report's currency, converted at a rate frozen at creation (`units_per_gen`). The demo uses 1 GEN = EUR 10m.
- **Day count.** `year_seconds` sets the day count: 365 days for ACT/365, 360 days for ACT/360. The demo compresses a year into four 65-minute periods so the amounts are visible.
- **Demo schedule.** With 65-minute periods, 30-minute report and cure windows and a 15-minute grace, acceleration for a period-1 breach can only come after maturity. In the Oskendale story the lender therefore accelerates a loan that has already matured unpaid, to apply the DSRA and close the facility.
- **Term facility.** Repaid amounts cannot be redrawn. The undrawn commitment stays available until the availability end unless the borrower cancels it.
- **Write-off.** A write-off ends this facility's record, not any legal claim. After a write-off, `get_facility` still reports the written-off interest under `interest_owed` and `payoff`; the site shows 0 for a written-off facility. A payment to a closed facility is credited straight back.
- **Indexes.** The offers list (`get_offers`) is a convenience index of the latest 200 offers to a borrower and can be flooded. A facility can always be opened by id.
- **Withdrawals on Bradbury.** `withdraw(amount)` sends GEN to the caller as an external message, so the transaction must carry an external-message fee allocation for a transfer to the caller's own address. The site's Bradbury view is read-only; with genlayer-js 2 this is a `messageAllocations` entry for your own address, as in our runner (100,000 gas at 1 gwei). A withdrawal sent without one can be dropped by the network, and the amount withdrawn is then gone. A small first `withdraw(amount)` is a cheap way to check your setup.

## Methods

| Method | Who | What |
|---|---|---|
| `create(...)` payable | lender | Offer a facility; send the whole commitment. |
| `cancel(id)` | lender | Withdraw an offer that is not yet accepted. |
| `accept(id)` payable | borrower | Fund the exact DSRA. |
| `draw(id, amount)` | borrower | Draw a tranche (credited). |
| `pay(id, prepay=0)` payable | borrower | Pay through the waterfall; name any prepayment. |
| `cancel_undrawn(id)` | borrower | Cancel the undrawn commitment. |
| `cure(id, period)` payable | borrower | Equity cure for a leverage breach. |
| `test_period(id, period)` | anyone | Covenant test during the report window. |
| `apply_time(id)` | anyone | Apply set-date steps up to now. |
| `waive(id, period, scope)` | lender | Waive a period's covenant, payment default or both. |
| `accelerate(id)` | lender | Call the loan once an event has continued for `grace_seconds`. |
| `close(id)` | lender | Close after acceleration, writing off the rest. |
| `withdraw(amount=0)` | anyone | Take what is credited to the caller, from every facility: everything (0) or the amount named. |
| `get_facility(id, at)` | view | The facility, or a projection to time `at` with pending payouts. |
| `quote_cure(id, period, at)` | view | The exact cure amount at time `at`, or why none is possible. |
| `get_claimable(address)`, `get_claims_total()` | view | Credits not yet withdrawn. |
| `get_rules()` | view | Every rule, for audit. |
| `get_latest`, `get_by_party`, `get_offers`, `get_count`, `get_locked` | view | Indexes and totals. |

## Run it yourself

Tested with Python 3.13 and Node 22.

```
python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt
PYTHONPATH=. pytest tests/direct                 # the 369 tests, no network
python tools/pcg.py deploy                       # your own copy on GenLayer Studio (throwaway key)
cd web && npm ci && npm run dev && cd ..          # the site; PCG addresses are in web/src/config.js
cd tools/bradbury && npm ci && cd ../..          # Bradbury read tools (genlayer-js 2)
python tools/verify_record.py examples/live/bradbury-bradbury-2-merged.json
python tools/check_bradbury_code.py
```

The two Bradbury checks only read, with a throwaway key made for the run (or the key file named in `BRADBURY_READ_KEY`).

## Checks

- `PYTHONPATH=. pytest tests/direct` runs the direct-mode tests (369 tests), with web pages and the model mocked. They cover:
  - every rule, refusal and money path;
  - set-date timing at every edge;
  - a randomised test that keeps the books exact over random action sequences, including withdrawals;
  - validator acceptance and refusal, including lying, malformed and one-unit-off leaders, and a different reason;
  - the number parser, including the float trap, European formats, scale words, currencies, time zones and finance labels;
  - credits and withdrawals (whole and partial), scoped waivers, the acceleration grace (including a late-processed payment), the credit log (parties only), the demo pages and stories;
  - a check that the Bradbury build equals this source.
- `tools/test_v6.sh <venv>` runs the same test files on GenVM v0.6 (genlayer-test 0.30.0rc2) against the packed Bradbury build in `bradbury/build/`, made by `tools/port_bradbury.py --pack`. Only the shared helpers differ (`tests/conftest_v6.py`).
- `PYTHONPATH=. python tools/mutate.py` breaks the contract on purpose, one change at a time, and checks that the tests catch every break: 198 of 198 caught. The equivalent mutants left out are listed in the tool.
- `genvm-lint check contracts/privatecredit_gate.py` runs the GenLayer linter.
- `python tools/verify_record.py examples/live/bradbury-<tag>.json` checks a Bradbury run record against the chain, transaction by transaction.
- **The code on Bradbury.** To fit Bradbury's deployment limits, the contract is deployed as `bradbury/build/privatecredit_gate.py`: the same source, packed by `tools/port_bradbury.py --pack` into a short stub that decompresses and runs it. A test checks that the build unpacks to this source. `python tools/check_bradbury_code.py` reads the deploy transaction ([0x021fd787…748d](https://scan.bradbury.genlayer.com/tx/0x021fd78789d9aa0f570a20199d1bbf139dd6fa4fed486f5566acfded682d748d)) and confirms that its code is byte-identical to the build. On Studio the deployed code is the source file itself.
- Independent reviews, each by an agent wearing private-credit and GenLayer hats, preceded each deployment: four before the first, two before the second, and one of the whole package before submission. Every finding was fixed, or disclosed above.

## Live runs (second deployment, 17 November 2026)

Both runs use the contract in this repository: the source on Studio, the packed build (`bradbury/build/`) on Bradbury. Every transaction is listed on the site with an explorer link, and the records are in `examples/live/`.

| | GenLayer Studio | Testnet Bradbury Phase 2 |
|---|---|---|
| Contract | [`0x6f07…f478`](https://explorer-studio.genlayer.com/address/0x6f07a7aa418701c7f02C54BE13cA776De7B1f478) | [`0x8c17…e1f0`](https://scan.bradbury.genlayer.com/address/0x8c17b9742700539D3A2Ec97111073e5c93A6e1f0) |
| Transactions | 66, all accepted | 63, all decided by majority agreement |
| Covenant tests | 15: 13 READ, 1 NOT_PUBLISHED, 1 NO_READING | 20: the same 15, plus 5 refused repeats |
| Withdrawals | lender and borrower of each facility | lender and borrower, once each at the end |
| Record | `studio-studio-2.json` | `bradbury-bradbury-2-merged.json` (checked against the chain: 63 of 63 match) |

The five stories end the same way on both networks:
- **Ashcarrow Logistics**, compliant throughout: an acceptance with the wrong DSRA is refused and credited back, then three tranches, three readings, repaid at maturity.
- **Quillstrand Materials**, compliant but leverage rises: the margin steps up from band 1 to band 3 at the period-1 window close; repaid at maturity.
- **Brenthollow Foods**, leverage breach in period 1 (3.75x against 3.50x): a cure that is too small is refused and credited back, the equity cure from `quote_cure` prepays the principal needed, period 2 is compliant, repaid at maturity.
- **Oskendale Retail**, interest-cover breach in period 1 (3.11x against 4.00x), which no equity cure can fix: E1 falls at the cure deadline. The loan reaches maturity unpaid, and the undrawn commitment returns to the lender at the availability end. After the grace period the lender accelerates (the DSRA is applied) and closes with a write-off.
- **Tarrowmere Aerospace**, late report: period 1 is first NOT_PUBLISHED, then a page without units (NO_READING, `N2_UNITS_MISSING`). The window closes with no reading (top band), E2 falls, and the lender waives the covenant for period 1. Period 2 is compliant; repaid at maturity.

At the end of the Bradbury run the contract held nothing: `get_locked()` 0, `get_claims_total()` 0, balance 0. The lender withdrew 4.727134 GEN and the borrower 3.118959 GEN, each in one transaction.

**What Bradbury showed.**
- **A leader timeout can still execute.** Brenthollow's period-1 test was first reported as a leader timeout. After leader rotation the same transaction executed and stored the official reading. The runner, which had read the timeout as "nothing stored", tested again five times. Each repeat was refused because the period already had its reading, and nothing changed. The runner now waits for a timed-out transaction's final state before testing again.
- **The continuation.** Once the timeout was reported, a continuation script was started for that facility while the runner was still retrying. The two overlapped for a few minutes: the continuation's refused small cure came before the runner's last repeat. The continuation finished the story (cure, period 2, repayment), and the runner's thread for that facility stopped. `bradbury-bradbury-2.json` and `bradbury-bradbury-2-brenthollow-continued.json` are the two records as written. `tools/merge_continuation.py` combines them into the merged record without changing either. The timed-out step keeps the status first seen under `recorded_status`.
- **Refusals are credited.** Both refused payable calls (wrong DSRA, cure too small) were credited back to the sender in the same transaction, and the senders later withdrew them with the rest.
- **Withdrawals reach the wallet.** Each withdrawal carried an external-message allocation for the caller's own address and was finalized, and each caller's claimable amount fell to 0. The record also shows each wallet's balance change across its withdrawal. The borrower's rose by the amount credited less that transaction's fees. The lender's rose by 0.0998 GEN more than its credit. That interval most likely also took in fee refunds as the lender's last transactions finalized; we did not trace them one by one.

## Reuse

The pattern carries over to any agreement that turns on figures someone publishes: royalty audits, revenue-share notes, ESG-linked margins, rent reviews. The pattern has five parts:
- freeze the source address per period;
- let the model copy, not judge;
- convert and decide in code;
- agree exactly on everything stored, and put every money effect on a set date;
- credit payouts and let each payee withdraw.
