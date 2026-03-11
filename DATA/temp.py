import pandas as pd

# csv = "station_summary.csv"
# df = pd.read_csv(csv)
# no_issue = df[df["issue"] == "No"]
# ss_issue = df[df["issue"] == "Station Stopped"]
# nod_issue = df[df["issue"] == "Not enough data"]
# c_issue = df[df["issue"] == "Coverage"]

# print("No", len(no_issue))
# print("Stopped", len(ss_issue))
# print("Not enough", len(nod_issue))
# print("Coverage", len(c_issue))
# print(len(df), (len(no_issue) + len(ss_issue) + len(nod_issue) + len(c_issue)))


new_csv = "combine_data.csv"
new_df = pd.read_csv(new_csv)
print("total", len(new_df))

temp1 = new_df[new_df["evapotranspiration(mm)"] == " "]
print("empty evapotranspiration", len(temp1))

temp2 = new_df[new_df["rain(mm)"] == " "]
print("empty rain", len(temp2))

temp3 = new_df[new_df["maximum temperature(°C)"] == " "]
print("empty maximum temperature(¬∞C)", len(temp3))

temp4 = new_df[new_df["minimum temperature(°C)"] == " "]
print("empty minimum temperature(¬∞C)", len(temp4))

temp5 = new_df[new_df["maximum relative humidity(%)"] == " "]
print("empty maximum relative humidity(%)", len(temp5))

temp6 = new_df[new_df["minimum relative humidity(%)"] == " "]
print("empty minimum relative humidity(%)", len(temp6))

temp7 = new_df[new_df["average 10m wind speed(m/sec)"] == " "]
print("empty average 10m wind speed(m/sec)", len(temp7))