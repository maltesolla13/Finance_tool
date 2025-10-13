export class OptionsService {
  constructor(api, { debounceMs = 250 } = {}) {
    this.api = api;
    this.debouncedRefresh = this._debounce(this.refresh.bind(this), debounceMs);
  }

  async loadAll({ includeSecurities = true } = {}) {
    return this.refresh(
      { users: "", konten: "", cats: "", laden: "" },
      includeSecurities
    );
  }

  async refresh(q = {}, includeSecurities = false) {
    const queries = { users: "", konten: "", cats: "", laden: "", ...q };
    const [users, konten, cats, shops, secs = []] = await Promise.all([
      this.api.searchOptions("users", queries.users || ""),
      this.api.searchOptions("konten", queries.konten || ""),
      this.api.searchOptions("kategorien", queries.cats || ""),
      this.api.searchOptions("laden", queries.laden || ""),
      includeSecurities
        ? this.api.listSecurities().catch(() => [])
        : Promise.resolve([]),
    ]);
    const options = {
      users: users ?? [],
      konten: konten ?? [],
      cats: cats ?? [],
      laden: shops ?? [],
      securities: secs ?? [],
    };
    const mapById = (arr = []) =>
      Object.fromEntries(arr.map((o) => [o.id, o.name]));
    const maps = {
      usersById: mapById(options.users),
      kontenById: mapById(options.konten),
      catsById: mapById(options.cats),
      ladenById: mapById(options.laden),
      securitiesById: mapById(options.securities),
    };
    return { options, maps };
  }

  ensureKategorie(name) {
    return this.api.ensureOption("kategorien", name);
  }
  ensureLaden(name) {
    return this.api.ensureOption("laden", name);
  }

  _debounce(fn, ms = 250) {
    let t;
    return (...args) => {
      clearTimeout(t);
      t = setTimeout(() => fn(...args), ms);
    };
  }
}
