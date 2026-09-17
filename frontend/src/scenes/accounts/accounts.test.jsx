import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { Link, MemoryRouter, useLocation } from "react-router-dom";
import Accounts from "./index";
import AddAccount from "../forms/addaccounts";
import { ApiRequests } from "../../data/ApiFrontend";

jest.mock("../../data/ApiFrontend");

test("portfolio accounts render the persisted total value history", async () => {
  ApiRequests.prototype.accountSummary.mockResolvedValue({
    account: { id: 1, name: "Depot" },
    balance: 50,
    income: 50,
    expenses: 0,
    as_of: "2026-09-17",
    has_portfolio: true,
    portfolio_value: 300,
    purchase_value: 280,
    portfolio_profit: 20,
    total_value: 350,
    valuation_date: "2026-09-17",
    transactions: [],
    history: [{ date: "2026-09-17", balance: 50 }],
    value_history: [{ date: "2026-09-17", balance: 350 }],
  });
  render(
    <MemoryRouter initialEntries={["/accounts?user=1&konto=1"]}>
      <Accounts />
    </MemoryRouter>,
  );
  expect(
    await screen.findByRole("img", { name: "Gesamtwertentwicklung in Euro" }),
  ).toBeTruthy();
  expect(screen.getByText("Einkauf")).toBeTruthy();
  expect(screen.getByText("Gewinn")).toBeTruthy();
  expect(screen.getByText("Gesamtvermögen")).toBeTruthy();
  expect(screen.queryByText("Guthaben")).toBeNull();
  expect(screen.queryByText("Eingänge")).toBeNull();
  expect(screen.queryByText("Ausgänge")).toBeNull();
  expect(screen.getByRole("heading", { name: /280,00/ })).toBeTruthy();
  expect(screen.getByRole("heading", { name: /20,00/ })).toBeTruthy();
  expect(screen.getByRole("heading", { name: /350,00/ })).toBeTruthy();
});

function UserNavigation() {
  const location = useLocation();
  return (
    <>
      <Link to="/accounts?user=1">Anna öffnen</Link>
      <Link to="/accounts?user=2">Ben öffnen</Link>
      <output data-testid="location">{location.search}</output>
    </>
  );
}

const accounts = [
  { id: 1, name: "Gemeinschaft", user_ids: [1, 2] },
  { id: 2, name: "Einzelkonto", user_ids: [1] },
];

beforeEach(() => {
  jest.clearAllMocks();
  ApiRequests.prototype.listKonten.mockResolvedValue(accounts);
  ApiRequests.prototype.listUsers.mockResolvedValue([
    { id: 1, name: "Anna" },
    { id: 2, name: "Ben" },
  ]);
  ApiRequests.prototype.accountSummary.mockResolvedValue({
    account: accounts[0],
    balance: 75,
    income: 100,
    expenses: -25,
    as_of: "2026-09-17",
    has_checkpoints: false,
    history: [
      { date: "2026-09-01", balance: 100 },
      { date: "2026-09-17", balance: 75 },
    ],
    transactions: [
      {
        id: "receipt:1",
        date: "2026-09-17",
        name: "Einkauf",
        type: "Einkauf",
        user: "Ben",
        category: "Essen",
        amount: -25,
        cash_change: -25,
        balance: 75,
      },
    ],
  });
});

test("account links show cash development and attributable bookings, not the editor", async () => {
  render(
    <MemoryRouter initialEntries={["/accounts?konto=1"]}>
      <Accounts />
    </MemoryRouter>,
  );
  expect(
    await screen.findByRole("table", { name: "Kontobuchungen" }),
  ).toBeTruthy();
  expect(
    screen.getByRole("img", { name: "Guthabenentwicklung in Euro" }),
  ).toBeTruthy();
  expect(screen.getByText("Ben")).toBeTruthy();
  expect(screen.queryByLabelText("Kontoname")).toBeNull();
  expect(ApiRequests.prototype.accountSummary).toHaveBeenCalledWith(1);
  fireEvent.change(screen.getByLabelText("Buchungen filtern"), {
    target: { value: "nicht vorhanden" },
  });
  expect(screen.getByText("Keine Buchungen gefunden.")).toBeTruthy();
});

test("Add new Account edits the name and retains all assigned users", async () => {
  ApiRequests.prototype.updateKonto.mockResolvedValue({ ok: true });
  render(
    <MemoryRouter initialEntries={["/forms/addaccount?konto=1"]}>
      <AddAccount />
    </MemoryRouter>,
  );
  await waitFor(() =>
    expect(screen.getByLabelText(/Kontoname/).value).toBe("Gemeinschaft"),
  );
  fireEvent.change(screen.getByLabelText(/Kontoname/), {
    target: { value: "Haushaltskonto" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Speichern" }));
  await waitFor(() =>
    expect(ApiRequests.prototype.updateKonto).toHaveBeenCalledWith(1, {
      name: "Haushaltskonto",
      user_ids: [1, 2],
    }),
  );
  expect(
    await screen.findByText("Konto und User-Zuordnung gespeichert."),
  ).toBeTruthy();
});

test("a failed account request shows the error and allows retry", async () => {
  ApiRequests.prototype.accountSummary.mockRejectedValue(
    new Error("Konto nicht gefunden."),
  );
  render(
    <MemoryRouter initialEntries={["/accounts?konto=99"]}>
      <Accounts />
    </MemoryRouter>,
  );
  expect(await screen.findByRole("alert")).toBeTruthy();
  expect(screen.getByText("Konto nicht gefunden.")).toBeTruthy();
  await waitFor(() =>
    expect(screen.getByRole("button", { name: "Aktualisieren" }).disabled).toBe(
      false,
    ),
  );
});

test("only assigned accounts are offered and foreign account links are reset", async () => {
  render(
    <MemoryRouter initialEntries={["/accounts?user=2&konto=2"]}>
      <UserNavigation />
      <Accounts />
    </MemoryRouter>,
  );
  await screen.findByRole("table", { name: "Kontobuchungen" });
  expect(ApiRequests.prototype.accountSummary).toHaveBeenCalledWith(1);
  expect(ApiRequests.prototype.accountSummary).not.toHaveBeenCalledWith(2);
  fireEvent.mouseDown(screen.getByRole("combobox", { name: "Konto" }));
  expect(screen.getByRole("option", { name: "Gemeinschaft" })).toBeTruthy();
  expect(screen.queryByRole("option", { name: "Einzelkonto" })).toBeNull();
  expect(screen.getByTestId("location").textContent).toBe("?user=2&konto=1");
});

test("account selection retains the user, and changing user resets an unassigned account", async () => {
  ApiRequests.prototype.accountSummary.mockImplementation(async (id) => ({
    account: accounts.find((account) => account.id === id),
    balance: 0,
    income: 0,
    expenses: 0,
    as_of: "2026-09-17",
    history: [],
    transactions: [],
  }));
  render(
    <MemoryRouter initialEntries={["/accounts?user=1"]}>
      <UserNavigation />
      <Accounts />
    </MemoryRouter>,
  );
  await screen.findByRole("table", { name: "Kontobuchungen" });
  fireEvent.mouseDown(screen.getByRole("combobox", { name: "Konto" }));
  fireEvent.click(screen.getByRole("option", { name: "Einzelkonto" }));
  await waitFor(() =>
    expect(screen.getByTestId("location").textContent).toBe("?user=1&konto=2"),
  );
  await waitFor(() =>
    expect(ApiRequests.prototype.accountSummary).toHaveBeenCalledWith(2),
  );
  fireEvent.click(screen.getByRole("link", { name: "Ben öffnen" }));
  await waitFor(() =>
    expect(screen.getByTestId("location").textContent).toBe("?user=2&konto=1"),
  );
  expect(screen.getByRole("combobox", { name: "Konto" }).value).toBe(
    "Gemeinschaft",
  );
});

test("users without accounts see an empty state without requesting another account", async () => {
  ApiRequests.prototype.listUsers.mockResolvedValue([{ id: 3, name: "Clara" }]);
  render(
    <MemoryRouter initialEntries={["/accounts?user=3"]}>
      <Accounts />
    </MemoryRouter>,
  );
  expect(
    await screen.findByText(/Diesem User sind noch keine Konten zugeordnet/),
  ).toBeTruthy();
  expect(ApiRequests.prototype.accountSummary).not.toHaveBeenCalled();
  expect(screen.queryByRole("table", { name: "Kontobuchungen" })).toBeNull();
});
