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
