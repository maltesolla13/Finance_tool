// forms/Services/calendar.edit.js
import * as DateUtils from "./date.utils";

/**
 * Erzeugt den onEventClick-Handler für FullCalendar.
 * Öffnet deinen Edit-Dialog mit dem korrekten Item.
 */
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

/**
 * Speichert die Änderungen des Edit-Dialogs.
 * Entspricht inhaltlich deiner bisherigen saveEdit-Logik.
 */
export async function saveEditItem(
  editItem,
  { api, setOk, closeEdit, loadMonthlyCosts, setErr }
) {
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
}
