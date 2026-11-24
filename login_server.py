"""
Flask login endpoint protected by proof_of_work_guard.

Flow:
  1. Client:  GET  /challenge            -> gets a puzzle
  2. Client solves it (costs CPU time)
  3. Client:  POST /login {challenge, counter, username, password}
  4. Server checks the puzzle FIRST (1 cheap hash). Only if it is valid
     does it run the expensive password check.

Run server:   python3 login_server.py serve
Run self-test: python3 login_server.py
Needs proof_of_work_guard.py in the same folder.
"""
import hashlib
import hmac
import secrets
import sys

from flask import Flask, jsonify, request

from proof_of_work_guard import issue_challenge, solve, verify

app = Flask(__name__)

# --- demo user store (use a real database in production) ---
def _hash_password(password: str, salt: bytes) -> bytes:
    # scrypt is memory-hard and in the standard library.
    # In production prefer Argon2 (argon2-cffi).
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
        challenge, counter = data["challenge"], int(data["counter"])
        username, password = str(data["username"]), str(data["password"])
    except (KeyError, ValueError, TypeError):
        return jsonify(error="bad request"), 400

    # Step 1: cheap check. Reject bots before doing any expensive work.
    try:
        if not verify(challenge, counter):
            return jsonify(error="invalid or expired proof of work"), 403
    except KeyError:
        return jsonify(error="bad challenge"), 400

    # Step 2: password check (constant-time compare, same work if user unknown).
    salt, stored = USERS.get(username, (_salt, b"\x00" * 64))
    candidate = _hash_password(password, salt)
    if username in USERS and hmac.compare_digest(candidate, stored):
        return jsonify(status="logged in")
    return jsonify(error="wrong username or password"), 401


def self_test():
    c = app.test_client()

    def attempt(password, reuse=None):
        ch = c.get("/challenge").get_json()
        n = solve(ch)
        body = {"challenge": ch, "counter": n,
                "username": "alice", "password": password}
        return c.post("/login", json=body), body

    r, body = attempt("correct horse battery")
    print("Correct password + valid PoW :", r.status_code, r.get_json())

    r, _ = attempt("wrong")
    print("Wrong password + valid PoW   :", r.status_code, r.get_json())

    r2 = c.post("/login", json=body)  # replay the first request
    print("Replayed request             :", r2.status_code, r2.get_json())

    ch = c.get("/challenge").get_json()
    r = c.post("/login", json={"challenge": ch, "counter": 0,
                               "username": "alice",
                               "password": "correct horse battery"})
    print("Right password, NO PoW work  :", r.status_code, r.get_json())


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "serve":
        app.run(host="127.0.0.1", port=5000)
    else:
        self_test()
