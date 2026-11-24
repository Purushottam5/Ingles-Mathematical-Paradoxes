"""
Time-Lock Guard: Rivest-Shamir-Wagner (1996) repeated-squaring puzzle.

Puzzle:  given (N, x, T), compute  y = x^(2^T) mod N.
- Client WITHOUT the secret must do T squarings, strictly one after another.
  Extra cores / GPUs do not help (unlike hash-based proof of work).
- Server WITH the secret factorization (phi) computes the same y in
  milliseconds:  y = x^(2^T mod phi) mod N.

NOTE: this is a *privately verifiable* puzzle (only the server can check),
which is fine for a login server. Public verifiability needs Pietrzak or
Wesolowski VDFs. Security rests on an unproven assumption (sequentiality of
repeated squaring in a group of unknown order), not on a proof.
"""
import hashlib
import hmac
import secrets
import time
from collections import defaultdict, deque

TTL_SECONDS = 120
BASE_SECONDS = 0.3        # target client work for a normal visitor
MAX_SECONDS = 8.0         # cap for heavy spammers
KEY_BITS = 2048           # size of N (primes are KEY_BITS/2 each)


# ---------- key generation (server secret) ----------
def _is_probable_prime(n: int, rounds: int = 40) -> bool:
    if n < 2:
        return False
    for sp in (2, 3, 5, 7, 11, 13, 17, 19, 23, 29):
        if n % sp == 0:
            return n == sp
    d, s = n - 1, 0
    while d % 2 == 0:
        d //= 2
        s += 1
    for _ in range(rounds):
        a = secrets.randbelow(n - 3) + 2
        x = pow(a, d, n)
        if x in (1, n - 1):
            continue
        for _ in range(s - 1):
            x = x * x % n
            if x == n - 1:
                break
        else:
            return False
    return True


def _gen_prime(bits: int) -> int:
    while True:
        c = secrets.randbits(bits) | (1 << (bits - 1)) | 1
        if _is_probable_prime(c):
            return c


_P = _gen_prime(KEY_BITS // 2)
_Q = _gen_prime(KEY_BITS // 2)
N = _P * _Q
_PHI = (_P - 1) * (_Q - 1)         # SECRET: never leaves the server
_SIGN_KEY = secrets.token_bytes(32)

_used = {}                         # nonce -> expiry (replay protection)
_recent = defaultdict(deque)       # client_id -> timestamps


def _calibrate(samples: int = 30000) -> float:
    """Squarings per second on this machine (an honest client's speed)."""
    y = secrets.randbelow(N - 2) + 2
    t = time.perf_counter()
    for _ in range(samples):
        y = y * y % N
    return samples / (time.perf_counter() - t)


RATE = _calibrate()


def _sign(msg: str) -> str:
    return hmac.new(_SIGN_KEY, msg.encode(), hashlib.sha256).hexdigest()


def _seconds_for(client_id: str) -> float:
    now = time.time()
    q = _recent[client_id]
    q.append(now)
    while q and now - q[0] > 60:
        q.popleft()
    return min(BASE_SECONDS + 0.2 * (len(q) // 3), MAX_SECONDS)


# ---------- SERVER ----------
def issue_challenge(client_id: str) -> dict:
    nonce = secrets.token_hex(16)
    expiry = int(time.time()) + TTL_SECONDS
    T = int(_seconds_for(client_id) * RATE)
    x = secrets.randbelow(N - 2) + 2
    sig = _sign(f"{nonce}:{expiry}:{T}:{x}")
    # big integers sent as strings so any client language handles them
    return {"nonce": nonce, "expiry": expiry, "T": T,
            "x": str(x), "N": str(N), "sig": sig}


def verify(ch: dict, y: str) -> bool:
    nonce, expiry, T, x = ch["nonce"], ch["expiry"], ch["T"], ch["x"]
    if not hmac.compare_digest(_sign(f"{nonce}:{expiry}:{T}:{x}"), ch["sig"]):
        return False                       # tampered (e.g. smaller T)
    now = time.time()
    if now > expiry:
        return False
    for n in [n for n, e in _used.items() if e < now]:
        del _used[n]
    if nonce in _used:
        return False                       # replay
    _used[nonce] = expiry                  # one attempt per puzzle
    try:
        claimed = int(y)
    except (ValueError, TypeError):
        return False
    expected = pow(int(x), pow(2, T, _PHI), N)   # shortcut: milliseconds
    return hmac.compare_digest(str(expected), str(claimed))


# ---------- CLIENT ----------
def solve(ch: dict) -> str:
    n, y = int(ch["N"]), int(ch["x"])
    for _ in range(ch["T"]):               # inherently sequential
        y = y * y % n
    return str(y)


if __name__ == "__main__":
    print(f"Calibrated speed: {RATE:,.0f} squarings/second")
    ch = issue_challenge("user-1")
    print(f"Puzzle: T = {ch['T']:,} sequential squarings")

    t = time.perf_counter(); ans = solve(ch); st = time.perf_counter() - t
    t = time.perf_counter(); ok = verify(ch, ans); vt = time.perf_counter() - t
    print(f"Client solve : {st:.3f} s")
    print(f"Server verify: {vt * 1000:.2f} ms  -> valid={ok}")
    print(f"Replay accepted?     {verify(ch, ans)}")

    ch2 = issue_challenge("user-2")
    print(f"Wrong answer accepted? {verify(ch2, '12345')}")
    ch3 = issue_challenge("user-3")
    cheat = dict(ch3, T=10)
    print(f"Tampered smaller T accepted? {verify(cheat, solve(cheat))}")
