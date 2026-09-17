// Services/autocomplete.js
import React from "react";
import Autocomplete, { createFilterOptions } from "@mui/material/Autocomplete";
import { TextField, Stack } from "@mui/material";

/* --------------------------------- Helpers -------------------------------- */

const baseFilter = createFilterOptions();

/** Liefert den Options-Eintrag zur id (oder null) */
const byId = (options = [], id) =>
  options.find((o) => (o?.id ?? o?.value) === id) ?? null;

/** Default-Label-Ermittlung für Options-Objekte */
const labelOf = (o) => {
  if (o == null) return "";
  if (typeof o === "string") return o;
  return (
    o.name ??
    o.title ??
    o.label ??
    o.email ??
    (o.first_name && o.last_name
      ? `${o.first_name} ${o.last_name}`.trim()
      : "") ??
    ""
  );
};

/**
 * Erstellt eine filterOptions-Funktion, die einen "Neu erstellen: <eingabe>"-Dummy
 * anhängt, wenn der eingegebene Text nicht mit einer existierenden Option exakt matcht.
 */
export const makeCreatableFilter = (createPrefix = "Neu erstellen") => {
  return (options, params) => {
    const filtered = baseFilter(options, params);
    const { inputValue } = params;
    const hasExact = options.some(
      (opt) => labelOf(opt).toLowerCase() === String(inputValue).toLowerCase()
    );

    if (inputValue !== "" && !hasExact) {
      filtered.push({
        id: "__create__",
        inputValue,
        name: `${createPrefix}: ${inputValue}`,
        _isCreate: true,
      });
    }
    return filtered;
  };
};

/** Einheitlicher onChange-Handler für Creatable-Autocompletes */
const handleCreatableChange =
  ({ onSelectId, onCreate }) =>
  async (_, value) => {
    if (!value) {
      onSelectId?.(null);
      return;
    }

    // 1) Nutzer wählt direkt eine bestehende Option (Objekt mit id)
    if (typeof value === "object" && value._isCreate !== true) {
      onSelectId?.(value.id ?? value.value ?? null);
      return;
    }

    // 2) Nutzer wählt "Neu erstellen: …"
    if (value?._isCreate && onCreate) {
      const name = value.inputValue ?? "";
      const created = await onCreate(name);
      // Erwartet wird ein Objekt mit { id, name } zurück
      onSelectId?.(created?.id ?? null);
      return;
    }

    // 3) Sicherheitsnetz (falls value ein String ist)
    if (typeof value === "string") {
      if (onCreate) {
        const created = await onCreate(value);
        onSelectId?.(created?.id ?? null);
      } else {
        onSelectId?.(null);
      }
    }
  };

/* --------------------------- Generic base component ------------------------ */

const BaseAutocomplete = ({
  label = "Auswahl",
  required = false,
  options = [],
  valueId,
  inputValue,
  onInputChange, // (string) => void
  onSelectId, // (id|null) => void
  filterOptions, // optional; bei creatable verwenden
  onChange, // optional; überschreibt Standard-Change-Handler
  getOptionLabel = labelOf,
  loading = false,
  disabled = false,
  fullWidth = true,
  error = false,
  helperText,
}) => {
  return (
    <Autocomplete
      options={options}
      value={byId(options, valueId)}
      inputValue={inputValue}
      onInputChange={(_, v) => onInputChange?.(v)}
      onChange={onChange ?? ((_, v) => onSelectId?.(v?.id ?? v?.value ?? null))}
      getOptionLabel={getOptionLabel}
      isOptionEqualToValue={(opt, val) =>
        (opt?.id ?? opt?.value) === (val?.id ?? val?.value)
      }
      filterOptions={filterOptions ?? ((x) => x)}
      loading={loading}
      disabled={disabled}
      fullWidth={fullWidth}
      renderInput={(params) => (
        <TextField
          {...params}
          label={label}
          required={required}
          error={error}
          helperText={helperText}
        />
      )}
    />
  );
};

/* ------------------------- Domain Autocompletes (std) ---------------------- */

export function UserAutocomplete(props) {
  // Label lässt sich überschreiben: label="User"
  return (
    <BaseAutocomplete
      filterOptions={baseFilter}
      label={props.label ?? "User"}
      required={props.required ?? true}
      {...props}
    />
  );
}

export function KontoAutocomplete(props) {
  return (
    <BaseAutocomplete
      filterOptions={baseFilter}
      label={props.label ?? "Konto"}
      required={props.required ?? true}
      {...props}
    />
  );
}

/* --------------------------- Creatable Autocompletes ----------------------- */

export function KategorieAutocomplete({
  onCreate, // async (name) => { id, name }
  ...props
}) {
  const filterOptions = makeCreatableFilter("Neu erstellen");
  return (
    <BaseAutocomplete
      label={props.label ?? "Kategorie"}
      required={props.required ?? true}
      filterOptions={filterOptions}
      onChange={handleCreatableChange({
        onSelectId: props.onSelectId,
        onCreate,
      })}
      {...props}
    />
  );
}

export function LadenAutocomplete({ onCreate, ...props }) {
  const filterOptions = makeCreatableFilter("Neu erstellen");
  return (
    <BaseAutocomplete
      label={props.label ?? "Laden"}
      required={props.required ?? true}
      filterOptions={filterOptions}
      onChange={handleCreatableChange({
        onSelectId: props.onSelectId,
        onCreate,
      })}
      {...props}
    />
  );
}

/* ------------------------------ Securities -------------------------------- */

export function SecurityAutocomplete(props) {
  // Gleiche Logik/Optik wie Konto/User, aber mit eigenem Default-Label.
  return (
    <BaseAutocomplete
      label={props.label ?? "Wertpapier (Optional)"}
      required={props.required ?? false}
      {...props}
    />
  );
}

/* ------------------------- Dual-Konto (Out/In) Combo ----------------------- */

export function DualKontoAutocomplete({
  options = [],
  outId,
  inId,
  outInput,
  inInput,
  onOutInput,
  onInInput,
  onOutSelect,
  onInSelect,
  disabled = false,
  loading = false,
  errorOut = false,
  errorIn = false,
  helperTextOut,
  helperTextIn,
  labels = {},
}) {
  return (
    <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
      <KontoAutocomplete
        label={labels.out ?? "Ausgangskonto"}
        options={options}
        valueId={outId}
        inputValue={outInput}
        onInputChange={onOutInput}
        onSelectId={onOutSelect}
        disabled={disabled}
        loading={loading}
        required={false}
        error={errorOut}
        helperText={helperTextOut}
      />
      <KontoAutocomplete
        label={labels.in ?? "Eingangskonto"}
        options={options}
        valueId={inId}
        inputValue={inInput}
        onInputChange={onInInput}
        onSelectId={onInSelect}
        disabled={disabled}
        loading={loading}
        required={false}
        error={errorIn}
        helperText={helperTextIn}
      />
    </Stack>
  );
}

/* --------------------------------- Exports -------------------------------- */

export default {
  BaseAutocomplete,
  makeCreatableFilter,
  UserAutocomplete,
  KontoAutocomplete,
  KategorieAutocomplete,
  LadenAutocomplete,
  SecurityAutocomplete,
  DualKontoAutocomplete,
};
