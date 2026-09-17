import { fireEvent, render, screen } from "@testing-library/react";
import AccountUserField from "./AccountUserField";

const users = [
  { id: 1, name: "Anna" },
  { id: 2, name: "Ben" },
  { id: 3, name: "Clara" },
];
const accounts = [
  { id: 10, name: "Anna privat", user_ids: [1] },
  { id: 20, name: "Gemeinsam", user_ids: [1, 2] },
  { id: 30, name: "Clara privat", user_ids: [3] },
  { id: 40, name: "Unzugeordnet", user_ids: [] },
];
const props = { accounts, users, valueId: null };

test("assigns the sole user automatically and shows a read-only field", () => {
  const onSelectId = jest.fn();
  render(
    <AccountUserField {...props} accountIds={[10]} onSelectId={onSelectId} />,
  );
  expect(onSelectId).toHaveBeenCalledWith(1);
  expect(screen.getByLabelText("User").value).toBe("Anna");
  expect(screen.getByLabelText("User").readOnly).toBe(true);
  expect(screen.queryByRole("combobox")).toBeNull();
});

test("shared accounts offer only their assigned users", () => {
  const onSelectId = jest.fn();
  render(
    <AccountUserField {...props} accountIds={[20]} onSelectId={onSelectId} />,
  );
  fireEvent.mouseDown(screen.getByRole("combobox"));
  expect(screen.getByRole("option", { name: "Anna" })).toBeTruthy();
  expect(screen.getByRole("option", { name: "Ben" })).toBeTruthy();
  expect(screen.queryByRole("option", { name: "Clara" })).toBeNull();
  fireEvent.click(screen.getByRole("option", { name: "Ben" }));
  expect(onSelectId).toHaveBeenCalledWith(2);
});

test("switching accounts clears an incompatible selected user", () => {
  const onSelectId = jest.fn();
  render(
    <AccountUserField
      {...props}
      valueId={3}
      accountIds={[20]}
      onSelectId={onSelectId}
    />,
  );
  expect(onSelectId).toHaveBeenCalledWith(null);
});

test("two accounts use their common user and reject incompatible accounts", () => {
  const onSelectId = jest.fn();
  const { rerender } = render(
    <AccountUserField
      {...props}
      accountIds={[10, 20]}
      onSelectId={onSelectId}
    />,
  );
  expect(onSelectId).toHaveBeenCalledWith(1);
  rerender(
    <AccountUserField
      {...props}
      valueId={1}
      accountIds={[10, 30]}
      onSelectId={onSelectId}
    />,
  );
  expect(screen.getByRole("alert").textContent).toContain("gemeinsamen User");
  expect(onSelectId).toHaveBeenCalledWith(null);
});

test("clearing the account removes the user and an unassigned account is blocked", () => {
  const onSelectId = jest.fn();
  const { rerender } = render(
    <AccountUserField
      {...props}
      valueId={1}
      accountIds={[null]}
      onSelectId={onSelectId}
    />,
  );
  expect(onSelectId).toHaveBeenCalledWith(null);
  expect(screen.getByLabelText("User").disabled).toBe(true);
  rerender(
    <AccountUserField {...props} accountIds={[40]} onSelectId={onSelectId} />,
  );
  expect(screen.getByRole("alert").textContent).toContain("noch kein User");
});
