const sameDay = (d1, d2) =>
  d1.getFullYear() === d2.getFullYear() &&
  d1.getMonth() === d2.getMonth() &&
  d1.getDate() === d2.getDate();

/**
 * Steuerung für Hover + Popover:
 * - enterDelay/leaveDelay verhindern Zucken
 * - Popover bleibt offen, solange Maus darüber ist
 * - liefert Popover-Props, die du direkt spreadest
 */
export function makeHoverController(
  events,
  { setHoverAnchor, setHoverItems, setHoverDate },
  { enterDelay = 120, leaveDelay = 160 } = {}
) {
  let openT = null;
  let closeT = null;
  let currentAnchor = null;

  const clearOpen = () => {
    if (openT) clearTimeout(openT);
    openT = null;
  };
  const clearClose = () => {
    if (closeT) clearTimeout(closeT);
    closeT = null;
  };

  const open = (info) => {
    const eventDate = new Date(info.event.startStr);
    const items = events.filter((e) => sameDay(new Date(e.start), eventDate));
    const cell = info.el.closest(".fc-daygrid-day") || info.el;
    currentAnchor = info.el;
    setHoverItems(items);
    setHoverDate(eventDate);
    setHoverAnchor(info.el);
  };

  const close = () => {
    currentAnchor = null;
    setHoverAnchor(null);
    setHoverItems([]);
    setHoverDate(null);
  };

  const onEnter = (info) => {
    clearClose();
    if (currentAnchor === info.el) return;
    clearOpen();
    openT = setTimeout(() => open(info), enterDelay);
  };

  const onLeave = () => {
    clearOpen();
    clearClose();
    closeT = setTimeout(close, leaveDelay);
  };

  // ➜ Diese beiden benutzt du am Popover-Paper
  const onPopoverEnter = () => clearClose();
  const onPopoverLeave = onLeave;

  return {
    onEnter,
    onLeave,
    popoverProps: {
      onMouseEnter: onPopoverEnter,
      onMouseLeave: onPopoverLeave,
      sx: { pointerEvents: "auto" }, // Popover bedienbar machen
    },
  };
}

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
