import { calculateTrade } from "./trade.utils";

test("80 EUR buys 79 EUR of shares but sells 80 EUR before the fee", () => {
  expect(
    calculateTrade({ side: "Kauf", price: 10, amount: 80, basis: "betrag" }),
  ).toEqual({ amount: "80.00", shares: "7.900000", fee: 1 });
  expect(
    calculateTrade({ side: "Verkauf", price: 10, amount: 80, basis: "betrag" }),
  ).toEqual({ amount: "80.00", shares: "8.000000", fee: 1 });
});

test("entering shares includes the fee in the purchase budget", () => {
  expect(
    calculateTrade({ side: "Kauf", price: 10, shares: 8, basis: "anteile" }),
  ).toEqual({ amount: "81.00", shares: "8", fee: 1 });
});

test("savings plans stay free and invalid purchase budgets have no preview", () => {
  expect(
    calculateTrade({
      side: "Sparplan",
      price: 10,
      amount: 80,
      basis: "betrag",
    }),
  ).toEqual({ amount: "80.00", shares: "8.000000", fee: 0 });
  expect(
    calculateTrade({ side: "Kauf", price: 10, amount: 1, basis: "betrag" }),
  ).toBeNull();
});
