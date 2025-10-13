export const buildMonthlyCostEvents = (rows = [], monthStart, monthEnd) => {
  const inRange = (d) => d >= monthStart && d <= monthEnd;
  return rows
    .filter((s) => inRange(new Date(s.next_due)))
    .map((s) => ({
      id: String(s.id),
      title: s.name,
      start: s.next_due,
      extendedProps: { ...s },
    }));
};
