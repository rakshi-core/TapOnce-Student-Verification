"""
TapOnce: Python simulation of issue -> tap -> verify -> settle  (Team NovaStack)
Run:  pip install cryptography   then   python tapsim.py
NFC and Secure Element are simulated: a dict is the "air", an Ed25519 key is the "secure element".
The Tezos contract is simulated by TezosSim (a spent-token set); swap it for a real
SmartPy/Taquito call on testnet using the same (cid, counter) key.
"""
import json, secrets, time
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.hazmat.primitives import serialization as ser
from cryptography.exceptions import InvalidSignature

DISCOUNT, CAP = 0.8, 500
canon = lambda o: json.dumps(o, sort_keys=True, separators=(",", ":")).encode()
raw = lambda pub: pub.public_bytes(ser.Encoding.Raw, ser.PublicFormat.Raw).hex()

def ok(pub_hex, sig_hex, msg):
    try:
        Ed25519PublicKey.from_public_bytes(bytes.fromhex(pub_hex)).verify(bytes.fromhex(sig_hex), msg); return True
    except InvalidSignature:
        return False

class Issuer:                                   # the university
    def __init__(self):
        self.key = Ed25519PrivateKey.generate(); self.pub = raw(self.key.public_key()); self.revoked = set()
    def issue(self, device_pub, days=365):      # anonymous: no name, photo or roll number
        cred = {"cid": "S-" + secrets.token_hex(3), "dev": device_pub, "exp": time.time() + days * 86400}
        return cred, self.key.sign(canon(cred)).hex()

class Wallet:                                   # student phone (secure element simulated)
    def __init__(self, issuer, days=365):
        self.key = Ed25519PrivateKey.generate(); self.counter = 0; self.balance = CAP
        self.cred, self.isig = issuer.issue(raw(self.key.public_key()), days)
    def tap(self, challenge, amount, counter=None):
        c = counter if counter is not None else self.counter + 1
        body = {"cid": self.cred["cid"], "ch": challenge, "amt": amount, "c": c}
        self.counter = max(self.counter, c)
        return {"cred": self.cred, "isig": self.isig, "body": body, "sig": self.key.sign(canon(body)).hex()}

class Terminal:                                 # merchant, fully offline
    def __init__(self, name, issuer_pub, revoked):
        self.name, self.ipub, self.revoked = name, issuer_pub, revoked
        self.seen, self.counters, self.spent, self.ledger, self.sale = set(), {}, {}, [], None
    def new_sale(self, item, price):
        self.sale = {"ch": secrets.token_hex(4), "item": item, "price": price, "disc": round(price * DISCOUNT)}
        return self.sale
    def verify(self, p):
        cred, b = p["cred"], p["body"]
        if not ok(self.ipub, p["isig"], canon(cred)):            return "FORGED"
        if cred["exp"] < time.time():                            return "EXPIRED"
        if cred["cid"] in self.revoked:                          return "REVOKED"
        if not ok(cred["dev"], p["sig"], canon(b)):              return "TAMPERED"
        if b["ch"] in self.seen:                                 return "DUPLICATE"
        if not self.sale or b["ch"] != self.sale["ch"]:          return "WRONG_CHALLENGE"
        if b["amt"] != self.sale["disc"]:                        return "AMOUNT"
        if b["c"] <= self.counters.get(b["cid"], 0):             return "REPLAY"
        if self.spent.get(b["cid"], 0) + b["amt"] > CAP:         return "CAP"
        return "OK"
    def pay(self, p):
        r = self.verify(p)
        if r == "OK":
            b = p["body"]; self.seen.add(b["ch"]); self.counters[b["cid"]] = b["c"]
            self.spent[b["cid"]] = self.spent.get(b["cid"], 0) + b["amt"]
            self.ledger.append({"term": self.name, "cid": b["cid"], "c": b["c"], "amt": b["amt"], "status": "pending"})
        return r

class TezosSim:                                 # stand-in for the settlement smart contract
    def __init__(self): self.spent = {}
    def settle(self, terminal):
        out = []
        for e in terminal.ledger:
            if e["status"] != "pending": continue
            k = (e["cid"], e["c"])
            if k in self.spent: e["status"] = "rejected"; out.append(("DOUBLE-SPEND", k, terminal.name))
            else:               self.spent[k] = terminal.name; e["status"] = "settled"; out.append(("SETTLED", k, terminal.name))
        return out

def show(title, result, expect):
    mark = "PASS" if result == expect else "FAIL"
    print(f"[{mark}] {title:<42} -> {result}")

if __name__ == "__main__":
    uni, chain = Issuer(), TezosSim()
    A = Terminal("A", uni.pub, uni.revoked); B = Terminal("B", uni.pub, uni.revoked)
    me = Wallet(uni)
    print("TapOnce simulation\n")

    s = A.new_sale("Masala dosa", 100)
    p1 = me.tap(s["ch"], s["disc"]);                 show("Normal tap (Rs 100 -> Rs 80)", A.pay(p1), "OK")
    show("Replay same packet (duplicate payment)", A.pay(p1), "DUPLICATE")

    s = A.new_sale("Notebook", 150)
    p2 = me.tap(s["ch"], s["disc"]); p2["body"]["amt"] = 1
    show("Amount edited in transit", A.pay(p2), "TAMPERED")

    s = A.new_sale("Coffee", 40)
    stale = me.tap("deadbeef", s["disc"]);           show("Packet for a different sale", A.pay(stale), "WRONG_CHALLENGE")

    s = A.new_sale("Lab record", 250)
    cheat = me.tap(s["ch"], s["disc"], counter=1);   show("Counter reused at same terminal", A.pay(cheat), "REPLAY")

    old = Wallet(uni, days=-1); s = A.new_sale("Tea", 20)
    show("Expired credential", A.pay(old.tap(s["ch"], s["disc"])), "EXPIRED")

    gone = Wallet(uni); uni.revoked.add(gone.cred["cid"]); s = A.new_sale("Tea", 20)
    show("Revoked student", A.pay(gone.tap(s["ch"], s["disc"])), "REVOKED")

    fake = Wallet(Issuer()); s = A.new_sale("Tea", 20)
    show("Credential from a fake issuer", A.pay(fake.tap(s["ch"], s["disc"])), "FORGED")

    rich = Wallet(uni); big = A.new_sale("Laptop bag", 800)
    show("Offline balance cap exceeded", A.pay(rich.tap(big["ch"], big["disc"])), "CAP")

    # Cloned wallet: same counter accepted offline at Terminal B, caught only at settlement
    sb = B.new_sale("Samosa", 30); clone = me.tap(sb["ch"], sb["disc"], counter=1)
    show("Clone accepted offline at Terminal B", B.pay(clone), "OK")

    print("\nBatch settlement on simulated Tezos:")
    for t in (A, B):
        for r in chain.settle(t): print("  ", r)
    print("\nLedger A:", A.ledger, "\nLedger B:", B.ledger)
