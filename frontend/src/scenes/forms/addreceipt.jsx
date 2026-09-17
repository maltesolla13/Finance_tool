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
  LadenAutocomplete,
} from "./Services/autocomplete";

export default function AddReceipt() {
  const theme = useTheme();
  const colors = tokens(theme.palette.mode);

  // === API + FormService ===
  const api = useMemo(() => new ApiRequests(new ApiClient()), []);
  const optionsSvc = useMemo(() => new OptionsService(api), [api]);

  // ====== Form State ======
  const [userId, setUserId] = useState(null);
  const [kontoId, setKontoId] = useState(null);
  const [kategorieId, setKategorieId] = useState(null);
  const [ladenId, setLadenId] = useState(null);

  const [name, setName] = useState("");
  const [betrag, setBetrag] = useState("");
  const [datum, setDatum] = useState(DateUtils.toISODate(new Date()));

  // ====== Options (Autocomplete) ======
  const [optUsers, setOptUsers] = useState([]);
  const [optKonten, setOptKonten] = useState([]);
  const [optCats, setOptCats] = useState([]);
  const [optLaden, setOptLaden] = useState([]);

  const inputUser = "";
  const [inputKonto, setInputKonto] = useState("");
  const [inputCat, setInputCat] = useState("");
  const [inputLaden, setInputLaden] = useState("");
  const [loadingOpts, setLoadingOpts] = useState(false);

  // maps for Anzeige (id -> name)
  const [usersById, setUsersById] = useState({});
  const [kontenById, setKontenById] = useState({});
  const [catsById, setCatsById] = useState({});
  const [ladenById, setLadenById] = useState({});

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
      setOptLaden(options.laden);
      setUsersById(maps.usersById);
      setKontenById(maps.kontenById);
      setCatsById(maps.catsById);
      setLadenById(maps.ladenById);
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
          laden: inputLaden,
        });
        if (!alive) return;
        setOptUsers(options.users);
        setOptKonten(options.konten);
        setOptCats(options.cats);
        setOptLaden(options.laden);
        setUsersById(maps.usersById);
        setKontenById(maps.kontenById);
        setCatsById(maps.catsById);
        setLadenById(maps.ladenById);
      } catch {
        /* ignore */
      }
    }, 250);
    return () => {
      alive = false;
      clearTimeout(t);
    };
  }, [inputUser, inputKonto, inputCat, inputLaden, optionsSvc]);

  // ====== Receipts laden ======
  const [receipts, setReceipts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");
  const [ok, setOk] = useState("");

  const loadReceipts = useCallback(async () => {
    setLoading(true);
    setErr("");
    try {
      const rows = await api.listReceipt();
      setReceipts(Array.isArray(rows) ? rows : []);
    } catch (e) {
      console.warn(e);
      setErr("Konnte Einkäufe nicht laden.");
    } finally {
      setLoading(false);
    }
  }, [api]);

  useEffect(() => {
    loadReceipts();
  }, [loadReceipts]);

  const receiptsSorted = useReactMemo(() => {
    return [...receipts].sort((a, b) => {
      const da = new Date(a.datum || 0).getTime();
      const db = new Date(b.datum || 0).getTime();
      return db - da; // neueste zuerst
    });
  }, [receipts]);

  // ====== Formular Submit (Create) ======
  const onCreate = async (e) => {
    e.preventDefault();
    setErr("");
    setOk("");

    const errMsg = Validators.validateReceipt({
      userId,
      kontoId,
      kategorieId,
      ladenId,
      name,
      betrag,
      datum,
    });
    if (errMsg) {
      setErr(errMsg);
      return;
    }

    try {
      const payload = Payloads.toPayloadReceipt({
        userId,
        kontoId,
        kategorieId,
        ladenId,
        name,
        betrag,
        datum,
      });
      await api.createReceipt(payload);
      setOk("Einkauf angelegt.");
      setName("");
      setBetrag("");
      setKategorieId(null);
      setLadenId(null);
      setKontoId(null);
      // userId bewusst nicht resetten
      loadReceipts();
    } catch (e2) {
      console.error(e2);
      setErr(e2?.message || "Anlegen fehlgeschlagen");
    }
  };

  return (
    <Box m="20px">
      <Box display="flex" justifyContent="space-between" alignItems="center">
        <Header title="New Receipt" subtitle="Add a new Receipt" />
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
              Einkauf hinzufügen
            </Typography>

            <Box component="form" onSubmit={onCreate}>
              <Stack spacing={2}>
                <TextField
                  label="Bezeichnung"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  required
                />

                <TextField
                  label="Betrag (€)"
                  type="number"
                  inputProps={{ step: "0.01" }}
                  value={betrag}
                  onChange={(e) => setBetrag(e.target.value)}
                  required
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

                <LadenAutocomplete
                  options={optLaden}
                  valueId={ladenId}
                  inputValue={inputLaden}
                  onInputChange={setInputLaden}
                  onSelectId={setLadenId}
                  onCreate={async (name) => {
                    const created = await optionsSvc.ensureLaden(name);
                    setOptLaden((prev) => [created, ...prev]);
                    setLadenId(created.id);
                  }}
                />

                <TextField
                  label="Datum"
                  type="date"
                  value={datum}
                  onChange={(e) => setDatum(e.target.value)}
                  InputLabelProps={{ shrink: true }}
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

        {/* RECHTE SEITE: Tabelle der Einkäufe */}
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
              Einkäufe (nach Datum)
            </Typography>

            <TableContainer>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Datum</TableCell>
                    <TableCell>Betrag (€)</TableCell>
                    <TableCell>Name</TableCell>
                    <TableCell>Laden</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {receiptsSorted.map((r) => (
                    <TableRow key={r.id} hover>
                      <TableCell>{DateUtils.formatDateDE(r.datum)}</TableCell>
                      <TableCell>
                        {r.betrag != null ? Number(r.betrag).toFixed(2) : "-"}
                      </TableCell>
                      <TableCell>{r.name}</TableCell>
                      <TableCell>
                        {ladenById[r.laden_id] ?? r.laden_id}
                      </TableCell>
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
