import { useState } from "react";
import {
  Sidebar as ProSidebar,
  Menu,
  MenuItem,
  SubMenu,
  sidebarClasses,
} from "react-pro-sidebar";
import { Box, IconButton, Typography, useTheme } from "@mui/material";
import { Link, useLocation } from "react-router-dom";
import { tokens } from "../../theme";
import MenuOutlinedIcon from "@mui/icons-material/MenuOutlined";
import HomeOutlinedIcon from "@mui/icons-material/HomeOutlined";
import CreateOutlinedIcon from "@mui/icons-material/CreateOutlined"; //Eingabe
import PersonAddOutlinedIcon from "@mui/icons-material/PersonAddOutlined"; //User
import AddCardOutlinedIcon from "@mui/icons-material/AddCardOutlined"; //Konto
import ReceiptLongOutlinedIcon from "@mui/icons-material/ReceiptLongOutlined"; //Einkauf
import PaymentsOutlinedIcon from "@mui/icons-material/PaymentsOutlined"; //Fixkosten
import AddCircleOutlineOutlinedIcon from "@mui/icons-material/AddCircleOutlineOutlined"; //Wertpapier

import ShowChartOutlinedIcon from "@mui/icons-material/ShowChartOutlined"; //Portfolio

import AccountBalanceOutlinedIcon from "@mui/icons-material/AccountBalanceOutlined"; //Account
import AccountBalanceWalletOutlinedIcon from "@mui/icons-material/AccountBalanceWalletOutlined"; //Konto

import PriceChangeOutlinedIcon from "@mui/icons-material/PriceChangeOutlined"; //MonthlyCost

import SavingsOutlinedIcon from "@mui/icons-material/SavingsOutlined"; //Sparen
import PriceCheckOutlinedIcon from "@mui/icons-material/PriceCheckOutlined"; //PriceCheck

const Item = ({ title, to, icon, selected, setSelected }) => {
  const theme = useTheme();
  const colors = tokens(theme.palette.mode);
  return (
    <MenuItem
      active={selected === title}
      icon={icon}
      onClick={() => setSelected(title)}
      component={<Link to={to} />}
    >
      <Typography component="span" color="inherit">
        {title}
      </Typography>
    </MenuItem>
  );
};

const Sidebar = () => {
  const theme = useTheme();
  const colors = tokens(theme.palette.mode);
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [selected, setSelected] = useState("Dashboard");
  const { pathname } = useLocation();
  const HOVER = "#868dfb";
  const ACTIVE = "#6870fa";
  // small helper
  const isOn = (path) => pathname === path || pathname.startsWith(path + "/");

  return (
    <Box>
      <ProSidebar
        collapsed={isCollapsed}
        transitionDuration={300}
        rootStyles={{
          height: "100vh",
          [`.${sidebarClasses.container}`]: {
            backgroundColor: colors.primary[400],
            color: colors.grey[100],
          },
        }}
      >
        <Menu
          menuItemStyles={{
            button: ({ active }) => ({
              padding: "5px 35px 5px 20px",
              backgroundColor: "transparent",
              color: active ? ACTIVE : colors.grey[100],
              "&:hover": {
                backgroundColor: "transparent",
                color: HOVER,
              },
            }),
            subMenuContent: () => ({
              backgroundColor: colors.primary[800],
            }),
            icon: { color: "inherit", backgroundColor: "transparent" },
            label: { color: "inherit" },
          }}
        >
          {/* LOGO AND MENU ICON */}
          <MenuItem
            onClick={() => setIsCollapsed(!isCollapsed)}
            icon={isCollapsed ? <MenuOutlinedIcon /> : undefined}
            style={{
              margin: "10px 0 20px 0",
              color: colors.grey[100],
            }}
          >
            {!isCollapsed && (
              <Box
                display="flex"
                justifyContent="space-between"
                alignItems="center"
                ml="15px"
              >
                <Typography variant="h3" color={colors.grey[100]}>
                  Finance Tool
                </Typography>
                <IconButton onClick={() => setIsCollapsed(!isCollapsed)}>
                  <MenuOutlinedIcon />
                </IconButton>
              </Box>
            )}
          </MenuItem>

          {/* USER */}
          {!isCollapsed && (
            <Box mb="25px">
              <Box display="flex" justifyContent="center" alignItems="center">
                <img
                  alt="profile-user"
                  width="100px"
                  height="100px"
                  src={`../../assets/user.png`}
                  style={{ cursor: "pointer", borderRadius: "50%" }}
                />
              </Box>

              <Box textAlign="center">
                <Typography
                  variant="h2"
                  color={colors.grey[100]}
                  fontWeight="bold"
                  sx={{ m: "10px 0 0 0" }}
                >
                  Malte
                </Typography>
                <Typography variant="h5" color={colors.greenAccent[500]}>
                  VP Fancy Admin
                </Typography>
              </Box>
            </Box>
          )}

          {/* MENU ITEMS */}
          <Box paddingLeft={isCollapsed ? undefined : "10%"}>
            {/* Dashboard */}
            <Item
              title="Dashboard"
              to="/"
              icon={<HomeOutlinedIcon />}
              selected={selected}
              setSelected={setSelected}
            />

            {/* FORMS */}
            <SubMenu
              label="Forms"
              icon={<CreateOutlinedIcon />}
              defaultOpen={isOn("/forms")}
            >
              <Item
                title="Add new User"
                to="/forms/adduser"
                icon={<PersonAddOutlinedIcon />}
                selected={selected}
                setSelected={setSelected}
              />
              <Item
                title="Add new Account"
                to="/forms/addaccount"
                icon={<AddCardOutlinedIcon />}
                selected={selected}
                setSelected={setSelected}
              />
              <Item
                title="Add new Receipt"
                to="/forms/receipt"
                icon={<ReceiptLongOutlinedIcon />}
                selected={selected}
                setSelected={setSelected}
              />
              <Item
                title="Add Monthly Costs"
                to="/forms/addmonthlycosts"
                icon={<PaymentsOutlinedIcon />}
                selected={selected}
                setSelected={setSelected}
              />
              <Item
                title="Add new Securities"
                to="/forms/securities"
                icon={<AddCircleOutlineOutlinedIcon />}
                selected={selected}
                setSelected={setSelected}
              />
            </SubMenu>

            {/* ACCOUNTS */}
            <Item
              title="Accounts"
              to="/accounts"
              icon={<AccountBalanceOutlinedIcon />}
              selected={selected}
              setSelected={setSelected}
            />
            <Item
              title="Portfolio"
              to="/portfolio"
              icon={<ShowChartOutlinedIcon />}
              selected={selected}
              setSelected={setSelected}
            />
            <Item
              title="Monthly Costs"
              to="/monthlycost"
              icon={<PriceChangeOutlinedIcon />}
              selected={selected}
              setSelected={setSelected}
            />
            <Item
              title="Savings"
              to="/savings"
              icon={<SavingsOutlinedIcon />}
              selected={selected}
              setSelected={setSelected}
            />
          </Box>
        </Menu>
      </ProSidebar>
    </Box>
  );
};

export default Sidebar;
