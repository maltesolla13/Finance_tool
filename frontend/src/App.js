import { ColorModeContext, useMode } from "./theme";
import { CssBaseline, ThemeProvider } from "@mui/material";
import { Routes, Route } from "react-router-dom";
import Topbar from "./scenes/global/Topbar";
import Sidebar from "./scenes/global/Sidebar";
import Dashboard from "./scenes/dashboard";
import AddAccount from "./scenes/forms/addaccounts";
import Accounts from "./scenes/accounts";
import AddReceipt from "./scenes/forms/addreceipt";
import AddUser from "./scenes/forms/adduser";
import AddSecurities from "./scenes/forms/addsecurities";
import AddMonthlyCosts from "./scenes/forms/addmonthlycosts";
import AddSavings from "./scenes/forms/addsavings";
import BuySellSecurities from "./scenes/forms/buysellsecurities";
import Portfolio from "./scenes/portfolio/home";
// import Perfomrance from "./scenes/portfolio/performance";
// import Development from "./scenes/portfolio/development";

// import Account from "./scenes/account/home";
// import MonthlyCost from "./scenes/monthlycost/home";
// import Distribution from "./scenes/distribution/home";

function App() {
  const [theme, colorMode] = useMode();

  return (
    <ColorModeContext.Provider value={colorMode}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <div className="app">
          <Sidebar />
          <main className="content">
            <Topbar />
            <Routes>
              <Route path="/" element={<Dashboard />} />
              {/* <Route path="/forms" element={<Input/>}/> */}
              <Route path="/forms/adduser" element={<AddUser />} />
              <Route path="/forms/addaccount" element={<AddAccount />} />
              <Route path="/forms/addreceipt" element={<AddReceipt />} />
              <Route
                path="/forms/addmonthlycosts"
                element={<AddMonthlyCosts />}
              />
              <Route path="/forms/addsecurities" element={<AddSecurities />} />
              <Route path="/forms/addsavings" element={<AddSavings />} />
              <Route
                path="/forms/buysellsecurities"
                element={<BuySellSecurities />}
              />
              <Route path="/accounts" element={<Accounts />} />
              <Route path="/portfolio" element={<Portfolio />} />
              {/* <Route path="/monthlycost" element={<MonthlyCost/>}/> />*/}
              {/* <Route path="/savings" element={<Distribution/>}/> />*/}
            </Routes>
          </main>
        </div>
      </ThemeProvider>
    </ColorModeContext.Provider>
  );
}

export default App;
