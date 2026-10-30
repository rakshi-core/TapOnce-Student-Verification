from flask import Flask, jsonify, render_template, request
from tapsim import Issuer, Wallet, Terminal, TezosSim

app = Flask(__name__)

# One in-memory demo session. Restarting the server resets this simulated data.
uni = Issuer()
chain = TezosSim()
wallet = Wallet(uni)
merchant = Terminal("Campus Canteen", uni.pub, uni.revoked)

@app.get("/")
def home():
    return render_template("index.html")

@app.get("/api/state")
def state():
    return jsonify({
        "student_id": wallet.cred["cid"],
        "wallet_balance": wallet.balance - merchant.spent.get(wallet.cred["cid"], 0),
        "discount_percent": 20,
        "queue": merchant.ledger,
        "settlement_type": "SIMULATED",
    })

@app.post("/api/sale")
def create_sale():
    data = request.get_json(silent=True) or {}
    item = str(data.get("item", "Campus purchase")).strip()[:60]
    try:
        price = round(float(data.get("price", 0)), 2)
    except (TypeError, ValueError):
        return jsonify({"error": "Enter a valid price."}), 400
    if not item or price <= 0 or price > 100000:
        return jsonify({"error": "Enter an item and a price greater than zero."}), 400

    sale = merchant.new_sale(item, price)
    return jsonify({
        "sale": sale,
        "discount_percent": 20,
        "message": "Fresh merchant challenge created. Ready for student tap."
    })

@app.post("/api/tap")
def tap():
    data = request.get_json(silent=True) or {}
    if not merchant.sale:
        return jsonify({"error": "Create a sale at the merchant terminal first."}), 400

    packet = wallet.tap(merchant.sale["ch"], merchant.sale["disc"])
    result = merchant.pay(packet)

    if result == "OK":
        return jsonify({
            "status": "approved",
            "result": result,
            "message": "Student verified. Discounted payment added to the offline queue.",
            "sale": merchant.sale,
            "queue_count": sum(e["status"] == "pending" for e in merchant.ledger)
        })
    return jsonify({"status": "declined", "result": result, "message": "Verification declined."}), 400

@app.post("/api/settle")
def settle():
    # This deliberately uses TezosSim from tapsim.py, not a real Tezos RPC.
    results = chain.settle(merchant)
    return jsonify({
        "results": [{"result": r[0], "cid": r[1][0], "counter": r[1][1], "merchant": r[2]} for r in results],
        "queue": merchant.ledger,
        "settlement_type": "SIMULATED",
        "message": "Local TezosSim settlement complete. No blockchain transaction was submitted."
    })

@app.post("/api/reset")
def reset():
    global uni, chain, wallet, merchant
    uni = Issuer()
    chain = TezosSim()
    wallet = Wallet(uni)
    merchant = Terminal("Campus Canteen", uni.pub, uni.revoked)
    return jsonify({"message": "Demo session reset."})

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
