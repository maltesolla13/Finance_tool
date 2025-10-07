export class ApiRequests {
  constructor(apiClient) {
    this.api = apiClient;
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
  } // jetzt vorhanden

  // konten (dein Backend hat voll CRUD)
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
}
