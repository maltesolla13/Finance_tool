import { useEffect, useMemo, useState } from "react";
import { MenuItem, SubMenu } from "react-pro-sidebar";
import { Link, useLocation } from "react-router-dom";
import AccountBalanceOutlinedIcon from "@mui/icons-material/AccountBalanceOutlined";
import PersonOutlineIcon from "@mui/icons-material/PersonOutline";
import { ApiClient } from "../../data/ApiClient";
import { ApiRequests } from "../../data/ApiFrontend";

export default function AccountsMenu() {
  const api = useMemo(() => new ApiRequests(new ApiClient()), []);
  const { pathname, search } = useLocation();
  const [users, setUsers] = useState([]);
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(false);
  const [revision, setRevision] = useState(0);

  useEffect(() => {
    const refresh = () => setRevision((value) => value + 1);
    window.addEventListener("accounts-changed", refresh);
    return () => window.removeEventListener("accounts-changed", refresh);
  }, []);

  useEffect(() => {
    if (!open) return;
    let active = true;
    setLoading(true);
    setError(false);
    api
      .listUsers()
      .then((nextUsers) => {
        if (!active) return;
        setUsers(
          [...nextUsers].sort((a, b) => a.name.localeCompare(b.name, "de")),
        );
      })
      .catch(() => {
        if (active) setError(true);
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [api, open, revision, pathname]);

  return (
    <SubMenu
      label="Accounts"
      icon={<AccountBalanceOutlinedIcon />}
      open={open}
      onOpenChange={setOpen}
    >
      {loading && <MenuItem disabled>User werden geladen...</MenuItem>}
      {error ? (
        <MenuItem onClick={() => setRevision((value) => value + 1)}>
          Ladefehler - erneut versuchen
        </MenuItem>
      ) : (
        users.map((user) => (
          <MenuItem
            key={user.id}
            icon={<PersonOutlineIcon />}
            active={
              pathname === "/accounts" &&
              Number(new URLSearchParams(search).get("user")) === user.id
            }
            component={<Link to={`/accounts?user=${user.id}`} />}
          >
            {user.name}
          </MenuItem>
        ))
      )}
      {!loading && !error && !users.length && (
        <MenuItem disabled>Noch keine User angelegt</MenuItem>
      )}
    </SubMenu>
  );
}
