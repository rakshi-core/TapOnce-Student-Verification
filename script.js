const $ = (id) => document.getElementById(id);
let currentSale = null;

async function api(path, method = "GET", body = null) {
  const options = { method, headers: { "Content-Type": "application/json" } };
  if (body) options.body = JSON.stringify(body);
  const response = await fetch(path, options);
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || data.message || "Request failed");
  return data;
}
function money(value) { return "₹" + Number(value).toFixed(2); }

async function refresh() {
  const data = await api("/api/state");
  $("heroCid").textContent = data.student_id;
  $("studentCid").textContent = data.student_id;
  $("heroBalance").textContent = money(data.wallet_balance);
  $("walletBalance").textContent = money(data.wallet_balance);
  const pending = data.queue.filter(x => x.status === "pending");
  $("queueCount").textContent = `${pending.length} pending`;
  $("queueRows").innerHTML = data.queue.length ? data.queue.map(x => `
    <tr><td>${escapeHtml(x.item || "Campus purchase")}</td>
    <td>${money(x.amt)}</td><td>${escapeHtml(x.cid)}</td>
    <td><span class="badge ${x.status === "settled" ? "settled" : ""}">${x.status.toUpperCase()}</span></td></tr>`).join("") :
    '<tr><td colspan="4" class="empty">No transactions yet. Run a demo purchase.</td></tr>';
}
function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
}

$("createSale").addEventListener("click", async () => {
  try {
    const data = await api("/api/sale", "POST", { item: $("item").value, price: $("price").value });
    currentSale = data.sale;
    $("saleBox").innerHTML = `<div class="sale-amount"><span>${escapeHtml(data.sale.item)} · Original</span><strong>${money(data.sale.price)}</strong></div>
      <div class="sale-amount"><span>Student price (20% discount)</span><strong>${money(data.sale.disc)}</strong></div>`;
    $("tapButton").disabled = false;
    $("result").className = "result";
    $("result").textContent = data.message;
  } catch (e) { $("result").className = "result error"; $("result").textContent = e.message; }
});

$("tapButton").addEventListener("click", async () => {
  try {
    const data = await api("/api/tap", "POST", {});
    $("result").className = "result success";
    $("result").textContent = `✓ ${data.message} Verification: ${data.result}.`;
    $("tapButton").disabled = true;
    currentSale = null;
    await refresh();
  } catch (e) { $("result").className = "result error"; $("result").textContent = e.message; }
});

$("settleButton").addEventListener("click", async () => {
  try {
    const data = await api("/api/settle", "POST", {});
    $("chainStatus").textContent = "SIMULATION COMPLETE";
    $("result").className = "result";
    $("result").textContent = data.message;
    await refresh();
    alert(data.results.length ? `Processed ${data.results.length} simulated settlement record(s). No real blockchain transaction was sent.` : "There were no pending transactions to settle.");
  } catch (e) { alert(e.message); }
});

$("resetButton").addEventListener("click", async () => {
  if (!confirm("Reset the demo wallet, merchant and transaction ledger?")) return;
  await api("/api/reset", "POST", {});
  currentSale = null;
  $("tapButton").disabled = true;
  $("saleBox").innerHTML = '<span class="muted">Create a sale to see the discounted amount.</span>';
  $("result").className = "result";
  $("result").textContent = "Demo reset. Ready for a new purchase.";
  $("chainStatus").textContent = "SIMULATION MODE";
  await refresh();
});

refresh().catch(e => { $("result").textContent = e.message; });
