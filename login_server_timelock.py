"""
Flask login protected by the time-lock puzzle (timelock_guard.py).

  GET  /challenge -> {nonce, expiry, T, x, N, sig}
  client computes y = x^(2^T) mod N  (T sequential squarings)
  POST /login {challenge, answer, username, password}

The server checks the puzzle first (cheap), and runs the expensive password
hash only if the puzzle is correct.

Run server:    python3 login_server_timelock.py serve
Run self-test: python3 login_server_timelock.py
"""
import hashlib
import hmac
import secrets
import sys
import time

from flask import Flask, jsonify, request

from timelock_guard import issue_challenge, solve, verify

app = Flask(__name__)


def _hash_password(password: str, salt: bytes) -> bytes:
    # Prefer Argon2 (argon2-cffi) in production; scrypt is stdlib.
    return hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1)


_salt = secrets.token_bytes(16)
USERS = {"alice": (_salt, _hash_password("correct horse battery", _salt))}


@app.get("/challenge")
def get_challenge():
    return jsonify(issue_challenge(request.remote_addr or "unknown"))


@app.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    try:
        challenge, answer = data["challenge"], str(data["answer"])
        username, password = str(data["username"]), str(data["password"])
    except (KeyError, TypeError):
        return jsonify(error="bad request"), 400

    try:
        if not verify(challenge, answer):
            return jsonify(error="invalid, expired or reused puzzle"), 403
    except (KeyError, TypeError, ValueError):
        return jsonify(error="bad challenge"), 400

    salt, stored = USERS.get(username, (_salt, b"\x00" * 64))
    candidate = _hash_password(password, salt)
    if username in USERS and hmac.compare_digest(candidate, stored):
        return jsonify(status="logged in")
    return jsonify(error="wrong username or password"), 401


def self_test():
    c = app.test_client()

    def attempt(password):
        ch = c.get("/challenge").get_json()
        t = time.perf_counter()
        ans = solve(ch)
        took = time.perf_counter() - t
        body = {"challenge": ch, "answer": ans,
                "username": "alice", "password": password}
        return c.post("/login", json=body), body, took

    r, body, took = attempt("correct horse battery")
    print(f"Correct password + solved puzzle : {r.status_code} {r.get_json()}"
          f"  (client work {took:.2f}s)")

    r, _, _ = attempt("wrong")
    print(f"Wrong password + solved puzzle   : {r.status_code} {r.get_json()}")

    r = c.post("/login", json=body)
    print(f"Replayed request                 : {r.status_code} {r.get_json()}")

    ch = c.get("/challenge").get_json()
    r = c.post("/login", json={"challenge": ch, "answer": "1",
                               "username": "alice",
                               "password": "correct horse battery"})
    print(f"Right password, no puzzle work   : {r.status_code} {r.get_json()}")

    print("\nA spammer from one IP gets progressively harder puzzles:")
    for i in range(1, 25):
        ch = c.get("/challenge").get_json()
        if i % 6 == 0:
            print(f"  request #{i}: T = {ch['T']:,} squarings")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "serve":
        app.run(host="127.0.0.1", port=5000)
    else:
        self_test()
