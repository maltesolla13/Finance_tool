export function calculateTrade({ side, price, amount, shares, basis }) {
  if (!Number.isFinite(price) || price <= 0) return null;
  const fee = side === "Kauf" || side === "Verkauf" ? 1 : 0;
  if (basis === "anteile") {
    if (!Number.isFinite(shares) || shares <= 0) return null;
    const total = shares * price + (side === "Kauf" ? fee : 0);
    return { amount: total.toFixed(2), shares: String(shares), fee };
  }
  if (!Number.isFinite(amount) || amount <= 0) return null;
  const investment = amount - (side === "Kauf" ? fee : 0);
  if (investment <= 0 || amount < fee) return null;
  const quantity = Math.floor((investment / price) * 1e6) / 1e6;
  return { amount: amount.toFixed(2), shares: quantity.toFixed(6), fee };
}
