export const toISODate = (d) => {
  if (!d) return "";
  if (typeof d === "string") return d.split("T")[0];
  return new Date(d).toISOString().slice(0, 10);
};
export const isoDateTime = (d) =>
  !d
    ? null
    : typeof d === "string"
      ? d.includes("T")
        ? d
        : `${d}T00:00:00`
      : new Date(d).toISOString();
export const formatDateDE = (val) => {
  if (!val) return "";
  if (typeof val === "string") {
    const [y, m, d] = val.split("T")[0].split("-");
    if (y && m && d) return `${d}.${m}.${y}`;
  }
  const dt = new Date(val);
  return Number.isNaN(dt.getTime())
    ? String(val)
    : new Intl.DateTimeFormat("de-DE").format(dt);
};
export const currentMonthRange = (base = new Date()) => {
  const y = base.getFullYear();
  const m = base.getMonth();
  return [new Date(y, m, 1), new Date(y, m + 1, 0, 23, 59, 59)];
};
