import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Alert,
  Autocomplete,
  Box,
  Checkbox,
  Chip,
  Grid,
  LinearProgress,
  Paper,
  Stack,
  TextField,
  ToggleButton,
  ToggleButtonGroup,
  Typography,
  useTheme,
} from "@mui/material";
import CheckBoxOutlineBlankIcon from "@mui/icons-material/CheckBoxOutlineBlank";
import CheckBoxIcon from "@mui/icons-material/CheckBox";
import Header from "../../components/Header";
import { tokens } from "../../theme";
import { ApiClient } from "../../data/ApiClient";
import { ApiRequests } from "../../data/ApiFrontend";

const PERIODS = [
  { value: "WEEK", label: "Woche" },
  { value: "MONTH", label: "Monat" },
  { value: "HALFYEAR", label: "Halbjahr" },
  { value: "YEAR", label: "Jahr" },
  { value: "5Y", label: "5 Jahre" },
  { value: "MAX", label: "Max" },
];

const SELECT_ALL = { id: "__all__", name: "Alle Konten" };

const euro = new Intl.NumberFormat("de-DE", {
  style: "currency",
  currency: "EUR",
});

const euroWhole = new Intl.NumberFormat("de-DE", {
  style: "currency",
  currency: "EUR",
  minimumFractionDigits: 0,
  maximumFractionDigits: 0,
});

const percent = new Intl.NumberFormat("de-DE", {
  minimumFractionDigits: 1,
  maximumFractionDigits: 1,
});

const fmtEuro = (v) => euro.format(Number(v || 0));
const fmtEuroWhole = (v) => euroWhole.format(Number(v || 0));
const fmtPct = (v) => `${percent.format(Number(v || 0))} %`;
const fmtShares = (v) =>
  new Intl.NumberFormat("de-DE", {
    minimumFractionDigits: 0,
    maximumFractionDigits: 6,
  }).format(Number(v || 0));

const PIE_COLORS = [
  "#4cceac",
  "#6870fa",
  "#f1b53f",
  "#db4f4a",
  "#7fc8f8",
  "#c77dff",
  "#8ac926",
  "#ff8fab",
];

const polarToCartesian = (cx, cy, radius, angle) => {
  const rad = ((angle - 90) * Math.PI) / 180;
  return {
    x: cx + radius * Math.cos(rad),
    y: cy + radius * Math.sin(rad),
  };
};

const describeArc = (cx, cy, radius, startAngle, endAngle) => {
  const start = polarToCartesian(cx, cy, radius, endAngle);
  const end = polarToCartesian(cx, cy, radius, startAngle);
  const largeArcFlag = endAngle - startAngle <= 180 ? "0" : "1";
  return [
    `M ${cx} ${cy}`,
    `L ${start.x} ${start.y}`,
    `A ${radius} ${radius} 0 ${largeArcFlag} 0 ${end.x} ${end.y}`,
    "Z",
  ].join(" ");
};

function InstrumentPieChart({ data = [] }) {
  const theme = useTheme();
  const colors = tokens(theme.palette.mode);
  const total = data.reduce((sum, item) => sum + Number(item.value || 0), 0);

  if (!data.length || total <= 0) {
    return (
      <Box height="100%" display="flex" alignItems="center" justifyContent="center">
        Keine Aufteilung vorhanden.
      </Box>
    );
  }

  let current = 0;
  const slices = data.map((item, index) => {
    const value = Number(item.value || 0);
    const angle = (value / total) * 360;
    const start = current;
    const end = current + angle;
    current = end;
    return {
      ...item,
      color: PIE_COLORS[index % PIE_COLORS.length],
      path: describeArc(170, 170, 130, start, end),
      labelPoint: polarToCartesian(170, 170, 92, start + angle / 2),
    };
  });

  return (
    <Box
      height="100%"
      display="flex"
      alignItems="center"
      justifyContent="center"
      sx={{ minHeight: 320 }}
    >
      <svg viewBox="0 0 340 340" width="100%" height="100%">
        {slices.map((slice) => (
          <g key={slice.id}>
            <path
              d={slice.path}
              fill={slice.color}
              stroke={colors.primary[500]}
              strokeWidth="3"
            />
            {Number(slice.percentage || 0) >= 6 && (
              <text
                x={slice.labelPoint.x}
                y={slice.labelPoint.y}
                textAnchor="middle"
                dominantBaseline="middle"
                fill="#ffffff"
                fontSize="13"
                fontWeight="700"
              >
                {fmtPct(slice.percentage)}
              </text>
            )}
          </g>
        ))}
        <circle cx="170" cy="170" r="68" fill={colors.primary[400]} />
        <text
          x="170"
          y="162"
          textAnchor="middle"
          fill={colors.grey[100]}
          fontSize="15"
          fontWeight="700"
        >
          Wert
        </text>
        <text
          x="170"
          y="184"
          textAnchor="middle"
          fill={colors.grey[300]}
          fontSize="12"
        >
          {fmtEuro(total)}
        </text>
      </svg>
    </Box>
  );
}

function LineChart({ series = [], height = 320, compact = false }) {
  const theme = useTheme();
  const colors = tokens(theme.palette.mode);
  const width = 900;
  const chartHeight = compact ? 210 : height;
  const pad = compact
    ? { top: 18, right: 16, bottom: 30, left: 80 }
    : { top: 22, right: 22, bottom: 42, left: 66 };
  const innerW = width - pad.left - pad.right;
  const innerH = chartHeight - pad.top - pad.bottom;

  const points = series.map((d, i) => ({
    ...d,
    xIndex: i,
    value: Number(d.value || 0),
    invested: Number(d.invested || 0),
  }));

  if (!points.length) {
    return (
      <Box
        height={chartHeight}
        display="flex"
        alignItems="center"
        justifyContent="center"
        color={colors.grey[300]}
      >
        Keine Daten im gewaehlten Zeitraum.
      </Box>
    );
  }

  const maxY = Math.max(
    1,
    ...points.flatMap((p) => [p.value, p.invested])
  );
  const xFor = (i) =>
    pad.left + (points.length === 1 ? innerW / 2 : (i / (points.length - 1)) * innerW);
  const yFor = (v) => pad.top + innerH - (v / maxY) * innerH;
  const pathFor = (key) =>
    points
      .map((p, i) => `${i === 0 ? "M" : "L"} ${xFor(i)} ${yFor(p[key])}`)
      .join(" ");
  const last = points[points.length - 1];
  const first = points[0];

  return (
    <Box sx={{ width: "100%", overflow: "hidden" }}>
      <svg viewBox={`0 0 ${width} ${chartHeight}`} width="100%" height={chartHeight}>
        <line
          x1={pad.left}
          y1={pad.top}
          x2={pad.left}
          y2={pad.top + innerH}
          stroke={colors.grey[600]}
        />
        <line
          x1={pad.left}
          y1={pad.top + innerH}
          x2={pad.left + innerW}
          y2={pad.top + innerH}
          stroke={colors.grey[600]}
        />
        {[0, 0.25, 0.5, 0.75, 1].map((t) => {
          const y = pad.top + innerH - innerH * t;
          return (
            <g key={t}>
              <line
                x1={pad.left}
                y1={y}
                x2={pad.left + innerW}
                y2={y}
                stroke={colors.primary[400]}
                strokeWidth="1"
              />
              <text
                x={pad.left - 10}
                y={y + 4}
                textAnchor="end"
                fill={colors.grey[300]}
                fontSize="12"
              >
                {fmtEuroWhole(maxY * t)}
              </text>
            </g>
          );
        })}
        <path
          d={pathFor("invested")}
          fill="none"
          stroke={colors.blueAccent[400]}
          strokeWidth="3"
        />
        <path
          d={pathFor("value")}
          fill="none"
          stroke={colors.greenAccent[400]}
          strokeWidth="3"
        />
        <circle cx={xFor(last.xIndex)} cy={yFor(last.value)} r="4" fill={colors.greenAccent[400]} />
        <circle cx={xFor(last.xIndex)} cy={yFor(last.invested)} r="4" fill={colors.blueAccent[400]} />
        <text x={pad.left} y={chartHeight - 8} fill={colors.grey[300]} fontSize="12">
          {first.date}
        </text>
        <text
          x={pad.left + innerW}
          y={chartHeight - 8}
          textAnchor="end"
          fill={colors.grey[300]}
          fontSize="12"
        >
          {last.date}
        </text>
      </svg>
      <Stack direction="row" spacing={2} justifyContent="center" sx={{ mt: -1 }}>
        <LegendSwatch color={colors.greenAccent[400]} label="Wert" />
        <LegendSwatch color={colors.blueAccent[400]} label="Kaufpreis" />
      </Stack>
    </Box>
  );
}

function LegendSwatch({ color, label }) {
  return (
    <Stack direction="row" spacing={0.75} alignItems="center">
      <Box sx={{ width: 12, height: 12, bgcolor: color, borderRadius: "2px" }} />
      <Typography variant="body2">{label}</Typography>
    </Stack>
  );
}

function Metric({ label, value, tone }) {
  const theme = useTheme();
  const colors = tokens(theme.palette.mode);
  const color =
    tone === "positive"
      ? colors.greenAccent[400]
      : tone === "negative"
      ? colors.redAccent[400]
      : colors.grey[100];
  return (
    <Box>
      <Typography variant="body2" color={colors.grey[300]}>
        {label}
      </Typography>
      <Typography variant="h4" color={color} fontWeight="700">
        {value}
      </Typography>
    </Box>
  );
}

const accountLabel = (option) => option?.name ?? "";

const Portfolio = () => {
  const theme = useTheme();
  const colors = tokens(theme.palette.mode);
  const api = useMemo(() => new ApiRequests(new ApiClient()), []);
  const [period, setPeriod] = useState("MAX");
  const [summary, setSummary] = useState(null);
  const [selectedIds, setSelectedIds] = useState([]);
  const [initialized, setInitialized] = useState(false);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");

  const accounts = useMemo(() => summary?.accounts ?? [], [summary]);
  const selectedAccounts = accounts.filter((a) => selectedIds.includes(a.id));
  const allSelected = accounts.length > 0 && selectedIds.length === accounts.length;

  const load = useCallback(
    async ({ nextPeriod = period, nextIds = selectedIds } = {}) => {
      setLoading(true);
      setErr("");
      try {
        const data = await api.portfolioSummary({
          period: nextPeriod,
          account_ids: nextIds.join(","),
        });
        setSummary(data);
        if (!initialized) {
          setSelectedIds(data.selected_account_ids ?? []);
          setInitialized(true);
        }
      } catch (e) {
        console.warn(e);
        setErr("Portfolio konnte nicht geladen werden.");
      } finally {
        setLoading(false);
      }
    },
    [api, period, selectedIds, initialized]
  );

  useEffect(() => {
    load();
  }, [load]);

  const accountOptions = useMemo(() => [SELECT_ALL, ...accounts], [accounts]);

  const onAccountsChange = (_, value, reason, details) => {
    if (details?.option?.id === SELECT_ALL.id) {
      const next = allSelected ? [] : accounts.map((a) => a.id);
      setSelectedIds(next);
      load({ nextIds: next });
      return;
    }
    const next = value
      .filter((v) => v.id !== SELECT_ALL.id)
      .map((v) => v.id);
    setSelectedIds(next);
    load({ nextIds: next });
  };

  const totals = summary?.totals ?? {};
  const developmentTone =
    Number(totals.development || 0) >= 0 ? "positive" : "negative";
  const pieData = summary?.allocation ?? [];
  const assets = summary?.assets ?? [];

  return (
    <Box m="20px">
      <Stack
        direction={{ xs: "column", md: "row" }}
        spacing={2}
        alignItems={{ xs: "stretch", md: "center" }}
        justifyContent="space-between"
      >
        <Header title="Portfolio" subtitle="Depotentwicklung und Positionen" />
        <Autocomplete
          multiple
          disableCloseOnSelect
          options={accountOptions}
          value={selectedAccounts}
          getOptionLabel={accountLabel}
          isOptionEqualToValue={(a, b) => a.id === b.id}
          onChange={onAccountsChange}
          sx={{ minWidth: { xs: "100%", md: 360 } }}
          renderTags={(value, getTagProps) =>
            value.length === accounts.length ? (
              <Chip label="Alle Konten" size="small" />
            ) : (
              value.map((option, index) => (
                <Chip
                  label={option.name}
                  size="small"
                  {...getTagProps({ index })}
                  key={option.id}
                />
              ))
            )
          }
          renderOption={(props, option) => {
            const checked =
              option.id === SELECT_ALL.id
                ? allSelected
                : selectedIds.includes(option.id);
            return (
              <li {...props}>
                <Checkbox
                  icon={<CheckBoxOutlineBlankIcon fontSize="small" />}
                  checkedIcon={<CheckBoxIcon fontSize="small" />}
                  checked={checked}
                  sx={{ mr: 1 }}
                />
                {option.name}
              </li>
            );
          }}
          renderInput={(params) => (
            <TextField {...params} label="Depotkonten" placeholder="Auswahl" />
          )}
        />
      </Stack>

      {loading && <LinearProgress sx={{ mb: 2 }} />}
      {err && <Alert severity="error" sx={{ mb: 2 }}>{err}</Alert>}

      <Paper sx={{ p: 2, mb: 2 }}>
        <Stack
          direction={{ xs: "column", md: "row" }}
          spacing={2}
          alignItems={{ xs: "stretch", md: "center" }}
          justifyContent="space-between"
          sx={{ mb: 2 }}
        >
          <Typography variant="h5" fontWeight="700">
            Depotentwicklung
          </Typography>
          <ToggleButtonGroup
            size="small"
            exclusive
            value={period}
            onChange={(_, value) => {
              if (!value) return;
              setPeriod(value);
              load({ nextPeriod: value });
            }}
          >
            {PERIODS.map((p) => (
              <ToggleButton key={p.value} value={p.value}>
                {p.label}
              </ToggleButton>
            ))}
          </ToggleButtonGroup>
        </Stack>
        <Grid container spacing={2}>
          <Grid item xs={12} lg={9}>
            <LineChart series={summary?.overview ?? []} height={360} />
          </Grid>
          <Grid item xs={12} lg={3}>
            <Stack spacing={2} sx={{ height: "100%", justifyContent: "center" }}>
              <Metric label="Angelegter Betrag" value={fmtEuro(totals.invested)} />
              <Metric label="Vermoegen" value={fmtEuro(totals.value)} />
              <Metric
                label="Entwicklung"
                value={`${fmtEuro(totals.development)} (${fmtPct(
                  totals.development_pct
                )})`}
                tone={developmentTone}
              />
            </Stack>
          </Grid>
        </Grid>
      </Paper>

      <Paper sx={{ p: 2, mb: 2 }}>
        <Typography variant="h5" fontWeight="700" sx={{ mb: 2 }}>
          Depotaufteilung
        </Typography>
        <Grid container spacing={2}>
          <Grid item xs={12} md={7}>
            <Box height={340}>
              <InstrumentPieChart data={pieData} />
            </Box>
          </Grid>
          <Grid item xs={12} md={5}>
            <Stack spacing={1.5}>
              {pieData.map((item, index) => (
                <Stack
                  key={item.id}
                  direction="row"
                  alignItems="center"
                  justifyContent="space-between"
                  spacing={3}
                  sx={{ borderBottom: `1px solid ${colors.primary[400]}`, pb: 1 }}
                >
                  <Stack direction="row" spacing={1} alignItems="center">
                    <Box
                      sx={{
                        width: 12,
                        height: 12,
                        bgcolor: PIE_COLORS[index % PIE_COLORS.length],
                        borderRadius: "2px",
                      }}
                    />
                    <Typography variant="body1" sx={{ minWidth: 120 }}>
                      {item.label}
                    </Typography>
                  </Stack>
                  <Typography
                    variant="body1"
                    fontWeight="700"
                    textAlign="right"
                    sx={{ minWidth: 190 }}
                  >
                    {fmtPct(item.percentage)} · {fmtEuro(item.value)}
                  </Typography>
                </Stack>
              ))}
            </Stack>
          </Grid>
        </Grid>
      </Paper>

      <Grid container spacing={2}>
        {assets.map((asset) => {
          const dev = Number(asset.value || 0) - Number(asset.invested || 0);
          const devPct = asset.invested ? (dev / asset.invested) * 100 : 0;
          return (
            <Grid item xs={12} xl={6} key={asset.security_id}>
              <Paper sx={{ p: 2, height: "100%" }}>
                <Typography variant="h5" fontWeight="700" sx={{ mb: 2 }}>
                  {asset.name}
                </Typography>
                <Grid container spacing={2}>
                  <Grid item xs={12} md={7}>
                    <LineChart series={asset.series} compact />
                  </Grid>
                  <Grid item xs={12} md={5}>
                    <Stack spacing={1.5}>
                      <Metric label="Anteile" value={fmtShares(asset.shares)} />
                      <Metric label="Wert" value={fmtEuro(asset.value)} />
                      <Metric label="Einkaufspreis" value={fmtEuro(asset.invested)} />
                      <Metric
                        label="Entwicklung"
                        value={`${fmtEuro(dev)} (${fmtPct(devPct)})`}
                        tone={dev >= 0 ? "positive" : "negative"}
                      />
                      <Metric
                        label="Aktiver Sparplan"
                        value={fmtEuro(asset.active_savings)}
                      />
                      <Metric
                        label="Sparplanausfuehrung"
                        value={asset.next_execution_date || "-"}
                      />
                    </Stack>
                  </Grid>
                </Grid>
              </Paper>
            </Grid>
          );
        })}
      </Grid>
    </Box>
  );
};

export default Portfolio;
