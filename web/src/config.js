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
    examples: [
      { id: "1", slug: "ashcarrow", company: "Ashcarrow Logistics Ltd" },
      { id: "2", slug: "quillstrand", company: "Quillstrand Materials plc" },
      { id: "3", slug: "brenthollow", company: "Brenthollow Foods SA" },
      { id: "4", slug: "oskendale", company: "Oskendale Retail Group" },
      { id: "5", slug: "tarrowmere", company: "Tarrowmere Aerospace Components" },
    ],
    withdrawals: [],
    txs: {
      "1": [
        [
          "Offer the facility (commitment deposited)",
          "0x262f27d4f7407507b5c3f8354a4aa52bdbcc52f30a3fc3fae45c1cb5e3b12682"
        ],
        [
          "Accept with the wrong DSRA (refused, credited back)",
          "0x4039351893f80cc57509de3a2f8df243ba205900e7b2ff50ca6b67b22508cdf8"
        ],
        [
          "Accept: fund the DSRA",
          "0xb6e58b58c3219114e3fffe1dcb8d55272d7b8115c8ce020806d1294366563cd6"
        ],
        [
          "Test period 0: READ",
          "0xfde2757233bbb0a80489ee76f9cf12c15f6c2099f2cc0eed8eefe51597f45cd5"
        ],
        [
          "Draw tranche 1",
          "0x98632066d687db9564a2cc70d3c1ad5df79e667462f07a05102fccaa913781e9"
        ],
        [
          "Draw tranche 2",
          "0x73c2642b94f519cec9e20ac16e00af29e046d012158e31dad8c47da1f55549a4"
        ],
        [
          "Apply time",
          "0xfd717667bf7d30b8cef5efa9eb7d20cd45c808cd333712602ccf2de4be559ab8"
        ],
        [
          "Pay interest and fees due at period 1",
          "0xe47cb7d3afe5c3d8a240c0e25bbdb6865876440bc68669d10aa99b01bc2a1f12"
        ],
        [
          "Test period 1: READ",
          "0x479376323aba7b1dd5d4e3e16406e5a78c69d9e56b05e58e64a4012245694d11"
        ],
        [
          "Draw tranche 3",
          "0x6d6aa3e92f5da958c5d8b0049ab0cdb23d197c4673c7bb9465c724e31dd47896"
        ],
        [
          "Test period 2: READ",
          "0xd7214aca08d0a5d15969c61e8ce98f2a7c9859f4b1a6f55536a6e6c2b74842d7"
        ],
        [
          "Repay in full at maturity",
          "0x2b2f229e498c29c9b6225918fe31a133068efb34cbbe2c10b6fac6d4372a2994"
        ],
        [
          "Withdraw credits (lender)",
          "0xac5adf68e905d9f9bc1293aa0e0efde84d88e701b2c25bb7745ce75dcffe4a94"
        ],
        [
          "Withdraw credits (borrower)",
          "0xbbf5e4eb6eac229b21d17cca65128f88b1b47375e57fda338e2288252268a47e"
        ]
      ],
      "2": [
        [
          "Offer the facility (commitment deposited)",
          "0xaac3b0ad5f40feb632e73cf25999911eaf427f4ad4936d37cf75e06f3ace0c2f"
        ],
        [
          "Accept: fund the DSRA",
          "0xf3af2787d735128cf096ad03f394e5693a789886c00042eaf7c1d7c9ece74a43"
        ],
        [
          "Test period 0: READ",
          "0xe7c31c226a6fb75cddfef716f624adecde3663e98473167972f62900b8e14134"
        ],
        [
          "Draw",
          "0x6bb3d03365de21294a74a729d9191c5f9d5f13bc0111751cd86c90a0dfa52933"
        ],
        [
          "Apply time",
          "0x509c984d0e4d00a2fb95be5fe95c6ecc5de02e51ae0abbcbf008951b5ed72144"
        ],
        [
          "Pay interest and fees due at period 1",
          "0xfabe176b0af5c9b08e027682b1f1d9573dd83daee01e375fc4920edef734b83c"
        ],
        [
          "Test period 1: READ",
          "0xc4cd9cb44d97552eb4f137bb75283870bd58627d982be09748e4f6778a31a2b8"
        ],
        [
          "Apply time after window close 1 (margin steps up)",
          "0x73619cde478e44740b1125aec25a1c981acc8dc0dc14b745683f18c566042d9f"
        ],
        [
          "Test period 2: READ",
          "0x29b0014b76bfdbe300b24cc42234581220d38e8a0123d96418af55fd44ac4c85"
        ],
        [
          "Repay in full at maturity",
          "0x6c905c3de293795bcb746d07df39445b80ef4707c2f212484491323ad109c4ef"
        ],
        [
          "Withdraw credits (lender)",
          "0x5830d6b2cdb305659666e898117e02ef7fe898c0b4a4006fc2ae2f9d01514e7b"
        ],
        [
          "Withdraw credits (borrower)",
          "0x2b6822e74d913c4e559543851f5dc3f8e190442c68ed4b1e4a6fe1271b1509fb"
        ]
      ],
      "3": [
        [
          "Offer the facility (commitment deposited)",
          "0x0436f20f3819deb92e28369584d391cd6ee7b67031d9f21a330ef2a702298ce8"
        ],
        [
          "Accept: fund the DSRA",
          "0x83ebbba1be042b1f89b7ec7ecd498945cdbb22527c1871196d97f42a3d40991c"
        ],
        [
          "Test period 0: READ",
          "0x9836a0743b694e50372d81cc648fd14f07e43977dc4088f84a7339a4de2823ba"
        ],
        [
          "Draw tranche 1",
          "0xbc3c70f5fe048a34a2fcf0a7e66ae355eec77ed1daec750ec5610e55b2edb619"
        ],
        [
          "Draw tranche 2",
          "0x6a41610b9f73d94d1ba48521a2fe6f3479b8b8fa44884fc7a7c526c676cc3778"
        ],
        [
          "Apply time",
          "0x3c6b515c968e7be42cb1f94a9f258bbd5a45d3efa9c1a2273f0e06160264e459"
        ],
        [
          "Pay interest and fees due at period 1",
          "0xeaf57b377204815608d8fcfa6d8c6c51002fe01ada49d2459f28952c1d328803"
        ],
        [
          "Test period 1: READ",
          "0x2ed32bbb3182f9199caffcd1632b08230fd86a27e755f1b3b6a8f7d0e4739be0"
        ],
        [
          "Cure too small (refused, credited back)",
          "0xbd1801b5efb80fefb0037dfd720a3007be95e908ddece20a1b9244f46c054d2e"
        ],
        [
          "Equity cure (quote plus a cushion that comes back)",
          "0xab27f005311843d3bfbb6fd913632766919a19179dd85daf3e190fc46f7717e0"
        ],
        [
          "Test period 2: READ",
          "0xdd161d2b40dde453a91656db20c25cafa5f8d72fbb8c31996800d927b187c529"
        ],
        [
          "Repay in full at maturity",
          "0x7647be43716a83ffa6b586c520a6e4ef28e533346d14cf2469a469e03086a042"
        ],
        [
          "Withdraw credits (lender)",
          "0x0cabe48449ee5acae8537fe7855387de0460dafdde929b2f393946be687e6067"
        ],
        [
          "Withdraw credits (borrower)",
          "0xdb12363918dd6c3ddfed95deb083f56c0c8d520882b83188f13a0316e32ff933"
        ]
      ],
      "4": [
        [
          "Offer the facility (commitment deposited)",
          "0x2a39914a61cac1d7e7263e9d3b4e6ae5b9457f7093fe34a73e18f2c891a4e7c8"
        ],
        [
          "Accept: fund the DSRA",
          "0xfd0c67b0885fdf2f3305eee36620609a792a9a9f0194aa00c9caff75887dd27e"
        ],
        [
          "Test period 0: READ",
          "0x3be391260762366481ae38527b7ce7d428d56e59a95d50e31aae301d25075554"
        ],
        [
          "Draw",
          "0x7dd5047c7f55534ac6efa3d1209473b005dd90ac92107aa14248b2167a7df470"
        ],
        [
          "Apply time",
          "0x2d33f04c304e8f472375c7d0803f84c0a0430e03681c0db803869d9ffa0bcaed"
        ],
        [
          "Pay interest and fees due at period 1",
          "0x3b139ebf502b307e0cb7e1c17739049a258d7a1b99ec2528cad1d7534dce807f"
        ],
        [
          "Test period 1: READ",
          "0x83fe682133b978229a9635d4dd6a7ccb08f33164c31cdb79467169c2a5bfef70"
        ],
        [
          "Apply time at the cure deadline (E1 falls)",
          "0x3a1411ab7911dde206f03171bc646dfe65d3df9031674feeffd7791dd0f3b162"
        ],
        [
          "Accelerate after the grace period (DSRA applied; the undrawn commitment returned at the availability end)",
          "0x1c0c2f05c7a340e678391d7ae42d954d14a86460086acd823be56cb86056ee28"
        ],
        [
          "Close with a write-off",
          "0x9bd5007e94dd907e39df1c7b84c4e2f4b6f6fe861e5d1c7df356efd4c5596eb9"
        ],
        [
          "Withdraw credits (lender)",
          "0x793503c0753625f540785277ca4a3f3125219e2a1ce4b8031a2a77fa9e17dfdf"
        ],
        [
          "Withdraw credits (borrower)",
          "0xe80a250c4c88b3eff829ec129f6328af356fb467a4db79a72a1e24b25e368191"
        ]
      ],
      "5": [
        [
          "Offer the facility (commitment deposited)",
          "0xb8adc911793337735a4b7096958ab6db57b0078660c201627f928bab6c178cf9"
        ],
        [
          "Accept: fund the DSRA",
          "0x5311dcf2e95a4d5db72e45c6e55a139500ff64b8bc0535cb87f03aacaa5e8407"
        ],
        [
          "Test period 0: READ",
          "0xa116acbba88f28771860662fb9db330c51fa5cf7102d8c46e19e6e8bdcf08e12"
        ],
        [
          "Draw",
          "0xc86e7547939944021b17a684485cc94a21494d7c17493c97b62c8510b00a5b04"
        ],
        [
          "Apply time",
          "0x1b098cae151d8d2836b36b47d5e169adaa9cdacf91928276ab78e629c8310d05"
        ],
        [
          "Pay interest and fees due at period 1",
          "0xfcebe8307bd6c7ae791fbbb7679479d84308ead53f17722e756098032368caa4"
        ],
        [
          "Test period 1: NOT_PUBLISHED",
          "0x82c8a8e935f8cab8fa733283906dea2e9e709df8d3e9251556125f3a499435b5"
        ],
        [
          "Test period 1: NO_READING N2_UNITS_MISSING",
          "0xf379e06955a985844780e981d039b7b37de3de9e1add1bef296262acf51157d4"
        ],
        [
          "Apply time at the cure deadline (E2 falls)",
          "0x486708f44b4afc6c5503f26290e6e2c7796c0b77488e9c3986377b107789b5c5"
        ],
        [
          "Lender waives the covenant for period 1",
          "0xd0047a96be85f2a53ac9f6b4595b7b592e9d3e2c5656c5771074df4104f14e66"
        ],
        [
          "Test period 2: READ",
          "0xac6bdc01eeadf4cffb6b9cc1634d6478986d22d22a8df45874bec3f935d8e972"
        ],
        [
          "Repay in full at maturity",
          "0x6514fde517de6244f20c5543d3c97e06c026dc6ad93672c097b9565ae371cfb4"
        ],
        [
          "Withdraw credits (lender)",
          "0xcd050e97beea7c211d0698d94b0b3cb93f0c0638a48aebdf8ba8eeb45373d310"
        ],
        [
          "Withdraw credits (borrower)",
          "0xd5c8217d0c228b5972c912c687a67f5a09067bba8e0e7c33cce006727f76dff1"
        ]
      ]
    },
  },
  bradbury: {
    key: "bradbury",
    label: "Bradbury testnet",
    name: "GenLayer Testnet Bradbury Phase 2",
    contract: "0x8c17b9742700539D3A2Ec97111073e5c93A6e1f0",
    explorer: "https://scan.bradbury.genlayer.com",
    rpc: "https://rpc-bradbury.genlayer.com",
    readOnly: true,
    examples: [
      { id: "1", slug: "ashcarrow", company: "Ashcarrow Logistics Ltd" },
      { id: "2", slug: "quillstrand", company: "Quillstrand Materials plc" },
      { id: "3", slug: "brenthollow", company: "Brenthollow Foods SA" },
      { id: "4", slug: "oskendale", company: "Oskendale Retail Group" },
      { id: "5", slug: "tarrowmere", company: "Tarrowmere Aerospace Components" },
    ],
    withdrawals: [["Withdraw credits (lender): 4.727134 GEN", "0x58d7d324076f4f98db06f1fff3db68232ee3bf59429ab894043ae4ccbb753dac"], ["Withdraw credits (borrower): 3.118959 GEN", "0x5b759ae6b0789a1dbb8512ee2195e5d625a1015b2477bf558984a626d7f3dda8"]],
    txs: {
      "1": [
        [
          "Offer the facility (commitment deposited)",
          "0x527bc610cf9e452c24991aa23e30a059458959a5b04c9149064d27e14ed62c9c"
        ],
        [
          "Accept with the wrong DSRA (refused, credited back)",
          "0x49f0da542ab406ba29b2a1c871df34a9ca460b17e0123bdbe3a69a0a13aacdc2"
        ],
        [
          "Accept: fund the DSRA",
          "0x8515fa2d2ff97aeab5d26e95f80e379c063657728289bb1450728c1852dfd43b"
        ],
        [
          "Test period 0: READ",
          "0x2600b8bd965631c6c2fa04a1844fb5a68e4e9333fb26c0fae208f4693decd721"
        ],
        [
          "Draw tranche 1",
          "0x9d411bdd964b88d99c30b14e929d90fb7716d65bd43940420b4b76c4433b503e"
        ],
        [
          "Draw tranche 2",
          "0xf0c4ff5e4138c0d0d8c6ad13e0d977a0ddeed08fa2611a9c4a0eed1cf5a9aaad"
        ],
        [
          "Apply time",
          "0xb3f038cf3c2cbf080a22b2cd592047e2028378e96e6627a36641e44284ec3eae"
        ],
        [
          "Pay interest and fees due at period 1",
          "0x3950d37eb0263f33355888736c2c9c35756c5d326a92044df6964552e838ecc3"
        ],
        [
          "Test period 1: READ",
          "0x301eb196cc21e7f37482ba6947c5ef2fcb6c791ac770964e1d0bd924fba4a08c"
        ],
        [
          "Draw tranche 3",
          "0x7d1a36c96b963e277fcd736ecdfa9b9437d9cda2f430e71ee0c6320bfdf9773a"
        ],
        [
          "Test period 2: READ",
          "0x4dc1e1814fb7821d6689fe009ded3d8ed031c509dd88c103412300710b80518c"
        ],
        [
          "Repay in full at maturity",
          "0x916a6d7c760fa86f629c3078871ebd617a2121f3fbe8c54762f7f03f0fcb83a7"
        ]
      ],
      "2": [
        [
          "Offer the facility (commitment deposited)",
          "0xeda43271428ab6f8f71ba79466112cf5e7ec5c0a5734ad68ec723ba7692e613b"
        ],
        [
          "Accept: fund the DSRA",
          "0xdebf58db759cc65ab1489ef89dac23b5d3d88e82ea268777f75d0e6d4f73d17c"
        ],
        [
          "Test period 0: READ",
          "0x4f3ec6bdf146adc588b1acbc69a7d7dc62d287d0ae8cdd5d50738fbb8c60d83b"
        ],
        [
          "Draw",
          "0x0227c81fef21a75881e1e83c049e37302503a0d990a3662f300183efc057dc01"
        ],
        [
          "Apply time",
          "0x479d428cefef82671ae5a6683ef58072bb2555f943a1fa495946ad14daae8a24"
        ],
        [
          "Pay interest and fees due at period 1",
          "0x312e59eee97420ce5f31a660e5c979af9abe1cff657039b4be4ef3dfad68f13b"
        ],
        [
          "Test period 1: READ",
          "0x22bf213015f2a1b862377f739de17b4fd183b42ef5ba53c75c92089f328a54db"
        ],
        [
          "Apply time after window close 1 (margin steps up)",
          "0x339012031ccc3dcb191d6632a6e66654875a22d42659ed630eada837eebec909"
        ],
        [
          "Test period 2: READ",
          "0x3bff9bc42d8e9c726e0c22d53cf604f66b30857479c558f7972c1ee3099124f9"
        ],
        [
          "Repay in full at maturity",
          "0x548884b01556646ca3fcdb7eff4d53ac062a71a557aee5444d64438e797d76b8"
        ]
      ],
      "3": [
        [
          "Offer the facility (commitment deposited)",
          "0xb065503d825e9ce2da3b2ba0e340b4201e8c2b53061cb7e4cebb66b84c6068d9"
        ],
        [
          "Accept: fund the DSRA",
          "0x0c0b7d7f4e0769b0025afc58dbc157c82206828b8da088e183d331faa9939789"
        ],
        [
          "Test period 0: READ",
          "0x8a172d451b00a08ea655f9be37b57f30f67bb2be4c1732e05a9152e1f74c03a5"
        ],
        [
          "Draw tranche 1",
          "0xba8d9d9e47a3836129a3b3f64cdda784526b22981731d07d39b664c8f784929c"
        ],
        [
          "Draw tranche 2",
          "0xb8ccaec300fdbf2e573a03504c2e01b3b8f549891c746b20a6c57134e45658f6"
        ],
        [
          "Apply time",
          "0xa0624953375fcaaf7271ed85a038042b02744729b058416feeab94891cd1c43b"
        ],
        [
          "Pay interest and fees due at period 1",
          "0xfdb992b86d10dfc36cce752087b138620d299a81f9a7560e9458a52ec6439479"
        ],
        [
          "Test period 1: READ (stored after a leader timeout and rotation)",
          "0x3a18b4d36ef0c5bb3b645eb6c21724ee2ef41ac41ee69e2a0a6ddd03c7a19401"
        ],
        [
          "Test period 1 (repeat, refused: already read)",
          "0x82c14fceb35edac5ddb971a82385d7b74ac13a8490cd80eac184afff2e791100"
        ],
        [
          "Test period 1 (repeat, refused: already read)",
          "0xa1f58017ccd20ae89cf27bfdd0055cdc974d4cff630a81fb2d7ca77e8f26c84e"
        ],
        [
          "Test period 1 (repeat, refused: already read)",
          "0xb215e6b9cca6632887b523e4bc02f23f683df804f37e9c7279ffde9293bd4469"
        ],
        [
          "Test period 1 (repeat, refused: already read)",
          "0x468d42473275591ab58bac9d63b5df63626807aa2a0de6b02edabfc03ac40bf5"
        ],
        [
          "Test period 1 (repeat, refused: already read)",
          "0x61fd37da887a5cb6565801c54880a2fa0e98403eb91717a1a67563e117855af1"
        ],
        [
          "Cure too small (refused, credited back)",
          "0x54554d17ea1421fad6a04f562a063c9a825c45574496aa57f70dc4ff8c744052"
        ],
        [
          "Equity cure (quote plus a cushion that comes back)",
          "0xd812732b2077748a4aed9dd4aeee760a8b96f97f0447fb4444981e12f2b973d0"
        ],
        [
          "Test period 2: READ",
          "0xa2ebec2e111a91e9435446a85656663aca459849e8c0ab19d0fc48e2773c888c"
        ],
        [
          "Repay in full at maturity",
          "0xbd9845c4f11a682920c95f36ed13b18bbfa90b1a9de9d4776bb2061131ef19ae"
        ]
      ],
      "4": [
        [
          "Offer the facility (commitment deposited)",
          "0xa0e068dc2061ee4c92d0e9f3469718cfea8ca30ecd65a592587cbb9c4b21e235"
        ],
        [
          "Accept: fund the DSRA",
          "0x2aa28f1bdeeec916887e71e160e9e8f275462a2a47f2ca0aa009198bfcfbaaea"
        ],
        [
          "Test period 0: READ",
          "0x502f9eb1acc536f98a922f7bb646089b6e5318f93f43375056a29d2a3eb6b319"
        ],
        [
          "Draw",
          "0xc8601f5fc9e41fe81c8315e0724c1882796d6fe0be84a26700340554cee24f05"
        ],
        [
          "Apply time",
          "0x7639dbe90d6c6f3d00ed9e477f2de33701b361ef9b3c98c359ab8b1388af6a13"
        ],
        [
          "Pay interest and fees due at period 1",
          "0x9c97c60fc90325b838f326b8276f930c4520e2e685d7fa32b452f8af712f641b"
        ],
        [
          "Test period 1: READ",
          "0xfecffdad20e3e5e28bb90af69933835090fa1b484dc57235ac92cd852c0c6988"
        ],
        [
          "Apply time at the cure deadline (E1 falls)",
          "0xbe383641d7363f342991010d64cd4f5a98a7371ac4291e06260342d546dda2ac"
        ],
        [
          "Accelerate after the grace period (DSRA applied; the undrawn commitment returned at the availability end)",
          "0x550eda51594282db6606b01113f886e95976bef070d20e4e79a2045aa6b2074a"
        ],
        [
          "Close with a write-off",
          "0xc3669a239e178c27649732a8e135e3c176c2677c1f95756b6c2a23c2db859310"
        ]
      ],
      "5": [
        [
          "Offer the facility (commitment deposited)",
          "0x5bbec88602443fca1574d2b15ac505974e2d64dcfbc707a00853eec13ffef3ed"
        ],
        [
          "Accept: fund the DSRA",
          "0x064cf0340218db36d85ad49f95ee1887a33535701447282c8d1b10a4486a30f4"
        ],
        [
          "Test period 0: READ",
          "0x9224bf3c5969df9599daa6f66d167cd1fd45b10de97ebe9190c372e605adc971"
        ],
        [
          "Draw",
          "0xadc3502d106ace7c9fe9c5281e41ac30434419d592dd05608cfdba304f330572"
        ],
        [
          "Apply time",
          "0xd11dc994941e9dce75e16f108668af6184691b90cc098fbfcc993dedba8fd48a"
        ],
        [
          "Pay interest and fees due at period 1",
          "0xb87dcdea7c5d690da4f8ea1e7aa6c099bb23f9925752e53f66bd94f272aa523e"
        ],
        [
          "Test period 1: NOT_PUBLISHED",
          "0x6789c88130532883caaf7b0dc51d8bdcb703568b67bdae32dacb8f2c9572786c"
        ],
        [
          "Test period 1: NO_READING N2_UNITS_MISSING",
          "0x40068269c990133bda27fc3c2aee0b3b9cb83f66bfcd17df64badd8fec62e206"
        ],
        [
          "Apply time at the cure deadline (E2 falls)",
          "0x90c9c68510fcd5453f2d601f77545d29539b765963596ca9dc9d7862fda75742"
        ],
        [
          "Lender waives the covenant for period 1",
          "0x5545de332c05b56487abeda6bf7cde0a50e446118c0fa0aec0f0cc47d3a97f03"
        ],
        [
          "Test period 2: READ",
          "0x85b012ff7a103454a583c7b5980cbcae799404110e796e2c40ece899723fea0c"
        ],
        [
          "Repay in full at maturity",
          "0x2b32ffae7f7cae5d34c8a6d4c5e7bf9f3e4e95af3df9d31acf403f69ccdaff3e"
        ]
      ]
    },
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
  pellingrove: { company: "Pellingrove Foods plc", note: "period-1 leverage 3.74x: a breach you can cure (draw at least 3.1 GEN first)" },
};
