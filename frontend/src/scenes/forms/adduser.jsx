import { useEffect, useMemo, useState, useCallback } from "react";
import {
  Box,
  TextField,
  Button,
  Stack,
  Alert,
  LinearProgress,
  Typography,
  Grid,
  Paper,
  List,
  ListItem,
  ListItemText,
  useTheme,
} from "@mui/material";
//import { useTheme } from "@mui/material/styles";
import { ApiClient } from "../../data/ApiClient";
import { ApiRequests } from "../../data/ApiFrontend";
import { ApiError } from "../../data/ApiErrors";
import { tokens } from "../../theme";
import Header from "../../components/Header";

const AddUser = () => {
  const api = useMemo(() => new ApiRequests(new ApiClient()), []);

  const theme = useTheme();
  const colors = tokens(theme.palette.mode);
  const [name, setName] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [users, setUsers] = useState([]);
  const loadUsers = useCallback(async () => {
    try {
      const data = await api.listUsers();
      setUsers(Array.isArray(data) ? data : []);
    } catch (e) {
      console.warn("listUsers failed", e);
      setUsers([]);
    }
  }, [api]);

  useEffect(() => {
    loadUsers();
  }, [loadUsers]);
  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setSuccess("");

    const trimmed = name.trim();
    if (!trimmed) {
      setError("Name Eingeben");
      return;
    }

    setLoading(true);
    try {
      await api.createUser({ name: trimmed });
      setSuccess(`User "${trimmed}" wurde angelegt.`);
      setName("");
      await loadUsers();
    } catch (e) {
      if (e instanceof ApiError) {
        if (e.status === 409) setError("Name existiert ebreits");
        else setError(e.message || "Fehler beim Anlegen");
      } else {
        setError("Unbekannter Fehler.");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <Box m="20px" component="section" sx={{ p: 2 }}>
      <Box display="flex" justifyContent="space-between" alignItems="center">
        <Header title="New User" subtitle="Add a newe User" />
      </Box>

      {loading && <LinearProgress sx={{ mb: 2 }} />}

      {error && (
        <Alert severity="error" sx={{ mb: 2, color: colors.redAccent[500] }}>
          {error}
        </Alert>
      )}

      {success && (
        <Alert
          severity="success"
          sx={{ mb: 2, color: colors.greenAccent[500] }}
        >
          {success}
        </Alert>
      )}

      {/* Zweispaltiges Layout */}
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Paper
            sx={{
              p: 3,
              borderRadius: 3,
              bgcolor: colors?.primary?.[400] ?? "background.paper",
              border: "1px solid",
              borderColor: "divider",
            }}
          >
            <Typography variant="h6" sx={{ mb: 2 }}>
              Benutzer hinzufügen
            </Typography>
            <Box component="form" onSubmit={handleSubmit}>
              <Stack direction="row" spacing={2}>
                <TextField
                  label="Name"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  fullWidth
                  sx={{
                    "& .MuiOutlinedInput-notchedOutline": {
                      borderColor: colors?.grey?.[400],
                    },
                    "&:hover .MuiOutlinedInput-notchedOutline": {
                      borderColor: "#868dfb",
                    },
                    "& .MuiOutlinedInput-root.Mui-focused .MuiOutlinedInput-notchedOutline":
                      { borderColor: colors?.greenAccent?.[400] },
                    "& .MuiInputLabel-root.Mui-focused": {
                      color: colors?.greenAccent?.[400],
                    },
                  }}
                />
                <Button type="submit" variant="contained">
                  Anlegen
                </Button>
              </Stack>
            </Box>
          </Paper>
        </Grid>

        <Grid item xs={12} md={6}>
          <Paper
            sx={{
              p: 3,
              borderRadius: 3,
              bgcolor: colors?.primary?.[400] ?? "background.paper",
              border: "1px solid",
              borderColor: "divider",
            }}
          >
            <Typography variant="h6" sx={{ mb: 2 }}>
              Vorhandene User
            </Typography>
            {users.length === 0 ? (
              <Typography variant="body2" sx={{ opacity: 0.8 }}>
                Noch kein User vorhanden
              </Typography>
            ) : (
              <List dense>
                {users.map((u) => (
                  <ListItem
                    key={u.id}
                    sx={{
                      borderRadius: 2,
                      "&:hover": { backgroundColor: "action.hover" },
                    }}
                  >
                    <ListItemText
                      primary={u.name}
                      secondary={`ID: ${u.id}`}
                      primaryTypographyProps={{ color: "text.primary" }}
                      secondaryTypographyProps={{ color: "text.secondary" }}
                    />
                  </ListItem>
                ))}
              </List>
            )}
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default AddUser;
