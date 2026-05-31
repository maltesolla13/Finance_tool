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

const parseDateInput = (value) => {
  if (!value) return null;
  if (value instanceof Date) {
    return Number.isNaN(value.getTime()) ? null : value;
  }
  const [y, m, d] = String(value).split("T")[0].split("-").map(Number);
  if (!y || !m || !d) return null;
  const date = new Date(y, m - 1, d);
  return Number.isNaN(date.getTime()) ? null : date;
};

const toDateInputValue = (date) => {
  if (!date) return "";
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, "0");
  const d = String(date.getDate()).padStart(2, "0");
  return `${y}-${m}-${d}`;
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

export const addRepeatInterval = (
  date,
  repeatType = "MONTHLY",
  customInterval,
  customUnit = "MONTHS",
  anchorDay,
) => {
  const repeat = (repeatType || "MONTHLY").toUpperCase();
  if (repeat === "WEEKLY") {
    const d = new Date(date);
    d.setDate(d.getDate() + 7);
    return d;
  }
  if (repeat === "QUARTERLY") return addMonths(date, 3, anchorDay);
  if (repeat === "YEARLY") return addMonths(date, 12, anchorDay);
  if (repeat === "CUSTOM") {
    const count = Math.max(1, Number(customInterval) || 1);
    const unit = (customUnit || "MONTHS").toUpperCase();
    const d = new Date(date);
    if (unit === "DAYS") d.setDate(d.getDate() + count);
    else if (unit === "WEEKS") d.setDate(d.getDate() + count * 7);
    else if (unit === "YEARS") return addMonths(date, count * 12, anchorDay);
    else return addMonths(date, count, anchorDay);
    return d;
  }
  return addMonths(date, 1, anchorDay);
};

export const nextDueFromRepeat = ({
  startDate,
  repeatType = "MONTHLY",
  customInterval,
  customUnit = "MONTHS",
}) => {
  const start = parseDateInput(startDate);
  if (!start) return "";
  return toDateInputValue(
    addRepeatInterval(
      start,
      repeatType,
      customInterval,
      customUnit,
      start.getDate(),
    ),
  );
};
