import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import Accounts from "./index";
import AddAccount from "../forms/addaccounts";
import { ApiRequests } from "../../data/ApiFrontend";

jest.mock("../../data/ApiFrontend");

const accounts = [
  { id: 1, name: "Gemeinschaft", user_ids: [1, 2] },
  { id: 2, name: "Einzelkonto", user_ids: [1] },
];

beforeEach(() => {
  jest.clearAllMocks();
  ApiRequests.prototype.listKonten.mockResolvedValue(accounts);
  ApiRequests.prototype.listUsers.mockResolvedValue([{ id: 1, name: "Anna" }, { id: 2, name: "Ben" }]);
  ApiRequests.prototype.accountSummary.mockResolvedValue({
    account: accounts[0], balance: 75, income: 100, expenses: -25,
    as_of: "2026-09-17", has_checkpoints: false,
    history: [{ date: "2026-09-01", balance: 100 }, { date: "2026-09-17", balance: 75 }],
    transactions: [{
      id: "receipt:1", date: "2026-09-17", name: "Einkauf", type: "Einkauf",
      user: "Ben", category: "Essen", amount: -25, cash_change: -25, balance: 75,
    }],
  });
});

test("account links show cash development and attributable bookings, not the editor", async () => {
  render(<MemoryRouter initialEntries={["/accounts?konto=1"]}><Accounts /></MemoryRouter>);
  expect(await screen.findByRole("table", { name: "Kontobuchungen" })).toBeTruthy();
  expect(screen.getByRole("img", { name: "Guthabenentwicklung in Euro" })).toBeTruthy();
  expect(screen.getByText("Ben")).toBeTruthy();
  expect(screen.queryByLabelText("Kontoname")).toBeNull();
  expect(ApiRequests.prototype.accountSummary).toHaveBeenCalledWith(1);
  fireEvent.change(screen.getByLabelText("Buchungen filtern"), { target: { value: "nicht vorhanden" } });
  expect(screen.getByText("Keine Buchungen gefunden.")).toBeTruthy();
});

test("Add new Account edits the name and retains all assigned users", async () => {
  ApiRequests.prototype.updateKonto.mockResolvedValue({ ok: true });
  render(<MemoryRouter initialEntries={["/forms/addaccount?konto=1"]}><AddAccount /></MemoryRouter>);
  await waitFor(() => expect(screen.getByLabelText(/Kontoname/).value).toBe("Gemeinschaft"));
  fireEvent.change(screen.getByLabelText(/Kontoname/), { target: { value: "Haushaltskonto" } });
  fireEvent.click(screen.getByRole("button", { name: "Speichern" }));
  await waitFor(() => expect(ApiRequests.prototype.updateKonto).toHaveBeenCalledWith(1, {
    name: "Haushaltskonto", user_ids: [1, 2],
  }));
  expect(await screen.findByText("Konto und User-Zuordnung gespeichert.")).toBeTruthy();
});

test("a failed account request shows the error and allows retry", async () => {
  ApiRequests.prototype.accountSummary.mockRejectedValue(new Error("Konto nicht gefunden."));
  render(<MemoryRouter initialEntries={["/accounts?konto=99"]}><Accounts /></MemoryRouter>);
  expect(await screen.findByRole("alert")).toBeTruthy();
  expect(screen.getByText("Konto nicht gefunden.")).toBeTruthy();
  await waitFor(() => expect(screen.getByRole("button", { name: "Aktualisieren" }).disabled).toBe(false));
});

