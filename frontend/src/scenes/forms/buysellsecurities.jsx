import { useEffect, useMemo, useState, useCallback, useRef } from "react";
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
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  ToggleButtonGroup,
  ToggleButton,
} from "@mui/material";
import { ApiClient } from "../../data/ApiClient";
import { ApiRequests } from "../../data/ApiFrontend";
import Header from "../../components/Header";

// Services & Utils from ./Services
import { OptionsService } from "./Services/options.service";
import * as DateUtils from "./Services/date.utils";
import * as NumberUtils from "./Services/number.utils";
import * as Payloads from "./Services/payloads";
import { MarketService } from "./Services/market.service";
import {
  UserAutocomplete,
  KontoAutocomplete,
  SecurityAutocomplete,
  KategorieAutocomplete,
} from "./Services/autocomplete";

/* -------------------------------------------------------------------------- */
/*                              Helper / Validation                           */
/* -------------------------------------------------------------------------- */

function validateDepotbewegung({
  userId,
  kontoId,
  securityId,
  kategorieId,
  betrag,
  anteile,
  datum,
}) {
  if (!userId) return "Bitte User wählen.";
  if (!kontoId) return "Bitte Konto wählen.";
  if (!securityId) return "Bitte Wertpapier wählen.";
  if (!kategorieId) return "Bitte Kategorie wählen (oder neu anlegen).";
  if (!datum) return "Bitte Datum wählen.";
  const amount = NumberUtils.toNumber(betrag);
  const shares = NumberUtils.toNumber(anteile);
  if (amount == null && shares == null)
    return "Bitte Betrag ODER Anteile angeben.";
  return null;
}

/* -------------------------------------------------------------------------- */
/*                                  Component                                 */
/* -------------------------------------------------------------------------- */

const BuySellSecurities = () => {
  const api = useMemo(() => new ApiRequests(new ApiClient()), []);
  const market = useMemo(() => new MarketService(api), [api]);

  // Options & maps
  const [optUsers, setOptUsers] = useState([]);
  const [optKonten, setOptKonten] = useState([]);
  const [optSecs, setOptSecs] = useState([]);
  const [optCats, setOptCats] = useState([]);

  // maps (id -> name) für Tabellenanzeige
  const [kontenById, setKontenById] = useState({});
  const [secsById, setSecsById] = useState({});
  const [catsById, setCatsById] = useState({});

  const [loadingOpts, setLoadingOpts] = useState(false);

  // Autocomplete states
  const [userId, setUserId] = useState(null);
  const [kontoId, setKontoId] = useState(null);
  const [securityId, setSecurityId] = useState(null);
  const [kategorieId, setKategorieId] = useState(null);

  const [inputUser, setInputUser] = useState("");
  const [inputKonto, setInputKonto] = useState("");
  const [inputSec, setInputSec] = useState("");
  const [inputCat, setInputCat] = useState("");

  // Form states
  const [typ, setTyp] = useState("Kauf"); // "Kauf" | "Verkauf"
  const [betrag, setBetrag] = useState("");
  const [anteile, setAnteile] = useState("");
  const [datum, setDatum] = useState(DateUtils.toISODate(new Date()));

  const [submitting, setSubmitting] = useState(false);
  const [err, setErr] = useState("");
  const [okMsg, setOkMsg] = useState("");

  // Movements table
  const [rows, setRows] = useState([]);
  const [loadingRows, setLoadingRows] = useState(false);

  // Filter für Tabelle (default: aktueller Monat)
  const [from, to] = DateUtils.currentMonthRange(new Date());
  const [filterFrom, setFilterFrom] = useState(DateUtils.toISODate(from));
  const [filterTo, setFilterTo] = useState(DateUtils.toISODate(to));

  const optService = useMemo(
    () => new OptionsService(api, { debounceMs: 200 }),
    [api]
  );

  const refreshOptions = useCallback(
    async ({
      users = inputUser,
      konten = inputKonto,
      secs = inputSec,
      cats = inputCat,
    } = {}) => {
      try {
        setLoadingOpts(true);
        const { options, maps } = await optService.refresh(
          { users, konten, cats, laden: "" },
          true // securities mit laden
        );
        setOptUsers(options.users ?? []);
        setOptKonten(options.konten ?? []);
        setOptSecs(options.securities ?? []);
        setOptCats(options.cats ?? []);
        setKontenById(maps.kontenById ?? {});
        setSecsById(maps.securitiesById ?? {});
        setCatsById(maps.catsById ?? {});
      } catch (e) {
        console.warn(e);
      } finally {
        setLoadingOpts(false);
      }
    },
    [optService, inputUser, inputKonto, inputSec, inputCat]
  );

  // Preis und Anteil Berechnung
  const [lastEdited, setLastEdited] = useState(null); // "betrag" | "anteile"
  const [pricePerShare, setPricePerShare] = useState(null);
  const [priceSource, setPriceSource] = useState("auto"); // "auto" | "low" | "high"
  const reqIdRef = useRef(0); // Race-Condition Schutz

  // Hole den ausgewählten Security-Option-Eintrag (mit ticker)
  const selectedSec = useMemo(
    () => optSecs.find((o) => (o?.id ?? o?.value) === securityId) ?? null,
    [optSecs, securityId]
  );
  const ticker =
    selectedSec?.ticker || selectedSec?.symbol || selectedSec?.name;

  useEffect(() => {
    // initial load
    optService
      .loadAll({ includeSecurities: true })
      .then(({ options, maps }) => {
        setOptUsers(options.users ?? []);
        setOptKonten(options.konten ?? []);
        setOptSecs(options.securities ?? []);
        setOptCats(options.cats ?? []);
        setKontenById(maps.kontenById ?? {});
        setSecsById(maps.securitiesById ?? {});
        setCatsById(maps.catsById ?? {});
      });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // react auf Texteingaben in den Autocompletes (debounced)
  useEffect(() => {
    const id = setTimeout(() => {
      refreshOptions({
        users: inputUser,
        konten: inputKonto,
        secs: inputSec,
        cats: inputCat,
      });
    }, 250);
    return () => clearTimeout(id);
  }, [inputUser, inputKonto, inputSec, inputCat, refreshOptions]);

  const loadRows = useCallback(async () => {
    setLoadingRows(true);
    try {
      const params = {
        from: filterFrom,
        to: filterTo,
        user_id: userId ?? undefined,
        konto_id: kontoId ?? undefined,
        securities_id: securityId ?? undefined,
        kategorie_id: kategorieId ?? undefined,
      };
      const data = await api.listDepotbewegung(params);
      setRows(Array.isArray(data) ? data : (data?.rows ?? []));
    } catch (e) {
      console.warn(e);
    } finally {
      setLoadingRows(false);
    }
  }, [api, filterFrom, filterTo, userId, kontoId, securityId, kategorieId]);

  useEffect(() => {
    loadRows();
  }, [loadRows]);

  // Preis holen + fehlendes Feld berechnen (debounced)
  useEffect(() => {
    let active = true;
    const t = setTimeout(async () => {
      if (!ticker || !datum) return;
      try {
        const p = await market.price({
          ticker,
          date: datum,
          source: priceSource,
          side: typ,
        });
        if (!active || !Number.isFinite(Number(p))) return;
        setPricePerShare(p);

        // Nur berechnen, wenn genau EIN Feld gefüllt ist
        const hasBetrag = betrag !== "" && betrag != null;
        const hasAnteile = anteile !== "" && anteile != null;

        if (hasAnteile && !hasBetrag) {
          const total = Number(anteile) * Number(p);
          setBetrag(total.toFixed(2));
        } else if (hasBetrag && !hasAnteile && Number(p) > 0) {
          const qty = Number(betrag) / Number(p);
          setAnteile(qty.toFixed(6));
        } else if (!hasBetrag && !hasAnteile && lastEdited) {
          // Wenn Nutzer z.B. nur Quelle oder Datum ändert, NICHT überschreiben.
        }
      } catch (err) {
        console.warn("Preisabfrage fehlgeschlagen:", err);
      }
    }, 250);
    return () => {
      active = false;
      clearTimeout(t);
    };
  }, [ticker, datum, typ, priceSource, betrag, anteile, lastEdited, market]);

  const onSubmit = async (e) => {
    e?.preventDefault?.();
    setErr("");
    setOkMsg("");

    const validation = validateDepotbewegung({
      userId,
      kontoId,
      securityId,
      kategorieId,
      betrag,
      anteile,
      datum,
    });
    if (validation) {
      setErr(validation);
      return;
    }

    const payload = Payloads.toPayloadDepotbewegung({
      userId,
      kontoId,
      securityId,
      kategorieId,
      typ,
      betrag,
      anteile,
      datum,
    });

    try {
      setSubmitting(true);
      await api.createDepotBewegung(payload); // feste ApiFrontend-Methoden verwenden
      setOkMsg(`${typ} gespeichert.`);
      // Reset nur Beträge/Anteile für schnellen Folge-Eintrag
      setBetrag("");
      setAnteile("");
      await loadRows();
    } catch (e) {
      console.warn(e);
      setErr("Konnte Eintrag nicht speichern.");
    } finally {
      setSubmitting(false);
    }
  };

  const resetForm = () => {
    setTyp("Kauf");
    setBetrag("");
    setAnteile("");
    setDatum(DateUtils.toISODate(new Date()));
  };

  return (
    <Box m="20px">
      <Header
        title="Wertpapiere: Kauf / Verkauf"
        subtitle="Erfasse Käufe und Verkäufe; Einträge erscheinen unten in der Depotbewegung"
      />

      <Grid container spacing={2}>
        {/* Eingabeformular */}
        <Grid item xs={12} md={5}>
          <Paper sx={{ p: 2 }}>
            {submitting && <LinearProgress />}
            <Stack spacing={2} component="form" onSubmit={onSubmit}>
              {err && <Alert severity="error">{err}</Alert>}
              {okMsg && <Alert severity="success">{okMsg}</Alert>}

              <UserAutocomplete
                options={optUsers}
                valueId={userId}
                inputValue={inputUser}
                onInputChange={setInputUser}
                onSelectId={setUserId}
                loading={loadingOpts}
              />

              <KontoAutocomplete
                options={optKonten}
                valueId={kontoId}
                inputValue={inputKonto}
                onInputChange={setInputKonto}
                onSelectId={setKontoId}
                loading={loadingOpts}
              />

              <SecurityAutocomplete
                label="Wertpapier"
                options={optSecs}
                valueId={securityId}
                inputValue={inputSec}
                onInputChange={setInputSec}
                onSelectId={setSecurityId}
                loading={loadingOpts}
                required
              />

              <KategorieAutocomplete
                options={optCats}
                valueId={kategorieId}
                inputValue={inputCat}
                onInputChange={setInputCat}
                onSelectId={setKategorieId}
                onCreate={(name) => optService.ensureKategorie(name)}
                loading={loadingOpts}
                required
              />

              <Stack direction="row" spacing={2} alignItems="center">
                <Typography variant="body2" sx={{ minWidth: 80 }}>
                  Typ
                </Typography>
                <ToggleButtonGroup
                  size="small"
                  exclusive
                  value={typ}
                  onChange={(_, v) => v && setTyp(v)}
                >
                  <ToggleButton value="Kauf">Kauf</ToggleButton>
                  <ToggleButton value="Verkauf">Verkauf</ToggleButton>
                </ToggleButtonGroup>
              </Stack>

              <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
                <TextField
                  label="Betrag (€)"
                  value={betrag}
                  onChange={(e) => {
                    setLastEdited("betrag");
                    setBetrag(e.target.value);
                  }}
                  fullWidth
                  inputMode="decimal"
                  placeholder="z. B. 250"
                  helperText="Eins von beiden: Betrag ODER Anteile"
                />
                <TextField
                  label="Anteile (Stück)"
                  value={anteile}
                  onChange={(e) => {
                    setLastEdited("anteile");
                    setAnteile(e.target.value);
                  }}
                  fullWidth
                  inputMode="decimal"
                  placeholder="z. B. 1.5"
                />
              </Stack>

              <TextField
                label="Datum"
                type="date"
                value={datum}
                onChange={(e) => setDatum(e.target.value)}
                InputLabelProps={{ shrink: true }}
                fullWidth
              />

              <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
                <Button type="submit" variant="contained" disabled={submitting}>
                  {typ === "Kauf" ? "Kauf speichern" : "Verkauf speichern"}
                </Button>
                <Button
                  variant="text"
                  onClick={resetForm}
                  disabled={submitting}
                >
                  Zurücksetzen
                </Button>
              </Stack>
            </Stack>
          </Paper>
        </Grid>

        {/* Tabelle */}
        <Grid item xs={12} md={7}>
          <Paper sx={{ p: 2 }}>
            <Stack spacing={2}>
              <Typography variant="h6">Depotbewegung</Typography>
              <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
                <TextField
                  label="Von"
                  type="date"
                  value={filterFrom}
                  onChange={(e) => setFilterFrom(e.target.value)}
                  InputLabelProps={{ shrink: true }}
                />
                <TextField
                  label="Bis"
                  type="date"
                  value={filterTo}
                  onChange={(e) => setFilterTo(e.target.value)}
                  InputLabelProps={{ shrink: true }}
                />
                <Button
                  variant="outlined"
                  onClick={loadRows}
                  disabled={loadingRows}
                >
                  Aktualisieren
                </Button>
              </Stack>

              {loadingRows && <LinearProgress />}

              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Datum</TableCell>
                      <TableCell>Typ</TableCell>
                      <TableCell>Wertpapier</TableCell>
                      <TableCell>Kategorie</TableCell>
                      <TableCell>Konto</TableCell>
                      <TableCell align="right">Betrag (€)</TableCell>
                      <TableCell align="right">Anteile</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {rows?.length ? (
                      rows.map((r) => (
                        <TableRow key={r.id} hover>
                          <TableCell>
                            {DateUtils.formatDateDE(r.datum)}
                          </TableCell>
                          <TableCell>{r.type}</TableCell>
                          <TableCell>
                            {secsById[r.securities_id] ??
                              r.security_name ??
                              r.securities_id}
                          </TableCell>
                          <TableCell>
                            {catsById[r.kategorie_id] ??
                              r.kategorie_name ??
                              r.kategorie_id ??
                              ""}
                          </TableCell>
                          <TableCell>
                            {kontenById[r.konto_id] ??
                              r.konto_name ??
                              r.konto_id}
                          </TableCell>
                          <TableCell align="right">
                            {r.betrag != null
                              ? new Intl.NumberFormat("de-DE", {
                                  style: "currency",
                                  currency: "EUR",
                                }).format(Number(r.betrag))
                              : ""}
                          </TableCell>
                          <TableCell align="right">{r.anteile ?? ""}</TableCell>
                        </TableRow>
                      ))
                    ) : (
                      <TableRow>
                        <TableCell colSpan={7}>
                          <Typography variant="body2" color="text.secondary">
                            Keine Einträge gefunden.
                          </Typography>
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </TableContainer>
            </Stack>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default BuySellSecurities;
