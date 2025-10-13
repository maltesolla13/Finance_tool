import { toNumber, toNumberOrNull } from "./number.utils";
import { toISODate, isoDateTime } from "./date.utils";

export const toPayloadReceipt = (s) => ({
  user_id: s.userId,
  name: (s.name || "").trim(),
  betrag: toNumber(s.betrag),
  kategorie_id: s.kategorieId,
  konto_id: s.kontoId,
  laden_id: s.ladenId,
  datum: toISODate(s.datum),
});

export const toPayloadMonthlyCost = (s) => ({
  user_id: s.userId,
  name: (s.name || "").trim(),
  kategorie_id: s.kategorieId,
  start_datum: isoDateTime(s.startDatum),
  next_due: isoDateTime(s.nextDue || s.startDatum),
  active: !!s.active,
  ausgangs_konto_id: s.kontoOutId ?? null,
  eingangs_konto_id: s.kontoInId ?? null,
  betrag: toNumber(s.betrag),
  aktien_id: s.securityId ?? null,
  anteil: toNumberOrNull(s.anteil),
});
