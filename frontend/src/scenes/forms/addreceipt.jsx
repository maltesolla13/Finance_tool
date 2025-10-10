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

const filter = createFilterOptions();

function toISODate(d) {
  if (!d) return "";
  if (typeof d === "string") return d; // expect yyyy-mm-dd
  return new Date(d).toISOString().slice(0, 10);
}

export default function AddReceipt() {
  const theme = useTheme();
  const colors = tokens(theme.palette.mode);
  const api = useMemo(() => new ApiRequests(new ApiClient()), []);

  // ====== Form State ======
  const [userId, setUserId] = useState(null);
  const [kontoId, setKontoId] = useState(null);
  const [kategorieId, setKategorieId] = useState(null);
  const [ladenId, setLadenId] = useState(null);

  const [name, setName] = useState("");
  const [betrag, setBetrag] = useState("");
  const [datum, setDatum] = useState(toISODate(new Date()));

  // ====== Options (Autocomplete) ======
  const [optUsers, setOptUsers] = useState([]);
  const [optKonten, setOptKonten] = useState([]);
  const [optCats, setOptCats] = useState([]);
  const [optLaden, setOptLaden] = useState([]);

  const [inputUser, setInputUser] = useState("");
  const [inputKonto, setInputKonto] = useState("");
  const [inputCat, setInputCat] = useState("");
  const [inputLaden, setInputLaden] = useState("");
  const [loadingOpts, setLoadingOpts] = useState(false);

  // maps for Anzeige (id -> name)
  const [usersById, setUsersById] = useState({});
  const [kontenById, setKontenById] = useState({});
  const [catsById, setCatsById] = useState({});
  const [ladenById, setLadenById] = useState({});

  // debounce helper
  const debounce = (fn, ms = 250) => {
    let t;
    return (...args) => {
      clearTimeout(t);
      t = setTimeout(() => fn(...args), ms);
    };
  };

  const refreshOptions = useCallback(
    debounce(async (u, k, c, l) => {
      setLoadingOpts(true);
      try {
        const [users, konten, cats, shops] = await Promise.all([
          api.searchOptions("users", u || ""),
          api.searchOptions("konten", k || ""),
          api.searchOptions("kategorien", c || ""),
          api.searchOptions("laden", l || ""),
        ]);
        setOptUsers(users ?? []);
        setOptKonten(konten ?? []);
        setOptCats(cats ?? []);
        setOptLaden(shops ?? []);

        setUsersById(
          Object.fromEntries((users ?? []).map((o) => [o.id, o.name]))
        );
        setKontenById(
          Object.fromEntries((konten ?? []).map((o) => [o.id, o.name]))
        );
        setCatsById(
          Object.fromEntries((cats ?? []).map((o) => [o.id, o.name]))
        );
        setLadenById(
          Object.fromEntries((shops ?? []).map((o) => [o.id, o.name]))
        );
      } finally {
        setLoadingOpts(false);
      }
    }, 250),
    [api]
  );

  useEffect(() => {
    refreshOptions("", "", "", "");
  }, [refreshOptions]);

  useEffect(() => {
    refreshOptions(inputUser, inputKonto, inputCat, inputLaden);
  }, [inputUser, inputKonto, inputCat, inputLaden, refreshOptions]);

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
    try {
      if (
        !userId ||
        !kontoId ||
        !kategorieId ||
        !ladenId ||
        !name ||
        !betrag ||
        !datum
      ) {
        setErr("Bitte alle Felder ausfüllen.");
        return;
      }
      const payload = {
        user_id: userId,
        name: name.trim(),
        betrag: Number(betrag),
        kategorie_id: kategorieId,
        konto_id: kontoId,
        laden_id: ladenId,
        datum: toISODate(datum),
      };
      await api.createReceipt(payload);
      setOk("Einkauf angelegt.");
      setName("");
      setBetrag("");
      setKategorieId(null);
      setLadenId(null);
      setKontoId(null);
      // user bewusst nicht resetten
      loadReceipts();
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
          // Backend muss /options/ensure auch für 'laden' erlauben – Kategorien funktioniert bereits.
          const created = await api.ensureOption("kategorien", newVal.__create);
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

  const LadenAutocomplete = (
    <Autocomplete
      options={optLaden}
      value={optLaden.find((o) => o.id === ladenId) ?? null}
      inputValue={inputLaden}
      onInputChange={(_, v) => setInputLaden(v)}
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
        if (!newVal) return setLadenId(null);
        if (newVal.__create) {
          // HINWEIS: Dein Backend akzeptiert aktuell ensure NUR für 'kategorien'.
          // Erweitere es, damit auch 'laden' erlaubt ist – danach funktioniert das hier.
          const created = await api.ensureOption("laden", newVal.__create);
          setOptLaden((prev) => [created, ...prev]);
          setLadenById((prev) => ({ ...prev, [created.id]: created.name }));
          setLadenId(created.id);
        } else {
          setLadenId(newVal.id);
        }
      }}
      renderInput={(params) => <TextField {...params} label="Laden" required />}
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
                {UserAutocomplete}

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

                {KategorieAutocomplete}
                {KontoAutocomplete}
                {LadenAutocomplete}

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
                      <TableCell>{toISODate(r.datum)}</TableCell>
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
