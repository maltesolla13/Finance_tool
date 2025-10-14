import * as NumberUtils from "./number.utils";
import * as DateUtils from "./date.utils";

export const toPayloadReceipt = (s) => ({
  user_id: s.userId,
  name: String(s.name || "").trim(),
  betrag: NumberUtils.toNumber(s.betrag),
  kategorie_id: s.kategorieId,
  konto_id: s.kontoId,
  laden_id: s.ladenId,
  datum: DateUtils.toISODate(s.datum),
});

export const toPayloadMonthlyCost = ({
  userId,
  name,
  kategorieId,
  startDatum,
  nextDue,
  active,
  kontoOutId,
  kontoInId,
  betrag,
  securityId,
  anteil,
}) => ({
  user_id: userId,
  name: String(name || "").trim(),
  kategorie_id: kategorieId,
  ausgangs_konto_id: kontoOutId ?? null,
  eingangs_konto_id: kontoInId ?? null,
  betrag: NumberUtils.toNumberOrNull(betrag),
  anteil: NumberUtils.toNumberOrNull(anteil),
  securities_id: securityId ?? null,
  start_datum: DateUtils.isoDateTime(startDatum),
  next_due: DateUtils.isoDateTime(nextDue || startDatum),
  active: !!active,
});
