// Two networks. Studio: free temporary accounts, try every step yourself.
// Bradbury Phase 2: GenLayer's public testnet, shown read-only. Its facilities
// were run end to end with testnet wallets and moved real test GEN.
export const NETWORKS = {
  studio: {
    key: "studio",
    label: "Studio",
    name: "GenLayer Studio (studionet)",
    contract: "0x6f07a7aa418701c7f02C54BE13cA776De7B1f478",
    explorer: "https://explorer-studio.genlayer.com",
    // The five demo facilities run live on this contract (examples/live/studio-studio-2.json).
    examples: [],
    withdrawals: [],
    txs: {},
  },
  bradbury: {
    key: "bradbury",
    label: "Bradbury testnet",
    name: "GenLayer Testnet Bradbury Phase 2",
    contract: "0x8c17b9742700539D3A2Ec97111073e5c93A6e1f0",
    explorer: "https://scan.bradbury.genlayer.com",
    rpc: "https://rpc-bradbury.genlayer.com",
    readOnly: true,
    examples: [],
    withdrawals: [],
    txs: {},
  },
};

// The story each demo borrower tells (examples/demo_cases.json).
export const STORIES = {
  ashcarrow: "Compliant every period: three tranches, interest paid on time, margin band 1, repaid at maturity; the DSRA comes back.",
  quillstrand: "Reports in prose only. Leverage rises from 2.45x to 3.01x, so the margin steps up to band 3 at the period-1 window close.",
  brenthollow: "Period-1 leverage 3.75x breaches 3.50x. A cure that is too small is credited straight back; the right one prepays principal and the facility is ACTIVE again.",
  oskendale: "Period-1 interest cover 3.11x is below 4.00x. No cure can fix cover, so E1 falls at the cure deadline; after the grace period the lender accelerates, the DSRA is applied and the rest is written off.",
  tarrowmere: "The period-1 report is first 'not yet published', then published without units (no reading). The window closes with nothing read: top band, then E2; the lender waives the covenant for that period.",
};

export const NET = NETWORKS[new URLSearchParams(location.search).get("net")] || NETWORKS.studio;
export const CONTRACT_ADDRESS = NET.contract;
export const EXPLORER_BASE = NET.explorer;
export const REPO_URL = "https://github.com/brilliantnodes/privatecredit-gate";
export const SITE = "https://privatecredit.brilliantnodes.com";

// Terms a visitor's own facility uses on Studio (the same as the demo).
export const TRY_TERMS = {
  currency: "EUR",
  unitsPerGen: 1000000,
  resolution: 1000,
  periodSeconds: 3900,
  numPeriods: 3,
  reportSeconds: 1800,
  cureSeconds: 1800,
  graceSeconds: 900,
  yearSeconds: 15600,
  baseBp: 500,
  grid: "250:250,300:325,350:400,*:500",
  feeBp: 50,
  defaultBp: 200,
  maxLeverageX100: 350,
  minCoverX100: 400,
  minCash: 2000000,
};
export const TRY_BORROWERS = {
  kelvardine: { company: "Kelvardine Shipping Ltd", note: "compliant every period" },
  pellingrove: { company: "Pellingrove Foods plc", note: "period-1 leverage 3.73x: a breach you can cure (draw at least 3.1 GEN first)" },
};
