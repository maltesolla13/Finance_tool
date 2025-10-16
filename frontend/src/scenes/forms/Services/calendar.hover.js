// forms/Services/calendar.hover.js

// Kleine Helfer
const sameDay = (d1, d2) =>
  d1.getFullYear() === d2.getFullYear() &&
  d1.getMonth() === d2.getMonth() &&
  d1.getDate() === d2.getDate();

/**
 * Erzeugt die Event-Hover-Handler für FullCalendar.
 * Nutzt dein bereits berechnetes events-Array.
 */
export function makeHoverHandlers(
  events,
  { setHoverAnchor, setHoverItems, setHoverDate }
) {
  const onEnter = (info) => {
    const eventDate = new Date(info.event.startStr);
    const items = events.filter((e) => sameDay(new Date(e.start), eventDate));
    setHoverItems(items);
    setHoverDate(eventDate);
    setHoverAnchor(info.el);
  };

  const onLeave = () => {
    setHoverAnchor(null);
    setHoverItems([]);
    setHoverDate(null);
  };

  return { onEnter, onLeave };
}

/**
 * Baut den "secondary" Text für die Popover-Liste zusammen.
 * Erwartet die extendedProps des Events sowie die von dir gepflegten Maps.
 */
export function formatHoverSecondary(
  xp,
  { catsById, kontenById, securitiesById, usersById }
) {
  const parts = [];

  if (xp?.betrag != null)
    parts.push(`Betrag: ${Number(xp.betrag).toFixed(2)}€`);
  if (xp?.kategorie_id)
    parts.push(`Kategorie: ${catsById?.[xp.kategorie_id] ?? xp.kategorie_id}`);
  if (xp?.ausgangs_konto_id)
    parts.push(
      `Ausgang: ${kontenById?.[xp.ausgangs_konto_id] ?? xp.ausgangs_konto_id}`
    );
  if (xp?.eingangs_konto_id)
    parts.push(
      `Eingang: ${kontenById?.[xp.eingangs_konto_id] ?? xp.eingangs_konto_id}`
    );
  if (xp?.securities_id)
    parts.push(
      `Wertpapier: ${securitiesById?.[xp.securities_id] ?? xp.securities_id}`
    );
  if (xp?.anteil != null) parts.push(`Anteil: ${Number(xp.anteil)}`);
  if (xp?.user_id) parts.push(`User: ${usersById?.[xp.user_id] ?? xp.user_id}`);
  if (xp?.start_datum)
    parts.push(
      `Start: ${new Date(xp.start_datum).toLocaleDateString("de-DE")}`
    );
  if (xp?.next_due)
    parts.push(`Nächste: ${new Date(xp.next_due).toLocaleDateString("de-DE")}`);

  parts.push(xp?.active ? "Aktiv" : "Inaktiv");
  return parts.filter(Boolean).join(" · ");
}
