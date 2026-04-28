A smart contract is a computer program or a transaction protocol that is intended to automatically execute, control or document events and actions according to the terms of a contract or an agreement.[1][2][3][4] The objectives of smart contracts are the reduction of need for trusted intermediators, arbitration costs, and fraud losses, as well as the reduction of malicious and accidental exceptions.[5][2] Smart contracts are commonly associated with cryptocurrencies, and the smart contracts introduced by Ethereum are generally considered a fundamental building block for decentralized finance (DeFi) and non-fungible token (NFT) applications.[6]

The original Ethereum white paper by Vitalik Buterin in 2014[7] describes the Bitcoin protocol as a weak version of the smart contract concept as originally defined by Nick Szabo, and proposed a stronger version based on the Solidity language, which is Turing complete. Since then, various cryptocurrencies have supported programming languages which allow for more advanced smart contracts between untrusted parties.[8]

A smart contract should not be confused with a smart legal contract, which is a traditional, natural-language, legally binding agreement that has selected terms expressed and implemented in machine-readable code.[9][10][11]

Etymology
By 1996, Nick Szabo was using the term "smart contract" to refer to contracts which would be enforced by physical property (such as hardware or software) instead of by law. Szabo described vending machines as an example of this concept.[12][13] In 1998, the term was used to describe objects in rights management service layer of the system The Stanford Infobus, which was a part of Stanford Digital Library Project.[1]

Legal status of smart contracts
See also: Regulation of algorithms and distributed ledger technology law
A smart contract does not typically constitute a valid binding agreement at law.[14] Proposals exist to regulate smart contracts.[9][10][11]

Smart contracts are not legal agreements, but instead transactions which are executed automatically by a computer program or a transaction protocol,[14] such as technological means for the automation of payment obligations[15] such as by transferring cryptocurrencies or other tokens. Some scholars have argued that the imperative or declarative nature of programming languages would impact the legal validity of smart contracts.[16]

In some jurisdictions, legal scholars have examined how the rigidity of smart contracts interacts with traditional doctrines such as contractual unforeseeability. For instance, Colombian legal scholarship has proposed adapting the theory of supervening onerousness (teoría de la imprevisión) to account for the high economic and systemic costs of reversing smart contract effects through judicial intervention, emphasizing the need to internalize these costs and develop new procedural mechanisms for digital environments.[17]

Since the 2015 launch of the Ethereum blockchain, the term "smart contract" has been applied to general purpose computation that takes place on a blockchain. The US National Institute of Standards and Technology describes a "smart contract" as a "collection of code and data (sometimes referred to as functions and state) that is deployed using cryptographically signed transactions on the blockchain network".[18] In this interpretation a smart contract is any kind of computer program which uses a blockchain. A smart contract also can be regarded as a secured stored procedure, as its execution and codified effects (like the transfer of tokens between parties) cannot be manipulated without modifying the blockchain itself. In this interpretation, the execution of contracts is controlled and audited by the platform, not by arbitrary server-side programs connecting to the platform.[19][20]

In 2018, a US Senate report said: "While smart contracts might sound new, the concept is rooted in basic contract law. Usually, the judicial system adjudicates contractual disputes and enforces terms, but it is also common to have another arbitration method, especially for international transactions. With smart contracts, a program enforces the contract built into the code."[21] States in the US which have passed legislation on the use of smart contracts include Arizona,[22] Iowa,[23] Nevada,[24] Tennessee,[25] and Wyoming.[26]

In April 2021, the UK Jurisdiction Taskforce (UKJT) published the Digital Dispute Resolution Rules (the Digital DR Rules), which were intended to enable the rapid resolution of blockchain and crypto legal disputes in Britain.[27]

In 2021, the Law Commission of England and Wales advised that smart legal contracts are capable of being recognized and enforced under existing English law.[1]

Workings
Similar to a transfer of value on a blockchain, deployment of a smart contract on a blockchain occurs by sending a transaction from a wallet for the blockchain.[28] The transaction includes the compiled code for the smart contract as well as a special receiver address.[28] That transaction must then be included in a block that is added to the blockchain, at which point the smart contract's code will execute to establish the initial state of the smart contract.[28] Byzantine fault-tolerant algorithms secure the smart contract in a decentralized way from attempts to tamper with it. Once a smart contract is deployed, it cannot be updated.[29] Smart contracts on a blockchain can store arbitrary state and execute arbitrary computations. End clients interact with a smart contract through transactions. Such transactions with a smart contract can invoke other smart contracts. These transactions might result in changing the state and sending coins from one smart contract to another or from one account to another.[29]

The most popular blockchain for running smart contracts is Ethereum.[30] On Ethereum, smart contracts are typically written in a Turing-complete programming language called Solidity,[31] and compiled into low-level bytecode to be executed by the Ethereum Virtual Machine.[32] Due to the halting problem and other security problems, Turing-completeness is considered to be a risk and is deliberately avoided by languages like Vyper.[33][34] Some of the other smart contract programming languages missing Turing-completeness are Simplicity, Scilla, Ivy and Bitcoin Script.[34] Some newer platforms have explored "asset-oriented" domain-specific languages (such as Scrypto) that treat digital assets as native data types within the language environment to enforce finiteness and safety rules at the compiler level.[35] However, measurements in 2020 using regular expressions showed that only 35.3% of 53,757 Ethereum smart contracts at that time included recursions and loops — constructs connected to the halting problem.[36]

Several languages are designed to enable formal verification: Bamboo, IELE, Simplicity, Michelson (can be verified with Rocq),[34] Liquidity (compiles to Michelson), Scilla, DAML and Pact.[33]

Notable examples of blockchain platforms supporting smart contracts include the following:
Name	Description
Ethereum	Implements a Turing-complete language on its blockchain, a prominent smart contract framework[37]
Bitcoin	Provides a Turing-incomplete script language that allows the creation of custom smart contracts on top of Bitcoin like multisignature accounts, payment channels, escrows, time locks, atomic cross-chain trading, oracles, or multi-party lottery with no operator.[38]
Cardano	A blockchain platform for smart contracts[39]
Solana	A blockchain platform for smart contracts[40]
Tron	A blockchain platform for smart contracts[41]
Tezos	A blockchain platform for smart contracts[42]
Avalanche	A blockchain platform for smart contracts[43]
Processes on a blockchain are generally deterministic in order to ensure Byzantine fault tolerance.[44] Nevertheless, real world application of smart contracts, such as lotteries and casinos, require secure randomness.[45] In fact, blockchain technology reduces the costs for conducting of a lottery and is therefore beneficial for the participants. Randomness on blockchain can be implemented by using block hashes or timestamps, oracles, commitment schemes, special smart contracts like RANDAO[46][47] and Quanta, as well as sequences from mixed strategy Nash equilibria.[44]

Applications
In 1998, Szabo proposed that smart contract infrastructure can be implemented by replicated asset registries and contract execution using cryptographic hash chains and Byzantine fault-tolerant replication.[48] Askemos implemented this approach in 2002[49][50] using Scheme (later adding SQLite[51][52]) as the contract script language.[53]

One proposal for using Bitcoin for replicated asset registration and contract execution is called "colored coins".[54] Replicated titles for potentially arbitrary forms of property, along with replicated contract execution, are implemented in different projects.

As of 2015, UBS was experimenting with "smart bonds" that use the bitcoin blockchain[55] in which payment streams could hypothetically be fully automated, creating a self-paying instrument.[56]

Inheritance wishes could hypothetically be implemented automatically upon registration of a death certificate by means of smart contracts.[according to whom?][57][58] Birth certificates can also work together with smart contracts.[59][60]

Chris Snook of Inc.com suggests smart contracts could also be used to handle real estate transactions and could be used in the field of title records and in the public register.[61][62][63][64][65]

Seth Oranburg and Liya Palagashvili argue that smart contracts could also be used in employment contracts, especially temporary employment contracts, which according to them would benefit the employer.[66][67]

Security issues
The transactions data from a blockchain-based smart contract is visible to all users in the blockchain. The data provides cryptographic view of the transactions, however, this leads to a situation where bugs, including security holes, are visible to all yet may not be quickly fixed.[68] Such an attack, difficult to fix quickly, was successfully executed on The DAO in June 2016, draining approximately US$50 million worth of Ether at the time, while developers attempted to come to a solution that would gain consensus.[69] The DAO program had a time delay in place before the hacker could remove the funds; a hard fork of the Ethereum software was done to claw back the funds from the attacker before the time limit expired.[70] Other high-profile attacks include the Parity multisignature wallet attacks, and an integer underflow/overflow attack (2018), totaling over US$184 million.[71]

Issues in Ethereum smart contracts, in particular, include ambiguities and easy-but-insecure constructs in its contract language Solidity, compiler bugs, Ethereum Virtual Machine bugs, attacks on the blockchain network, the immutability of bugs and that there is no central source documenting known vulnerabilities, attacks and problematic constructs.[37]

Difference from smart legal contracts
Smart legal contracts are distinct from smart contracts. As mentioned above, a smart contract is not necessarily legally enforceable as a contract. On the other hand, a smart legal contract has all the elements of a legally enforceable contract in the jurisdiction in which it can be enforced and it can be enforced by a court or tribunal. Therefore, while every smart legal contract will contain some elements of a smart contract, not every smart contract will be a smart legal contract.[72]

There is no formal definition of a smart legal contract in the legal industry.[73]

A Ricardian contract is a type of smart legal contract.[74]