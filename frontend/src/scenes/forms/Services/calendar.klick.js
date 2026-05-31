// forms/Services/calendar.klick.js

// Hilfsfunktion: Datum-gleichheit (ohne Uhrzeit)
const sameDay = (d1, d2) =>
  d1.getFullYear() === d2.getFullYear() &&
  d1.getMonth() === d2.getMonth() &&
  d1.getDate() === d2.getDate();

/**
 * Baut die Klick-Controller für FullCalendar:
 * - onEventClick: Klick auf Event zeigt Popover mit allen Einträgen dieses Tages
 * - onDateClick: Klick in leere Zelle zeigt ggf. "Keine Einträge"
 * - close: schließt das Popover
 * - paperProps: Props fürs Popover-Paper (bedienbar halten)
 */
export function makeClickController(
  events,
  { setInfoAnchor, setInfoItems, setInfoDate },
) {
  const openAt = (cellEl, dateObj) => {
    const items = events.filter((e) => sameDay(new Date(e.start), dateObj));
    setInfoItems(items);
    setInfoDate(dateObj);
    setInfoAnchor(cellEl);
  };

  const close = () => {
    setInfoAnchor(null);
    setInfoItems([]);
    setInfoDate(null);
  };

  const onEventClick = (clickInfo) => {
    const cell = clickInfo.el.closest(".fc-daygrid-day") || clickInfo.el;
    openAt(cell, new Date(clickInfo.event.startStr));
    // WICHTIG: FullCalendar soll nicht navigieren/selektieren
    clickInfo.jsEvent?.preventDefault?.();
  };

  const onDateClick = (dateClickInfo) => {
    const cell = dateClickInfo.dayEl || dateClickInfo.jsEvent?.target;
    openAt(cell, dateClickInfo.date);
  };

  // Popover bedienbar halten (Buttons klickbar)
  const paperProps = { sx: { pointerEvents: "auto" } };

  return { onEventClick, onDateClick, close, paperProps };
}

/**
 * Formatiert den Secondary-Text (gleiches Format wie vormals im Hover)
 */
export function formatInfoSecondary(
  xp,
  { catsById, kontenById, securitiesById, usersById },
) {
  const parts = [];
  if (xp?.betrag != null)
    parts.push(`Betrag: ${Number(xp.betrag).toFixed(2)}€`);
  if (xp?.kategorie_id)
    parts.push(`Kategorie: ${catsById?.[xp.kategorie_id] ?? xp.kategorie_id}`);
  if (xp?.ausgangs_konto_id)
    parts.push(
      `Ausgang: ${kontenById?.[xp.ausgangs_konto_id] ?? xp.ausgangs_konto_id}`,
    );
  if (xp?.eingangs_konto_id)
    parts.push(
      `Eingang: ${kontenById?.[xp.eingangs_konto_id] ?? xp.eingangs_konto_id}`,
    );
  if (xp?.securities_id)
    parts.push(
      `Wertpapier: ${securitiesById?.[xp.securities_id] ?? xp.securities_id}`,
    );
  if (xp?.anteil != null) parts.push(`Anteil: ${Number(xp.anteil)}`);
  if (xp?.user_id) parts.push(`User: ${usersById?.[xp.user_id] ?? xp.user_id}`);
  if (xp?.execution_datum)
    parts.push(
      `Termin: ${new Date(xp.execution_datum).toLocaleDateString("de-DE")}`,
    );
  if (xp?.start_datum)
    parts.push(
      `Start: ${new Date(xp.start_datum).toLocaleDateString("de-DE")}`,
    );
  if (xp?.next_due)
    parts.push(`Nächste: ${new Date(xp.next_due).toLocaleDateString("de-DE")}`);
  if (xp?.status) parts.push(`Status: ${xp.status}`);
  else parts.push(xp?.active ? "Aktiv" : "Inaktiv");
  return parts.filter(Boolean).join(" · ");
}
