import { useEffect, useMemo, useState } from "react";
import { MenuItem, SubMenu } from "react-pro-sidebar";
import { Link, useLocation } from "react-router-dom";
import AccountBalanceOutlinedIcon from "@mui/icons-material/AccountBalanceOutlined";
import AccountBalanceWalletOutlinedIcon from "@mui/icons-material/AccountBalanceWalletOutlined";
import PersonOutlineIcon from "@mui/icons-material/PersonOutline";
import { ApiClient } from "../../data/ApiClient";
import { ApiRequests } from "../../data/ApiFrontend";

export default function AccountsMenu() {
  const api = useMemo(() => new ApiRequests(new ApiClient()), []);
  const { pathname, search } = useLocation();
  const [users, setUsers] = useState([]);
  const [accounts, setAccounts] = useState([]);
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
    Promise.all([api.listUsers(), api.listKonten()])
      .then(([nextUsers, nextAccounts]) => {
        if (!active) return;
        setUsers(
          [...nextUsers].sort((a, b) => a.name.localeCompare(b.name, "de")),
        );
        setAccounts(
          [...nextAccounts].sort((a, b) => a.name.localeCompare(b.name, "de")),
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
      {loading && <MenuItem disabled>Konten werden geladen...</MenuItem>}
      {error ? (
        <MenuItem onClick={() => setRevision((value) => value + 1)}>
          Ladefehler - erneut versuchen
        </MenuItem>
      ) : (
        users.map((user) => {
          const assigned = accounts.filter((account) =>
            account.user_ids?.includes(user.id),
          );
          return (
            <SubMenu
              key={user.id}
              label={user.name}
              icon={<PersonOutlineIcon />}
            >
              {assigned.length ? (
                assigned.map((account) => (
                  <MenuItem
                    key={account.id}
                    icon={<AccountBalanceWalletOutlinedIcon />}
                    active={
                      pathname === "/accounts" &&
                      Number(new URLSearchParams(search).get("konto")) ===
                        account.id
                    }
                    component={<Link to={`/accounts?konto=${account.id}`} />}
                  >
                    {account.name}
                  </MenuItem>
                ))
              ) : (
                <MenuItem disabled>Keine Konten zugeordnet</MenuItem>
              )}
            </SubMenu>
          );
        })
      )}
      {!loading && !error && !users.length && (
        <MenuItem disabled>Noch keine User angelegt</MenuItem>
      )}
      <MenuItem component={<Link to="/accounts" />}>Kontenübersicht</MenuItem>
    </SubMenu>
  );
}
