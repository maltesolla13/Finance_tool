import { toNumber } from "./number.utils";

export const validateReceipt = (s) => {
  if (!s.userId || !s.kontoId || !s.kategorieId || !s.ladenId)
    return "Bitte User, Konto, Kategorie und Laden wählen.";
  if (!s.name || !s.name.trim()) return "Bezeichnung fehlt.";
  if (toNumber(s.betrag) == null) return "Betrag fehlt/ungültig.";
  if (!s.datum) return "Datum fehlt.";
  return null;
};

export const validateMonthlyCost = (s) => {
  if (!s.userId || !s.kategorieId) return "Bitte User und Kategorie wählen.";
  if (!s.name || !s.name.trim()) return "Bezeichnung fehlt.";
  if (toNumber(s.betrag) == null) return "Betrag fehlt/ungültig.";
  if (!s.startDatum) return "Startdatum fehlt.";
  if (!s.kontoOutId && !s.kontoInId)
    return "Mindestens ein Konto (Ausgang/Eingang) wählen.";
  return null;
};
