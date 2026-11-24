# Ingle's Mathematical Paradoxes

Experiments in using mathematical ideas (Zeno's paradox, Collatz trees,
non-linear sequences, repeated squaring) to make attacks more costly.

**Author:** Purushottam Dnyaneshwar Ingle (independent learner)

## ⚠️ Read this first

- This repository is for **learning and experimentation**.
- **Do not use any of this code to protect real data.**
- No claim of "unbreakable" or "quantum-proof" security is made. Such claims
  are not proven for any code here.
- The original scripts (1, 3, 4, 5) are early prototypes. They only run
  locally and print their own messages; they do not interact with, trap, or
  harm any attacker. Their output messages describe intended behaviour, not
  verified behaviour.

## Original prototypes (kept for history)

| File | Idea | Known problems |
|------|------|----------------|
| `1_Infinite_Decimal_Tarpit.py` | Zeno-style halving loop | Closed form `target·(1−2⁻ⁿ)` skips the loop entirely |
| `3_Collatz_Blackhole_Encryption.py` | Recursive inverted Collatz tree | Not encryption (no key/data); recursion has no base case and can crash your own process |
| `4_Non_Linear_Sequence_Hashing.py` | Multi-step "hash" | Not a hash (no input, random output); uses `random`; `is_prime` is wrong; intermediate values reveal the seed |
| `5_Polymorphic_Poison_Pill_Trap.py` | `(C-1)²` growth | Defender pays the same cost as the attacker; "key" is `2·step`, authenticates nothing |

## Improved versions

| File | What it does |
|------|--------------|
| `proof_of_work_guard.py` | SHA-256 proof-of-work with HMAC-signed challenges, expiry, replay protection and adaptive difficulty |
| `login_server.py` | Flask login endpoint guarded by the proof-of-work |
| `timelock_guard.py` | Repeated-squaring time-lock puzzle (`y = x^(2^T) mod N`): sequential work that extra cores/GPUs do not speed up |
| `login_server_timelock.py` | Flask login endpoint guarded by the time-lock puzzle |

### Measured results (one machine, indicative only)

- Zeno loop vs closed form (3000 steps): ~9.3 ms vs ~0.009 ms.
- Proof-of-work, 16 bits: solve ~0.06 s, verify ~0.04 ms.
- Time-lock, T = 37,354 squarings: client ~0.31 s, server ~20 ms.
- 200,000 squarings mod N: ~0.49 s without the secret, ~3 ms with it.

## Limitations

- Time-lock security rests on an **unproven assumption**: repeated squaring in
  a group of unknown order cannot be sped up without the factorization of N.
- If the server's secret primes leak, the time-lock protection is gone.
- The time-lock version here is privately verifiable (only the server can
  check answers).
- These are cost-raising layers against automated abuse. They do **not**
  replace encryption, password hashing (use Argon2), HTTPS, rate limiting or
  account lockout.
- Demo state (used nonces, request counts, user store) lives in memory.

## Prior work

The time-lock idea is not new. It was introduced by Rivest, Shamir and Wagner
(1996) and later extended into verifiable delay functions by Pietrzak and by
Wesolowski (2018). Hashcash and Dwork–Naor "pricing functions" are earlier
forms of proof-of-work. This repository applies and explores these ideas; it
does not claim to have invented them.

## Run

```bash
pip install flask
python3 proof_of_work_guard.py          # PoW demo
python3 login_server.py                 # PoW login self-test
python3 timelock_guard.py               # time-lock demo
python3 login_server_timelock.py        # time-lock login self-test
```

---

## मराठी सारांश

हे रेपॉझिटरी **शिकण्यासाठी आणि प्रयोगांसाठी** आहे. यातील कोड खऱ्या
डेटाच्या संरक्षणासाठी वापरू नका. "अभेद्य" किंवा "क्वांटम-प्रूफ" असा कोणताही
दावा येथे सिद्ध केलेला नाही. जुन्या फाइल्स (1, 3, 4, 5) सुरुवातीचे प्रोटोटाइप
आहेत; सुधारलेल्या आवृत्त्या वर दिल्या आहेत.
