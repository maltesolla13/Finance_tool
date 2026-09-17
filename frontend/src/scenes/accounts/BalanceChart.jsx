import { Box, Typography, useTheme } from "@mui/material";
import { tokens } from "../../theme";

export const euro = (value) =>
  new Intl.NumberFormat("de-DE", {
    style: "currency",
    currency: "EUR",
  }).format(value ?? 0);
export const dateDE = (value) =>
  value ? value.slice(0, 10).split("-").reverse().join(".") : "";

export default function BalanceChart({
  data,
  label = "Guthabenentwicklung in Euro",
}) {
  const colors = tokens(useTheme().palette.mode);
  if (!data.length)
    return <Typography>Keine Guthabenentwicklung vorhanden.</Typography>;
  const width = 900,
    height = 280,
    left = 110,
    right = 20,
    top = 20,
    bottom = 40;
  const times = data.map((point) => Date.parse(point.date));
  const first = times[0],
    last = times[times.length - 1];
  const values = data.map((point) => point.balance);
  const min = Math.min(0, ...values),
    max = Math.max(0, ...values);
  const span = max - min || 1;
  const x = (index) =>
    left +
    ((times[index] - first) / (last - first || 1)) * (width - left - right);
  const y = (value) =>
    top + (1 - (value - min) / span) * (height - top - bottom);
  // Step line: a balance changes on booking days, not gradually between them.
  const path = data
    .map((point, index) =>
      index === 0
        ? `M ${x(index)} ${y(point.balance)}`
        : `H ${x(index)} V ${y(point.balance)}`,
    )
    .join(" ");
  return (
    <Box sx={{ width: "100%", overflowX: "auto" }}>
      <svg
        viewBox={`0 0 ${width} ${height}`}
        role="img"
        aria-label={label}
        style={{ width: "100%", minWidth: 420 }}
      >
        {[0, 0.25, 0.5, 0.75, 1].map((part) => {
          const value = min + part * span;
          return (
            <g key={part}>
              <line
                x1={left}
                x2={width - right}
                y1={y(value)}
                y2={y(value)}
                stroke={colors.grey[700]}
                strokeDasharray="4 4"
              />
              <text
                x={left - 10}
                y={y(value) + 4}
                textAnchor="end"
                fill={colors.grey[200]}
                fontSize="12"
              >
                {euro(value)}
              </text>
            </g>
          );
        })}
        <path
          d={path}
          fill="none"
          stroke={colors.greenAccent[500]}
          strokeWidth="3"
        />
        {data.map((point, index) => (
          <circle
            key={point.date}
            cx={x(index)}
            cy={y(point.balance)}
            r="4"
            fill={colors.greenAccent[400]}
            tabIndex={0}
            aria-label={`${dateDE(point.date)}: ${euro(point.balance)}`}
          >
            <title>
              {dateDE(point.date)}: {euro(point.balance)}
            </title>
          </circle>
        ))}
        <text x={left} y={height - 10} fill={colors.grey[200]} fontSize="12">
          {dateDE(data[0].date)}
        </text>
        <text
          x={width - right}
          y={height - 10}
          textAnchor="end"
          fill={colors.grey[200]}
          fontSize="12"
        >
          {dateDE(data[data.length - 1].date)}
        </text>
      </svg>
    </Box>
  );
}
