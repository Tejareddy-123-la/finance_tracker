/* Smart Finance Manager - frontend logic.
   The page talks to the backend through fetch() calls to /api/... (same server, so no CORS setup needed). */

const $ = (id) => document.getElementById(id);
const inr = (n) => "₹" + Number(n || 0).toLocaleString("en-IN", { maximumFractionDigits: 0 });
const esc = (s) => String(s).replace(/[&<>"']/g, (c) =>
  ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const today = () => new Date().toISOString().slice(0, 10);

/* One helper for every API call. Shows the server's error message if something fails. */
async function api(path, method = "GET", body) {
  const res = await fetch("/api" + path, {
    method,
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    let msg = "Please check the values you entered.";
    if (typeof err.detail === "string") {
      msg = err.detail;
    } else if (Array.isArray(err.detail) && err.detail[0]?.msg) {
      msg = err.detail[0].msg;
    }
    alert(msg);
    throw new Error(msg);
  }
  return res.json();
}

/* Enforce alphabets and spaces only (disallow numeric digits and special symbols) */
function restrictToAlphabets(el) {
  if (!el) return;
  el.addEventListener("input", () => {
    el.value = el.value.replace(/[^a-zA-Z\s]/g, "");
  });
}

/* ---------------------------------------------------------------- tabs */
$("tabs").addEventListener("click", (e) => {
  const tab = e.target.dataset.tab;
  if (!tab) return;
  document.querySelectorAll(".tabs button").forEach((b) => b.classList.toggle("active", b === e.target));
  document.querySelectorAll(".tab").forEach((s) => s.classList.toggle("active", s.id === tab));
  refresh(tab);
});

function refresh(tab) {
  const current = tab || document.querySelector(".tab.active").id;
  ({ dashboard: loadDashboard, transactions: loadTransactions, budgets: loadBudgets,
     debts: loadDebts, goals: loadGoals }[current])();
}

/* ---------------------------------------------------------------- dashboard */
const charts = {};
function draw(id, config) {
  if (charts[id]) charts[id].destroy();
  charts[id] = new Chart($(id), config);
}
const li = (items, cls = "") =>
  items.length ? items.map((t) => `<li class="${cls}">${esc(t)}</li>`).join("") : "<li>Nothing to show yet.</li>";

async function loadDashboard() {
  const s = await api("/summary?month=" + $("month").value);

  $("income").textContent = inr(s.income);
  $("expense").textContent = inr(s.expense);
  
  const balEl = $("balance");
  if (s.balance < 0) {
    balEl.textContent = "-" + inr(Math.abs(s.balance));
    balEl.className = "expense";
  } else {
    balEl.textContent = inr(s.balance);
    balEl.className = s.balance > 0 ? "income" : "";
  }
  
  $("score").textContent = s.health.score;
  $("scoreLabel").textContent = s.health.label;

  const hero = $("allowance");
  if (s.daily_allowance === null) {
    hero.textContent = "-";
    hero.classList.remove("over");
    $("allowanceNote").textContent = s.total_budget
      ? "Daily allowance is shown for the current month."
      : "Set budgets to unlock your daily allowance.";
  } else {
    hero.textContent = inr(s.daily_allowance);
    hero.classList.toggle("over", s.daily_allowance < 0);
    $("allowanceNote").textContent = s.daily_allowance < 0
      ? "You are over your total budget. Spend only what is essential."
      : `Total budget ${inr(s.total_budget)}, spent ${inr(s.expense)} so far. This updates as you spend.`;
  }

  const f = s.forecast;
  $("forecast").textContent = `After ${f.day} of ${f.days} days you have spent ${inr(s.expense)}. ` +
    `At this pace the month ends at ${inr(f.projected)}` +
    (s.income > 0 ? (f.projected > s.income
      ? `, which is ${inr(f.projected - s.income)} more than your income.`
      : `, leaving about ${inr(s.income - f.projected)} saved.`) : ".");

  $("alerts").innerHTML = li(s.alerts, "warn");
  $("insights").innerHTML = li(s.insights);
  $("tips").innerHTML = li(s.health.tips);
  $("anomalies").innerHTML = s.anomalies.length
    ? s.anomalies.map((a) => `<li class="warn">${esc(a.date)} ${esc(a.description)} ${inr(a.amount)}: ${esc(a.reason)}</li>`).join("")
    : "<li>No unusual charges this month.</li>";
  $("subs").innerHTML = s.subscriptions.length
    ? s.subscriptions.map((x) => `<li>${esc(x.name)}: ${inr(x.monthly)}/month (${inr(x.yearly)}/year)</li>`).join("")
    : "<li>None detected yet. Needs the same charge in 2+ months.</li>";

  const cats = Object.keys(s.by_category);
  draw("catChart", {
    type: "doughnut",
    data: { labels: cats, datasets: [{ data: cats.map((c) => s.by_category[c]),
      backgroundColor: ["#0f3d30", "#e0a526", "#1f7a4d", "#b3261e", "#6b8f80", "#8a6d1d", "#3d5c70", "#a9c7ba"] }] },
    options: { maintainAspectRatio: false, plugins: { legend: { position: "bottom" } } },
  });
  draw("budgetChart", {
    type: "bar",
    data: { labels: s.budget_status.map((b) => b.category),
      datasets: [
        { label: "Limit", data: s.budget_status.map((b) => b.limit), backgroundColor: "#a9c7ba" },
        { label: "Spent", data: s.budget_status.map((b) => b.spent), backgroundColor: "#0f3d30" },
      ] },
    options: { maintainAspectRatio: false, scales: { y: { beginAtZero: true } } },
  });
}

/* quick add (typed or spoken) */
$("quickBtn").addEventListener("click", async () => {
  const text = $("quickText").value.trim();
  if (!text) return;
  const r = await api("/quickadd", "POST", { text });
  $("quickText").value = "";
  alert(`Saved ${r.type}: ${inr(r.amount)} under ${r.category}.`);
  loadDashboard();
});
$("quickText").addEventListener("keydown", (e) => { if (e.key === "Enter") $("quickBtn").click(); });

const Speech = window.SpeechRecognition || window.webkitSpeechRecognition;
if (Speech) {
  $("micBtn").addEventListener("click", () => {
    const rec = new Speech();
    rec.lang = "en-IN";
    rec.onresult = (e) => { $("quickText").value = e.results[0][0].transcript; };
    rec.start();
  });
} else {
  $("micBtn").style.display = "none"; // browser has no speech support (use Chrome or Edge)
}

/* ---------------------------------------------------------------- transactions */
async function loadTransactions() {
  const rows = await api("/transactions?month=" + $("month").value);
  $("txnBody").innerHTML = rows.length ? rows.map((t) => `
    <tr>
      <td>${esc(t.date)}</td><td>${esc(t.description)}</td><td>${esc(t.category)}</td>
      <td class="num ${t.type}">${t.type === "income" ? "+" : "-"}${inr(t.amount)}</td>
      <td><button class="danger" data-del="${t.id}" aria-label="Delete transaction">Delete</button></td>
    </tr>`).join("") : `<tr><td colspan="5">No transactions in this month. Add one above.</td></tr>`;
}

$("txnBody").addEventListener("click", async (e) => {
  if (e.target.dataset.del) { await api("/transactions/" + e.target.dataset.del, "DELETE"); loadTransactions(); }
});

$("txnForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const description = $("tDesc").value.trim();
  const category = ($("tCat").value || "").trim();
  if (!/^[a-zA-Z\s]+$/.test(description)) {
    alert("Transaction description must contain only alphabets and spaces (no numbers).");
    return;
  }
  if (category && !/^[a-zA-Z\s]+$/.test(category)) {
    alert("Category must contain only alphabets and spaces (no numbers).");
    return;
  }
  await api("/transactions", "POST", {
    date: $("tDate").value, description,
    amount: parseFloat($("tAmount").value), type: $("tType").value,
    category: category || null,
  });
  $("tDesc").value = ""; $("tAmount").value = ""; $("tCat").value = "";
  loadTransactions();
});

$("csvFile").addEventListener("change", async (e) => {
  const file = e.target.files[0];
  if (!file) return;
  const lines = (await file.text()).split(/\r?\n/).filter((l) => l.trim());
  const items = [];
  for (const line of lines) {
    let [date, description, amount, type, category] = line.split(",").map((x) => x.trim());
    const value = parseFloat(amount);
    if (!/^\d{4}-\d{2}-\d{2}$/.test(date) || !description || !(value > 0)) continue;
    // Clean to alphabets and spaces only
    description = description.replace(/[^a-zA-Z\s]/g, " ").replace(/\s+/g, " ").trim();
    if (!description) continue;
    if (category) {
      category = category.replace(/[^a-zA-Z\s]/g, " ").replace(/\s+/g, " ").trim() || null;
    }
    items.push({ date, description, amount: value,
      type: (type || "expense").toLowerCase() === "income" ? "income" : "expense", category: category || null });
  }
  if (!items.length) { alert("No valid rows found. Expected: date(YYYY-MM-DD), description (alphabets only), amount, type, category"); return; }
  const r = await api("/transactions/bulk", "POST", items);
  alert(`Imported ${r.imported} transactions.`);
  e.target.value = "";
  loadTransactions();
});

/* ---------------------------------------------------------------- budgets */
async function loadBudgets() {
  const [budgets, s] = await Promise.all([api("/budgets"), api("/summary?month=" + $("month").value)]);
  
  // Case-insensitive lookup map from summary's budget_status
  const spent = {};
  for (const b of (s.budget_status || [])) {
    spent[b.category.trim().toLowerCase()] = b;
  }

  $("budgetList").innerHTML = budgets.length ? budgets.map((b) => {
    const key = b.category.trim().toLowerCase();
    const st = spent[key] || { spent: 0, percent: 0 };
    const pct = st.percent || 0;
    const cls = pct >= 100 ? "over" : pct >= 80 ? "mid" : "";
    return `<div class="item">
      <div class="grow"><strong>${esc(b.category)}</strong> ${inr(st.spent)} of ${inr(b.monthly_limit)} (${pct}%)
        <div class="bar"><i class="${cls}" style="width:${Math.min(pct, 100)}%"></i></div></div>
      <button class="danger" data-bdel="${esc(b.category)}">Remove</button></div>`;
  }).join("") : "<p>No budgets yet. Add a limit above, or let the app suggest limits from your history.</p>";
}

$("budgetList").addEventListener("click", async (e) => {
  if (e.target.dataset.bdel) { await api("/budgets/" + encodeURIComponent(e.target.dataset.bdel), "DELETE"); loadBudgets(); }
});
$("budgetForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const category = $("bCat").value.trim();
  if (!/^[a-zA-Z\s]+$/.test(category)) {
    alert("Category must contain only alphabets and spaces (no numbers).");
    return;
  }
  await api("/budgets", "PUT", { category, monthly_limit: parseFloat($("bLimit").value) });
  $("bCat").value = ""; $("bLimit").value = "";
  loadBudgets();
});
$("suggestBtn").addEventListener("click", async () => {
  const r = await api("/budgets/suggest", "POST");
  alert(`Set ${Object.keys(r.budgets).length} limits from ${r.based_on_months.join(", ")} (average minus 10%).`);
  loadBudgets();
});

/* ---------------------------------------------------------------- debts */
async function loadDebts() {
  const extra = parseFloat($("extra").value);
  $("extraLabel").textContent = inr(extra);
  const a = await api("/debts/analysis?extra=" + extra);

  $("debtBody").innerHTML = a.debts.length ? a.debts.map((d) => `
    <tr><td>${esc(d.name)}</td><td class="num">${inr(d.balance)}</td><td class="num">${d.annual_rate}%</td>
      <td class="num">${inr(d.monthly_interest)}</td>
      <td class="num">${d.paid_off ? d.months_to_clear : "Never (payment too low)"}</td>
      <td class="num">${d.paid_off ? inr(d.total_interest) : "-"}</td>
      <td><button class="danger" data-ddel="${d.id}">Delete</button></td></tr>`).join("")
    : `<tr><td colspan="7">No debts added. Add a loan or credit card above.</td></tr>`;
  $("debtTotal").textContent = a.debts.length ? `You pay about ${inr(a.total_monthly_interest)} in interest every month.` : "";

  if (!a.debts.length) { $("compare").innerHTML = ""; $("compareNote").textContent = ""; return; }
  const box = (title, r, best) => `<div class="${best ? "best" : ""}"><span>${title}</span>
    <strong>${r.paid_off ? r.months + " months" : "Not payable"}</strong>
    <span>${r.paid_off ? "Interest: " + inr(r.total_interest) : "Payments do not cover interest"}</span></div>`;
  const cheaper = a.avalanche.total_interest <= a.snowball.total_interest ? "avalanche" : "snowball";
  $("compare").innerHTML =
    box("Minimum payments only", a.minimum_only, false) +
    box("Avalanche (highest rate first)", a.avalanche, cheaper === "avalanche") +
    box("Snowball (smallest balance first)", a.snowball, cheaper === "snowball");
  $("compareNote").textContent = !a.minimum_only.paid_off
    ? (a.avalanche.paid_off ? `Minimum payments never clear your debt. Paying ${inr(extra)} extra clears it in ${a.avalanche.months} months.`
        : "Your payments do not cover the interest. Increase the payment or add extra with the slider.")
    : extra > 0
    ? `Paying ${inr(extra)} extra with Avalanche saves ${inr(a.interest_saved)} in interest and ${a.months_saved} months.`
    : "Move the slider to see how extra payments change your debt-free date.";
}

$("extra").addEventListener("input", loadDebts);
$("debtBody").addEventListener("click", async (e) => {
  if (e.target.dataset.ddel) { await api("/debts/" + e.target.dataset.ddel, "DELETE"); loadDebts(); }
});
$("debtForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const name = $("dName").value.trim();
  if (!/^[a-zA-Z\s]+$/.test(name)) {
    alert("Debt name must contain only alphabets and spaces (no numbers).");
    return;
  }
  await api("/debts", "POST", { name, balance: parseFloat($("dBalance").value),
    annual_rate: parseFloat($("dRate").value), min_payment: parseFloat($("dMin").value) });
  e.target.reset();
  loadDebts();
});

$("emiForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const r = await api(`/calc/emi?principal=${$("cP").value}&rate=${$("cR").value}&months=${$("cM").value}`);
  $("emiResult").textContent = `EMI ${inr(r.emi)} per month. Total payment ${inr(r.total_payment)}, of which interest is ${inr(r.total_interest)}.`;
});
$("siForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const r = await api(`/calc/interest?principal=${$("sP").value}&rate=${$("sR").value}&years=${$("sY").value}`);
  $("siResult").textContent = `Simple interest: ${inr(r.simple.interest)} (total ${inr(r.simple.total)}). ` +
    `Compound interest (monthly): ${inr(r.compound.interest)} (total ${inr(r.compound.total)}).`;
});

/* ---------------------------------------------------------------- goals */
async function loadGoals() {
  const goals = await api("/goals");
  $("goalList").innerHTML = goals.length ? goals.map((g) => `
    <div class="panel item">
      <div class="grow"><strong>${esc(g.name)}</strong> ${inr(g.saved)} of ${inr(g.target)} (${g.percent}%)
        <div class="bar"><i style="width:${g.percent}%"></i></div>
        <p class="hint">Save ${inr(g.monthly_needed)} per month for ${g.months_left} months to reach it by ${esc(g.deadline)}.</p></div>
      <div class="row"><input type="number" min="1" placeholder="Add" style="width:90px" id="add-${g.id}">
        <button data-gadd="${g.id}">Add savings</button>
        <button class="danger" data-gdel="${g.id}">Delete</button></div>
    </div>`).join("") : `<p>No goals yet. Create one above.</p>`;
}

$("goalList").addEventListener("click", async (e) => {
  if (e.target.dataset.gdel) { await api("/goals/" + e.target.dataset.gdel, "DELETE"); loadGoals(); }
  if (e.target.dataset.gadd) {
    const id = e.target.dataset.gadd;
    const amount = parseFloat($("add-" + id).value);
    if (amount > 0) { await api(`/goals/${id}/add`, "POST", { amount }); loadGoals(); }
  }
});
$("goalForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const name = $("gName").value.trim();
  if (!/^[a-zA-Z\s]+$/.test(name)) {
    alert("Goal name must contain only alphabets and spaces (no numbers).");
    return;
  }
  await api("/goals", "POST", { name, target: parseFloat($("gTarget").value),
    saved: parseFloat($("gSaved").value || 0), deadline: $("gDeadline").value });
  e.target.reset();
  $("gSaved").value = 0;
  loadGoals();
});

/* ---------------------------------------------------------------- start */
["tDesc", "tCat", "bCat", "dName", "gName"].forEach((id) => {
  restrictToAlphabets($(id));
});
$("month").value = today().slice(0, 7);
$("tDate").value = today();
$("month").addEventListener("change", () => refresh());
loadDashboard();
