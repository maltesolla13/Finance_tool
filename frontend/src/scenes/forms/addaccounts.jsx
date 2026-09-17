import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Alert,
  Autocomplete,
  Box,
  Button,
  LinearProgress,
  Grid,
  Paper,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import { useSearchParams } from "react-router-dom";
import { ApiClient } from "../../data/ApiClient";
import { ApiRequests } from "../../data/ApiFrontend";
import Header from "../../components/Header";

export default function AddAccount() {
  const api = useMemo(() => new ApiRequests(new ApiClient()), []);
  const [searchParams] = useSearchParams();
  const [accounts, setAccounts] = useState([]);
  const [users, setUsers] = useState([]);
  const [name, setName] = useState("");
  const [userIds, setUserIds] = useState([]);
  const [editId, setEditId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [nextAccounts, nextUsers] = await Promise.all([
        api.listKonten(),
        api.listUsers(),
      ]);
      setAccounts(nextAccounts);
      setUsers(nextUsers);
    } catch (err) {
      setError(err.message || "Konten konnten nicht geladen werden.");
    } finally {
      setLoading(false);
    }
  }, [api]);

  useEffect(() => {
    load();
  }, [load]);

  const startEdit = useCallback((account) => {
    setEditId(account.id);
    setName(account.name);
    setUserIds(account.user_ids ?? []);
    setError("");
    setSuccess("");
  }, []);

  useEffect(() => {
    const account = accounts.find(
      (item) => item.id === Number(searchParams.get("konto")),
    );
    if (account) startEdit(account);
  }, [accounts, searchParams, startEdit]);

  const reset = () => {
    setEditId(null);
    setName("");
    setUserIds([]);
  };

  const save = async (event) => {
    event.preventDefault();
    setError("");
    setSuccess("");
    if (!name.trim() || !userIds.length) {
      setError("Bitte Kontonamen und mindestens einen User angeben.");
      return;
    }
    setSaving(true);
    try {
      const payload = { name: name.trim(), user_ids: userIds };
      if (editId != null) await api.updateKonto(editId, payload);
      else await api.createKonto(payload);
      reset();
      await load();
      setSuccess("Konto und User-Zuordnung gespeichert.");
    } catch (err) {
      setError(err.message || "Speichern fehlgeschlagen.");
    } finally {
      setSaving(false);
    }
  };

  const usersById = Object.fromEntries(
    users.map((user) => [user.id, user.name]),
  );
  return (
    <Box m="20px">
      <Header
        title="Add new Account"
        subtitle="Konten anlegen, bearbeiten und User zuordnen"
      />
      {(loading || saving) && <LinearProgress />}
      <Stack spacing={2}>
        {error && <Alert severity="error">{error}</Alert>}
        {success && <Alert severity="success">{success}</Alert>}
        {!loading && !users.length && (
          <Alert severity="info">
            Bitte zuerst unter Forms einen User anlegen.
          </Alert>
        )}
        <Grid container spacing={3} alignItems="flex-start">
          <Grid size={{ xs: 12, lg: 5 }} sx={{ minWidth: 0 }}>
            <Paper
              sx={{
                p: 3,
                borderRadius: 3,
                border: "1px solid",
                borderColor: "divider",
              }}
            >
              <Stack spacing={2} component="form" onSubmit={save}>
                <Typography variant="h6">
                  {editId == null ? "Konto anlegen" : "Konto bearbeiten"}
                </Typography>
                <TextField
                  label="Kontoname"
                  value={name}
                  required
                  disabled={saving}
                  onChange={(event) => setName(event.target.value)}
                />
                <Autocomplete
                  multiple
                  options={users}
                  value={users.filter((user) => userIds.includes(user.id))}
                  onChange={(_, selected) =>
                    setUserIds(selected.map((user) => user.id))
                  }
                  getOptionLabel={(user) => user.name}
                  isOptionEqualToValue={(a, b) => a.id === b.id}
                  disabled={saving || loading}
                  renderInput={(params) => (
                    <TextField
                      {...params}
                      label="Zugeordnete User"
                      required={userIds.length === 0}
                      helperText="Mindestens ein User; mehrere User sind moeglich."
                    />
                  )}
                />
                <Stack direction="row" spacing={2}>
                  <Button
                    type="submit"
                    variant="contained"
                    disabled={saving || loading || !users.length}
                  >
                    {editId == null ? "Anlegen" : "Speichern"}
                  </Button>
                  {editId != null && (
                    <Button onClick={reset} disabled={saving}>
                      Abbrechen
                    </Button>
                  )}
                </Stack>
              </Stack>
            </Paper>
          </Grid>
          <Grid size={{ xs: 12, lg: 7 }} sx={{ minWidth: 0 }}>
            <Paper
              sx={{
                p: 3,
                borderRadius: 3,
                border: "1px solid",
                borderColor: "divider",
              }}
            >
              <Typography variant="h6" gutterBottom>
                Vorhandene Konten
              </Typography>
              {!loading && !accounts.length && (
                <Typography>Noch kein Konto angelegt.</Typography>
              )}
              <Stack spacing={2}>
                {accounts.map((account) => (
                  <Stack
                    key={account.id}
                    direction="row"
                    alignItems="center"
                    justifyContent="space-between"
                    spacing={2}
                  >
                    <Box>
                      <Typography>{account.name}</Typography>
                      <Typography
                        variant="body2"
                        color={
                          account.user_ids?.length ? "text.secondary" : "error"
                        }
                      >
                        {account.user_ids?.length
                          ? account.user_ids
                              .map((id) => usersById[id] ?? id)
                              .join(", ")
                          : "Bitte mindestens einen User zuordnen"}
                      </Typography>
                    </Box>
                    <Button
                      onClick={() => startEdit(account)}
                      disabled={saving}
                    >
                      Bearbeiten
                    </Button>
                  </Stack>
                ))}
              </Stack>
            </Paper>
          </Grid>
        </Grid>
      </Stack>
    </Box>
  );
}
