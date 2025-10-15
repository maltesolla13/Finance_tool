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
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Checkbox,
  FormControlLabel,
  Popover,
  List,
  ListItem,
  ListItemText,
} from "@mui/material";
import Autocomplete, { createFilterOptions } from "@mui/material/Autocomplete";
import FullCalendar from "@fullcalendar/react";
import dayGridPlugin from "@fullcalendar/daygrid";
import interactionPlugin from "@fullcalendar/interaction";
import { ApiClient } from "../../data/ApiClient";
import { ApiRequests } from "../../data/ApiFrontend";
import { tokens } from "../../theme";
import Header from "../../components/Header";
import { buildMonthlyCostEvents } from "./Services/calendar.utils";
import { OptionsService } from "./Services/options.service";
import * as Validators from "./Services/validators";
import * as Payloads from "./Services/payloads";
import * as DateUtils from "./Services/date.utils";
import {
  UserAutocomplete,
  DualKontoAutocomplete,
  KategorieAutocomplete,
  SecurityAutocomplete,
} from "./Services/autocomplete";

export default function AddMonthlyCosts() {
  const theme = useTheme();
  const colors = tokens(theme.palette.mode);

  // === API + Service ===
  const api = useMemo(() => new ApiRequests(new ApiClient()), []);
  const optionsSvc = useMemo(() => new OptionsService(api), [api]);

  // === Form State ===
  const [name, setName] = useState("");
  const [userId, setUserId] = useState(null);
  const [kategorieId, setKategorieId] = useState(null);
  const [betrag, setBetrag] = useState("");
  const [active, setActive] = useState(true);
  const [startDatum, setStartDatum] = useState(
    new Date().toISOString().slice(0, 10)
  );
  const [nextDue, setNextDue] = useState(""); // optional; fällt sonst auf startDatum zurück

  // zwei Konto-Felder (Ausgang + Eingang)
  const [kontoOutId, setKontoOutId] = useState(null);
  const [kontoInId, setKontoInId] = useState(null);
  const [inputKontoOut, setInputKontoOut] = useState("");
  const [inputKontoIn, setInputKontoIn] = useState("");

  // Wertpapier/Anteil (optional)
  const [securityId, setSecurityId] = useState(null);
  const [anteil, setAnteil] = useState("");

  // === Options (Autocomplete) ===
  const [optUsers, setOptUsers] = useState([]);
  const [optKonten, setOptKonten] = useState([]);
  const [optCats, setOptCats] = useState([]);
  const [optSecurities, setOptSecurities] = useState([]);
  const [inputUser, setInputUser] = useState("");
  const [inputCat, setInputCat] = useState("");
  const [loadingOpts, setLoadingOpts] = useState(false);

  // maps (id -> name) für Popover/Edit
  const [usersById, setUsersById] = useState({});
  const [kontenById, setKontenById] = useState({});
  const [catsById, setCatsById] = useState({});
  const [securitiesById, setSecuritiesById] = useState({});

  // === Optionen initial laden ===
  const loadAllOptions = useCallback(async () => {
    setLoadingOpts(true);
    try {
      const { options, maps } = await optionsSvc.loadAll({
        includeSecurities: true,
      });
      setOptUsers(options.users);
      setOptKonten(options.konten);
      setOptCats(options.cats);
      setOptSecurities(options.securities);
      setUsersById(maps.usersById);
      setKontenById(maps.kontenById);
      setCatsById(maps.catsById);
      setSecuritiesById(maps.securitiesById);
    } finally {
      setLoadingOpts(false);
    }
  }, [optionsSvc]);

  useEffect(() => {
    loadAllOptions();
  }, [loadAllOptions]);

  // Live-Suche (debounced) nach Nutzereingaben
  useEffect(() => {
    let alive = true;
    const t = setTimeout(async () => {
      try {
        const { options, maps } = await optionsSvc.refreshOptions(
          {
            users: inputUser,
            konten: inputKontoOut || inputKontoIn,
            cats: inputCat,
          },
          true
        );
        if (!alive) return;
        setOptUsers(options.users);
        setOptKonten(options.konten);
        setOptCats(options.cats);
        setOptSecurities(options.securities);
        setUsersById(maps.usersById);
        setKontenById(maps.kontenById);
        setCatsById(maps.catsById);
        setSecuritiesById(maps.securitiesById);
      } catch {
        /* ignore */
      }
    }, 250);
    return () => {
      alive = false;
      clearTimeout(t);
    };
  }, [inputUser, inputKontoOut, inputKontoIn, inputCat, optionsSvc]);

  // next_due automatisch vorbefüllen, solange der Nutzer nichts gesetzt hat
  useEffect(() => {
    if (!nextDue) setNextDue(startDatum);
  }, [startDatum]);

  // === MonthlyCosts Liste + Kalender ===
  const [monthlyCosts, setMonthlyCosts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");
  const [ok, setOk] = useState("");

  const loadMonthlyCosts = useCallback(async () => {
    setLoading(true);
    setErr("");
    try {
      const rows = await api.listMonthlyCosts();
      setMonthlyCosts(Array.isArray(rows) ? rows : []);
    } catch (e) {
      setErr("Konnte MonthlyCosts nicht laden.");
      console.warn(e);
    } finally {
      setLoading(false);
    }
  }, [api]);

  useEffect(() => {
    loadMonthlyCosts();
  }, [loadMonthlyCosts]);

  const [monthStart, monthEnd] = useMemo(
    () => DateUtils.currentMonthRange(new Date()),
    []
  );
  const events = useReactMemo(
    () => buildMonthlyCostEvents(monthlyCosts, monthStart, monthEnd),
    [monthlyCosts, monthStart, monthEnd]
  );

  // === Hover-Popover ===
  const [hoverAnchor, setHoverAnchor] = useState(null);
  const [hoverDate, setHoverDate] = useState(null);
  const [hoverItems, setHoverItems] = useState([]);
  const openHover = Boolean(hoverAnchor);

  const handleEventMouseEnter = (info) => {
    const eventDate = new Date(info.event.startStr);
    const sameDay = (d1, d2) =>
      d1.getFullYear() === d2.getFullYear() &&
      d1.getMonth() === d2.getMonth() &&
      d1.getDate() === d2.getDate();
    const items = events.filter((e) => sameDay(new Date(e.start), eventDate));
    setHoverItems(items);
    setHoverDate(eventDate);
    setHoverAnchor(info.el);
  };
  const handleEventMouseLeave = () => {
    setHoverAnchor(null);
    setHoverItems([]);
    setHoverDate(null);
  };

  // === Klick -> Edit ===
  const [editOpen, setEditOpen] = useState(false);
  const [editItem, setEditItem] = useState(null);

  const openEditForEvent = (clickInfo) => {
    const id = Number(clickInfo.event.id);
    const s = monthlyCosts.find((x) => x.id === id);
    if (!s) return;
    setEditItem({
      ...s,
      start_datum_ui: s.start_datum?.slice(0, 10),
      next_due_ui: s.next_due?.slice(0, 10),
    });
    setEditOpen(true);
  };
  const closeEdit = () => {
    setEditOpen(false);
    setEditItem(null);
  };

  const saveEdit = async () => {
    try {
      const payload = {
        user_id: editItem.user_id,
        name: editItem.name,
        kategorie_id: editItem.kategorie_id,
        start_datum: DateUtils.isoDateTime(editItem.start_datum_ui),
        next_due: DateUtils.isoDateTime(
          editItem.next_due_ui || editItem.start_datum_ui
        ),
        active: !!editItem.active,
        ausgangs_konto_id: editItem.ausgangs_konto_id ?? null,
        eingangs_konto_id: editItem.eingangs_konto_id ?? null,
        securities_id: editItem.securities_id ?? null,
        anteil: editItem.anteil ?? null,
        betrag: editItem.betrag ?? null,
      };
      await api.updateMonthlyCosts(editItem.id, payload);
      setOk("Eintrag aktualisiert.");
      closeEdit();
      loadMonthlyCosts();
    } catch (e) {
      console.error(e);
      setErr("Aktualisieren fehlgeschlagen");
    }
  };

  // === Anlegen ===
  const onCreate = async (e) => {
    e.preventDefault();
    setErr("");
    setOk("");

    const errMsg = Validators.validateMonthlyCost({
      userId,
      name,
      betrag,
      kategorieId,
      startDatum,
      kontoOutId,
      kontoInId,
    });
    if (errMsg) {
      setErr(errMsg);
      return;
    }

    try {
      const payload = Payloads.toPayloadMonthlyCost({
        userId,
        name,
        kategorieId,
        startDatum,
        nextDue,
        active,
        kontoOutId,
        kontoInId,
        betrag,
        securityId,
        anteil,
      });
      console.log("POST /monthlycosts payload", payload);
      await api.createMonthlyCosts(payload);
      setOk("Fixkosten angelegt");
      setName("");
      setBetrag("");
      setKategorieId(null);
      setKontoOutId(null);
      setKontoInId(null);
      setNextDue("");
      loadMonthlyCosts();
    } catch (e2) {
      console.error(e2);
      setErr("Anlegen fehlgeschlagen");
    }
  };

  // === Custom Event Content: Name + farbiger Punkt (aktiv/inaktiv) ===
  const renderEventContent = (arg) => {
    const activeFlag = !!arg.event.extendedProps.active;
    return (
      <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
        <span
          aria-label={activeFlag ? "aktiv" : "inaktiv"}
          title={activeFlag ? "aktiv" : "inaktiv"}
          style={{
            width: 8,
            height: 8,
            borderRadius: 999,
            background: activeFlag ? "#26a69a" : "#9e9e9e",
            display: "inline-block",
          }}
        />
        <span style={{ overflow: "hidden", textOverflow: "ellipsis" }}>
          {arg.event.title}
        </span>
      </div>
    );
  };

  return (
    <Box m="20px">
      <Box display="flex" justifyContent="space-between" alignItems="center">
        <Header title="New Monthly Cost" subtitle="Add a new Monthly Cost" />
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

      <Grid container spacing={3}>
        {/* Linke Spalte: Formular */}
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
              Fixkosten hinzufügen
            </Typography>

            <Box component="form" onSubmit={onCreate}>
              <Stack spacing={2}>
                <TextField
                  label="Bezeichnung"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  required
                />

                <UserAutocomplete
                  options={optUsers}
                  valueId={userId}
                  inputValue={inputUser}
                  onInputChange={setInputUser}
                  onSelectId={setUserId}
                />

                <DualKontoAutocomplete
                  options={optKonten}
                  // Werte
                  outId={kontoOutId}
                  inId={kontoInId}
                  // Input-Text
                  outInput={inputKontoOut}
                  inInput={inputKontoIn}
                  // Handler
                  onOutInput={setInputKontoOut}
                  onInInput={setInputKontoIn}
                  onOutSelect={setKontoOutId}
                  onInSelect={setKontoInId}
                  // (optional) Validierung wie bei dir: mind. eines muss gesetzt sein
                  errorOut={!kontoOutId && !kontoInId}
                  errorIn={!kontoOutId && !kontoInId}
                  helperTextOut="Mindestens eines der beiden Konto-Felder muss befüllt sein"
                  helperTextIn="Mindestens eines der beiden Konto-Felder muss befüllt sein"
                  // (optional)
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
                  helperText={
                    securityId
                      ? "Bei Wertpapier: Betrag ODER Anteil angeben."
                      : "Ohne Wertpapier ist Betrag erforderlich."
                  }
                />

                <SecurityAutocomplete
                  options={optSecurities}
                  valueId={securityId}
                  onSelectId={setSecurityId}
                />

                <TextField
                  label="Anteil (optional)"
                  type="number"
                  inputProps={{ step: "0.0001" }}
                  value={anteil}
                  onChange={(e) => setAnteil(e.target.value)}
                />

                <Stack direction="row" spacing={2}>
                  <TextField
                    label="Start"
                    type="date"
                    value={startDatum}
                    onChange={(e) => setStartDatum(e.target.value)}
                    InputLabelProps={{ shrink: true }}
                    required
                    sx={{ flex: 1 }}
                  />
                  <TextField
                    label="Nächste Ausführung (optional)"
                    type="date"
                    value={nextDue}
                    onChange={(e) => setNextDue(e.target.value)}
                    InputLabelProps={{ shrink: true }}
                    sx={{ flex: 1 }}
                  />
                </Stack>

                <FormControlLabel
                  control={
                    <Checkbox
                      checked={active}
                      onChange={(e) => setActive(e.target.checked)}
                    />
                  }
                  label="Aktiv"
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

        {/* Rechte Spalte: Kalender */}
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
              Fälligkeiten im aktuellen Monat
            </Typography>

            <FullCalendar
              plugins={[dayGridPlugin, interactionPlugin]}
              initialView="dayGridMonth"
              height="auto"
              events={events}
              eventContent={renderEventContent}
              eventMouseEnter={handleEventMouseEnter}
              eventMouseLeave={handleEventMouseLeave}
              eventClick={openEditForEvent}
              dayMaxEventRows={3}
              headerToolbar={{ left: "title", center: "", right: "" }}
            />

            <Popover
              open={openHover}
              anchorEl={hoverAnchor}
              onClose={() => setHoverAnchor(null)}
              anchorOrigin={{ vertical: "bottom", horizontal: "left" }}
            >
              <Box sx={{ p: 2, maxWidth: 380 }}>
                <Typography variant="h6" sx={{ mb: 1 }}>
                  {hoverDate ? hoverDate.toLocaleDateString() : "Details"}
                </Typography>
                <List dense>
                  {hoverItems.map((e) => {
                    const xp = e.extendedProps || {};
                    return (
                      <ListItem key={e.id} sx={{ py: 0.75 }}>
                        <ListItemText
                          primary={e.title}
                          secondary={[
                            xp.betrag != null
                              ? `Betrag: ${Number(xp.betrag).toFixed(2)}€`
                              : null,
                            xp.kategorie_id
                              ? `Kategorie: ${catsById[xp.kategorie_id] ?? xp.kategorie_id}`
                              : null,
                            xp.ausgangs_konto_id
                              ? `Ausgang: ${kontenById[xp.ausgangs_konto_id] ?? xp.ausgangs_konto_id}`
                              : null,
                            xp.eingangs_konto_id
                              ? `Eingang: ${kontenById[xp.eingangs_konto_id] ?? xp.eingangs_konto_id}`
                              : null,
                            xp.securities_id
                              ? `Wertpapier: ${securitiesById[xp.securities_id] ?? xp.securities_id}`
                              : null,
                            xp.anteil != null
                              ? `Anteil: ${Number(xp.anteil)}`
                              : null,
                            xp.user_id
                              ? `User: ${usersById[xp.user_id] ?? xp.user_id}`
                              : null,
                            xp.start_datum
                              ? `Start: ${new Date(xp.start_datum).toLocaleDateString("de-DE")}`
                              : null,
                            xp.next_due
                              ? `Nächste: ${new Date(xp.next_due).toLocaleDateString("de-DE")}`
                              : null,
                            xp.active ? "Aktiv" : "Inaktiv",
                          ]
                            .filter(Boolean)
                            .join(" · ")}
                        />
                      </ListItem>
                    );
                  })}
                </List>
              </Box>
            </Popover>
          </Paper>
        </Grid>
      </Grid>

      {/* Edit-Dialog */}
      <Dialog open={editOpen} onClose={closeEdit} fullWidth maxWidth="sm">
        <DialogTitle>Eintrag bearbeiten</DialogTitle>
        <DialogContent>
          {editItem && (
            <Stack spacing={2} sx={{ mt: 1 }}>
              <TextField
                label="Bezeichnung"
                value={editItem.name}
                onChange={(e) =>
                  setEditItem((p) => ({ ...p, name: e.target.value }))
                }
              />
              <TextField
                label="Betrag (€)"
                type="number"
                inputProps={{ step: "0.01" }}
                value={editItem.betrag ?? ""}
                onChange={(e) =>
                  setEditItem((p) => ({
                    ...p,
                    betrag:
                      e.target.value === "" ? null : Number(e.target.value),
                  }))
                }
              />
              <TextField
                label="Anteil"
                type="number"
                inputProps={{ step: "0.0001" }}
                value={editItem.anteil ?? ""}
                onChange={(e) =>
                  setEditItem((p) => ({
                    ...p,
                    anteil:
                      e.target.value === "" ? null : Number(e.target.value),
                  }))
                }
              />

              <Autocomplete
                options={optSecurities}
                value={
                  optSecurities.find((o) => o.id === editItem.securities_id) ??
                  null
                }
                getOptionLabel={(o) => o?.name ?? ""}
                onChange={(_, v) =>
                  setEditItem((p) => ({ ...p, securities_id: v?.id ?? null }))
                }
                filterOptions={(x) => x}
                renderInput={(p) => (
                  <TextField {...p} label="Wertpapier (optional)" />
                )}
              />

              <TextField
                label="Start"
                type="date"
                value={editItem.start_datum_ui}
                onChange={(e) =>
                  setEditItem((p) => ({ ...p, start_datum_ui: e.target.value }))
                }
                InputLabelProps={{ shrink: true }}
              />
              <TextField
                label="Nächste Fälligkeit"
                type="date"
                value={editItem.next_due_ui}
                onChange={(e) =>
                  setEditItem((p) => ({ ...p, next_due_ui: e.target.value }))
                }
                InputLabelProps={{ shrink: true }}
              />
              <FormControlLabel
                control={
                  <Checkbox
                    checked={!!editItem.active}
                    onChange={(e) =>
                      setEditItem((p) => ({ ...p, active: e.target.checked }))
                    }
                  />
                }
                label="Aktiv"
              />
            </Stack>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={closeEdit}>Abbrechen</Button>
          <Button onClick={saveEdit} variant="contained">
            Speichern
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
