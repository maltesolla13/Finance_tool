import { useEffect, useMemo, useState } from "react";
import {
  Alert,
  Autocomplete,
  Box,
  Button,
  LinearProgress,
  Paper,
  Stack,
  TextField,
  Typography,
  Table,
  TableHead,
  TableBody,
  TableRow,
  TableCell,
  TableContainer,
  TablePagination,
} from "@mui/material";
import { Link, useSearchParams } from "react-router-dom";
import Header from "../../components/Header";
import { ApiClient } from "../../data/ApiClient";
import { ApiRequests } from "../../data/ApiFrontend";
import BalanceChart, { euro, dateDE } from "./BalanceChart";

export default function Accounts() {
  const api = useMemo(() => new ApiRequests(new ApiClient()), []);
  const [searchParams, setSearchParams] = useSearchParams();
  const [accounts, setAccounts] = useState([]);
  const [users, setUsers] = useState([]);
  const [loadingOptions, setLoadingOptions] = useState(true);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [revision, setRevision] = useState(0);
  const [query, setQuery] = useState("");
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(25);
  const requestedId = searchParams.get("konto");
  const requestedUser = searchParams.get("user");
  const selectedUser = requestedUser
    ? users.find((user) => user.id === Number(requestedUser))
    : users[0];
  const userId = selectedUser?.id;
  const userAccounts = useMemo(
    () => accounts.filter((account) => account.user_ids?.includes(userId)),
    [accounts, userId],
  );
  const accountId =
    userAccounts.find((account) => account.id === Number(requestedId))?.id ??
    userAccounts[0]?.id;
  const visibleSummary = summary?.account.id === accountId ? summary : null;

  useEffect(() => {
    let active = true;
    setLoadingOptions(true);
    setError("");
    Promise.all([api.listKonten(), api.listUsers()])
      .then(([nextAccounts, nextUsers]) => {
        if (active) {
          setAccounts(nextAccounts);
          setUsers(
            [...nextUsers].sort((a, b) => a.name.localeCompare(b.name, "de")),
          );
        }
      })
      .catch((err) => {
        if (active) {
          setError(err.message);
        }
      })
      .finally(() => {
        if (active) setLoadingOptions(false);
      });
    return () => {
      active = false;
    };
  }, [api, revision]);

  useEffect(() => {
    if (loadingOptions) return;
    if (!accountId) {
      setSummary(null);
      setLoading(false);
      return;
    }
    let active = true;
    setLoading(true);
    setError("");
    setSummary(null);
    setQuery("");
    setPage(0);
    api
      .accountSummary(accountId)
      .then((data) => {
        if (active) setSummary(data);
      })
      .catch((err) => {
        if (active) setError(err.message);
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [api, accountId, userId, loadingOptions]);

  useEffect(() => {
    if (loadingOptions || !userId) return;
    if (
      requestedUser !== String(userId) ||
      requestedId !== (accountId ? String(accountId) : null)
    ) {
      setSearchParams(
        { user: userId, ...(accountId ? { konto: accountId } : {}) },
        { replace: true },
      );
    }
  }, [
    loadingOptions,
    userId,
    accountId,
    requestedUser,
    requestedId,
    setSearchParams,
  ]);

  const rows = useMemo(
    () =>
      (summary?.transactions ?? []).filter((row) =>
        [
          row.name,
          row.type,
          row.user,
          row.category,
          dateDE(row.date),
          euro(row.amount),
        ]
          .join(" ")
          .toLocaleLowerCase("de")
          .includes(query.trim().toLocaleLowerCase("de")),
      ),
    [summary, query],
  );
  const hasDepot = summary?.transactions.some(
    (row) => row.amount !== row.cash_change,
  );
  return (
    <Box m="20px" sx={{ minWidth: 0 }}>
      <Header
        title={selectedUser?.name ?? "Accounts"}
        subtitle={
          visibleSummary
            ? `${visibleSummary.account.name} – Guthabenentwicklung und Buchungen`
            : "Guthabenentwicklung und Buchungen"
        }
      />
      <Stack direction={{ xs: "column", sm: "row" }} spacing={2} sx={{ mb: 2 }}>
        <Autocomplete
          options={userAccounts}
          value={userAccounts.find((a) => a.id === accountId) ?? null}
          getOptionLabel={(account) => account.name}
          isOptionEqualToValue={(a, b) => a.id === b.id}
          onChange={(_, account) => {
            if (account) setSearchParams({ user: userId, konto: account.id });
          }}
          disabled={loadingOptions || !userAccounts.length}
          disableClearable
          sx={{ minWidth: 240, flex: 1 }}
          renderInput={(params) => <TextField {...params} label="Konto" />}
        />
        <Button
          variant="outlined"
          onClick={() => setRevision((value) => value + 1)}
          disabled={loading || loadingOptions}
        >
          Aktualisieren
        </Button>
      </Stack>
      {(loading || loadingOptions) && <LinearProgress sx={{ mb: 2 }} />}
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}
      {!loadingOptions && !selectedUser && !error && (
        <Alert severity="info">
          {requestedUser ? "User nicht gefunden." : "Noch keine User angelegt."}
        </Alert>
      )}
      {!loadingOptions && selectedUser && !userAccounts.length && !error && (
        <Alert severity="info">
          Diesem User sind noch keine Konten zugeordnet.{" "}
          <Link to="/forms/addaccount">Konten verwalten</Link>
        </Alert>
      )}
      {visibleSummary && (
        <Stack spacing={2}>
          <Box
            sx={{
              display: "grid",
              gap: 2,
              gridTemplateColumns: {
                xs: "1fr",
                md: "repeat(3, minmax(0, 1fr))",
              },
            }}
          >
            {[
              ["Guthaben", summary.balance],
              ["Eingänge", summary.income],
              ["Ausgänge", summary.expenses],
            ].map(([label, amount]) => (
              <Paper key={label} sx={{ p: 3, borderRadius: 3 }}>
                <Typography color="text.secondary">{label}</Typography>
                <Typography
                  variant="h3"
                  color={amount < 0 ? "error.light" : "secondary.main"}
                >
                  {euro(amount)}
                </Typography>
              </Paper>
            ))}
          </Box>
          <Paper sx={{ p: 3, borderRadius: 3, minWidth: 0 }}>
            <Typography variant="h5" gutterBottom>
              Guthabenentwicklung
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Stand: {dateDE(summary.as_of)}.{" "}
              {summary.has_checkpoints
                ? "Berechnet aus Buchungen und erfassten Kontoständen."
                : "Aus den erfassten Buchungen berechnet; Startwert 0 €. Ein Anfangsguthaben ist nicht hinterlegt."}
            </Typography>
            <BalanceChart data={summary.history} />
          </Paper>
          <Paper sx={{ p: 3, borderRadius: 3, minWidth: 0 }}>
            <Stack
              direction={{ xs: "column", sm: "row" }}
              justifyContent="space-between"
              spacing={2}
              sx={{ mb: 2 }}
            >
              <Typography variant="h5">
                Alle Buchungen ({rows.length})
              </Typography>
              <TextField
                label="Buchungen filtern"
                size="small"
                value={query}
                onChange={(event) => {
                  setQuery(event.target.value);
                  setPage(0);
                }}
              />
            </Stack>
            {hasDepot && (
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                Wertpapierkäufe und -verkäufe ändern das Guthaben auf dem
                zugehörigen Zahlungskonto. Der Wertpapierbetrag wird hier
                zusätzlich aufgeführt.
              </Typography>
            )}
            <TableContainer>
              <Table size="small" aria-label="Kontobuchungen">
                <TableHead>
                  <TableRow>
                    {[
                      "Datum",
                      "Buchung",
                      "Typ",
                      "User",
                      "Kategorie",
                      "Betrag",
                      ...(hasDepot ? ["Guthabenänderung"] : []),
                      "Saldo",
                    ].map((label, index) => (
                      <TableCell
                        key={label}
                        align={index >= 5 ? "right" : "left"}
                      >
                        {label}
                      </TableCell>
                    ))}
                  </TableRow>
                </TableHead>
                <TableBody>
                  {rows
                    .slice(page * pageSize, (page + 1) * pageSize)
                    .map((row) => (
                      <TableRow key={row.id} hover>
                        <TableCell sx={{ whiteSpace: "nowrap" }}>
                          {dateDE(row.date)}
                          {row.future ? " (zukünftig)" : ""}
                        </TableCell>
                        <TableCell>{row.name}</TableCell>
                        <TableCell>{row.type}</TableCell>
                        <TableCell>{row.user || "—"}</TableCell>
                        <TableCell>{row.category || "—"}</TableCell>
                        <TableCell
                          align="right"
                          sx={{
                            whiteSpace: "nowrap",
                            color:
                              row.amount < 0 ? "error.light" : "secondary.main",
                          }}
                        >
                          {euro(row.amount)}
                        </TableCell>
                        {hasDepot && (
                          <TableCell align="right">
                            {euro(row.cash_change)}
                          </TableCell>
                        )}
                        <TableCell align="right" sx={{ whiteSpace: "nowrap" }}>
                          {euro(row.balance)}
                        </TableCell>
                      </TableRow>
                    ))}
                  {!rows.length && (
                    <TableRow>
                      <TableCell colSpan={hasDepot ? 8 : 7}>
                        Keine Buchungen gefunden.
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </TableContainer>
            <TablePagination
              component="div"
              count={rows.length}
              page={page}
              rowsPerPage={pageSize}
              onPageChange={(_, value) => setPage(value)}
              rowsPerPageOptions={[25, 50, 100]}
              onRowsPerPageChange={(event) => {
                setPageSize(Number(event.target.value));
                setPage(0);
              }}
              labelRowsPerPage="Buchungen pro Seite"
              labelDisplayedRows={({ from, to, count }) =>
                `${from}–${to} von ${count}`
              }
            />
          </Paper>
        </Stack>
      )}
    </Box>
  );
}
