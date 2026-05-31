import * as DateUtils from "./date.utils";

const toDateInput = (value) => (value || "").slice(0, 10);

const executionPayloadFromEdit = (editItem) => ({
  monthlycost_id: editItem.monthlycost_id ?? editItem.id,
  user_id: editItem.user_id,
  name: editItem.name,
  kategorie_id: editItem.kategorie_id,
  execution_datum: `${editItem.execution_datum_ui}T00:00:00`,
  status: editItem.status || "PENDING",
  ausgangs_konto_id: editItem.ausgangs_konto_id ?? null,
  eingangs_konto_id: editItem.eingangs_konto_id ?? null,
  securities_id: editItem.securities_id ?? null,
  anteil: editItem.anteil ?? null,
  betrag: editItem.betrag ?? null,
});

const monthlyCostPayloadFromEdit = (editItem) => {
  const nextDue = DateUtils.nextDueFromRepeat({
    startDate: editItem.start_datum_ui,
    repeatType: editItem.repeat_type,
    customInterval: editItem.custom_interval,
    customUnit: editItem.custom_unit,
  });

  return {
    user_id: editItem.user_id,
    name: editItem.name,
    kategorie_id: editItem.kategorie_id,
    start_datum: `${editItem.start_datum_ui}T00:00:00`,
    next_due: `${nextDue || editItem.execution_datum_ui}T00:00:00`,
    active: !!editItem.active,
    ausgangs_konto_id: editItem.ausgangs_konto_id ?? null,
    eingangs_konto_id: editItem.eingangs_konto_id ?? null,
    securities_id: editItem.securities_id ?? null,
    anteil: editItem.anteil ?? null,
    betrag: editItem.betrag ?? null,
    repeat_type: editItem.repeat_type || "MONTHLY",
    custom_interval:
      (editItem.repeat_type || "MONTHLY") === "CUSTOM"
        ? Number(editItem.custom_interval)
        : null,
    custom_unit:
      (editItem.repeat_type || "MONTHLY") === "CUSTOM"
        ? editItem.custom_unit || "MONTHS"
        : null,
  };
};

export function openEditByEvent(
  event,
  { monthlyCosts, setEditItem, setEditOpen },
) {
  const xp = event.extendedProps || event;
  if (!xp?.editable) return;

  const monthlycostId = xp.monthlycost_id ?? xp.id;
  const sourceMonthlyCost = monthlyCosts.find(
    (x) => Number(x.id) === Number(monthlycostId),
  );
  const executionDate = toDateInput(xp.execution_datum || event.start);

  setEditItem({
    ...(sourceMonthlyCost || {}),
    ...xp,
    id: xp.id,
    monthlycost_id: monthlycostId,
    execution_id:
      xp.__source === "monthlycost_execution" ? Number(xp.id) : null,
    edit_scope: "single",
    start_datum_ui: toDateInput(
      sourceMonthlyCost?.start_datum || xp.start_datum,
    ),
    next_due_ui: toDateInput(sourceMonthlyCost?.next_due || xp.next_due),
    execution_datum_ui: executionDate,
  });
  setEditOpen(true);
}

export function openEditById(
  rawId,
  { monthlyCosts, setEditItem, setEditOpen },
) {
  const id = Number(rawId);
  const s = monthlyCosts.find((x) => Number(x.id) === id);
  if (!s) return;
  openEditByEvent(
    {
      ...s,
      extendedProps: {
        ...s,
        monthlycost_id: s.id,
        execution_datum: s.next_due,
        __source: "monthlycost_projection",
        editable: true,
      },
    },
    { monthlyCosts, setEditItem, setEditOpen },
  );
}

export function buildEditHandlers({ monthlyCosts, setEditItem, setEditOpen }) {
  const onEventClick = (clickInfo) => {
    openEditByEvent(clickInfo.event, {
      monthlyCosts,
      setEditItem,
      setEditOpen,
    });
  };
  return { onEventClick };
}

function validateEditItem(editItem) {
  const errs = {};
  const single = editItem?.edit_scope !== "following";
  const executionDate = (editItem?.execution_datum_ui || "").trim();
  const startDate = (editItem?.start_datum_ui || "").trim();

  if (!executionDate) {
    errs.execution_datum_ui = "Termin-Datum ist erforderlich.";
  } else if (
    !/^\d{4}-\d{2}-\d{2}$/.test(executionDate) ||
    Number.isNaN(new Date(executionDate).getTime())
  ) {
    errs.execution_datum_ui = "Ungueltiges Datum (Format: YYYY-MM-DD).";
  }

  if (!single) {
    if (!startDate) {
      errs.start_datum_ui = "Start-Datum ist erforderlich.";
    } else if (
      !/^\d{4}-\d{2}-\d{2}$/.test(startDate) ||
      Number.isNaN(new Date(startDate).getTime())
    ) {
      errs.start_datum_ui = "Ungueltiges Datum (Format: YYYY-MM-DD).";
    }
    if ((editItem?.repeat_type || "MONTHLY") === "CUSTOM") {
      const interval = Number(editItem?.custom_interval);
      if (!Number.isInteger(interval) || interval <= 0) {
        errs.custom_interval =
          "Bei benutzerdefinierter Wiederholung eine ganze Anzahl groesser 0 eingeben.";
      }
    }
  }
  return errs;
}

export async function saveEditItem(
  editItem,
  {
    api,
    setOk,
    closeEdit,
    loadMonthlyCosts,
    loadMonthlyCostsExecutions,
    setErr,
    setMonthlyCosts,
    setMonthlyCostsExecutions,
    setEditErrors,
    monthlyCostsExecutions = [],
  },
) {
  const errs = validateEditItem(editItem);
  if (Object.keys(errs).length) {
    setEditErrors?.(errs);
    setErr?.("Bitte die markierten Felder korrigieren.");
    return;
  }
  setEditErrors?.({});

  try {
    const scope = editItem.edit_scope || "single";
    const executionPayload = executionPayloadFromEdit(editItem);

    if (scope === "single") {
      if (editItem.execution_id) {
        await api.updateMonthlyCostsExecution(
          editItem.execution_id,
          executionPayload,
        );
      } else {
        await api.createMonthlyCostsExecution(executionPayload);
      }
      setOk?.("Termin aktualisiert.");
    } else {
      const monthlycostId = editItem.monthlycost_id ?? editItem.id;
      const monthlyPayload = monthlyCostPayloadFromEdit(editItem);
      const selectedDate = new Date(editItem.execution_datum_ui);

      await api.updateMonthlyCosts(monthlycostId, monthlyPayload);

      const followingExecutions = monthlyCostsExecutions.filter(
        (row) =>
          Number(row.monthlycost_id) === Number(monthlycostId) &&
          new Date(row.execution_datum) >= selectedDate,
      );

      await Promise.all(
        followingExecutions.map((row) =>
          api.updateMonthlyCostsExecution(row.id, {
            ...executionPayload,
            execution_datum: `${toDateInput(row.execution_datum)}T00:00:00`,
            status: row.status || executionPayload.status,
          }),
        ),
      );

      setMonthlyCosts?.((prev) =>
        prev.map((x) =>
          Number(x.id) === Number(monthlycostId)
            ? { ...x, ...monthlyPayload }
            : x,
        ),
      );
      setOk?.("Eintrag und folgende Termine aktualisiert.");
    }

    closeEdit();
    setMonthlyCostsExecutions?.((prev) => prev);
    loadMonthlyCosts?.();
    loadMonthlyCostsExecutions?.();
  } catch (e) {
    console.error(e);
    setErr?.("Aktualisieren fehlgeschlagen");
  }
}
