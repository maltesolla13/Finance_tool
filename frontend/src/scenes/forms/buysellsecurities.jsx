import AccountUserField from "./Services/AccountUserField";
import { useEffect, useMemo, useState, useCallback } from "react";
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
  TableSortLabel,
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
  DualKontoAutocomplete,
  SecurityAutocomplete,
  KategorieAutocomplete,
} from "./Services/autocomplete";

/* -------------------------------------------------------------------------- */
/*                              Helper / Validation                           */
/* -------------------------------------------------------------------------- */

function validateDepotbewegung({
  userId,
  kontoOutId,
  kontoInId,
  securityId,
  kategorieId,
  betrag,
  anteile,
  datum,
}) {
  if (!userId) return "Bitte User wählen.";
  if (!kontoOutId || !kontoInId)
    return "Bitte Ausgangs- und Eingangskonto wählen.";
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
  const [kontoOutId, setKontoOutId] = useState(null);
  const [kontoInId, setKontoInId] = useState(null);
  const [securityId, setSecurityId] = useState(null);
  const [kategorieId, setKategorieId] = useState(null);

  const inputUser = "";
  const [inputKontoOut, setInputKontoOut] = useState("");
  const [inputKontoIn, setInputKontoIn] = useState("");
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
  const [columnFilters, setColumnFilters] = useState({});
  const [dateOrder, setDateOrder] = useState("desc");

  const columns = useMemo(
    () => [
      {
        key: "datum",
        label: "Datum",
        value: (r) => DateUtils.formatDateDE(r.datum),
      },
      { key: "type", label: "Typ", value: (r) => r.type ?? "" },
      {
        key: "security",
        label: "Wertpapier",
        value: (r) =>
          secsById[r.securities_id] ?? r.security_name ?? r.securities_id ?? "",
      },
      {
        key: "category",
        label: "Kategorie",
        value: (r) =>
          catsById[r.kategorie_id] ?? r.kategorie_name ?? r.kategorie_id ?? "",
      },
      {
        key: "out",
        label: "Ausgangskonto",
        value: (r) =>
          kontenById[r.ausgangs_konto_id] ??
          r.ausgangs_konto_name ??
          r.ausgangs_konto_id ??
          "",
      },
      {
        key: "in",
        label: "Eingangskonto",
        value: (r) =>
          kontenById[r.eingangs_konto_id] ??
          r.eingangs_konto_name ??
          r.eingangs_konto_id ??
          "",
      },
      {
        key: "betrag",
        label: "Betrag (\u20ac)",
        align: "right",
        value: (r) =>
          r.betrag != null
            ? new Intl.NumberFormat("de-DE", {
                style: "currency",
                currency: "EUR",
              }).format(Number(r.betrag))
            : "",
      },
      {
        key: "anteile",
        label: "Anteile",
        align: "right",
        value: (r) => r.anteile ?? "",
      },
    ],
    [secsById, catsById, kontenById],
  );

  const visibleRows = useMemo(() => {
    const normalize = (value) =>
      String(value ?? "")
        .trim()
        .toLocaleLowerCase("de-DE");
    return rows
      .filter((row) =>
        columns.every((column) => {
          const query = normalize(columnFilters[column.key]);
          const values = [column.value(row)];
          if (column.key === "datum") values.push(row.datum);
          if (column.key === "betrag" || column.key === "anteile") {
            values.push(
              row[column.key],
              String(row[column.key] ?? "").replace(".", ","),
            );
          }
          return (
            !query || values.some((value) => normalize(value).includes(query))
          );
        }),
      )
      .sort((a, b) => {
        const aTime = Date.parse(a.datum);
        const bTime = Date.parse(b.datum);
        if (!Number.isFinite(aTime)) return Number.isFinite(bTime) ? 1 : 0;
        if (!Number.isFinite(bTime)) return -1;
        return dateOrder === "desc" ? bTime - aTime : aTime - bTime;
      });
  }, [rows, columns, columnFilters, dateOrder]);

  // Filter für Tabelle (default: aktueller Monat)
  const [from, to] = DateUtils.currentMonthRange(new Date());
  const [filterFrom, setFilterFrom] = useState(DateUtils.toISODate(from));
  const [filterTo, setFilterTo] = useState(DateUtils.toISODate(to));

  const optService = useMemo(
    () => new OptionsService(api, { debounceMs: 200 }),
    [api],
  );

  const refreshOptions = useCallback(
    async ({
      users = inputUser,
      konten = "",
      secs = inputSec,
      cats = inputCat,
    } = {}) => {
      try {
        setLoadingOpts(true);
        const { options, maps } = await optService.refresh(
          { users, konten, cats, laden: "" },
          true, // securities mit laden
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
    [optService, inputUser, inputSec, inputCat],
  );

  const depotKontoId = useMemo(() => {
    if (typ === "Verkauf") return kontoOutId;
    return kontoInId;
  }, [typ, kontoOutId, kontoInId]);

  // Preis und Anteil Berechnung
  const [lastEdited, setLastEdited] = useState(null); // "betrag" | "anteile"
  const priceSource = "auto"; // "auto" | "low" | "high"

  // Hole den ausgewählten Security-Option-Eintrag (mit ticker)
  const selectedSec = useMemo(
    () => optSecs.find((o) => (o?.id ?? o?.value) === securityId) ?? null,
    [optSecs, securityId],
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
        konten: "",
        secs: inputSec,
        cats: inputCat,
      });
    }, 250);
    return () => clearTimeout(id);
  }, [inputUser, inputSec, inputCat, refreshOptions]);

  const loadRows = useCallback(async () => {
    setLoadingRows(true);
    try {
      const params = {
        from: filterFrom,
        to: filterTo,
        user_id: userId ?? undefined,
        konto_id: depotKontoId ?? undefined,
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
  }, [
    api,
    filterFrom,
    filterTo,
    userId,
    depotKontoId,
    securityId,
    kategorieId,
  ]);

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
      kontoOutId,
      kontoInId,
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
      kontoId: depotKontoId,
      kontoOutId,
      kontoInId,
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
      setOkMsg(
        `${typ} gespeichert. Die Depotbewertung wird im Hintergrund aktualisiert.`,
      );
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

      <Grid container spacing={3} alignItems="flex-start">
        {/* Eingabeformular */}
        <Grid size={{ xs: 12, lg: 5 }} sx={{ minWidth: 0 }}>
          <Paper
            sx={{
              p: 3,
              borderRadius: 3,
              border: "1px solid",
              borderColor: "divider",
            }}
          >
            {submitting && <LinearProgress />}
            <Stack spacing={2} component="form" onSubmit={onSubmit}>
              {err && <Alert severity="error">{err}</Alert>}
              {okMsg && <Alert severity="success">{okMsg}</Alert>}

              <DualKontoAutocomplete
                options={optKonten}
                outId={kontoOutId}
                inId={kontoInId}
                outInput={inputKontoOut}
                inInput={inputKontoIn}
                onOutInput={setInputKontoOut}
                onInInput={setInputKontoIn}
                onOutSelect={setKontoOutId}
                onInSelect={setKontoInId}
                loading={loadingOpts}
                errorOut={!kontoOutId}
                errorIn={!kontoInId}
              />
              <AccountUserField
                accounts={optKonten}
                users={optUsers}
                accountIds={[kontoOutId, kontoInId]}
                valueId={userId}
                onSelectId={setUserId}
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
        <Grid size={{ xs: 12, lg: 7 }} sx={{ minWidth: 0 }}>
          <Paper
            sx={{
              p: 3,
              borderRadius: 3,
              border: "1px solid",
              borderColor: "divider",
            }}
          >
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
                      {columns.map((column) => (
                        <TableCell
                          key={column.key}
                          align={column.align}
                          sortDirection={
                            column.key === "datum" ? dateOrder : false
                          }
                        >
                          {column.key === "datum" ? (
                            <TableSortLabel
                              active
                              direction={dateOrder}
                              onClick={() =>
                                setDateOrder((order) =>
                                  order === "desc" ? "asc" : "desc",
                                )
                              }
                            >
                              {column.label}
                            </TableSortLabel>
                          ) : (
                            column.label
                          )}
                        </TableCell>
                      ))}
                    </TableRow>
                    <TableRow>
                      {columns.map((column) => (
                        <TableCell key={column.key}>
                          <TextField
                            size="small"
                            placeholder="Filtern..."
                            value={columnFilters[column.key] ?? ""}
                            onChange={(event) =>
                              setColumnFilters((filters) => ({
                                ...filters,
                                [column.key]: event.target.value,
                              }))
                            }
                            inputProps={{
                              "aria-label": column.label + " filtern",
                            }}
                            sx={{ minWidth: 110 }}
                            fullWidth
                          />
                        </TableCell>
                      ))}
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {visibleRows.length ? (
                      visibleRows.map((r) => (
                        <TableRow key={r.id} hover>
                          {columns.map((column) => (
                            <TableCell key={column.key} align={column.align}>
                              {column.value(r)}
                            </TableCell>
                          ))}
                        </TableRow>
                      ))
                    ) : (
                      <TableRow>
                        <TableCell colSpan={8}>
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
