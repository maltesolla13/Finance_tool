import * as NumberUtils from "./number.utils";

export const validateReceipt = (s) => {
  if (!s.userId || !s.kontoId || !s.kategorieId || !s.ladenId)
    return "Bitte User, Konto, Kategorie und Laden wählen.";
  if (!s.name || !s.name.trim()) return "Bezeichnung fehlt.";
  if (NumberUtils.toNumber(s.betrag) == null) return "Betrag fehlt/ungültig.";
  if (!s.datum) return "Datum fehlt.";
  return null;
};

export const validateMonthlyCost = ({
  userId,
  name,
  kategorieId,
  kontoOutId,
  kontoInId,
  betrag,
  anteil,
  securityId,
  startDatum,
}) => {
  if (!userId) return "Bitte User wählen.";
  if (!name?.trim()) return "Bezeichnung fehlt.";
  if (!kategorieId) return "Kategorie wählen.";
  if (!kontoOutId && !kontoInId)
    return "Mindestens ein Konto (Ausgang oder Eingang) wählen.";
  if (!startDatum) return "Start-Datum setzen.";

  const amount = NumberUtils.toNumberOrNull(betrag);
  const shares = NumberUtils.toNumberOrNull(anteil);

  if (securityId) {
    if (amount == null && shares == null) {
      return "Bei Wertpapier bitte Betrag ODER Anteil angeben.";
    }
  } else {
    if (amount == null) return "Ohne Wertpapier ist Betrag erforderlich.";
  }
  return "";
};

export function validateSavings({
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
  const num = (x) =>
    x === "" || x === null || x === undefined ? null : Number(x);

  if (!name?.trim()) return "Bezeichnung ist erforderlich.";
  if (!userId) return "User ist erforderlich.";
  if (!kontoId) return "Konto ist erforderlich.";
  if (!kategorieId) return "Kategorie ist erforderlich.";

  const start = new Date(startDatum);
  const end = new Date(endDatum);
  if (isNaN(+start)) return "Ungültiges Startdatum.";
  if (isNaN(+end)) return "Ungültiges Enddatum.";
  if (end < start) return "Enddatum muss nach dem Startdatum liegen.";

  const b = num(betrag);
  const se = num(sparrate_e);
  const sp = num(sparrate_p);
  if (b !== null && isNaN(b)) return "Betrag muss eine Zahl sein.";
  if (se !== null && isNaN(se)) return "Sparrate (€) muss eine Zahl sein.";
  if (sp !== null && isNaN(sp)) return "Sparrate (%) muss eine Zahl sein.";

  return ""; // alles ok
}
