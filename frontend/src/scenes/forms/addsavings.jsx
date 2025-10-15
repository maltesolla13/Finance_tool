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
} from "@mui/material";
import Autocomplete, { createFilterOptions } from "@mui/material/Autocomplete";
import { ApiClient } from "../../data/ApiClient";
import { ApiRequests } from "../../data/ApiFrontend";
import { tokens } from "../../theme";
import Header from "../../components/Header";
import { OptionsService } from "./Services/options.service";
import * as Validators from "./Services/validators";
import * as Payloads from "./Services/payloads";
import * as DateUtils from "./Services/date.utils";

const filter = createFilterOptions();

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
  const [endDatum, setEndDatum] = useState(DateUtils.toISODate(new Date()));
  const [sparrate_e, setSparrate_e] = useState("");
  const [sparrate_p, setSparrate_p] = useState("");

  // ====== Options (Autocomplete) ======
  const [optUsers, setOptUsers] = useState([]);
  const [optKonten, setOptKonten] = useState([]);
  const [optCats, setOptCats] = useState([]);

  const [inputUser, setInputUser] = useState("");
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
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");
  const [ok, setOk] = useState("");

  const loadSavings = useCallback(async () => {
    setLoading(true);
    setErr("");
    try {
      const rows = await api.listSavings();
      setSavings(Array.isArray(rows) ? rows : []);
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
      const da = new Date(a.datum || 0).getTime();
      const db = new Date(b.datum || 0).getTime();
      return db - da; // neueste zuerst
    });
  }, [savings]);

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
      endDatum,
      sparrate_e,
      sparrate_p,
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
        endDatum,
        sparrate_e,
        sparrate_p,
      });
      await api.createSavings(payload);
      setOk("Savings angelegt.");
      // Einträge resetten
      setName("");
      setBetrag("");
      setKategorieId(null);
      setKontoId(null);
      loadSavingss();
    } catch (e2) {
      console.error(e2);
      setErr(e2?.message || "Anlegen fehlgeschlagen");
    }
  };

  // ====== UI: Autocomplete helpers ======
  const KategorieAutocomplete = (
    <Autocomplete
      options={optCats}
      value={optCats.find((o) => o.id === kategorieId) ?? null}
      inputValue={inputCat}
      onInputChange={(_, v) => setInputCat(v)}
      getOptionLabel={(o) => (typeof o === "string" ? o : (o?.name ?? ""))}
      filterOptions={(opts, params) => {
        const filtered = filter(opts, params);
        const { inputValue } = params;
        const exists = opts.some(
          (o) => o.name?.toLowerCase() === inputValue.toLowerCase()
        );
        if (inputValue && !exists) {
          filtered.push({
            id: -1,
            name: `Neu erstellen: "${inputValue}"`,
            __create: inputValue,
          });
        }
        return filtered;
      }}
      onChange={async (_, newVal) => {
        if (!newVal) return setKategorieId(null);
        if (newVal.__create) {
          const created = await optionsSvc.ensureKategorie(newVal.__create);
          setOptCats((prev) => [created, ...prev]);
          setCatsById((prev) => ({ ...prev, [created.id]: created.name }));
          setKategorieId(created.id);
        } else {
          setKategorieId(newVal.id);
        }
      }}
      renderInput={(params) => (
        <TextField {...params} label="Kategorie" required />
      )}
    />
  );

  const UserAutocomplete = (
    <Autocomplete
      options={optUsers}
      value={optUsers.find((o) => o.id === userId) ?? null}
      inputValue={inputUser}
      onInputChange={(_, v) => setInputUser(v)}
      getOptionLabel={(o) => o?.name ?? ""}
      onChange={(_, v) => setUserId(v?.id ?? null)}
      filterOptions={(x) => x}
      renderInput={(p) => <TextField {...p} label="User" required />}
    />
  );

  const KontoAutocomplete = (
    <Autocomplete
      options={optKonten}
      value={optKonten.find((o) => o.id === kontoId) ?? null}
      inputValue={inputKonto}
      onInputChange={(_, v) => setInputKonto(v)}
      getOptionLabel={(o) => o?.name ?? ""}
      onChange={(_, v) => setKontoId(v?.id ?? null)}
      filterOptions={(x) => x}
      renderInput={(p) => <TextField {...p} label="Konto" required />}
    />
  );

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

                {UserAutocomplete}
                {KontoAutocomplete}
                {KategorieAutocomplete}

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
                  onChange={(e) => setDatum(e.target.value)}
                  InputLabelProps={{ shrink: true }}
                  required
                />

                <TextField
                  label="End Datum"
                  type="date"
                  value={endDatum}
                  onChange={(e) => setDatum(e.target.value)}
                  InputLabelProps={{ shrink: true }}
                  required
                />

                <TextField
                  label="Sparrate (€)"
                  type="number"
                  inputProps={{ step: "0.01" }}
                  value={betrag}
                  onChange={(e) => setBetrag(e.target.value)}
                  required
                />

                <TextField
                  label="Sparrate (% von Einkommen)"
                  type="number"
                  inputProps={{ step: "0.01" }}
                  value={betrag}
                  onChange={(e) => setBetrag(e.target.value)}
                  required
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
              Sparziele (nach Datum)
            </Typography>

            <TableContainer>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Ziel Datum</TableCell>
                    <TableCell>Betrag (€)</TableCell>
                    <TableCell>Name</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {receiptsSorted.map((r) => (
                    <TableRow key={r.id} hover>
                      <TableCell>
                        {DateUtils.formatDateDE(r.endDatum)}
                      </TableCell>
                      <TableCell>
                        {r.betrag != null ? Number(r.betrag).toFixed(2) : "-"}
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
