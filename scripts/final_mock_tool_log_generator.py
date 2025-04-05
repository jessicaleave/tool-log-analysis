
import pandas as pd
import random
from datetime import datetime, timedelta

# -------------------------------
# Parameters
# -------------------------------
tool_ids = [f'TOOL_{i:03}' for i in range(1, 13)]
start_date = datetime(2024, 4, 1)
end_date = datetime(2025, 4, 1)

# -------------------------------
# Step 1: Generate base 2–3 hour slots of Regular Production
# -------------------------------
records = []
for tool_id in tool_ids:
    current_time = start_date
    while current_time < end_date:
        slot_hours = random.choice([2, 3])
        slot_end = current_time + timedelta(hours=slot_hours)
        if slot_end > end_date:
            slot_end = end_date
        records.append({
            "tool_id": tool_id,
            "start_time": current_time,
            "end_time": slot_end,
            "tool_status": "Productive; Regular Production"
        })
        current_time = slot_end
df_mock = pd.DataFrame(records)

# -------------------------------
# Step 2: Inject 24 PMs per tool
# -------------------------------
updated_records = []
for tool_id in tool_ids:
    tool_slots = df_mock[df_mock["tool_id"] == tool_id].reset_index(drop=True)
    total_slots = len(tool_slots)
    interval = total_slots // 24
    pm_indices = [i * interval for i in range(24)]
    for i in pm_indices:
        pm_duration = random.randint(1, 3)
        for j in range(pm_duration):
            idx = i + j
            if idx < total_slots:
                tool_slots.at[idx, "tool_status"] = "Scheduled Downtime; Preventive Maintenance; Bi-Weekly PM"
    updated_records.append(tool_slots)
df_pm_injected = pd.concat(updated_records).sort_values(by=["tool_id", "start_time"]).reset_index(drop=True)

# -------------------------------
# Step 3: Merge consecutive PM slots
# -------------------------------
df_pm_injected["pm_flag"] = (df_pm_injected["tool_status"] == "Scheduled Downtime; Preventive Maintenance; Bi-Weekly PM").astype(int)
df_pm_injected["pm_group"] = (
    (df_pm_injected["tool_id"] != df_pm_injected["tool_id"].shift()) |
    (df_pm_injected["tool_status"] != df_pm_injected["tool_status"].shift())
).cumsum()
df_pm = df_pm_injected[df_pm_injected["pm_flag"] == 1]
df_non_pm = df_pm_injected[df_pm_injected["pm_flag"] == 0]
df_pm_merged = df_pm.groupby(["tool_id", "tool_status", "pm_group"]).agg(
    start_time=("start_time", "min"),
    end_time=("end_time", "max")
).reset_index()
df_combined = pd.concat([
    df_pm_merged[["tool_id", "tool_status", "start_time", "end_time"]],
    df_non_pm[["tool_id", "tool_status", "start_time", "end_time"]]
]).sort_values(by=["tool_id", "start_time"]).reset_index(drop=True)

# -------------------------------
# Step 4: Add 1–2 slots of follow-up after each PM
# -------------------------------
df_with_followup = df_combined.copy()
final_records = []
for tool_id in tool_ids:
    tool_slots = df_with_followup[df_with_followup["tool_id"] == tool_id].reset_index(drop=True)
    for i, row in tool_slots.iterrows():
        if row["tool_status"] == "Scheduled Downtime; Preventive Maintenance; Bi-Weekly PM":
            followup_count = random.randint(1, 2)
            followup_status = random.choice([
                "Productive; Engineering Runs; Post Maintenance Qual",
                "Scheduled Downtime; User Maintenance Delay;"
            ])
            for j in range(1, followup_count + 1):
                idx = i + j
                if idx < len(tool_slots):
                    tool_slots.at[idx, "tool_status"] = followup_status
    final_records.append(tool_slots)
df_pm_followup = pd.concat(final_records).sort_values(by=["tool_id", "start_time"]).reset_index(drop=True)

# -------------------------------
# Step 5: Add 1–2 PM slots after User Maintenance Delay → 
# -------------------------------
records_with_pm_after_user_delay = []
for tool_id in tool_ids:
    tool_slots = df_pm_followup[df_pm_followup["tool_id"] == tool_id].reset_index(drop=True)
    for i, row in tool_slots.iterrows():
        if row["tool_status"] == "Scheduled Downtime; User Maintenance Delay;":
            followup_count = random.randint(1, 2)
            for j in range(1, followup_count + 1):
                idx = i + j
                if idx < len(tool_slots):
                    tool_slots.at[idx, "tool_status"] = "Scheduled Downtime; Preventive Maintenance; Bi-Weekly PM"
    records_with_pm_after_user_delay.append(tool_slots)
df_after_delay_pm = pd.concat(records_with_pm_after_user_delay).sort_values(by=["tool_id", "start_time"]).reset_index(drop=True)

# -------------------------------
# Step 6: Merge same-status blocks (exclude Regular Production)
# -------------------------------
df_after_delay_pm["merge_key"] = (
    (df_after_delay_pm["tool_id"] != df_after_delay_pm["tool_id"].shift()) |
    (df_after_delay_pm["tool_status"] != df_after_delay_pm["tool_status"].shift()) |
    (df_after_delay_pm["tool_status"] == "Productive; Regular Production")
).cumsum()
df_step6_merged = df_after_delay_pm.groupby(["tool_id", "tool_status", "merge_key"]).agg(
    start_time=("start_time", "min"),
    end_time=("end_time", "max")
).reset_index().sort_values(by=["tool_id", "start_time"]).reset_index(drop=True)

# -------------------------------
# Step 7: If previous row is PM and current is Regular → change current to Qual
# -------------------------------
verify_qual = []
for tool_id in tool_ids:
    tool_slots = df_step6_merged[df_step6_merged["tool_id"] == tool_id].reset_index(drop=True)
    pm_mask = tool_slots["tool_status"] == "Scheduled Downtime; Preventive Maintenance; Bi-Weekly PM"
    regular_mask = tool_slots["tool_status"] == "Productive; Regular Production"
    pm_before = pm_mask.shift(1, fill_value=False)
    to_replace = pm_before & regular_mask
    tool_slots.loc[to_replace, "tool_status"] = "Productive; Engineering Runs; Post Maintenance Qual"
    verify_qual.append(tool_slots)
df_verify_qual = pd.concat(verify_qual).sort_values(by=["tool_id", "start_time"]).reset_index(drop=True)

# -------------------------------
# Step 8: Inject 600 sets of Unscheduled Downtime (Repair + Qual)
# -------------------------------
df_unscheduled = df_verify_qual.copy().reset_index(drop=True)
candidates = []
for i in range(len(df_unscheduled) - 2):
    s1 = df_unscheduled.loc[i, "tool_status"]
    s2 = df_unscheduled.loc[i + 1, "tool_status"]
    s3 = df_unscheduled.loc[i + 2, "tool_status"]
    if s1 == s2 == s3 == "Productive; Regular Production":
        candidates.append([i, i + 1, i + 2])
selected_sets = random.sample(candidates, 600)
used_indices = set()
for idx_set in selected_sets:
    if any(idx in used_indices for idx in idx_set):
        continue
    repair_count = random.randint(1, 2)
    repair_idxs = idx_set[:repair_count]
    qual_idxs = idx_set[repair_count:]
    df_unscheduled.loc[repair_idxs, "tool_status"] = "Unscheduled Downtime; Repair; Repair - Repair"
    df_unscheduled.loc[qual_idxs, "tool_status"] = "Productive; Engineering Runs; Post Maintenance Qual"
    used_indices.update(idx_set)

# -------------------------------
# Step 9: Merge same-status again (exclude Regular Production)
# -------------------------------
df_unscheduled["merge_key"] = (
    (df_unscheduled["tool_id"] != df_unscheduled["tool_id"].shift()) |
    (df_unscheduled["tool_status"] != df_unscheduled["tool_status"].shift()) |
    (df_unscheduled["tool_status"] == "Productive; Regular Production")
).cumsum()
df_step9_merged = df_unscheduled.groupby(["tool_id", "tool_status", "merge_key"]).agg(
    start_time=("start_time", "min"),
    end_time=("end_time", "max")
).reset_index().sort_values(by=["tool_id", "start_time"]).reset_index(drop=True)

# -------------------------------
# Step 10: add 200 User Maintenance Delay before Repair 
# -------------------------------
df_step10 = df_step9_merged.copy().reset_index(drop=True)
repair_rows = df_step10[df_step10["tool_status"] == "Unscheduled Downtime; Repair; Repair - Repair"].reset_index()
selected_repairs = repair_rows.sample(n=200, random_state=42).reset_index(drop=True)
for _, row in selected_repairs.iterrows():
    idx = row["index"]
    if idx > 0 and df_step10.loc[idx - 1, "tool_status"] == "Productive; Regular Production":
        df_step10.loc[idx - 1, "tool_status"] = "Unscheduled Downtime; User Maintenance Delay"

# -------------------------------
# Step 11: add 10 sets of (Supplier Delay + Repair + Qual) between July and Oct for each tool
# -------------------------------
df_step11 = df_step10.copy().reset_index(drop=True)
for tool_id in tool_ids:
    tool_df = df_step11[(df_step11["tool_id"] == tool_id) &
                        (df_step11["start_time"] >= "2024-07-01") &
                        (df_step11["start_time"] < "2024-11-01")].reset_index()
    candidate_sets = []
    for i in range(len(tool_df) - 5):
        group = tool_df.loc[i:i+5]
        if all(group["tool_status"] == "Productive; Regular Production"):
            candidate_sets.append(group["index"].tolist())
    selected_sets = candidate_sets[:10]
    modified_indices = set()
    for slot_group in selected_sets:
        if any(idx in modified_indices for idx in slot_group):
            continue
        supplier_count = random.randint(2, 3)
        qual_count = random.randint(1, 2)
        supplier_idxs = slot_group[:supplier_count]
        qual_idxs = slot_group[-qual_count:]
        remaining_idxs = [idx for idx in slot_group if idx not in supplier_idxs + qual_idxs]
        for idx in supplier_idxs:
            df_step11.loc[idx, "tool_status"] = "Unscheduled Downtime; Supplier Maintenance Delay; Waiting for Parts (Vendor)"
        for idx in qual_idxs:
            df_step11.loc[idx, "tool_status"] = "Productive; Engineering Runs; Post Maintenance Qual"
        for idx in remaining_idxs:
            df_step11.loc[idx, "tool_status"] = "Unscheduled Downtime; Repair; Repair - Repair"
        modified_indices.update(slot_group)

# -------------------------------
# Step 12: random change 1600 Regular production to Engineering time or Standby
# -------------------------------
df_step12 = df_step11.copy()
regular_slots = df_step12[df_step12["tool_status"] == "Productive; Regular Production"]
selected_regular = regular_slots.sample(n=1600, random_state=42)
replacement_options = [
    "Productive; Engineering Runs; Holding for Priority Lot",
    "Productive; Engineering Runs; Processing - Do Not Reload",
    "Productive; Engineering Runs; Service Routine - Do Not Reload",
    "Standby; No Operator; Waiting For Carrier Delivery/Pickup",
    "Standby; No Product"
]
df_step12.loc[selected_regular.index, "tool_status"] = [
    random.choice(replacement_options) for _ in range(len(selected_regular))
]

df_step12.to_csv("mock_tool_log_final.csv", index=False)
