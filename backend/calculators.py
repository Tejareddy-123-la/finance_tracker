"""All the finance logic lives here (no web code), so it is easy to test and explain."""
import re
import statistics
from collections import defaultdict

# ---------------------------------------------------------------- categorization
RULES = {
    "Income": ["salary", "stipend", "refund", "cashback", "freelance", "bonus"],
    "Rent": ["rent", "landlord"],
    "Food": ["swiggy", "zomato", "restaurant", "cafe", "lunch", "dinner", "breakfast",
             "grocery", "bigbasket", "blinkit", "zepto", "dmart", "snack", "tea", "coffee"],
    "Transport": ["uber", "ola", "rapido", "petrol", "fuel", "metro", "irctc", "bus", "auto", "cab"],
    "Bills": ["electricity", "bescom", "recharge", "jio", "airtel", "wifi", "broadband", "gas", "water bill"],
    "Shopping": ["amazon", "flipkart", "myntra", "ajio", "mall", "shopping"],
    "Entertainment": ["netflix", "spotify", "hotstar", "prime", "movie", "bookmyshow", "game"],
    "Health": ["pharmacy", "apollo", "medplus", "hospital", "doctor", "medicine"],
    "Education": ["course", "udemy", "book", "tuition", "college", "fees"],
    "Loan EMI": ["emi", "loan"],
}


def categorize(description: str, ttype: str = "expense") -> str:
    """Keyword-based auto-categorization, e.g. 'SWIGGY*ORDER123' -> Food."""
    text = description.lower()
    for category, keywords in RULES.items():
        if any(k in text for k in keywords):
            return category
    return "Income" if ttype == "income" else "Other"


# ---------------------------------------------------------------- interest maths
def simple_interest(principal, annual_rate, years):
    """SI = P * R * T / 100"""
    interest = principal * annual_rate * years / 100
    return {"interest": round(interest, 2), "total": round(principal + interest, 2)}


def compound_interest(principal, annual_rate, years, n=12):
    """A = P (1 + R/n)^(n*T)"""
    amount = principal * (1 + annual_rate / 100 / n) ** (n * years)
    return {"interest": round(amount - principal, 2), "total": round(amount, 2)}


def emi(principal, annual_rate, months):
    """EMI = P r (1+r)^n / ((1+r)^n - 1), r = monthly rate"""
    r = annual_rate / 1200
    if months <= 0:
        raise ValueError("months must be > 0")
    if r == 0:
        value = principal / months
    else:
        f = (1 + r) ** months
        value = principal * r * f / (f - 1)
    emi_val = round(value, 2)
    total = round(emi_val * months, 2)
    return {"emi": emi_val, "total_payment": total,
            "total_interest": round(total - principal, 2)}


# ---------------------------------------------------------------- debt payoff
def simulate_payoff(debts, extra=0.0, strategy="avalanche"):
    """
    Month-by-month payoff simulation.
    Every month: add interest, pay every minimum, then throw ALL leftover money
    (extra + freed-up minimums of cleared debts) at one target debt.
      avalanche = highest interest rate first (cheapest overall)
      snowball  = smallest balance first (quick wins)
    """
    ds = [dict(d) for d in debts if d["balance"] > 0]
    if not ds:
        return {"months": 0, "total_interest": 0.0, "paid_off": True}

    budget = sum(d["min_payment"] for d in ds) + max(extra, 0)
    total_interest = 0.0
    months = 0
    while any(d["balance"] > 0.01 for d in ds) and months < 600:
        months += 1
        for d in ds:
            if d["balance"] > 0:
                interest = d["balance"] * d["annual_rate"] / 1200
                d["balance"] += interest
                total_interest += interest

        available = budget
        active = [d for d in ds if d["balance"] > 0.01]
        for d in active:  # minimum payments first
            pay = min(d["min_payment"], d["balance"])
            d["balance"] -= pay
            available -= pay

        if strategy == "snowball":
            order = sorted(active, key=lambda d: d["balance"])
        else:
            order = sorted(active, key=lambda d: -d["annual_rate"])
        for d in order:  # everything left goes to the target debt
            if available <= 0:
                break
            pay = min(available, d["balance"])
            d["balance"] -= pay
            available -= pay

    return {"months": months, "total_interest": round(total_interest, 2),
            "paid_off": months < 600 and all(d["balance"] <= 0.01 for d in ds)}


# ---------------------------------------------------------------- forecasting & score
def forecast(expense_so_far, day, days_in_month):
    """Linear run-rate forecast of month-end spending."""
    day = max(day, 1)
    return round(expense_so_far / day * days_in_month, 2)


def _clamp(x, lo=0.0, hi=1.0):
    return max(lo, min(hi, x))


def health_score(income, expense, debt_payments, discipline):
    """
    0-100 score:
      40 pts savings rate (20% saved = full marks)
      30 pts debt-to-income (0% = full, 40%+ = zero)
      30 pts budget discipline (share of budgets not exceeded)
    """
    if income <= 0:
        return {"score": 0, "label": "Add income to see score",
                "tips": ["Add your monthly income to calculate your score."]}
    savings_rate = (income - expense) / income
    dti = debt_payments / income
    score = 40 * _clamp(savings_rate / 0.20) + 30 * (1 - _clamp(dti / 0.40)) + 30 * discipline
    score = round(score)

    tips = []
    if savings_rate < 0.20:
        tips.append(f"You save {max(savings_rate, 0) * 100:.0f}% of income. Aim for 20%.")
    if dti > 0.30:
        tips.append(f"Debt payments take {dti * 100:.0f}% of income. Keep it under 30%.")
    if discipline < 1:
        tips.append("Some budgets are exceeded. Review the red categories.")
    if not tips:
        tips.append("Great balance. Keep it up and grow your emergency fund.")

    label = ("Excellent" if score >= 75 else "Good" if score >= 50
             else "Needs work" if score >= 30 else "Critical")
    return {"score": score, "label": label, "tips": tips}


# ---------------------------------------------------------------- anomalies & subscriptions
def find_anomalies(expenses):
    """Flag duplicate charges and amounts far above a category's normal (mean + 2 std)."""
    results = []
    by_cat = defaultdict(list)
    for e in expenses:
        by_cat[e["category"]].append(e["amount"])

    for e in expenses:
        amounts = by_cat[e["category"]]
        if len(amounts) >= 5:
            mean, std = statistics.mean(amounts), statistics.pstdev(amounts)
            if std > 0 and e["amount"] > mean + 2 * std:
                results.append({**e, "reason": f"Unusually high for {e['category']} (average {mean:.0f})"})

    seen = defaultdict(int)
    for e in expenses:
        key = (e["date"], e["description"].lower(), e["amount"])
        seen[key] += 1
        if seen[key] == 2:
            results.append({**e, "reason": "Possible duplicate charge"})
    return results


def detect_subscriptions(expenses):
    """Same merchant, similar amount, in 2+ different months = probably a subscription."""
    groups = defaultdict(list)
    for e in expenses:
        name = re.sub(r"[^a-z ]", "", e["description"].lower()).strip()
        if name:
            groups[name].append(e)
    subs = []
    for name, items in groups.items():
        months = {i["date"][:7] for i in items}
        amounts = [i["amount"] for i in items]
        if len(months) >= 2 and max(amounts) - min(amounts) <= 0.1 * max(amounts):
            subs.append({"name": name.title(), "monthly": round(statistics.mean(amounts), 2),
                         "yearly": round(statistics.mean(amounts) * 12, 2)})
    return subs


def make_insights(by_category, budgets, projected_expense, income):
    """Plain-language optimisation suggestions."""
    out = []
    if by_category:
        top = max(by_category, key=by_category.get)
        share = by_category[top] / max(sum(by_category.values()), 1) * 100
        out.append(f"{top} is your biggest expense ({share:.0f}% of spending).")
    for cat, limit in budgets.items():
        spent = by_category.get(cat, 0)
        if spent > limit:
            out.append(f"Cut {cat} by {spent - limit:,.0f} to get back on budget.")
    if income > 0 and projected_expense > income:
        out.append(f"At this pace you will overspend income by {projected_expense - income:,.0f} this month.")
    return out
