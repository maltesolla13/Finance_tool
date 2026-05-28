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
  repeatType,
  customInterval,
  customUnit,
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
  repeat_type: repeatType || "MONTHLY",
  custom_interval:
    repeatType === "CUSTOM" ? NumberUtils.toNumberOrNull(customInterval) : null,
  custom_unit: repeatType === "CUSTOM" ? customUnit || "MONTHS" : null,
  active: !!active,
});

export function toPayloadSavings({
  name,
  userId,
  kontoId,
  kategorieId,
  betrag,
  startDatum,
  endDatum,
  sparrate_e,
  sparrate_p,
}) {
  const num = (x) => (x === "" || x == null ? null : Number(x));
  return {
    name: name.trim(),
    user_id: userId,
    konto_id: kontoId,
    kategorie_id: kategorieId,
    betrag: num(betrag),
    start_datum: DateUtils.toISODate(startDatum),
    end_datum: endDatum ? DateUtils.toISODate(endDatum) : null,
    sparrate_e: num(sparrate_e),
    sparrate_p: num(sparrate_p),
  };
}

export const toPayloadDepotbewegung = ({
  userId,
  kontoId,
  securityId,
  kategorieId,
  typ,
  betrag,
  anteile,
  datum,
}) => {
  const num = (x) => (x === "" || x == null ? null : Number(x));
  return {
    user_id: userId,
    konto_id: kontoId,
    securities_id: securityId,
    kategorie_id: kategorieId,
    type: typ,
    betrag: num(betrag),
    anteile: num(anteile),
    datum: DateUtils.toISODate(datum),
  };
};
