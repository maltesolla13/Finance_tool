import AccountUserField from "./Services/AccountUserField";
import {
  useEffect,
  useMemo,
  useState,
  useCallback,
  useMemo as useReactMemo,
} from "react";
import {
  Box,
  TextField,
  Button,
  Stack,
  Alert,
  LinearProgress,
  Typography,
  Grid,
  Paper,
  useTheme,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  ToggleButton,
  ToggleButtonGroup,
} from "@mui/material";
import { ApiClient } from "../../data/ApiClient";
import { ApiRequests } from "../../data/ApiFrontend";
import { tokens } from "../../theme";
import Header from "../../components/Header";
import { OptionsService } from "./Services/options.service";
import * as Validators from "./Services/validators";
import * as Payloads from "./Services/payloads";
import * as DateUtils from "./Services/date.utils";
import {
  KontoAutocomplete,
  KategorieAutocomplete,
} from "./Services/autocomplete";

export default function AddSavings() {
  const theme = useTheme();
  const colors = tokens(theme.palette.mode);

  // === API + FormService ===
  const api = useMemo(() => new ApiRequests(new ApiClient()), []);
  const optionsSvc = useMemo(() => new OptionsService(api), [api]);

  // ====== Form State ======
  const [name, setName] = useState("");
  const [userId, setUserId] = useState(null);
  const [kontoId, setKontoId] = useState(null);
  const [kategorieId, setKategorieId] = useState(null);
  const [betrag, setBetrag] = useState("");
  const [startDatum, setStartDatum] = useState(DateUtils.toISODate(new Date()));
  const [planMode, setPlanMode] = useState("end");
  const [endDatum, setEndDatum] = useState("");
  const [sparrate_e, setSparrate_e] = useState("");
  const [sparrate_p, setSparrate_p] = useState("");

  // ====== Options (Autocomplete) ======
  const [optUsers, setOptUsers] = useState([]);
  const [optKonten, setOptKonten] = useState([]);
  const [optCats, setOptCats] = useState([]);

  const inputUser = "";
  const [inputKonto, setInputKonto] = useState("");
  const [inputCat, setInputCat] = useState("");
  const [loadingOpts, setLoadingOpts] = useState(false);

  // maps for Anzeige (id -> name)
  const [usersById, setUsersById] = useState({});
  const [kontenById, setKontenById] = useState({});
  const [catsById, setCatsById] = useState({});

  // === Optionen initial laden ===
  const loadAllOptions = useCallback(async () => {
    setLoadingOpts(true);
    try {
      const { options, maps } = await optionsSvc.loadAll({
        includeSecurities: false,
      });
      setOptUsers(options.users);
      setOptKonten(options.konten);
      setOptCats(options.cats);
      setUsersById(maps.usersById);
      setKontenById(maps.kontenById);
      setCatsById(maps.catsById);
    } finally {
      setLoadingOpts(false);
    }
  }, [optionsSvc]);

  useEffect(() => {
    loadAllOptions();
  }, [loadAllOptions]);

  // Live-Suche (leicht debounced)
  useEffect(() => {
    let alive = true;
    const t = setTimeout(async () => {
      try {
        const { options, maps } = await optionsSvc.refreshOptions({
          users: inputUser,
          konten: inputKonto,
          cats: inputCat,
        });
        if (!alive) return;
        setOptUsers(options.users);
        setOptKonten(options.konten);
        setOptCats(options.cats);
        setUsersById(maps.usersById);
        setKontenById(maps.kontenById);
        setCatsById(maps.catsById);
      } catch {}
    }, 250);
    return () => {
      alive = false;
      clearTimeout(t);
    };
  }, [inputUser, inputKonto, inputCat, optionsSvc]);

  // ====== Savings laden ======
  const [savings, setSavings] = useState([]);
  const [savingsExecutions, setSavingsExecutions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");
  const [ok, setOk] = useState("");

  const loadSavings = useCallback(async () => {
    setLoading(true);
    setErr("");
    try {
      const rows = await api.listSavings();

      // snake_case -> camelCase normalisieren
      const normalized = (Array.isArray(rows) ? rows : []).map((r) => ({
        ...r,
        startDatum: r.startDatum ?? r.start_datum ?? null,
        endDatum: r.endDatum ?? r.end_datum ?? null,
      }));

      setSavings(normalized);
      const execRows = await api.listSavingsExecution();
      setSavingsExecutions(Array.isArray(execRows) ? execRows : []);
    } catch (e) {
      console.warn(e);
      setErr("Konnte Sparziele nicht laden.");
    } finally {
      setLoading(false);
    }
  }, [api]);

  useEffect(() => {
    loadSavings();
  }, [loadSavings]);

  const savingsSorted = useReactMemo(() => {
    return [...savings].sort((a, b) => {
      const da = new Date(a.endDatum || 0).getTime();
      const db = new Date(b.endDatum || 0).getTime();
      return db - da; // neueste zuerst
    });
  }, [savings]);

  const executionTotalsBySavings = useReactMemo(() => {
    return savingsExecutions.reduce((acc, row) => {
      const key = row.savings_id;
      const current = acc[key] || { count: 0, amount: 0 };
      current.count += 1;
      current.amount += Number(row.amount || 0);
      acc[key] = current;
      return acc;
    }, {});
  }, [savingsExecutions]);

  // ====== Formular Submit (Create) ======
  const onCreate = async (e) => {
    e.preventDefault();
    setErr("");
    setOk("");

    const errMsg = Validators.validateSavings({
      name,
      userId,
      kontoId,
      kategorieId,
      betrag,
      startDatum,
      endDatum: planMode === "end" ? endDatum : "",
      sparrate_e: planMode === "amount" ? sparrate_e : "",
      sparrate_p: planMode === "percent" ? sparrate_p : "",
    });
    if (errMsg) {
      setErr(errMsg);
      return;
    }

    try {
      const payload = Payloads.toPayloadSavings({
        name,
        userId,
        kontoId,
        kategorieId,
        betrag,
        startDatum,
        endDatum: planMode === "end" ? endDatum : "",
        sparrate_e: planMode === "amount" ? sparrate_e : "",
        sparrate_p: planMode === "percent" ? sparrate_p : "",
      });
      await api.createSavings(payload);
      setOk("Savings angelegt.");
      // Einträge resetten
      setName("");
      setBetrag("");
      setEndDatum("");
      setSparrate_e("");
      setSparrate_p("");
      setPlanMode("end");
      setKategorieId(null);
      setKontoId(null);
      loadSavings();
    } catch (e2) {
      console.error(e2);
      setErr(e2?.message || "Anlegen fehlgeschlagen");
    }
  };

  return (
    <Box m="20px">
      <Box display="flex" justifyContent="space-between" alignItems="center">
        <Header title="New Savings goal" subtitle="Add a new Savings goal" />
      </Box>

      {loading && <LinearProgress sx={{ mb: 2 }} />}
      {!!err && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {err}
        </Alert>
      )}
      {!!ok && (
        <Alert severity="success" sx={{ mb: 2 }}>
          {ok}
        </Alert>
      )}

      {/* Zweispaltiges Layout */}
      <Grid container spacing={3}>
        {/* LINKE SEITE FORMULAR */}
        <Grid item xs={12} md={6}>
          <Paper
            sx={{
              p: 3,
              borderRadius: 3,
              backgroundColor: colors?.primary?.[400] ?? "background.paper",
              border: "1px solid",
              borderColor: "divider",
            }}
          >
            <Typography variant="h6" sx={{ mb: 2 }}>
              Sparziel hinzufügen
            </Typography>

            <Box component="form" onSubmit={onCreate}>
              <Stack spacing={2}>
                <TextField
                  label="Bezeichnung"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  required
                />

                <KontoAutocomplete
                  options={optKonten}
                  valueId={kontoId}
                  inputValue={inputKonto}
                  onInputChange={setInputKonto}
                  onSelectId={setKontoId}
                />
                <AccountUserField
                  accounts={optKonten}
                  users={optUsers}
                  accountIds={[kontoId]}
                  valueId={userId}
                  onSelectId={setUserId}
                  loading={loadingOpts}
                />

                <KategorieAutocomplete
                  options={optCats}
                  valueId={kategorieId}
                  inputValue={inputCat}
                  onInputChange={setInputCat}
                  onSelectId={setKategorieId}
                  onCreate={async (name) => {
                    const created = await optionsSvc.ensureKategorie(name);
                    setOptCats((prev) => [created, ...prev]);
                    setKategorieId(created.id);
                  }}
                />

                <TextField
                  label="Betrag (€)"
                  type="number"
                  inputProps={{ step: "0.01" }}
                  value={betrag}
                  onChange={(e) => setBetrag(e.target.value)}
                  required
                />

                <TextField
                  label="Start Datum"
                  type="date"
                  value={startDatum}
                  onChange={(e) => setStartDatum(e.target.value)}
                  InputLabelProps={{ shrink: true }}
                  required
                />

                <TextField
                  label="End Datum"
                  type="date"
                  value={endDatum}
                  onChange={(e) => setEndDatum(e.target.value)}
                  InputLabelProps={{ shrink: true }}
                  required={planMode === "end"}
                  sx={{ display: planMode === "end" ? "flex" : "none" }}
                />

                <ToggleButtonGroup
                  exclusive
                  fullWidth
                  color="primary"
                  value={planMode}
                  onChange={(_, value) => {
                    if (!value) return;
                    setPlanMode(value);
                    setEndDatum("");
                    setSparrate_e("");
                    setSparrate_p("");
                  }}
                >
                  <ToggleButton value="end">Enddatum</ToggleButton>
                  <ToggleButton value="amount">EUR/Monat</ToggleButton>
                  <ToggleButton value="percent">% Gehalt</ToggleButton>
                </ToggleButtonGroup>

                <TextField
                  label="Sparrate (€)"
                  type="number"
                  inputProps={{ step: "0.01" }}
                  value={sparrate_e}
                  onChange={(e) => setSparrate_e(e.target.value)}
                  required={planMode === "amount"}
                  sx={{ display: planMode === "amount" ? "flex" : "none" }}
                />

                <TextField
                  label="Sparrate (% von Einkommen)"
                  type="number"
                  inputProps={{ step: "0.01" }}
                  value={sparrate_p}
                  onChange={(e) => setSparrate_p(e.target.value)}
                  required={planMode === "percent"}
                  sx={{ display: planMode === "percent" ? "flex" : "none" }}
                />

                <Box>
                  <Button type="submit" variant="contained">
                    Anlegen
                  </Button>
                </Box>
              </Stack>
            </Box>
            {loadingOpts && <LinearProgress sx={{ mt: 2 }} />}
          </Paper>
        </Grid>

        {/* RECHTE SEITE: Tabelle der Sparziele */}
        <Grid item xs={12} md={6}>
          <Paper
            sx={{
              p: 3,
              borderRadius: 3,
              bgcolor: colors?.primary?.[400] ?? "background.paper",
              border: "1px solid",
              borderColor: "divider",
            }}
          >
            <Typography variant="h6" sx={{ mb: 2 }}>
              Sparziele (nach Enddatum)
            </Typography>

            <TableContainer>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Ziel Datum</TableCell>
                    <TableCell>Betrag (€)</TableCell>
                    <TableCell>Rate</TableCell>
                    <TableCell>Ausgefuehrt</TableCell>
                    <TableCell>Name</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {savingsSorted.map((r) => (
                    <TableRow key={r.id} hover>
                      <TableCell>
                        {DateUtils.formatDateDE(r.endDatum)}
                      </TableCell>
                      <TableCell>
                        {r.betrag != null ? Number(r.betrag).toFixed(2) : "-"}
                      </TableCell>
                      <TableCell>
                        {r.sparrate_e != null
                          ? `${Number(r.sparrate_e).toFixed(2)} EUR`
                          : r.sparrate_p != null
                            ? `${Number(r.sparrate_p).toFixed(2)}%`
                            : "-"}
                      </TableCell>
                      <TableCell>
                        {executionTotalsBySavings[r.id]
                          ? `${executionTotalsBySavings[r.id].count} / ${executionTotalsBySavings[r.id].amount.toFixed(2)} EUR`
                          : "-"}
                      </TableCell>
                      <TableCell>{r.name}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
}
