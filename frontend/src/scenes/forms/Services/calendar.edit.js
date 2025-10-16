// forms/Services/calendar.edit.js
import * as DateUtils from "./date.utils";

export function openEditById(
  rawId,
  { monthlyCosts, setEditItem, setEditOpen }
) {
  const id = Number(rawId);
  const s = monthlyCosts.find((x) => Number(x.id) === id);
  if (!s) return;
  setEditItem({
    ...s,
    start_datum_ui: "",
    next_due_ui: (s.next_due || "").slice(0, 10),
  });
  setEditOpen(true);
}

export function buildEditHandlers({ monthlyCosts, setEditItem, setEditOpen }) {
  const onEventClick = (clickInfo) => {
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
  return { onEventClick };
}

function validateEditItem(editItem) {
  const errs = {};
  const d = (editItem?.start_datum_ui || "").trim();

  if (!d) {
    errs.start_datum_ui = "Start-Datum ist erforderlich.";
  } else if (
    !/^\d{4}-\d{2}-\d{2}$/.test(d) ||
    Number.isNaN(new Date(d).getTime())
  ) {
    errs.start_datum_ui = "Ungültiges Datum (Format: YYYY-MM-DD).";
  }
  return errs;
}

export async function saveEditItem(
  editItem,
  {
    api,
    setOk,
    closeEdit,
    loadMonthlyCosts,
    setErr,
    setMonthlyCosts,
    setEditErrors,
  }
) {
  // 1) Frontend-Validierung
  const errs = validateEditItem(editItem);
  if (Object.keys(errs).length) {
    setEditErrors?.(errs);
    setErr?.("Bitte das Start-Datum korrigieren.");
    return;
  }
  setEditErrors?.({});

  try {
    const payload = {
      user_id: editItem.user_id,
      name: editItem.name,
      kategorie_id: editItem.kategorie_id,
      start_datum: `${editItem.start_datum_ui}T00:00:00`,
      next_due: editItem.next_due_ui
        ? `${editItem.next_due_ui}T00:00:00`
        : `${editItem.start_datum_ui}T00:00:00`,
      active: !!editItem.active,
      ausgangs_konto_id: editItem.ausgangs_konto_id ?? null,
      eingangs_konto_id: editItem.eingangs_konto_id ?? null,
      securities_id: editItem.securities_id ?? null,
      anteil: editItem.anteil ?? null,
      betrag: editItem.betrag ?? null,
    };

    const updated = await api.updateMonthlyCosts(editItem.id, payload);

    // Dialog sofort schließen
    closeEdit();

    // Optimistisch updaten
    setMonthlyCosts?.((prev) =>
      prev.map((x) =>
        Number(x.id) === Number(editItem.id)
          ? { ...x, ...updated, ...payload }
          : x
      )
    );

    // Sicherheitshalber frisch laden
    loadMonthlyCosts?.();
    setOk?.("Eintrag aktualisiert.");
  } catch (e) {
    console.error(e);
    setErr?.("Aktualisieren fehlgeschlagen");
  }
}
