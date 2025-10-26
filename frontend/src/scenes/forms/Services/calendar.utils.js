// Anstehende Ausführung
export const buildMonthlyCostEvents = (rows = [], monthStart, monthEnd) => {
  const inRange = (d) => d >= monthStart && d <= monthEnd;
  return rows
    .filter((s) => inRange(new Date(s.next_due)))
    .map((s) => ({
      id: String(s.id),
      title: s.name,
      start: s.next_due,
      extendedProps: { ...s, __source: "monthlycost", editable: true },
    }));
};

// Ausgeführte Buchungen
export const buildDepotSparplanEvents = (rows = [], monthStart, monthEnd) => {
  const inRange = (d) => d >= monthStart && d <= monthEnd;
  return rows
    .map((r) => ({
      ...r,
      _date: new Date(r.datum || r.buchungs_datum || r.day || r.date),
    }))
    .filter((r) => !Number.isNaN(r._date?.getTime()) && inRange(r._date))
    .map((r) => ({
      id: `dep-${r.id}`,
      title: r.name || r.ticker || "Sparplan",
      start: r._date.toISOString(),
      extendedProps: { ...r, __source: "depotbewegung", editable: false },
    }));
};
