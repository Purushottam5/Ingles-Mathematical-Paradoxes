"""
Proof-of-Work Guard (Poison Pill, rebuilt as a real puzzle)

Idea: the server hands out a puzzle that is CHEAP to verify (1 hash)
but EXPENSIVE to solve (~2**difficulty hashes). A normal user pays a
fraction of a second; someone sending thousands of requests pays a lot.

Properties:
- Stateless issuing: challenge is signed with HMAC, so the server
  does not need to remember it (only used nonces, to stop replay).
- Expiry: old challenges are rejected.
- Adaptive difficulty: the more requests a client sends, the harder it gets.
- Uses only standard, vetted primitives (SHA-256, HMAC, secrets).
"""
import hashlib
import hmac
import secrets
import time
from collections import defaultdict, deque

SECRET = secrets.token_bytes(32)   # server-side signing key (never sent)
TTL_SECONDS = 60                   # challenge lifetime
BASE_DIFFICULTY = 16               # leading zero bits (~65k hashes)
MAX_DIFFICULTY = 28

_used_nonces = {}                  # nonce -> expiry (replay protection)
_recent = defaultdict(deque)       # client_id -> request timestamps


def _sign(msg: str) -> str:
    return hmac.new(SECRET, msg.encode(), hashlib.sha256).hexdigest()


def _leading_zero_bits(digest: bytes) -> int:
    return len(digest) * 8 - int.from_bytes(digest, "big").bit_length()


def _difficulty_for(client_id: str) -> int:
    """Harder puzzle if this client made many requests in the last minute."""
    now = time.time()
    q = _recent[client_id]
    q.append(now)
    while q and now - q[0] > 60:
        q.popleft()
    extra = len(q) // 5            # +1 bit per 5 recent requests
    return min(BASE_DIFFICULTY + extra, MAX_DIFFICULTY)


# ---------------- SERVER SIDE ----------------
def issue_challenge(client_id: str) -> dict:
    nonce = secrets.token_hex(16)
    expiry = int(time.time()) + TTL_SECONDS
    difficulty = _difficulty_for(client_id)
    sig = _sign(f"{nonce}:{expiry}:{difficulty}")
    return {"nonce": nonce, "expiry": expiry,
            "difficulty": difficulty, "sig": sig}


def verify(challenge: dict, counter: int) -> bool:
    nonce, expiry = challenge["nonce"], challenge["expiry"]
    difficulty, sig = challenge["difficulty"], challenge["sig"]

    # 1. Was this challenge really issued by us (not tampered)?
    expected = _sign(f"{nonce}:{expiry}:{difficulty}")
    if not hmac.compare_digest(expected, sig):
        return False
    # 2. Still valid?
    if time.time() > expiry:
        return False
    # 3. Not used before (replay)?
    now = time.time()
    for n in [n for n, e in _used_nonces.items() if e < now]:
        del _used_nonces[n]
    if nonce in _used_nonces:
        return False
    # 4. The actual work: ONE hash to check.
    data = f"{nonce}:{expiry}:{difficulty}:{counter}".encode()
    if _leading_zero_bits(hashlib.sha256(data).digest()) < difficulty:
        return False
    _used_nonces[nonce] = expiry
    return True


# ---------------- CLIENT SIDE ----------------
def solve(challenge: dict) -> int:
    prefix = f"{challenge['nonce']}:{challenge['expiry']}:{challenge['difficulty']}:"
    counter = 0
    while True:
        digest = hashlib.sha256(f"{prefix}{counter}".encode()).digest()
        if _leading_zero_bits(digest) >= challenge["difficulty"]:
            return counter
        counter += 1


if __name__ == "__main__":
    ch = issue_challenge("user-1")
    print(f"Difficulty: {ch['difficulty']} bits")

    t = time.time()
    answer = solve(ch)
    solve_time = time.time() - t

    t = time.time()
    ok = verify(ch, answer)
    verify_time = time.time() - t

    print(f"Solved with counter={answer} in {solve_time:.3f}s")
    print(f"Verified: {ok} in {verify_time * 1000:.4f} ms")
    print(f"Replay attempt accepted? {verify(ch, answer)}")        # False
    forged = dict(ch, difficulty=1)
    print(f"Forged easier puzzle accepted? {verify(forged, 0)}")   # False

    print("\nAdaptive difficulty for a spammer:")
    for i in range(1, 41):
        c = issue_challenge("spammer")
        if i % 10 == 0:
            print(f"  request #{i}: difficulty {c['difficulty']} bits "
                  f"(~{2 ** c['difficulty']:,} hashes)")
