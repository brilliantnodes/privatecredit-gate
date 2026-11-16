// Two networks. Studio: free temporary accounts, try every step yourself.
// Bradbury Phase 2: GenLayer's public testnet, shown read-only. Its facilities
// were run end to end with testnet wallets and moved real test GEN.
export const NETWORKS = {
  studio: {
    key: "studio",
    label: "Studio",
    name: "GenLayer Studio (studionet)",
    contract: "0xd9622598107edAaF059A84Bb563bB2765655cA01",
    explorer: "https://explorer-studio.genlayer.com",
    // The five demo facilities run live on this contract (examples/live/studio-studio-1.json).
    examples: [
      { id: "4", slug: "harbourline", company: "Harbourline Logistics Ltd" },
      { id: "3", slug: "quarrystone", company: "Quarrystone Materials plc" },
      { id: "7", slug: "brightwater", company: "Brightwater Foods SA" },
      { id: "6", slug: "northgate", company: "Northgate Retail Group" },
      { id: "5", slug: "fenwick", company: "Fenwick Aerospace Components" },
    ],
    txs: {
      "3": [
        [
          "Offer the facility (commitment deposited)",
          "0xead92d806a61477a059b0e1ccd87d4cb9cf1c94f82266504c9a864f48a7132dd"
        ],
        [
          "Accept: fund the DSRA",
          "0xab38e266d8d1e4c415cff8ac5a2fd462b03454cc05bbf4f45df53fdb50bcef04"
        ],
        [
          "Test period 0: READ",
          "0x6a2376abaf8d05445c181e2a5c98ce04eaff42aa94b959bd74c961eea38f5aaa"
        ],
        [
          "Draw",
          "0xfddbc3ebce989335d834a8e9506779daff8d40e1826463f9b3034bca60d5ca3f"
        ],
        [
          "Apply time",
          "0xb9cebe99e227b551681e0232e000ca493ccb75eeaf0f5444db09ba2b7d2560ad"
        ],
        [
          "Pay interest and fees due at period 1",
          "0x5900fcbb9cc6255a09989d0344cefbffb5c9abe67516c39043a2a9ae7395b2b9"
        ],
        [
          "Test period 1: READ",
          "0x50e048bacf133077098bda72efb88b4822cb1cfb68372b0093dbff168e5627f8"
        ],
        [
          "Apply time after window close 1 (margin steps up)",
          "0x6ae81c69002f4eb6eb5961258fc54b9d532e79bddfbeb995132da254db41f4ec"
        ],
        [
          "Test period 2: READ",
          "0xc6f3941b368fcf3f13d6acfb8e83d458b25739c150af91a3759aa3be0d38892d"
        ],
        [
          "Repay in full at maturity",
          "0xa5bca84ed6786e39d7a66a6c18c88171b96c4dba5cbaed32a3ce12e8c29dec28"
        ]
      ],
      "4": [
        [
          "Offer the facility (commitment deposited)",
          "0x52753d3f9caa31ccd68c5746eedbbf198950326fd5e2c187ca58f7b6b5ee3bae"
        ],
        [
          "Accept with the wrong DSRA (refused, refunded)",
          "0x5885eda2c1e560c34646303e5fba5e17a907b8aec122f8eaa5ef7f9a07fba0e6"
        ],
        [
          "Accept: fund the DSRA",
          "0x4a3b7d4ace90c387bf8f62acd1777dfc494e9c7e8079dddf470097a681833d11"
        ],
        [
          "Test period 0: READ",
          "0x7968ee7c7f58a5e977accdd40996dcbcfb5f0312c59dbee5b0cacaa51b3a24b1"
        ],
        [
          "Draw tranche 1",
          "0x382a7f2c72236c184a628b555951eea25bfd3fa5738e42af8ae3905531855929"
        ],
        [
          "Draw tranche 2",
          "0xcabb0018b26ae8eeb2e67a99a1fe1809fb1670461a83540177b30c1419b13923"
        ],
        [
          "Apply time",
          "0x5f40d7da789ffc973347eaf931304d8f4e3155a1474603e50ec41c2e7bb9beb1"
        ],
        [
          "Pay interest and fees due at period 1",
          "0xda0563ab83a4a29dafdaa4f094b2684e931af6773f7428fe19e98e333b18d155"
        ],
        [
          "Test period 1: READ",
          "0x3d27068205feb318b66aa8b47aeab08873459ef7e748475d274b403461c49403"
        ],
        [
          "Draw tranche 3",
          "0xb9598833c551f1576e26ce09eb12527813c9b62eb096ecd60169fb7c9f03a7a7"
        ],
        [
          "Test period 2: READ",
          "0x4b25609c5f3804568a387f5b8bff9dd4ffd87afd4a1bd951a674c8df987491fd"
        ],
        [
          "Repay in full at maturity",
          "0xbb7be2c55d0d1bb5443ce7458d5cfc03077a8566039930f802a72ffbf44ade2b"
        ]
      ],
      "5": [
        [
          "Offer the facility (commitment deposited)",
          "0xa5a420cf545620c32517c624c9a7476e7f1348aafec7ef7dd1833a935235eb1a"
        ],
        [
          "Accept: fund the DSRA",
          "0xc7ab7a39c8d0be8a1f8fdb2f0398c9a00bad08d71f7f1286be6158350e26be2b"
        ],
        [
          "Test period 0: READ",
          "0x9422f2dfbd6eaf527e03b8e592d938c9f2b57cce42cbdf48d0f5eda60b677c55"
        ],
        [
          "Draw",
          "0xa087b8ff4f6a545739c9c366c481a91e11ee600f08949a46d3858e63f4a60e36"
        ],
        [
          "Apply time",
          "0x48f5e336c5f5e02a0d3d8baab767dff3e2ea7d88982b7af0e08c6d7eb708105c"
        ],
        [
          "Pay interest and fees due at period 1",
          "0xe44bce7b2fa598b90e54a411cb188dbe4e991b303d298ce193e3148aa4941a72"
        ],
        [
          "Test period 1: NOT_PUBLISHED",
          "0xe11aca146c0b738a3fd0a891576c546f21b3d2ba268ff0ab1961aed479d54b18"
        ],
        [
          "Test period 1: NO_READING N2_UNITS_MISSING",
          "0x4bb6d1e059cf8314165f63371b19b725c80cea90719c242c28eaca848272210b"
        ],
        [
          "Apply time at the cure deadline (E2 falls)",
          "0x73a6c9ede347273f9b727d3ba45155e4f3b1f68ccd4deec4536a6d06fdb91d24"
        ],
        [
          "Lender waives period 1",
          "0xa256402c9d69622f7e467bddf820c7f9f36b3c854e517209dd833a7081d40163"
        ],
        [
          "Test period 2: READ",
          "0x3ffe9f8a092364dc200872e3e43f40b8f09715a086f9ceb0e7ff4045538b678f"
        ],
        [
          "Repay in full at maturity",
          "0x7a8ead4fb6613a93c66211f3d4edef92b69f3bc9fbced6b10f84f337f994b510"
        ]
      ],
      "6": [
        [
          "Offer the facility (commitment deposited)",
          "0x7bcb6d6e652259c69b24f1027c14af31278d997cc8f0c7a70f3e855a554bd50a"
        ],
        [
          "Accept: fund the DSRA",
          "0x66d814b8fe1822f01406e561c25b317592d42a60055bfb752c0e41e002c040fa"
        ],
        [
          "Test period 0: READ",
          "0x53eb3303dfabc6fcf13af919ec6271ba4c45f982372f5493b43a63a48795f1c4"
        ],
        [
          "Draw",
          "0x28f7d86d7983bb333d31f00b6c04bed6b61ea145b0b70e31a13528b42a50febf"
        ],
        [
          "Apply time",
          "0x667918760fa9a59cedc70953d0276e7579867f6e698caac9cf2cd8292dba6a3d"
        ],
        [
          "Pay interest and fees due at period 1",
          "0xacbde8869844fcf2bd13af771fa32c0944f893e98a8a581190b69d942943923a"
        ],
        [
          "Test period 1: READ",
          "0x6dedbaf4d424d6eebf2be435975b8b3b6bc2d68dc420b6bacaf9814be2a6a1e9"
        ],
        [
          "Apply time at the cure deadline (E1 falls)",
          "0xf1e00a795649da015af4dc8e9fb392a6b4d1bd81ac677fd1b07a38897cbb989f"
        ],
        [
          "Accelerate (undrawn back, DSRA applied)",
          "0x5674d8ab627a0b409db89527b28799ed18181a7a5336029caecd084006409eae"
        ],
        [
          "Close with a write-off",
          "0xee99058275a65ac9f411f59236446ec973da9233b822b9259a9cfb2cf51603a9"
        ]
      ],
      "7": [
        [
          "Offer the facility (commitment deposited)",
          "0xe8300f23eb2a07a85a99b9026a590ab0295bc3b975208f3391becef7d13dafbc"
        ],
        [
          "Accept: fund the DSRA",
          "0xf57289dd4739c13cfca6226ddeb8387633c867c5e169b81172d9e9ec480cc094"
        ],
        [
          "Test period 0: READ",
          "0x021586c6f94c4423a5eb69013ba10da2a10898321e1cdfbfbe44d6d6750fa723"
        ],
        [
          "Draw tranche 1",
          "0xdc9f721f9e271175db4a61a15cfe1cdd538547f22a3f7b736063279db39a785a"
        ],
        [
          "Draw tranche 2",
          "0xd1109ec8291c3e1d1768ff0b9dc6de0d3e7d490f1317211cd5984b934e41f3b5"
        ],
        [
          "Apply time",
          "0xb4ebb65e93133919d341213dcdc6d17051131b32c7c68a9f1c41dc678088f1c4"
        ],
        [
          "Pay interest and fees due at period 1",
          "0x13d728bc03d1e9fdc4cee33d8b325c3c5bec28349069a8636951123fed5a5657"
        ],
        [
          "Test period 1: READ",
          "0x13fb3ce0835d2521cab1a9867c07739553a21ea92c30221ff2f72db6f6937895"
        ],
        [
          "Cure too small (refused, refunded)",
          "0xea55e4ca86df3fa8d5a99488e40ab41d08c7710e2011bc9f5166379ba0066e14"
        ],
        [
          "Equity cure (quote plus a cushion that comes back)",
          "0xbedf936a7c3ebdc00f47dcd0b833be89308e46ec3d7a04b6776df8b29ce5c5ea"
        ],
        [
          "Test period 2: READ",
          "0xeb20c7bd92f1dc7ca70c894d1ccd50fcbb6c38f960d782a27cf2ab28517b282e"
        ],
        [
          "Repay in full at maturity",
          "0x6e1862c0ccd9b2f099d34fc48c044937105cb1b6e31cabe67f98def4fe556c89"
        ]
      ]
    },
  },
  bradbury: {
    key: "bradbury",
    label: "Bradbury testnet",
    name: "GenLayer Testnet Bradbury Phase 2",
    contract: "0x4170241d2F9547EEe7FcD6fdfe6E061f5F87C67B",
    explorer: "https://scan.bradbury.genlayer.com",
    rpc: "https://rpc-bradbury.genlayer.com",
    readOnly: true,
    examples: [
      { id: "1", slug: "harbourline", company: "Harbourline Logistics Ltd" },
      { id: "2", slug: "quarrystone", company: "Quarrystone Materials plc" },
      { id: "3", slug: "brightwater", company: "Brightwater Foods SA" },
      { id: "4", slug: "northgate", company: "Northgate Retail Group" },
      { id: "5", slug: "fenwick", company: "Fenwick Aerospace Components" },
    ],
    txs: {
      "1": [
        [
          "Offer the facility (commitment deposited)",
          "0x6e331b5c2d2f65eee46e15ad4f0baca3b5ee9f26901050224f13f702304de4bb"
        ],
        [
          "Accept: fund the DSRA",
          "0x133c82b231779e4f75e7a4b4d5056f8d05838cfde6ead0443057040f32bad86b"
        ],
        [
          "Test period 0: READ",
          "0x8160134121fb68467717d4978aa8a75a0d1209e8745dfa9736ad53f322acef2c"
        ],
        [
          "Test period 0 (repeat, refused: already read)",
          "0xf6d816bf893ae2a1f77c5605ef8830f43f0cba70eaa28ee39f5d9e1bc558bccc"
        ],
        [
          "Draw tranche 1",
          "0x7181e7b4b08f0f5a9cd8d521a2ee61b77f76f896498b53dcd4fca67fd82eee42"
        ],
        [
          "Draw tranche 2",
          "0x7d960457aab0094872dbe1e5a410e3d669b20669dfdae0f7a6312622e7279460"
        ],
        [
          "Apply time",
          "0x803a5bc2ae65875a45775a4b6a2f5bdc8823029305878bffa79a1e85f9083b73"
        ],
        [
          "Pay interest and fees due at period 1",
          "0x6e66c284ec729e6eab9779d1d30a9e8a2707b8a4f73133561e24e5ca5bfbaedf"
        ],
        [
          "Test period 1 (validators disagreed: nothing stored, tested again)",
          "0xe28e3b8a391f04edd04e6f41c46e3e7ccef917a2e7141806a09b9b9d7589640b"
        ],
        [
          "Test period 1: READ",
          "0x17f8845be10102a849cc16438d67cabcc1e8f87035783ad4635330c03cf6176c"
        ],
        [
          "Draw tranche 3",
          "0x746b215e742c33763274bea798bcf057047db4bcdb6d7bc405b203fd6bd8f6dd"
        ],
        [
          "Test period 2: READ",
          "0x8d820edae43a8929b1572540e3ef83aed62749526a40dc23262778e81f4ae0a0"
        ],
        [
          "Test period 2 (repeat, refused: already read)",
          "0x25302ffa358eed1b2444ca08e05bc97d2d39caa5769ea6ab96f67f4a1ad6863d"
        ],
        [
          "Repay in full at maturity",
          "0x2e52c3c10221af44a00cc8b5b2fffec2d38f8c52a50566374f4aa97db4f69420"
        ]
      ],
      "2": [
        [
          "Offer the facility (commitment deposited)",
          "0x20aeee55dcde428b66e27aacc85fb0de0c116ac98c4a388cd1bd76ad31a6c94b"
        ],
        [
          "Accept: fund the DSRA",
          "0xc337eef691c02d24b16593546f55f016578457e00af5d517d04c978ec4132358"
        ],
        [
          "Test period 0: READ",
          "0x53a8279eff3caf8edf96c71828a25dddec950b62525ae39a5b30b1def910e580"
        ],
        [
          "Test period 0 (repeat, refused: already read)",
          "0x7a85ef1c4f27d4ff0ea87a36143115fd017754be3e9bfab3d4586fd422019aad"
        ],
        [
          "Draw",
          "0xc7d878c3f6e16c84c824332dfe316415171d9f3c652311ebd966a371feec1bc2"
        ],
        [
          "Apply time",
          "0xfd1a9749f469bfd44423f0301a29b025098ac6a219784ad37c4eb157fd226bac"
        ],
        [
          "Pay interest and fees due at period 1",
          "0xa01c69e84bf3f03079d5c203764a247e392d3ce62f77ebe6d9e89b7faf57b9fe"
        ],
        [
          "Test period 1: READ",
          "0xbdd7657fbe4e4e937b3bbe9c78a72828bdd3d3e902048384661c3e7c3903985d"
        ],
        [
          "Apply time after window close 1 (margin steps up)",
          "0x2cda1f681cd4f7a1519936a84897b47881982506ae31a254bcfe584c0bf42bce"
        ],
        [
          "Test period 2: READ",
          "0x0547e82b6cdc366b8ef25b7c8e11eb260cdcfb59950dfc0355277e30a58f939f"
        ],
        [
          "Repay in full at maturity",
          "0xbb0d74ef9049855926d5b479fe943a459181f95ac1561aefe0a990dae1f9ad0a"
        ]
      ],
      "3": [
        [
          "Offer the facility (commitment deposited)",
          "0xb9ab173981c736f23643d321696c53e4c0146f6a7cc4abaffcc1bd5ba2e74f1b"
        ],
        [
          "Accept: fund the DSRA",
          "0xe7a6f9378932edbec651e1f00b443154a2e4a3f2c90dabfda816c1cabf7354df"
        ],
        [
          "Test period 0: READ",
          "0x3883fb5a9c8138f3ce8d754ef5199ecc4286f947b90bae7efdb364258219daea"
        ],
        [
          "Test period 0 (repeat, refused: already read)",
          "0x102ba87cc14372f421221ebcb84150d404948b0f1f08de09d694cc07a16a1af7"
        ],
        [
          "Draw tranche 1",
          "0x24ac486b4558ba0a15308884fb82292124e3ccbece48e92c0ebea83fa28774a7"
        ],
        [
          "Draw tranche 2",
          "0x7d4299104109af8216d0f58be3bb6907d2716dab0f54989524291e2f1b434a17"
        ],
        [
          "Apply time",
          "0xebf463910571f797e8bca2853dc0cd8554eb665627c4af35b6d22d72c879ea50"
        ],
        [
          "Pay interest and fees due at period 1",
          "0x1b2cf8ab410856ccd184c507b79ac7ef25f8b1218156d567371ce2de20a1bf83"
        ],
        [
          "Test period 1: READ",
          "0xf58fb31a4f2f34fd094b8875b34108cc71179f12e9e6518734f1c4233bf45cd1"
        ],
        [
          "Equity cure (quote plus a cushion that comes back)",
          "0x92be5c9e54dbaead3e15075d791c13bbd6c875452bc3b25c31f48b073d777431"
        ],
        [
          "Test period 2: READ",
          "0xb18180ebd1e169c8ad6242009682251dd4e603931e0daf19371413c16fe0eed2"
        ],
        [
          "Repay in full at maturity",
          "0xb81ae6cbdf01d713d12b9c364c1eb3a42efe6ec85d460b7bf80ae897f1d93b22"
        ]
      ],
      "4": [
        [
          "Offer the facility (commitment deposited)",
          "0xa10e9f3ed83a3762b8038549ebab11aec4652a820dc2ed006b51a4269bf2bda7"
        ],
        [
          "Accept: fund the DSRA",
          "0x669732ae5a940970605e65ca22625dddb214f9bbb2a52329cf2d442f4cbd51c9"
        ],
        [
          "Test period 0: READ",
          "0x79044c2d94ebbdfbb37f9d921ce256628d53f01a64ee6d8afc34a743991979cb"
        ],
        [
          "Draw",
          "0x6ac189e6f3c802ea0cb54127b806fbc3779817bdee762fde17bc879f95cf7bfc"
        ],
        [
          "Apply time",
          "0xe6f6bd51114b019149dc4f3848279701874c7e2f27897d4d29354074eec54b06"
        ],
        [
          "Pay interest and fees due at period 1",
          "0xd6158bdd04cfaae26b52b120ea738fbd3815493bd574df93549522fa7b329ff8"
        ],
        [
          "Test period 1: READ",
          "0x5845b1d78760fcf85dfa1a8858617a95c939649de70431f66f691bd3f04813d2"
        ],
        [
          "Apply time at the cure deadline (E1 falls)",
          "0xa9e1d94f578382c6d3630806f6cba256ee6b7a771442e7fa4bb8f3cb5d322f00"
        ],
        [
          "Accelerate (undrawn back, DSRA applied)",
          "0x8f91be96d61ded8048a52af6c41326917603a7c9e3f3a17429efa786d5e05be8"
        ],
        [
          "Close with a write-off",
          "0x097dbd04800d274e2b84cc94cd0c2a9f57928de51f6a87c1414f00b2654e4a65"
        ]
      ],
      "5": [
        [
          "Offer the facility (commitment deposited)",
          "0x79bd4a85f8119f07a7eff0e91dfcfc9cba014d6f82a570c243be44451e614efc"
        ],
        [
          "Accept: fund the DSRA",
          "0x0ac2dca640af5ed3ceedf9f8a10d02d4427613e47cfee6da72a4027a817ab215"
        ],
        [
          "Test period 0: READ",
          "0x6e080d8ee6b6b3b8abc1f81adc8b075f74a960f0093bf0cf32897da94e70e520"
        ],
        [
          "Draw",
          "0x50ac034d1b6511579fdddf092f6936ad0b09002f97c66bfa2ae6418d12c2a7a8"
        ],
        [
          "Apply time",
          "0xda84b0baffa9e77ca3699660c8965e0af8317169ac799ba45e49c4b1a917615c"
        ],
        [
          "Pay interest and fees due at period 1",
          "0xb95496edaf123b71ebf4d7442e17fc0696aa204582d2dfc7a0ce9f7216a495f5"
        ],
        [
          "Test period 1: NOT_PUBLISHED",
          "0x5ec87c84088c4ac6ad2fb05991ce556a04535246580dcd03c619557e058fa67e"
        ],
        [
          "Test period 1: NO_READING N2_UNITS_MISSING",
          "0xb5bb4a8ea4509c71faa65a89eb9a254b5c356e5512d9c34aee7efc33a0cc2860"
        ],
        [
          "Apply time at the cure deadline (E2 falls)",
          "0x7ae1a32628212a5fc1f0ca28ba03268e5ccd9b2c7274599d9bc3591f427952c9"
        ],
        [
          "Lender waives period 1",
          "0x8e4dc3c2433d23b11072264ccfafc3ee75fdfb727dae19d87a9917abc947d9a4"
        ],
        [
          "Test period 2: READ",
          "0x577be3a718370bf70ea3e11974934b4cc2e79a56c30e7399766e8e682dbddce0"
        ],
        [
          "Repay in full at maturity",
          "0x7927bb495dee9739b7f1e7c38d977e21d73f11a489a48f43125e96fd15a5d616"
        ]
      ]
    },
  },
};

// The story each demo borrower tells (examples/demo_cases.json).
export const STORIES = {
  harbourline: "Compliant every period: three tranches, interest paid on time, margin band 1, repaid at maturity; the DSRA comes back.",
  quarrystone: "Reports in prose only. Leverage rises from 2.45x to 3.01x, so the margin steps up to band 3 at the period-1 window close.",
  brightwater: "Period-1 leverage 3.75x breaches 3.50x. A cure that is too small comes straight back; the right one prepays principal and the facility is ACTIVE again.",
  northgate: "Period-1 interest cover 3.11x is below 4.00x. A cure cannot fix cover, E1 falls at the cure deadline, the lender accelerates, the DSRA is applied, the rest is written off.",
  fenwick: "The period-1 report is first 'not yet published', then published without units (no reading). The window closes with nothing read: top band, then E2; the lender waives.",
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
  saltmere: { company: "Saltmere Shipping Ltd", note: "compliant every period" },
  ridgeway: { company: "Ridgeway Foods plc", note: "period-1 leverage 3.73x: a breach you can cure (draw at least 3.1 GEN first)" },
};
