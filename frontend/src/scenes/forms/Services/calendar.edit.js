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
    start_datum_ui: (s.start_datum || "").slice(0, 10),
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

export async function saveEditItem(
  editItem,
  { api, setOk, closeEdit, loadMonthlyCosts, setErr, setMonthlyCosts }
) {
  try {
    const payload = {
      user_id: editItem.user_id,
      name: editItem.name,
      kategorie_id: editItem.kategorie_id,
      start_datum: editItem.start_datum_ui
        ? `${editItem.start_datum_ui}T00:00:00`
        : null,
      next_due: editItem.next_due_ui
        ? `${editItem.next_due_ui}T00:00:00`
        : null,
      active: !!editItem.active,
      ausgangs_konto_id: editItem.ausgangs_konto_id ?? null,
      eingangs_konto_id: editItem.eingangs_konto_id ?? null,
      securities_id: editItem.securities_id ?? null,
      anteil: editItem.anteil ?? null,
      betrag: editItem.betrag ?? null,
    };

    // 1) Server-Update
    const updated = await api.updateMonthlyCosts(editItem.id, payload);

    // 2) Dialog sofort schließen
    closeEdit();

    // 3) Optimistische Aktualisierung (UI sofort updaten)
    if (setMonthlyCosts) {
      setMonthlyCosts((prev) =>
        prev.map((x) =>
          Number(x.id) === Number(editItem.id)
            ? { ...x, ...updated, ...payload }
            : x
        )
      );
    }

    // 4) Zur Sicherheit frisch laden (falls Server noch weitere Felder setzt)
    loadMonthlyCosts?.();

    setOk("Eintrag aktualisiert.");
  } catch (e) {
    console.error(e);
    setErr("Aktualisieren fehlgeschlagen");
  }
}
