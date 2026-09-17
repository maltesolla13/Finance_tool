import { useEffect, useMemo } from "react";
import { Alert, TextField } from "@mui/material";
import { UserAutocomplete } from "./autocomplete";

export function accountUserOptions(accounts, users, accountIds) {
  const ids = [...new Set(accountIds.filter((id) => id != null))];
  if (!ids.length) return [];
  const selected = ids.map((id) =>
    accounts.find((account) => account.id === id),
  );
  return users.filter((user) =>
    selected.every((account) => account?.user_ids?.includes(user.id)),
  );
}

export default function AccountUserField({
  accounts,
  users,
  accountIds,
  valueId,
  onSelectId,
  loading = false,
}) {
  const allowed = useMemo(
    () => accountUserOptions(accounts, users, accountIds),
    [accounts, users, accountIds],
  );
  const hasAccount = accountIds.some((id) => id != null);
  const validId =
    allowed.length === 1
      ? allowed[0].id
      : allowed.some((user) => user.id === valueId)
        ? valueId
        : null;

  useEffect(() => {
    if (!loading && valueId !== validId) onSelectId(validId);
  }, [loading, validId, valueId, onSelectId]);

  if (!hasAccount) {
    return (
      <TextField
        label="User"
        value=""
        disabled
        fullWidth
        helperText="Zuerst ein Konto auswaehlen."
      />
    );
  }
  if (loading) {
    return (
      <TextField
        label="User"
        value=""
        disabled
        fullWidth
        helperText="Zuordnung wird geladen..."
      />
    );
  }
  if (!allowed.length) {
    return (
      <Alert severity="warning">
        {accountIds.filter((id) => id != null).length > 1
          ? "Die Konten brauchen mindestens einen gemeinsamen User. Bitte die Zuordnung unter Accounts bearbeiten."
          : "Diesem Konto ist noch kein User zugeordnet. Bitte die Zuordnung unter Accounts bearbeiten."}
      </Alert>
    );
  }
  if (allowed.length === 1) {
    return (
      <TextField
        label="User"
        value={allowed[0].name}
        fullWidth
        slotProps={{ input: { readOnly: true } }}
        helperText="Automatisch dem Konto zugeordnet."
      />
    );
  }
  return (
    <UserAutocomplete
      options={allowed}
      valueId={validId}
      onSelectId={onSelectId}
      helperText="Bitte einen User dieses Kontos auswaehlen."
    />
  );
}
