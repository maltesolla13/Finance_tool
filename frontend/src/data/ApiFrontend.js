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
  listKkategorie() {
    return this.api.get("/kategorie");
  }
  createKkategorie(data) {
    return this.api.post("/kategorie", data);
  }
  updateKkategorie(id, data) {
    return this.api.put(`/kategorie/${id}`, data);
  }
  deleteKkategorie(id) {
    return this.api.delete(`/kategorie/${id}`);
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
}
