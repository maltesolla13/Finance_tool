const asDate = (value) => {
  const d = new Date(value);
  return Number.isNaN(d.getTime()) ? null : d;
};

const dateKey = (value) => {
  const d = asDate(value);
  return d ? d.toISOString().slice(0, 10) : "";
};

const addMonths = (date, months, anchorDay) => {
  const d = new Date(date);
  const day = anchorDay || d.getDate();
  d.setDate(1);
  d.setMonth(d.getMonth() + months);
  const last = new Date(d.getFullYear(), d.getMonth() + 1, 0).getDate();
  d.setDate(Math.min(day, last));
  return d;
};

const addInterval = (date, row, anchorDay) => {
  const repeatType = (row.repeat_type || "MONTHLY").toUpperCase();
  if (repeatType === "WEEKLY") {
    const d = new Date(date);
    d.setDate(d.getDate() + 7);
    return d;
  }
  if (repeatType === "QUARTERLY") return addMonths(date, 3, anchorDay);
  if (repeatType === "YEARLY") return addMonths(date, 12, anchorDay);
  if (repeatType === "CUSTOM") {
    const count = Math.max(1, Number(row.custom_interval) || 1);
    const unit = (row.custom_unit || "MONTHS").toUpperCase();
    const d = new Date(date);
    if (unit === "DAYS") d.setDate(d.getDate() + count);
    else if (unit === "WEEKS") d.setDate(d.getDate() + count * 7);
    else if (unit === "YEARS") return addMonths(date, count * 12, anchorDay);
    else return addMonths(date, count, anchorDay);
    return d;
  }
  return addMonths(date, 1, anchorDay);
};

const buildExecutionEvent = (row) => ({
  id: `mce-${row.id}`,
  title: row.name,
  start: row.execution_datum,
  extendedProps: {
    ...row,
    __source: "monthlycost_execution",
    editable: true,
  },
});

// Bestehende Stammsatz-Events, fuer alte Call-Sites beibehalten.
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

export const buildMonthlyCostExecutionEvents = (
  executions = [],
  monthlyCosts = [],
  monthStart,
  monthEnd,
  horizonStart = new Date(),
  horizonEnd = addMonths(new Date(), 12),
) => {
  const inRange = (d) => d >= monthStart && d <= monthEnd;
  const executionKeys = new Set(
    executions.map((e) => `${e.monthlycost_id}:${dateKey(e.execution_datum)}`),
  );

  const executed = executions
    .map((e) => ({ ...e, _date: asDate(e.execution_datum) }))
    .filter((e) => e._date)
    .map(buildExecutionEvent);

  const projected = [];
  monthlyCosts
    .filter((row) => row.active)
    .forEach((row) => {
      let due = asDate(row.next_due || row.start_datum);
      const anchorDate = asDate(row.start_datum || row.next_due);
      const anchorDay = anchorDate?.getDate();
      if (!due) return;

      let guard = 0;
      while (due < horizonStart && guard < 500) {
        due = addInterval(due, row, anchorDay);
        guard += 1;
      }

      while (due <= horizonEnd && guard < 1000) {
        const key = `${row.id}:${dateKey(due)}`;
        if (!executionKeys.has(key) && inRange(due)) {
          const executionDate = due.toISOString().slice(0, 10);
          projected.push({
            id: `mcp-${row.id}-${executionDate}`,
            title: row.name,
            start: executionDate,
            extendedProps: {
              ...row,
              monthlycost_id: row.id,
              execution_datum: executionDate,
              __source: "monthlycost_projection",
              editable: true,
            },
          });
        }
        due = addInterval(due, row, anchorDay);
        guard += 1;
      }
    });

  return [...executed, ...projected];
};

// Ausgefuehrte Buchungen
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
