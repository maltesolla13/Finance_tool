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
import { ApiError } from "../../data/ApiErrors";
import { tokens } from "../../theme";
import Header from "../../components/Header";

const filter = createFilterOptions();

function iso(d) {
  return typeof d === "string" ? d : new Date(d).toISOString();
}

const AddMonthlyCosts = () => {
  const theme = useTheme();
  const colors = tokens(theme.palette.mode);
  const api = useMemo(() => new ApiRequests(new ApiClient()), []);

  // ====== Form State (MonthlyCosts erstellen) ======
  const [name, setName] = useState("");
  const [userId, setUserId] = useState(null);
  const [kontoId, setKontoId] = useState(null);
  const [kategorieId, setKategorieId] = useState(null);
  const [betrag, setBetrag] = useState("");
  const [active, setActive] = useState(true);
  const [startDatum, setStartDatum] = useState(
    new Date().toISOString().slice(0, 10)
  );
  const [nextDue, setNextDue] = useState(new Date().toISOString().slice(0, 10));

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

  // debounce helper
  const debounce = (fn, ms = 250) => {
    let t;
    return (...args) => {
      clearTimeout(t);
      t = setTimeout(() => fn(...args), ms);
    };
  };

  const refreshOptions = useCallback(
    debounce(async (u, k, c) => {
      setLoadingOpts(true);
      try {
        const [users, konten, cats] = await Promise.all([
          api.searchOptions("users", u || ""),
          api.searchOptions("konten", k || ""),
          api.searchOptions("kategorien", c || ""),
        ]);
        setOptUsers(users ?? []);
        setOptKonten(konten ?? []);
        setOptCats(cats ?? []);
        setUsersById(
          Object.fromEntries((users ?? []).map((o) => [o.id, o.name]))
        );
        setKontenById(
          Object.fromEntries((konten ?? []).map((o) => [o.id, o.name]))
        );
        setCatsById(
          Object.fromEntries((cats ?? []).map((o) => [o.id, o.name]))
        );
      } finally {
        setLoadingOpts(false);
      }
    }, 250),
    [api]
  );

  useEffect(() => {
    refreshOptions("", "", "");
  }, [refreshOptions]);

  useEffect(() => {
    refreshOptions(inputUser, inputKonto, inputCat);
  }, [inputUser, inputKonto, inputCat, refreshOptions]);

  // ====== MonthlyCosts Liste + Kalender Events ======
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

  // Kalender: Events nur für aktuellen Monat, basierend auf next_due
  const [monthStart, monthEnd] = (() => {
    const now = new Date();
    const start = new Date(now.getFullYear(), now.getMonth(), 1);
    const end = new Date(now.getFullYear(), now.getMonth() + 1, 0, 23, 59, 59);
    return [start, end];
  })();

  const events = useMemo(() => {
    return (monthlyCosts ?? [])
      .filter((s) => {
        const d = new Date(s.next_due);
        return d >= monthStart && d <= monthEnd;
      })
      .map((s) => ({
        id: String(s.id),
        title: s.name,
        start: s.next_due, // ISO from backend, siehe load_monthlycosts/select next_due :contentReference[oaicite:2]{index=2}
        extendedProps: {
          betrag: s.betrag,
          konto_id: s.ausgangs_konto_id,
          active: s.active,
          kategorie_id: s.kategorie_id,
        },
        backgroundColor: s.active ? "#26a69a" : "#9e9e9e", // grün vs grau
        borderColor: s.active ? "#26a69a" : "#9e9e9e",
        textColor: "#fff", //colors.grey[100],
      }));
  }, [monthlyCosts, monthStart, monthEnd]);

  // ====== Hover: alle Transaktionen des Tages in einem Popover ======
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

  // ====== Klick: Edit-Dialog ======
  const [editOpen, setEditOpen] = useState(false);
  const [editItem, setEditItem] = useState(null);

  const openEditForEvent = (clickInfo) => {
    const id = Number(clickInfo.event.id);
    const s = monthlyCosts.find((x) => x.id === id);
    if (!s) return;
    setEditItem({
      ...s,
      // normalize date inputs to 'yyyy-mm-dd' for date fields
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
        start_datum: iso(editItem.start_datum_ui),
        next_due: iso(editItem.next_due_ui),
        active: !!editItem.active,
        ausgangs_konto_id: editItem.ausgangs_konto_id ?? null,
        eingangs_konto_id: editItem.eingangs_konto_id ?? null,
        aktien_id: editItem.aktien_id ?? null,
        anteil: editItem.anteil ?? null,
        betrag: editItem.betrag ?? null,
      };
      await api.updateMonthlyCosts(editItem.id, payload);
      setOk("Einrag aktualisiert.");
      closeEdit();
      loadMonthlyCosts();
    } catch (e) {
      console.error(e);
      setErr("Aktualisieren Fehlgeschlagen");
    }
  };

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
        !name ||
        !nextDue ||
        !startDatum
      ) {
        setErr(
          "Bitte alle Pflichtfelder ausfüllen. Pflichtfelder sind: User, Konto, Kategorie, Name, Startdatum und nächste Ausführung"
        );
        return;
      }
      const payload = {
        user_id: userId,
        name,
        kategorie_id: kategorieId,
        start_datum: iso(startDatum),
        next_due: iso(nextDue),
        active: !!active,
        ausgangs_konto_id: kontoId,
        betrag: betrag ? Number(betrag) : null,
        eingangs_konto_id: null,
        aktien_id: null,
        anteil: null,
      };
      await api.createMonthlyCosts(payload);
      setOk("Fixkosten angelegt");
      setName("");
      setBetrag("");
      setKategorieId(null);
      loadMonthlyCosts();
    } catch (e2) {
      console.error(e2);
      setErr("Anlegen fehlgeschlagen");
    }
  };

  // ====== Kategorie-Autocomplete mit „Neu erstellen“ ======
  const renderKategorie = (
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
        if (!newVal) {
          setKategorieId(null);
          return;
        }
        if (newVal.__create) {
          //Nur Kategorien "ensure"-n (User/Konto Nicht hier erstellen)
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

  // ====== User/Konto Autocomplete (ohne Neu-Erstellen) ======
  const renderUser = (
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

  const renderKonto = (
    <Autocomplete
      options={optKonten}
      value={optKonten.find((o) => o.id === kontoId) ?? null}
      inputValue={inputKonto}
      onInputChange={(_, v) => setInputKonto(v)}
      getOptionLabel={(o) => o?.name ?? ""}
      onChange={(_, v) => setKontoId(v?.id ?? null)}
      filterOptions={(x) => x}
      renderInput={(p) => <TextField {...p} label="Ausgangs-Konto" required />}
    />
  );

  return (
    <Box m="20px">
      <Box display="flex" justifyContent="space-between" alignItems="center">
        <Header title="New Monthly Cost" subtitle="Add a newe Monthly Cost" />
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
                {renderUser}
                {renderKonto}
                {renderKategorie}

                <TextField
                  label="Betrag"
                  type="number"
                  inputProps={{ step: "0.01" }}
                  value={betrag}
                  onChange={(e) => setBetrag(e.target.value)}
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
                    label="Nächste Ausführung"
                    type="date"
                    value={nextDue}
                    onChange={(e) => setNextDue(e.target.value)}
                    InputLabelProps={{ shrink: true }}
                    required
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

        {/* RECHTE SEITE KALEDNER */}

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
              eventMouseEnter={handleEventMouseEnter}
              eventMouseLeave={handleEventMouseLeave}
              eventClick={openEditForEvent}
              dayMaxEventRows={3}
              headerToolbar={{
                left: "title",
                center: "",
                right: "",
              }}
            />

            {/* Hover-Popover: alle Transaktionen an dem Tag */}
            <Popover
              open={openHover}
              anchorEl={hoverAnchor}
              onClose={() => setHoverAnchor(null)}
              anchorOrigin={{ vertical: "bottom", horizontal: "left" }}
            >
              <Box sx={{ p: 2, maxWidth: 360 }}>
                <Typography variant="h6" sx={{ mb: 1 }}>
                  {hoverDate ? hoverDate.toLocaleDateString() : "Transaktionen"}
                </Typography>
                <List dense>
                  {hoverItems.map((e) => (
                    <ListItem key={e.id} sx={{ py: 0.5 }}>
                      <ListItemText
                        primary={e.title}
                        secondary={[
                          e.extendedProps?.betrag != null
                            ? `Betrag: ${Number(e.extendedProps.betrag).toFixed(2)}€`
                            : null,
                          e.extendedProps?.konto_id
                            ? `Konto: ${kontenById[e.extendedProps.konto_id] ?? e.extendedProps.konto_id}`
                            : null,
                          e.extendedProps?.active ? "Aktiv" : "Inaktiv",
                        ]
                          .filter(Boolean)
                          .join(" · ")}
                      />
                    </ListItem>
                  ))}
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
};

export default AddMonthlyCosts;
