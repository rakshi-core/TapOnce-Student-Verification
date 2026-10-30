# TapOnce --- Privacy-First Student Concession Verification

**Team:** NovaStack\
**Project type:** Hackathon prototype\
**Current status:** Local web prototype with simulated NFC, offline
verification flow, and simulated Tezos settlement.

## Overview

TapOnce is a prototype for verifying student concession eligibility at
campus merchants without requiring students to show a physical college
ID for every purchase.

The proposed flow uses an anonymous university-issued credential. A
student wallet signs a one-time merchant challenge containing the
transaction amount and a counter. The merchant terminal verifies the
credential and signature, checks the challenge and spending limits, and
records an approved transaction for later settlement.

The goal is to make student discount verification faster and more
privacy-conscious, including in situations where campus connectivity is
unreliable.

## The Problem

Campus students are often asked to show a physical student ID to receive
a concession. This can expose identifying information that is not
necessary for a simple eligibility check, slow down checkout, and make
verification difficult when network connectivity is poor.

TapOnce explores a way to prove student eligibility while sharing less
personal information with the merchant.

## Proposed Solution

TapOnce demonstrates five stages:

1.  **Issue:** A university issuer creates and signs an anonymous
    student credential associated with a student's device public key.
2.  **Challenge:** The merchant creates a fresh, one-time challenge for
    a sale.
3.  **Tap:** The student wallet signs the challenge, discounted amount,
    credential ID, and transaction counter.
4.  **Verify:** The merchant terminal checks the issuer signature,
    credential expiry, revocation status, device signature, challenge,
    amount, replay counter, and spending cap.
5.  **Settle:** Approved transactions are added to a local ledger and
    processed by the prototype's `TezosSim` settlement stand-in.

## Features in the Current Prototype

-   Anonymous credential structure: the sample credential does not
    include a student's name, photograph, or roll number.
-   Ed25519 signatures for issuer credentials and student transaction
    packets.
-   One-time merchant challenges.
-   Merchant-side checks for forged credentials, expired or revoked
    credentials, tampered packets, duplicate challenges, wrong
    challenges, replayed counters, and spending-cap violations.
-   Python simulation of student wallet and merchant terminal behavior.
-   Flask web interface with Student Wallet, Merchant Terminal,
    simulated NFC tap, transaction queue, and settlement dashboard.
-   Local batch settlement through `TezosSim`, including duplicate
    `(credential ID, counter)` detection across terminals in the
    simulator.

## Technology Stack

-   **Python** --- simulation and backend logic
-   **Flask** --- local web server and API routes
-   **HTML, CSS, JavaScript** --- browser interface
-   **cryptography** --- Ed25519 signing and verification
-   **Tezos / SmartPy** --- intended blockchain settlement integration;
    see the implementation-status note below

## Architecture

``` text
University Issuer
       |
       | issues signed anonymous credential
       v
Student Wallet
       |
       | signs one-time challenge + amount + counter
       v
Merchant Terminal
       |
       | verifies credential and transaction packet
       v
Local Pending Transaction Ledger
       |
       | batch settlement in current prototype
       v
TezosSim (local simulation only)
```

The browser communicates with the Flask backend. The backend uses the
classes in `tapsim.py` for credential issuance, wallet signing, merchant
verification, and simulated settlement.

## Project Structure

``` text
TapOnce/
├── app.py
├── tapsim.py
├── requirements.txt
├── README.md
├── .gitignore
├── templates/
│   └── index.html
└── static/
    ├── style.css
    └── script.js
```

If the repository includes a SmartPy contract source file, place it in a
clearly named folder such as `contracts/` and document its network and
deployment status separately. Do not imply that the Flask demo calls
that contract unless the integration has actually been implemented and
tested.

## Run Locally

### Requirements

-   Python 3.10 or later recommended
-   pip
-   A modern web browser

### 1. Clone the repository

``` bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd TapOnce
```

Replace `<YOUR_GITHUB_REPOSITORY_URL>` with the actual repository clone
URL.

### 2. Create and activate a virtual environment (recommended)

**Windows PowerShell**

``` powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**macOS / Linux**

``` bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

``` bash
python -m pip install -r requirements.txt
```

### 4. Start the application

``` bash
python app.py
```

Open `http://127.0.0.1:5000` in your browser. Keep the terminal running
while using the local interface. Press `Ctrl+C` in the terminal to stop
the Flask development server.

## Demo Flow

1.  Open the local TapOnce page.
2.  In **Merchant Terminal**, enter an item and its original price.
3.  Select **Create sale challenge**.
4.  Select **Simulate NFC tap** to create a signed student packet and
    send it to the merchant verifier.
5.  Check the verification result and pending transaction queue.
6.  Select **Sync & settle demo batch** to process pending entries using
    `TezosSim`.
7.  Use **Reset demo** to restart the in-memory demonstration session.

## Implementation Status and Limitations

This repository is a prototype. These distinctions are important:

-   **NFC is simulated.** The Python prototype passes data in software;
    it does not read a physical NFC card or phone.
-   **Secure Element is simulated.** The Ed25519 private key is
    generated and held by the Python wallet object; it is not stored in
    a hardware-backed Secure Element.
-   **Offline behavior is a simulation.** The merchant verification
    logic demonstrates local verification and a pending ledger. The
    current Flask demo stores state in server memory; it does not
    provide durable offline storage, multi-device synchronization, or
    automatic reconnect synchronization.
-   **Tezos settlement is simulated in the current web demo.**
    `TezosSim` uses an in-memory spent-token record. The web demo does
    not submit a transaction to a Tezos network and does not produce a
    real transaction hash or on-chain confirmation.
-   **SmartPy deployment and frontend integration must be verified
    separately.** A deployed contract, if present, does not mean this
    Flask application is connected to it. Document the exact network,
    contract address, entrypoints, and tested transaction flow only
    after verifying them.
-   **Prototype security is not production security.** Keys, credential
    issuance, revocation distribution, persistence, concurrency,
    merchant authentication, and offline double-spend controls require
    further design and testing before real-world use.

The interface labels settlement as simulated so demo results are not
mistaken for blockchain confirmations.

## Security and Privacy Notes

-   Do not commit `.env` files, private keys, seed phrases, passwords,
    API tokens, or real student records.
-   Use synthetic data for demonstrations.
-   Do not reuse sample/test secrets as production secrets.
-   Review all files and Git history before making the repository
    public. Removing a secret from the latest commit does not remove it
    from earlier Git history.

## Roadmap

-   Persistent transaction storage and a durable offline queue.
-   Secure key storage using a supported device-backed key store.
-   Tested NFC integration.
-   A defined credential revocation update mechanism for offline
    merchants.
-   Stronger offline double-spend controls across multiple terminals.
-   Integration tests for the SmartPy contract and Flask backend.
-   Real Tezos testnet integration with wallet signing, contract calls,
    and verifiable transaction hashes.
-   Automated tests and deployment documentation.

## Team

**NovaStack**

Built as a hackathon prototype exploring privacy-conscious student
concession verification.

------------------------------------------------------------------------

*TapOnce is a demonstration project, not a production payment or
identity system.*
