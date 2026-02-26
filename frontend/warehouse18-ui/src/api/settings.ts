export async function getRfidSettings() {
  const r = await fetch("/api/settings/rfid");
  if (!r.ok) throw new Error("Failed to load RFID settings");
  return r.json() as Promise<{ create_movements: boolean }>;
}

export async function setRfidSettings(create_movements: boolean) {
  const r = await fetch("/api/settings/rfid", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ create_movements }),
  });
  if (!r.ok) throw new Error("Failed to update RFID settings");
  return r.json() as Promise<{ create_movements: boolean }>;
}