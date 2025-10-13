// src/scenes/forms/FormService.js
// Zentrale, wiederverwendbare Helfer + API-Wrapper fÃ¼r deine Form-Seiten
// Benutzung in Komponenten:
//   const api = useMemo(() => new ApiRequests(new ApiClient()), []);
//   const formSvc = useMemo(() => new FormService(api), [api]);
//
//   // Optionen laden (einmalig alle)
//   const { options, maps } = await formSvc.loadAllOptions({ includeSecurities: true });
//   // oder getypte Suche (debounced in der Klasse verfÃ¼gbar)
//   formSvc.debouncedRefreshOptions({ users: q1, konten: q2, cats: q3, laden: q4 }, true)
//     .then(({ options, maps }) => { /* setState(...) */ });
//
//   // Payloads bauen + Validierung
//   const err = FormService.validateReceipt(formState);
//   if (!err) await api.createReceipt(formSvc.toPayloadReceipt(formState));

export default class FormService {
  constructor(apiRequests) {
    this.api = apiRequests; // erwartet Instanz von ApiRequests

    // Public: Debounced Options-Refresh
    this.debouncedRefreshOptions = this.debounce(
      (queries, includeSecurities = false) =>
        this.refreshOptions(queries, includeSecurities),
      250
    );
  }

  /* =========================
   *   API-gestÃ¼tzte Loader
   * ========================= */

  async loadAllOptions({ includeSecurities = true } = {}) {
    return this.refreshOptions(
      { users: "", konten: "", cats: "", laden: "" },
      includeSecurities
    );
  }

  /**
   * LÃ¤dt Optionsdaten passend zu den eingegebenen Suchstrings.
   * @param {{users?: string, konten?: string, cats?: string, laden?: string}} queries
   * @param {boolean} includeSecurities
   * @returns {Promise<{options: object, maps: object}>}
   */
  async refreshOptions(queries = {}, includeSecurities = false) {
    const q = { users: "", konten: "", cats: "", laden: "", ...queries };

    const promises = [
      this.api.searchOptions("users", q.users || ""),
      this.api.searchOptions("konten", q.konten || ""),
      this.api.searchOptions("kategorien", q.cats || ""),
      this.api.searchOptions("laden", q.laden || ""),
    ];
    if (includeSecurities)
      promises.push(this.api.listSecurities().catch(() => []));

    const [users, konten, cats, shops, secs = []] = await Promise.all(promises);

    const options = {
      users: users ?? [],
      konten: konten ?? [],
      cats: cats ?? [],
      laden: shops ?? [],
      securities: secs ?? [],
    };

    const maps = {
      usersById: FormService.mapById(options.users),
      kontenById: FormService.mapById(options.konten),
      catsById: FormService.mapById(options.cats),
      ladenById: FormService.mapById(options.laden),
      securitiesById: FormService.mapById(options.securities),
    };

    return { options, maps };
  }

  /** Kategorie/Laden per ensure anlegen (nutzt dein Backend-Endpoint /options/ensure) */
  async ensureKategorie(name) {
    return this.api.ensureOption("kategorien", name);
  }
  async ensureLaden(name) {
    return this.api.ensureOption("laden", name);
  }

  /* =========================
   *   Payload-Builder
   * ========================= */

  /** Baut das Payload fÃ¼r einen Receipt aus einem einfachen Form-State-Objekt */
  toPayloadReceipt(s) {
    return {
      user_id: s.userId,
      name: (s.name || "").trim(),
      betrag: FormService.toNumber(s.betrag),
      kategorie_id: s.kategorieId,
      konto_id: s.kontoId,
      laden_id: s.ladenId,
      datum: FormService.toISODate(s.datum),
    };
  }

  /** Baut das Payload fÃ¼r MonthlyCosts */
  toPayloadMonthlyCost(s) {
    return {
      user_id: s.userId,
      name: (s.name || "").trim(),
      kategorie_id: s.kategorieId,
      start_datum: FormService.isoDateTime(s.startDatum),
      next_due: FormService.isoDateTime(s.nextDue || s.startDatum),
      active: !!s.active,
      ausgangs_konto_id: s.kontoOutId ?? null,
      eingangs_konto_id: s.kontoInId ?? null,
      betrag: FormService.toNumber(s.betrag),
      aktien_id: s.securityId ?? null,
      anteil: FormService.toNumberOrNull(s.anteil),
    };
  }

  /* =========================
   *   Validierung
   * ========================= */

  static validateReceipt(s) {
    if (!s.userId || !s.kontoId || !s.kategorieId || !s.ladenId)
      return "Bitte User, Konto, Kategorie und Laden wÃ¤hlen.";
    if (!s.name || !s.name.trim()) return "Bezeichnung fehlt.";
    if (FormService.toNumber(s.betrag) == null)
      return "Betrag fehlt/ungÃ¼ltig.";
    if (!s.datum) return "Datum fehlt.";
    return null; // ok
  }

  static validateMonthlyCost(s) {
    if (!s.userId || !s.kategorieId) return "Bitte User und Kategorie wÃ¤hlen.";
    if (!s.name || !s.name.trim()) return "Bezeichnung fehlt.";
    if (FormService.toNumber(s.betrag) == null)
      return "Betrag fehlt/ungÃ¼ltig.";
    if (!s.startDatum) return "Startdatum fehlt.";
    if (!s.kontoOutId && !s.kontoInId)
      return "Mindestens ein Konto (Ausgang/Eingang) wÃ¤hlen.";
    return null;
  }

  /* =========================
   *   Kalender-Helfer (MonthlyCosts)
   * ========================= */

  static currentMonthRange(baseDate = new Date()) {
    const y = baseDate.getFullYear();
    const m = baseDate.getMonth();
    const start = new Date(y, m, 1);
    const end = new Date(y, m + 1, 0, 23, 59, 59);
    return [start, end];
  }

  /** Baut FullCalendar-Events aus MonthlyCosts-Rows */
  static buildMonthlyCostEvents(rows = [], monthStart, monthEnd) {
    const inRange = (d) => d >= monthStart && d <= monthEnd;
    return rows
      .filter((s) => inRange(new Date(s.next_due)))
      .map((s) => ({
        id: String(s.id),
        title: s.name,
        start: s.next_due,
        extendedProps: {
          user_id: s.user_id,
          betrag: s.betrag,
          anteil: s.anteil,
          aktien_id: s.aktien_id,
          ausgangs_konto_id: s.ausgangs_konto_id,
          eingangs_konto_id: s.eingangs_konto_id,
          active: s.active,
          kategorie_id: s.kategorie_id,
          start_datum: s.start_datum,
          next_due: s.next_due,
        },
      }));
  }

  /* =========================
   *   Kleine Utils
   * ========================= */

  static mapById(arr = []) {
    return Object.fromEntries((arr || []).map((o) => [o.id, o.name]));
  }

  static toNumber(v) {
    if (v === "" || v == null) return null;
    const n = Number(v);
    return Number.isFinite(n) ? n : null;
  }

  static toNumberOrNull(v) {
    if (v === "" || v == null) return null;
    const n = Number(v);
    return Number.isFinite(n) ? n : null;
  }

  static toISODate(d) {
    if (!d) return "";
    if (typeof d === "string") return d.split("T")[0];
    const iso = new Date(d).toISOString();
    return iso.slice(0, 10);
  }

  /** Liefert ISO-String mit Zeitanteil ("YYYY-MM-DDTHH:mm:ss.sssZ"). */
  static isoDateTime(d) {
    if (!d) return null;
    return typeof d === "string"
      ? d.includes("T")
        ? d
        : `${d}T00:00:00`
      : new Date(d).toISOString();
  }

  static formatDateDE(val) {
    if (!val) return "";
    if (typeof val === "string") {
      const part = val.split("T")[0];
      const [y, m, d] = part.split("-");
      if (y && m && d) return `${d}.${m}.${y}`;
    }
    const dt = new Date(val);
    return Number.isNaN(dt.getTime())
      ? String(val)
      : new Intl.DateTimeFormat("de-DE").format(dt);
  }

  /** simples Debounce */
  debounce(fn, ms = 250) {
    let t;
    return (...args) => {
      clearTimeout(t);
      t = setTimeout(() => fn(...args), ms);
    };
  }
}
