export class ApiRequests {
  constructor(apiClient) {
    this.api = apiClient;
  }

  // Options
  searchOptions(entity, q = "") {
    return this.api.get("/options", { entity, q });
  }
  ensureOption(entity, name) {
    return this.api.post("/options/ensure", { entity, name });
  }

  // users
  createUser(data) {
    return this.api.post("/users", data);
  }
  listUsers() {
    return this.api.get("/users");
  }
  getUser(id) {
    return this.api.get(`/users/${id}`);
  } // jetzt vorhanden
  checkExists({ name }) {
    return this.api.get("/users/exists", { name });
  }

  // konten
  listKonten() {
    return this.api.get("/konten");
  }
  createKonto(data) {
    return this.api.post("/konten", data);
  }
  updateKonto(id, data) {
    return this.api.put(`/konten/${id}`, data);
  }
  deleteKonto(id) {
    return this.api.delete(`/konten/${id}`);
  }

  // kategorie
  listKategorie() {
    return this.api.get("/kategorie");
  }
  createKategorie(data) {
    return this.api.post("/kategorie", data);
  }
  updateKategorie(id, data) {
    return this.api.put(`/kategorie/${id}`, data);
  }
  deleteKategorie(id) {
    return this.api.delete(`/kategorie/${id}`);
  }

  // Securities
  listSecurities() {
    return this.api.get("/securities");
  }
  createSecurities(data) {
    return this.api.post("/securities", data);
  }
  updateSecurities(id, data) {
    return this.api.put(`/securities/${id}`, data);
  }
  deleteSecurities(id) {
    return this.api.delete(`/securities/${id}`);
  }

  // Receipt
  listReceipt() {
    return this.api.get("/receipt");
  }
  createReceipt(data) {
    return this.api.post("/receipt", data);
  }
  updateReceipt(id, data) {
    return this.api.put(`/receipt/${id}`, data);
  }
  deleteReceipt(id) {
    return this.api.delete(`/receipt/${id}`);
  }

  // Monthly Costs
  listMonthlyCosts() {
    return this.api.get("/monthlycosts");
  }
  createMonthlyCosts(data) {
    return this.api.post("/monthlycosts", data);
  }
  updateMonthlyCosts(id, data) {
    return this.api.put(`/monthlycosts/${id}`, data);
  }
  deleteMonthlyCosts(id) {
    return this.api.delete(`/monthlycosts/${id}`);
  }
  listMonthlyCostsExecution() {
    return this.api.get("/monthlycosts_execution");
  }
  createMonthlyCostsExecution(data) {
    return this.api.post("/monthlycosts_execution", data);
  }
  updateMonthlyCostsExecution(id, data) {
    return this.api.put(`/monthlycosts_execution/${id}`, data);
  }

  // Savings
  listSavings() {
    return this.api.get("/savings");
  }
  createSavings(data) {
    return this.api.post("/savings", data);
  }
  updateSavings(id, data) {
    return this.api.put(`/savings/${id}`, data);
  }
  deleteSavings(id) {
    return this.api.delete(`/savings/${id}`);
  }
  listSavingsExecution() {
    return this.api.get("/savings_execution");
  }

  // Depot Bewegung
  listDepotbewegung(params = {}) {
    return this.api.get("/depotbewegung", params);
  }
  createDepotBewegung(data) {
    return this.api.post("/depotbewegung", data);
  }
  updateDepotBewegung(id, data) {
    return this.api.put(`/depotbewegung/${id}`, data);
  }
  deleteDepotBewegung(id) {
    return this.api.delete(`/depotbewegung/${id}`);
  }

  // Depot Stand
  listDepotStand() {
    return this.api.get("/depotstand");
  }
  createDepotStand(data) {
    return this.api.post("/depotstand", data);
  }
  updateDepotStand(id, data) {
    return this.api.put(`/depotstand/${id}`, data);
  }
  deleteDepotStand(id) {
    return this.api.delete(`/depotstand/${id}`);
  }

  // Portfolio
  portfolioSummary(params = {}) {
    return this.api.get("/portfolio/summary", params);
  }

  //Market API
  marketLow({ ticker, date }) {
    return this.api.get("/market/low", { ticker, date });
  }
  marketHigh({ ticker, date }) {
    return this.api.get("/market/high", { ticker, date });
  }
}
