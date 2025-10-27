export class MarketService {
  constructor(api) {
    this.api = api;
  }
  async price({ ticker, date, source = "auto", side = "Kauf" }) {
    const src = source === "auto" ? (side === "Kauf" ? "low" : "high") : source; // "low" | "high"
    const res =
      src === "low"
        ? await this.api.marketLow({ ticker, date })
        : await this.api.marketHigh({ ticker, date });

    // erwarte z.B. { price } oder { low }/{ high }; fallback auf Zahl
    return res?.price ?? res?.low ?? res?.high ?? Number(res);
  }
}
